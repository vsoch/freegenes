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
from django.shortcuts import render
from django.shortcuts import redirect
from fg.apps.factory.models import FactoryOrder
from fg.apps.factory.forms import UploadFactoryPlateJsonForm
from fg.apps.factory.utils import read_json

from ratelimit.decorators import ratelimit
from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

import json
import uuid

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def factory_view(request):
    '''Show different factory operations to the user, including importing
       and managing orders from twist
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    orders = FactoryOrder.objects.all()
    return render(request, 'factory/incoming.html', {"orders": orders})

# Parts Tables

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def view_factoryorder_parts_completed(request, uuid):
    return view_factoryorder_parts(request, uuid, subset="completed")

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def view_factoryorder_parts_failed(request, uuid):
    return view_factoryorder_parts(request, uuid, subset="failed")

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def view_factoryorder_parts(request, uuid, subset=None):
    '''Given a unique ID for a factory order, show a table of parts 
       associated. This view is linked from the main factory page.
       If subset is set to be "failed" or "completed" we filter a subset
       of the parts.
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    try:
        order = FactoryOrder.objects.get(uuid=uuid)
    except FactoryOrder.DoesNotExist:
        messages.info(request, "This factory order does not exist.")
        return redirect('factory')

    # Custom filtering of parts
    if subset == "completed":
        parts = order.get_completed_parts()
    elif subset == "failed":
        parts = order.get_failed_parts()
    else:
        parts = order.parts.all()

    context = {
        "order": order,
        "parts": parts,
        "subset": subset
    }
    return render(request, 'tables/twist_parts.html', context)


# Import Tasks

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def import_factory_plate(request):
    '''An exported plate (json) can be imported here
    '''
    from fg.apps.main.models import Container

    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = UploadFactoryPlateJsonForm(request.POST, request.FILES)
        if form.is_valid():       

            try:            
                container = Container.objects.get(uuid=form.data['container'])
            except Container.DoesNotExist:
                return JsonResponse({"message": "We couldn't find that container."})
                 
            data = read_json(request.FILES['json_file'])
            message = import_plates_task(data, container)
            return JsonResponse({"message": message})

        # Form isn't valid
        else:
            return JsonResponse({"message": form.errors})

    context = {"form": UploadFactoryPlateJsonForm()}
    return render(request, 'factory/factory_plate_import.html', context)


def import_plates_task(data, container):
    '''read in a list of plates from an imported json. The json (to be valid)
       should be a list of plates, each of which has wells, each well
       should have a sample and part.
    '''
    from fg.apps.main.models import (
        Plate, Well, Part, Sample, Author, Tag, Organism, PlateSet, Distribution
    )

    # must be a list
    if not isinstance(data, list):
        return "Invalid file: data must be a list of plates."

    plate_fields = ['uuid', 'plate_type', 'plate_form', 'status', 'name', 
                    'thaw_count', 'notes', 'height', 'length', 
                    'wells', 'plate_vendor_id']

    well_fields = ['uuid', 'address', 'volume', 'quantity', 'media', 'organism', 'sample']

    sample_fields = ['uuid', 'outside_collaborator', 'sample_type', 'status',
                     'evidence', 'vendor', 'part', 'index_forward', 'index_reverse']

    part_fields = ['uuid', 'name', 'description', 'status', 'gene_id', 'part_type', 
                   'genbank', 'original_sequence', 'optimized_sequence', 
                   'synthesized_sequence', 'full_sequence', 'vector', 
                   'primer_forward', 'primer_reverse', 'barcode', 
                   'translation', 'tags', 'collections', 'author']

    author_fields = ['uuid', 'name', 'email', 'affiliation', 'orcid', 'tags']

    # Optional imports
    plateset_fields = ['uuid', 'description', 'name']
    distribution_fields = ['uuid', 'name', 'description']

    print("Found %s contender plates" % len(data))

    # First validate all required - don't do any import if something is wrong
    for entry in data:
 
        # Ensure all plate fields present
        if not set(plate_fields).issubset(entry.keys()):
            return "Each plate must have fields %s" % ", ".join(plate_fields)

        # Plateset and Distribution (optional)
        if entry['plateset'] is not None:
            if not set(plateset_fields).issubset(entry['plateset'].keys()):
                return "Each defined plateset must have fields %s" % ", ".join(plateset_fields)

        if entry['distribution'] is not None:
            if not set(distribution_fields).issubset(entry['distribution'].keys()):
                return "Each defined distribution must have fields %s" % ", ".join(plateset_fields)

        # Cannot import distribution without plateset
        if entry['distribution'] is not None and entry['plateset'] is None:
            return "You cannot import a plate distribution without a plateset."

        for well in entry['wells']:

            # Well fields
            if not set(well_fields).issubset(well.keys()):
                return "Each well must have fields %s" % ", ".join(well_fields)

            # Sample fields
            if not set(sample_fields).issubset(well['sample'].keys()):
                return "Each sample must have fields %s" % ", ".join(sample_fields)

            # Part fields
            if not set(part_fields).issubset(well['sample']['part'].keys()):
                return "Each part must have fields %s" % ", ".join(part_fields)

            # Author fields
            if not set(author_fields).issubset(well['sample']['part']['author'].keys()):
                return "Each author must have fields %s" % ", ".join(author_fields)


    # Keep a count of objects created
    counts = {'plates': 0, 'samples': 0, 'parts': 0, 'tags': 0, 'authors': 0, 
              'wells': 0, 'platesets': 0, 'distributions': 0}

    # Now we can import knowing all data is provided
    for entry in data:
 
        # Only import if it doesn't exist
        try:
            plate = Plate.objects.get(uuid=entry['uuid'])
        except Plate.DoesNotExist:

            # time created and updated aren't included, specific to the node
            counts['plates']+=1  
            plate = Plate.objects.create(uuid=uuid.UUID(entry['uuid']),
                                         name=entry['name'],
                                         container=container,
                                         plate_vendor_id=entry['plate_vendor_id'],
                                         plate_type=entry['plate_type'],
                                         plate_form=entry['plate_form'],
                                         height=entry['height'],
                                         length=entry['length'],
                                         status=entry['status'],
                                         thaw_count=entry['thaw_count'])

            # If a distribution and plateset are defined
            plateset = None
            if entry['plateset'] is not None:

                psEntry = entry['plateset']
                try:
                    plateset = PlateSet.objects.get(uuid=psEntry['uuid'])
                except PlateSet.DoesNotExist:
                    counts['platesets']+=1
                    plateset = PlateSet.objects.create(uuid=uuid.UUID(psEntry['uuid']),
                                                       description=psEntry['description'],
                                                       name=psEntry['name'])

            # A distribution requires a plateset
            dist = None
            if entry['distribution'] is not None and plateset is not None:

                distEntry = entry['distribution']
                try:
                    dist = Distribution.objects.get(uuid=distEntry['uuid'])
                except Distribution.DoesNotExist:
                    counts['distributions']+=1
                    dist = Distribution.objects.create(uuid=uuid.UUID(distEntry['uuid']),
                                                       description=distEntry['description'],
                                                       name=distEntry['name'])

            # Create each well
            for wellEntry in entry['wells']:
                sampleEntry = wellEntry['sample']
                partEntry = sampleEntry['part']
                authorEntry = partEntry['author']               
                organismEntry = wellEntry['organism']

                # Author is associated with a part                
                try:
                    author = Author.objects.get(uuid=authorEntry['uuid'])
                except Author.DoesNotExist:
                    author = Author.objects.create(uuid=uuid.UUID(authorEntry['uuid']),
                                                   email=authorEntry['email'],
                                                   affiliation=authorEntry['affiliation'],
                                                   orcid=authorEntry['orcid'])

                # Create the Part (retrieve based on gene id, not uuid)
                try:
                    part = Part.objects.get(gene_id=partEntry['gene_id'])
                except Part.DoesNotExist:
                    counts['parts']+=1
                    part = Part.objects.create(uuid=uuid.UUID(partEntry['uuid']),
                                               description=partEntry['description'],
                                               status=partEntry['status'],
                                               original_sequence=partEntry['original_sequence'],
                                               genbank=partEntry['genbank'],
                                               synthesized_sequence=partEntry['synthesized_sequence'],
                                               full_sequence=partEntry['full_sequence'],
                                               vector=partEntry['vector'],
                                               primer_forward=partEntry['primer_forward'],
                                               primer_reverse=partEntry['primer_reverse'],
                                               barcode=partEntry['barcode'],
                                               translation=partEntry['translation'],
                                               author=author)

                # Tags are associated with a part
                for tagEntry in partEntry['tags']:
                    name = tagEntry.get('tag')
                    if name is not None:
                        tag, created = Tag.objects.get_or_create(tag=tagEntry)
                        part.tags.add(tag)
                        if created:
                            counts['tags']+=1

                part.save()

                # Generate the sample (we don't also import derived from)
                sample, created = generate_sample_entry(sampleEntry)
                if created:
                    counts['samples'] +=1

                # Add list of derive froms (oldest ancestor last)
                derived_froms = sampleEntry['derived_from']
                ancestors = []
                while derived_froms:
                    oldest = derived_froms.pop(-1) # use the same part
                    olderSample, created = generate_sample_entry(oldest, part)
                    if created:
                        counts['samples'] +=1
                    ancestors.append(olderSample)

                oldest = ancestors.pop(-1)        
                while len(ancestors) >= 1:
                    second = ancestors.pop(-1)                    
                    second.derived_from = oldest
                    second = oldest

                sample.derived_from = second

                # Organism is associated with a well
                try:
                    organism = Organism.objects.get(uuid=organismEntry['uuid'])
                except Organism.DoesNotExist:
                    counts['organisms']+=1
                    organism = Organism.objects.create(uuid=uuid.UUID(organismEntry['uuid']),
                                                       name=organismEntry['name'],
                                                       description=organismEntry['description'],
                                                       genotype=organismEntry['genotype'])

                # Finally, create the well
                try:
                    well = Well.objects.get(uuid=wellEntry['uuid'])
                except Well.DoesNotExist:
                    counts['wells']+=1
                    well = Well.objects.create(uuid=uuid.UUID(wellEntry['uuid']),
                                               address=wellEntry['address'], 
                                               volume=wellEntry['volume'],
                                               quantity=wellEntry['quantity'],
                                               media=wellEntry['media'],
                                               organism=organism)

                sample.wells.add(well)
                plate.wells.add(well)
                plate.save()
                sample.save()

                # Finally, add the plate to the plateset and plateset to distribution
                if plateset is not None:
                    plateset.plates.add(plate)
                    plateset.save()
                
                if dist is not None:
                    dist.platesets.add(plateset)
                    dist.save()

    return "Imported %s" % json.dumps(counts)


def generate_sample_entry(sampleEntry, part):
    '''generate a sample from an entry
    '''
    created = False
    try:
        sample = Sample.objects.get(uuid=sampleEntry['uuid'])
    except Sample.DoesNotExist:
        created = True
        sample = Sample.objects.create(uuid=uuid.UUID(sampleEntry['uuid']),
                                   outside_collaborator=sampleEntry['outside_collaborator'],
                                   sample_type=sampleEntry['sample_type'],
                                   status=sampleEntry['status'],
                                   evidence=sampleEntry['evidence'],
                                   vendor=sampleEntry['vendor'],
                                   part=part,
                                   index_forward=sampleEntry['index_forward'],
                                   index_reverse=sampleEntry['index_reverse'])
    return sample, created
