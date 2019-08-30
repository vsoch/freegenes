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

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename

        # Columns headers for plate wells
        columns = ['plate_name', 'plate_type', 
                   'well_address', 'part_name',
                   'part_gene_id', 'sample_evidence',
                   'part_sequence']

        writer = csv.writer(response)
        writer.writerow(columns)
 
        # Add each well to the csv
        for well in plate.wells.all():

            # We get the part via the associated sample
            sample = well.sample_wells.first()
            writer.writerow([plate.name,
                             plate.plate_type,
                             well.address,
                             sample.part.name,
                             sample.part.gene_id,
                             sample.evidence,
                             sample.part.synthesized_sequence])

        return response

    except Plate.DoesNotExist:
        pass
