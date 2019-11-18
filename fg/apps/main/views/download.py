'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render 
from django.http import Http404, HttpResponse
from django.views.generic import View
from ratelimit.decorators import ratelimit

from fg.apps.orders.models import Order
from fg.apps.main.models import (
    Distribution,
    Plate,
    PlateSet,
)

from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

from datetime import datetime
import json
import os
import csv

## Download and Export

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def download_mta(request, uuid):
    '''download an MTA from the server, only available to admin and staff.
       The uuid is for an order, since we render the link from the order page.
    '''

    # Staff or admin is required to download, as MTA isn't exposed via URL
    if request.user.is_staff or request.user.is_superuser:

        # Do we find the associated order?
        try:
            order = Order.objects.get(uuid=uuid)
        except Order.DoesNotExist:
            raise Http404

        # Stream the file to download if the mta exists
        if order.material_transfer_agreement:
            file_path = order.material_transfer_agreement.agreement_file.path
            if os.path.exists(file_path):
                _, ext = os.path.splitext(file_path)
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/%s" % ext.strip('.'))
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response

        # No MTA for this order
        messages.warning(request, "That order doesn't have a material transfer agreement.")

    raise Http404


def generate_plate_csv(plates, filename, content_type='text/csv'):
    '''a helper function to generate a csv file for one or more plates.
       a filename be provided for the csv writer from the 
       calling view. A HttpResponse is returned.

       Parameters
       ==========
       plates: a list of plates to include (can be from a plateset, a single
               plate, or a distribution)
       filename: the complete filename to download to
       content_type: the content type (defaults to text/csv)
    '''
    response = HttpResponse(content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    # Columns headers for plate wells
    columns = ['plate_name', 'plate_type', 'plate_form',
               'well_address', 'well_media', 'well_volume', 
               'part_name', 'part_gene_id',
               'sample_evidence', 'sample_status',
               'part_full_sequence', 'part_sequence',
               'part_description', 'part_author']

    writer = csv.writer(response)
    writer.writerow(columns)

    for plate in plates:
 
        # Add each well to the csv
        for well in plate.wells.all():

            # We get the part via the associated sample
            sample = well.sample_wells.first()
            part_description = sample.part.description or "" # can be None
            writer.writerow([plate.name,
                             plate.plate_type,
                             plate.plate_form,
                             well.address,
                             well.media,
                             well.volume,
                             sample.part.name,
                             sample.part.gene_id,
                             sample.evidence,
                             sample.status,
                             sample.part.full_sequence,
                             sample.part.optimized_sequence,
                             part_description.replace(',', ' '),
                             sample.part.author.name])

    return response


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def download_plate_csv(request, uuid):
    '''generate a response to write a csv for some number of plates (all plates,
       or a plateset) to return via a download view.
    '''
    try:
        plate = Plate.objects.get(uuid=uuid)

        # Add the date, number of wells
        filename = "freegenes-plate-%s-wells-%s.csv" %(datetime.now().strftime('%Y-%m-%d'),
                                                       plate.wells.count())
        return generate_plate_csv([plate], filename)

    except Plate.DoesNotExist:
        pass


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def download_plateset_csv(request, uuid):
    '''generate a csv for an entire (single) plateset. This means that if plates
       are defined for it, we return the first plate as a representative one.
       See https://github.com/vsoch/freegenes/issues/109#issuecomment-548831927
    '''
    try:
        plateset = PlateSet.objects.get(uuid=uuid)
        filename = "freegenes-plateset-%s-plates-%s.csv" %(datetime.now().strftime('%Y-%m-%d'),
                                                           plateset.plates.count())

        if plateset.plates.count() > 0:
            return generate_plate_csv([plateset.plates.first()], filename)

        # No plates returns an empty csv
        return generate_plate_csv([], filename)

    except PlateSet.DoesNotExist:
        pass


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def download_distribution_csv(request, uuid):
    '''generate a csv for an entire distribution (more than one plateset).
       Akin to the plateset download, we only return a single representative
       plate per plateset (only_first is set to True)
    '''
    try:
        dist = Distribution.objects.get(uuid=uuid)
        filename = "freegenes-distribution-%s-%s.csv" %(dist.name.replace(' ', '-').lower(),
                                                        datetime.now().strftime('%Y-%m-%d'))

        return generate_plate_csv(dist.get_plates(only_first=True), filename)

    except Distribution.DoesNotExist:
        pass


# Json Export

def generate_plate_json(plates, distribution=None, plateset=None):
    '''An export is distinguished from a download in that it's intended to 
       download all fields and associated models relevant to a Plate model,
       with the main intention to import it into another Bionet Server node.
       We export all fields (including uuid) so a plate in one node can be
       linked to the "same plate" in another. We don't export container,
       as that will vary by lab.

       Parameters
       ==========
       plates: a list of plates to include (can be from a plateset, a single
               plate, or a distribution)
       distribution: if provided, add the distribution to each plate.
       plateset: if provided, include with distribution (to add plate to)
    '''
    from fg.apps.api.urls.serializers import (
        AuthorSerializer,
        DistributionSerializer,
        PlateSerializer, 
        PlateSetSerializer,
        SampleSerializer,
        PartSerializer,
        TagSerializer,
        WellSerializer
    )

    # Export as one json dump, a list of plates
    data = []
 
    for plate in plates:

        # We can get far with the plate serializer, and then update objects
        entry = PlateSerializer(plate).data
        wells = [] 

        # We can optionally include distribution and plateset, or just plateset
        dist = None
        pset = None

        # Flattening out, will be represented under plate
        if plateset is not None:
            pset = PlateSetSerializer(plateset).data
            pset['plates'] = []

        # Distribution cannot be import without plateset
        if distribution is not None and plateset is not None:
            dist = DistributionSerializer(distribution).data
            dist['platesets'] = []

        # Add each well to the csv
        for well in plate.wells.all():

            # We get the part via the associated sample
            sample = well.sample_wells.first()
            author_tags = [TagSerializer(t).data for t in sample.part.author.tags.all()]
            author = AuthorSerializer(sample.part.author).data
            author['tags'] = author_tags
            tags = [TagSerializer(t).data for t in sample.part.tags.all()]
            part = PartSerializer(sample.part).data
            sample = SampleSerializer(sample).data
            
            # Remove reverse relationship of Sample.wells
            del sample['wells']
 
            # Create recursive loop of death to get list of all samples derived from
            derived_from = sample['derived_from']
            derived_froms = None
            if derived_from is not None:
                derived_froms = []
                while derived_from is not None:
                    next_sample = Sample.objects.get(uuid=derived_from)
                    next_sample = SampleSerializer(next_sample).data
                    next_sample['part'] = str(next_sample['part'])
                    derived_from = next_sample['derived_from']
                    next_sample['derived_from'] = None
                    del next_sample['wells']
                    derived_froms.append(next_sample)

            # part, should have uuids
            sample["part"] = str(sample["part"])

            # Update part tags, author, add part to the sample, sample to well
            part['tags'] = tags
            part['author'] = author
            part['collections'] = []
            sample['part'] = part             
            sample['derived_from'] = derived_froms
            well = WellSerializer(well).data
            well['sample'] = sample
            wells.append(well)

        # Add the wells back to the plate, remove container and protocol
        plate = PlateSerializer(plate).data
        plate['wells'] = wells
        plate['container'] = None
        plate['protocol'] = None
        plate['plateset'] = pset
        plate['distribution'] = dist
        data.append(plate)

    return data

def generate_plate_json_response(plates, filename, distribution=None, plateset=None, content_type='application/json'):
    '''a wrapper to generate the response, in case we need to modify the data

       Parameters
       ==========
       plates: a list of plates to include (can be from a plateset, a single
               plate, or a distribution)
       filename: the complete filename to download to
       content_type: the content type (defaults to application/json)
       distribution: if provided, add the distribution to each plate.
       plateset: if provided, include with distribution (to add plate to)
    '''
    data = generate_plate_json(plates, distribution, plateset)
    response = HttpResponse(json.dumps(data, indent=4), content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    return response


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def export_plate_json(request, uuid):
    '''export json for a single plate'''
    try:
        plate = Plate.objects.get(uuid=uuid)

        # Add the date, number of wells
        filename = "freegenes-plate-%s-wells-%s.json" %(datetime.now().strftime('%Y-%m-%d'),
                                                       plate.wells.count())
        return generate_plate_json_response([plate], filename)
    except Plate.DoesNotExist:
        pass


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def export_plateset_json(request, uuid):
    '''export json for a plateset (all plates)'''
    try:

        plateset = PlateSet.objects.get(uuid=uuid)
        filename = "freegenes-plateset-%s-plates-%s.json" %(datetime.now().strftime('%Y-%m-%d'),
                                                           plateset.plates.count())

        if plateset.plates.count() > 0:
            return generate_plate_json_response(plateset.plates.all(), plateset=plateset, filename=filename)

        # No plates returns an empty csv
        return generate_plate_json([], filename)

    except PlateSet.DoesNotExist:
        pass


# Distribution export requires selection of plates


class DistributionExportView(View):
    '''select a particular number of plates to export from a distribution.
    '''

    def get(self, *args, **kwargs):
        '''view to select original plates
        '''
        try:
            dist = Distribution.objects.get(uuid=kwargs.get('uuid'))
        except Distribution.DoesNotExist:
            raise Http404
            
        context = {'distribution': dist}
        return render(self.request, "export/export_distribution.html", context)

    def post(self, *args, **kwargs):
        '''Finish the export of the distribution, including some subset of plates
        '''
        try:
            dist = Distribution.objects.get(uuid=kwargs.get('uuid'))

            # We have to pair each plate with its plateset to import properly
            # [[uuid,plateset],[uuid,plateset]...]
            plate_ids = self.request.POST.getlist('plate_ids', [])
            plate_ids = [x.replace('plate_id', '').split('||') for x in plate_ids]

            # Retrieve corresponding plates
            data = []
            for plate_id_set in plate_ids:
                plate_id, plateset_id = plate_id_set
                plate = Plate.objects.get(uuid=plate_id)
                plateset = PlateSet.objects.get(uuid=plateset_id)            
                data += generate_plate_json([plate], dist, plateset)

            filename = "freegenes-distribution-plates-%s-%s.json" %(dist.name.replace(' ', '-').lower(),
                                                                    datetime.now().strftime('%Y-%m-%d'))

            response = HttpResponse(json.dumps(data, indent=4), content_type="application/json")
            response['Content-Disposition'] = 'attachment; filename="%s"' % filename
            return response

        except Distribution.DoesNotExist:
            message.error(self.request, 'That distribution does not exist.')
            return redirect('dashboard')


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def export_distribution_json(request, uuid):
    '''generate a json export for an entire distribution (include all plates)
    '''
    try:
        dist = Distribution.objects.get(uuid=uuid)

    except Distribution.DoesNotExist:
        pass
