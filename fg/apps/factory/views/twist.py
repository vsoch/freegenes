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

from fg.apps.main.models import (
    Container, 
    Plate,
    Well
)

from fg.apps.factory.utils import read_csv
from fg.apps.factory.twist import get_unique_plates
from fg.apps.factory.forms import UploadTwistPlatesForm
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

            # Case 1: First submit means no plate metadata
            if not fields:
                
                # We need to derive the unique plates from the data (uses cache)
                plate_ids = get_unique_plates(rows)
                return JsonResponse({"plate_ids": plate_ids})

            # Case 2: we have the fields! Import the plates
            count = import_plate_task(rows, fields)
            messages.info(request, "You have successfully imported %s plates." % count)
            return redirect('dashboard')

    context = {
        "form": UploadTwistPlatesForm(),
        "containers": Container.objects.all(),
        "plate_forms": Plate.PLATE_FORM
    }

    return render(request, 'twist/import.html', context)

# Tasks

def import_plate_task(rows, fields):
    '''Using the rows (plate map) import plates and wells (physicals) into 
       FreeGenes.

       Parameters
       ==========
       rows: rows from Twist, including the header
       fields: a lookup for plate_(id) and plate_container_(id), e.g.,

        {'plate_pSHPs0625B637913SH': ['name1'], 
         'plate_container_pSHPs0625B637913SH': ['05f2815e-7ff6-42d6-b42a-26d8273b133c'], 
         'plate_length_pSHPs0625B637913SH': ['12'], 
         'plate_height_pSHPs0625B637913SH': ['8'], 
         'plate_form_pSHPs0625B637913SH': ['standard96'],
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
    
    print('RUNNING IMPORT ORDER TASK')
    print("Found %s total entries" % (len(rows) -1))

    # Separate header list 
    headers = rows.pop(0)

    # First create the plates - we need a lookup row for plate metadata
    plate_lookup = dict()
    for row in rows:
        plate_lookup[row[headers.index("Plate ID")]] = row
    
    plate_ids = list(plate_lookup.keys())
    plates = dict()

    # Get plate names in advance
    names = set([row[headers.index("Name")] for row in rows])

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
                print("Missing plate name, skipping plate %s." % plate_od)
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


    # We will only import wells for existing parts
    existing = Part.objects.filter(gene_id__in=names).values_list('gene_id', flat=True)
    
    # Now create the wells, add to their correct plate
    for row in rows:
        name = row[headers.index("Name")]
        plate_id = row[headers.index("Plate ID")]

        # Only import existing parts
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

    # Confirm number of wells per plate
    for plate_id, plate in plates.items():
        print("Added %s wells to plate %s" %(plate.wells.count(), plate.name))
    return len(plates)
