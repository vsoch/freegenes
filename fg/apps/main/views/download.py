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
