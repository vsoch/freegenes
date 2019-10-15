'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    Http404, 
    JsonResponse
)
from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from django.shortcuts import redirect

from fg.apps.factory.models import FactoryOrder
from fg.apps.main.models import (
    Container, 
    Plate,
    Sample,
    Well
)

from fg.apps.factory.utils import read_csv
from fg.apps.factory.twist import get_unique_plates
from fg.apps.factory.forms import (
    UploadTwistPlatesForm,
    UploadTwistPartsForm
)
from ratelimit.decorators import ratelimit
from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

import os

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def twist_import_plates(request):
    '''Show the user a form to import a twist order. Since we don't
       know the number of platesets, this is the original upload of the csv
       file. The server can then parse some of the data, and the
       user's form is updated appropriately.
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = UploadTwistPlatesForm(request.POST, request.FILES)
        if form.is_valid():       

            # We are interested in fields for plate_container and plate
            fields = {k:v for k,v in request.POST.items() if k.startswith('plate')}

            # Read in rows from csv file - the first is the header
            rows = read_csv(fileobj=request.FILES['csv_file'], 
                            delim=form.data['delimiter'])

            # Temporary save to debug import
            import pickle
            pickle.dump(rows, open('rows.pkl', 'wb'))

            # Case 1: First submit means no plate metadata
            if not fields:
                
                # We need to derive the unique plates from the data (uses cache)
                plate_ids = get_unique_plates(rows)
                response = {"plate_ids": plate_ids}

                # If already imported, tell the user
                if len(plate_ids) == 0:
                    response['message'] = "All plates from this sheet have been imported."               

                return JsonResponse(response)

            # The user must also provide a factory order, and on/off generate samples
            factory_order = request.POST.get('factory_order')
            generate_samples = request.POST.get('generate_samples', 'off') == "on"

            # Case 2: we have the fields! Import the plates
            message = import_plate_task(rows=rows, 
                                        fields=fields,
                                        factory_order=factory_order, 
                                        generate_samples=generate_samples)

            messages.info(request, message)
            return redirect('factory')

        # Form isn't valid
        else:
            return JsonResponse({"message": form.errors})

    context = {
        "form": UploadTwistPlatesForm(),
        "containers": Container.objects.all(),
        "plate_forms": Plate.PLATE_FORM
    }

    return render(request, 'twist/import_plates.html', context)


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def twist_import_parts(request):
    '''Show the user a form to import an export of twist parts.
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = UploadTwistPartsForm(request.POST, request.FILES)
        if form.is_valid():       

            # Read in rows from csv file - the first is the header
            rows = read_csv(fileobj=request.FILES['csv_file'], 
                            delim=form.data['delimiter'])

            # The user must also provide a factory order, and on/off generate samples
            factory_order = request.POST.get('factory_order')

            # Case 2: we have the fields! Import the plates
            message = import_parts_task(rows=rows, factory_order=factory_order)
            return JsonResponse({"message": message})

        # Form isn't valid
        else:
            return JsonResponse({"message": form.errors})

    context = {"form": UploadTwistPartsForm()}
    return render(request, 'twist/import_parts.html', context)


def import_parts_task(rows, factory_order):
    '''given a csv with parts, import into a FactoryOrder. If all parts are 
       not represented in the database, we do not add them to the FactoryOrder.

       Parameters
       ==========
       rows: rows from Twist, including the header
       factory_order: should be the uuid of the chosen factory order.

       Headers:
		['Name',
		 'Insertion site name',
		 'Vector name',
		 'Insert length',
		 'Construct length',
		 'Insert sequence',
		 'Construct sequence',
		 'Step',
		 'Shipping est']
    '''
    from fg.apps.main.models import Part
    from fg.apps.users.models import User

    print('RUNNING IMPORT TWIST PARTS TASK')
    print("Found %s total entries" % (len(rows) -1))

    # Separate header list 
    headers = rows.pop(0)

    # Get the Factory Order
    try:
        factory_order = FactoryOrder.objects.get(uuid=factory_order)
    except:
        return "Invalid factory order uuid %s" % factory_order

    # First create the plates - we need a lookup row for plate metadata
    part_lookup = dict()
    for row in rows:
        part_lookup[row[headers.index("Name")]] = row
    
    part_ids = list(part_lookup.keys())
    parts = dict()

    # Get plate names in advance. We are required to have all parts
    names = set([row[headers.index("Name")] for row in rows])
    existing = Part.objects.filter(gene_id__in=names).values_list('gene_id', flat=True)

    # We are required to have all parts represented
    if len(existing) != len(names):
        missing = abs(len(existing) - len(names))
        return "All parts are required for import: missing %s, import cancelled." % missing

    for part_id in part_ids:

        # We are already sure that it exists
        name = part_lookup[part_id][headers.index("Name")]
        part = Part.objects.get(gene_id=name)
        factory_order.parts.add(part)

    factory_order.save()

    return "Successfully added %s parts to %s" %(len(part_ids), factory_order.name)


# Tasks

def import_plate_task(rows, fields, factory_order, generate_samples=False):
    '''Using the rows (plate map) import plates and wells (physicals) into 
       FreeGenes.

       Parameters
       ==========
       rows: rows from Twist, including the header
       fields: a lookup for plate_(id) and plate_container_(id), e.g.,
       factory_order: should be the uuid of the chosen factory order.
       generate_samples: if True, generate samples to correspond with each part.

        {'plate_pSHPs0725B133922SH': 'name1', 
         'plate_container_pSHPs0725B133922SH': 'f8780f18-fe74-4fa3-87ec-1718aa8352e4', 
         'plate_length_pSHPs0725B133922SH': '12', 
         'plate_height_pSHPs0725B133922SH': '8', 
         'plate_form_pSHPs0725B133922SH': 'standard96',
        ...
        } 

        Headers:
		['Name',
		 'Insertion point name',
		 'Vector name',
		 'Insert length',
		 'Construct length',
		 'Insert sequence',
		 'Construct sequence',
		 'Well Location',
		 'Yield',
		 'NGS',
		 'Yield (ng)',
		 'Product type',
		 'Plate ID']
    '''

    from fg.apps.main.models import (Part, Plate, Well)
    from fg.apps.users.models import User
    
    print('RUNNING IMPORT TWIST PLATES TASK')
    print("Found %s total entries" % (len(rows) -1))

    # Separate header list 
    headers = rows.pop(0)

    # Get the Factory Order
    if factory_order:
        try:
            factory_order = FactoryOrder.objects.get(uuid=factory_order)
        except:
            pass

    # First create the plates - we need a lookup row for plate metadata
    plate_lookup = dict()
    for row in rows:
        plate_lookup[row[headers.index("Plate ID")]] = row
    
    plate_ids = list(plate_lookup.keys())
    plates = dict()

    # Get plate names in advance. We are required to have all parts
    names = set([row[headers.index("Name")] for row in rows])
    existing = Part.objects.filter(gene_id__in=names).values_list('gene_id', flat=True)

    # We are required to have all parts represented
    if len(existing) != len(names):
        return "All parts are required to exist for import, import cancelled."

    for plate_id in plate_ids:

        container_id = fields.get("plate_container_%s" % plate_id)  
        plate_name = fields.get("plate_%s" % plate_id)
        plate_length = fields.get("plate_length_%s" % plate_id)
        plate_height = fields.get("plate_height_%s" % plate_id)
        plate_form = fields.get("plate_form_%s" % plate_id)
        product_type = plate_lookup[plate_id][headers.index("Product type")]
 
        # Create the plate if both exist
        if not container_id:
            print("Missing container id, skipping plate %s." % plate_id)
            continue

        container = Container.objects.get(uuid=container_id)

        # Try looking up the plate
        try:
            plate = Plate.objects.get(plate_vendor_id=plate_id)

        # We want to create only if doesn't exist!
        except Plate.DoesNotExist:
            plate = None

            # We can only create with a plate_name and container
            if not plate_name:
                print("Missing plate name, skipping plate %s." % plate_id)
                continue

            if product_type == "Clonal Genes":
                plate = Plate.objects.create(name=plate_name,
                                             container=container,
                                             plate_vendor_id=plate_id,
                                             plate_type="plasmid_plate",
                                             plate_form=plate_form,
                                             height=int(plate_height),
                                             length=int(plate_length),
                                             status="Stocked")

            elif product_type == "Glycerol stock":
                plate = Plate.objects.create(name=plate_name,
                                             container=container,
                                             plate_vendor_id=plate_id,
                                             plate_type="glycerol_stock",
                                             plate_form=plate_form,
                                             height=int(plate_height),
                                             length=int(plate_length),
                                             status="Stocked")

            # Save the object to lookup to add wells to
            if plate:
                plates[plate.plate_vendor_id] = plate
                
                # And if we have a factory order object
                if factory_order:
                    print("Adding %s to %s" %(plate, factory_order))
                    factory_order.plates.add(plate)
                    factory_order.save()

    # Sample lookup will hold samples for this order associated with parts
    samples = dict()    

    # Now create the wells, add to their correct plate
    for row in rows:
        name = row[headers.index("Name")] # gene_id of the part
        plate_id = row[headers.index("Plate ID")]

        # Only import existing parts (they should all exist, per check above)
        if name in existing and plate_id in plates:
 
            product_type = plate_lookup[plate_id][headers.index("Product type")]
            well_location = row[headers.index('Well Location')]
            plate = plates[plate_id]

            well = None
            if product_type == "Glycerol stock":
                well = Well.objects.create(address=well_location,
                                           volume=50,
                                           media="glycerol_lb")

            elif product_type == "Clonal genes":
                quantity = int(row[headers.index("Yield (ng)")])
                well = Well.objects.create(address=well_location,
                                           volume=0, # dried DNA
                                           quantity=quantity)

            if well:
                well.save()
                plate.wells.add(well)
                plate.save()

                # Look up the associated part
                part = Part.objects.get(gene_id=name)

                # Look for a Sample for a Part WITHIN a FactoryOrder
                sample = None
                for plate in factory_order.plates.all():

                   # Look for a sample already associated with plate from the factory order      
                    for plate_well in plate.wells.all():
                        contenders = Sample.objects.filter(wells=plate_well)
                        if contenders.count() > 0:
                            sample = contenders[0]
                            break

                # If we didn't find a sample already associated with the Factory order, create it
                if not sample:
                    sample = Sample.objects.create(vendor=factory_order.vendor.name,
                                                   part=part)
  
                sample.save()
                sample.wells.add(well)
                sample.save()


    # Confirm number of wells per plate
    for plate_id, plate in plates.items():
        print("Added %s wells to plate %s" %(plate.wells.count(), plate.name))
    return "%s plates were imported successfully." % len(plates)
