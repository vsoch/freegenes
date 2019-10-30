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
from django.shortcuts import render, redirect
from django.views.generic import View
from django.utils import timezone
from fg.apps.orders.forms import (
    ShippingForm
)

from fg.apps.orders.models import Order
from fg.apps.main.models import Distribution
from ratelimit.decorators import ratelimit
from fg.settings import (
    NODE_INSTITUTION,
    HELP_CONTACT_EMAIL,
    HELP_CONTACT_PHONE,
    SHIPPO_TOKEN,
    SHIPPO_CUSTOMER_REFERENCE,
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

from collections import OrderedDict
from operator import getitem

from datetime import datetime
import shippo
import requests

# Default parcel dimensions

parcel_default = {
    "length": "5",
    "width": "5",
    "height": "5",
    "distance_unit": "in",
    "weight": "2",
    "mass_unit": "lb"
}


class ShippingView(View):
    '''Checkout a cart, meaning finishing up an order and placing it. We check
       for the MTA, along with ensuring that the order exists, period.
    '''

    @ratelimit(key='ip', rate=rl_rate, block=rl_block, method="GET")
    def get(self, *args, **kwargs):
        '''create a shipment for a given order

           Parameters
           ==========
           uuid: the unique ID for the order, must exist.
        '''
        if not self.request.user.is_staff or not self.request.user.is_superuser:
            messages.warning(self.request, "You don't have permission to see this view.")
            return redirect('catalog_view')

        try:
            order = Order.objects.get(uuid=kwargs.get('uuid'))
        except Order.DoesNotExist:
            raise Http404
            
        # If no MTA, redirect back to the order page with instructions to get it
        if not order.material_transfer_agreement:
            messages.warning(self.request, "This order needs an MTA before proceeding.")
            return redirect('order_details', uuid=str(order.uuid))
 
        form = ShippingForm()
        context = {
            'form': form,
            'order': order
        }
        return render(self.request, "shipping/create.html", context)

    @ratelimit(key='ip', rate=rl_rate, block=rl_block, method="POST")
    def post(self, *args, **kwargs):
        '''Create the shipment from the order page.

           Parameters
           ==========
           uuid: the unique identifier for the order, must exist
        '''
        form = ShippingForm(self.request.POST or None)
        try:
            order = Order.objects.get(uuid=kwargs.get('uuid'))

            # If the form is valid, return that the shipment was created
            if form.is_valid():

                # Get cleaned form data
                data = form.cleaned_data
                print(data)

                data['shipping_email'] = self.request.user.email
                addresses = create_addresses(data)
                print(addresses)
 
                # Ensure that ice weight is greater than parcel weight
                if data.get('dryice_options', 'No') != 'No':
                    dryice_weight = data.get('dryice_options')
                    parcel_weight = data.get('parcel_weight', parcel_default['weight'])                
                    if float(parcel_weight) < float(dryice_weight):
                        messages.info(self.request, "Parcel weight must be greater than dry ice weight") 
                        return redirect('create_shipment', uuid=str(order.uuid))

                # Ensure that both addresses are valid
                for address_type, address_data in addresses.items():
                    if not address_data['validation_results']['is_valid']:
                        messages.info(self.request, address_data) 
                        return redirect('create_shipment', uuid=str(order.uuid))

                # Create the shipment, return to view
                shipment = create_shipment(addresses, data)
                print(shipment)
                context = {"shipment": shipment, "order": order}
                return render(self.request, "shipping/created.html", context)

            # Otherwise, return form again.
            context = {
                'form': form,
                'order': order
            }
            return render(self.request, "shipping/create.html", context)

        except Order.DoesNotExist:                
            message.error(self.request, 'That order does not exist.')
            return redirect('orders')


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def mark_as_shipped(request, uuid):
    '''mark an order as shipped.
    '''
    try:
        order = Order.objects.get(uuid=uuid)
    except Order.DoesNotExist:
        raise Http404
    order.date_shipped = timezone.now()
    order.save()
    return redirect('dashboard')



class ImportShippoView(View):
    '''Import an order id from Shippo, but only if it's not in the system yet.
       Since we can't reliably look up a transaction (and then label) based 
       on a shipment, here we ask the user to provide the tracking and
       label url for us, and we populate artificial objects.
    '''

    @ratelimit(key='ip', rate=rl_rate, block=rl_block, method="GET")
    def get(self, *args, **kwargs):
        '''return base page with form to select an order to import
        '''
        if not self.request.user.is_staff or not self.request.user.is_superuser:
            messages.warning(self.request, "You don't have permission to see this view.")
            return redirect('catalog_view')

        # Get all current shipments
        shipments = get_shippo_shipments()

        # Get set of shipments we currently have as orders
        haves = set()
        for order in Order.objects.all():
  
            # These should be the same
            haves.add(order.label.get('object_id'))
            haves.add(order.transaction.get('object_id'))

        haves.remove(None)

        results = {}
        for s in shipments:
            if s['object_id'] not in haves and s['status'] == "SUCCESS" and not s['test'] and s.get('order') is not None:
                results[s['object_id']] = {"name": s['address_to']['name'],
                                           "address": s['address_to']['street1'],
                                           "created": s['object_created']}

        # Sort by date
        results = OrderedDict(sorted(results.items(), 
                              key = lambda x: getitem(x[1], 'created'), reverse=True))

        # Add distributions
        context = {'shipments': results,
                   'distributions': Distribution.objects.all()}

        return render(self.request, "shipping/import_shippo.html", context)


    @ratelimit(key='ip', rate=rl_rate, block=rl_block, method="POST")
    def post(self, *args, **kwargs):
        '''Receive the post with the shipment id to import.
        '''
        selected = self.request.POST.get('select_order')
        order_name = self.request.POST.get("order_name")
        order_label = self.request.POST.get("order_label")
        order_tracking = self.request.POST.get("order_tracking")
        dist_ids = self.request.POST.get("dist_ids")

        # Single selection will just return one
        if not isinstance(dist_ids, list):
            dist_ids = [dist_ids]

        print(dist_ids)
        print(order_name)
        print(selected)

        distributions = Distribution.objects.filter(uuid__in=dist_ids)

        if selected and order_name and order_label and order_tracking:
            print('selected order is %s' % selected)
            shipment = shippo.Shipment.retrieve(object_id=selected, api_key=SHIPPO_TOKEN)

            # Confirm that both links work
            for url in [order_label, order_tracking]:
                response = requests.get(url)
                if not response.status_code == 200:
                    messages.info(self.request, "%s returned invalid response, %s" %(url, response.status_code))
                    return render(self.request, "shipping/import_shippo.html", context)

            # **Here we weren't able to look up label or transaction
            label = {'test': False, 
                     'status': 'SUCCESS',
                     'messages': [],
                     'metadata': '',
                     'label_url': order_label,
                     'object_owner': HELP_CONTACT_EMAIL,
                     'object_state': "VALID",
                     'tracking_url_provider': order_tracking,
                     'commercial_invoice_url': None,
                     'bionode_notes': 'This is an artificially created label'}

            # Generate the order
            order = Order.objects.create(name=order_name,
                                         user=self.request.user,
                                         date_ordered=convert_time(shipment['object_created']),
                                         date_shipped=convert_time(shipment['shipment_date']),
                                         ordered=True,
                                         received=True,
                                         label=label,
                                         transaction={'eta': None})

            # Add distributions
            for dist in distributions:
                order.distributions.add(dist)

            # redundant
            order.save()
            messages.info(self.request, "Order imported successfully")
            return redirect('order_details', uuid=str(order.uuid))
            
        messages.info(self.request, "You need to provide all valid fields on the form.")
        return render(self.request, "shipping/import_shippo.html", context)


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def create_transaction(request, uuid):
    '''we receive the response from the ShippingView, and create the transaction
       here. The order id is again the only required argument to save the transaction
       id with it, and the only thing we need for the Shippo API is the rate_id
       that was chosen, which already is associated with the particular parcel.
    '''
    try:
        order = Order.objects.get(uuid=uuid)
    except Order.DoesNotExist:
        raise Http404

    # Only staff, admins, and order owners can see
    if not request.user.is_staff and not request.user.is_superuser and not request.user == order.owner:
        messages.info(request, "This operation is not permitted")
        return redirect("orders")

    # A post indicates creating the transaction
    if request.method == "POST":

        rate_id = request.POST.get('select_provider')

        # Create the transaction
        transaction = shippo.Transaction.create(rate=rate_id,
                                                label_file_type="PDF",
                                                api_key=SHIPPO_TOKEN)

        # Save the transaction object
        order.add_transaction(transaction)

        if transaction['object_state'] != 'VALID':
            messages.info(request, 'There was an error creating that transaction.')
            return redirect('order_details', uuid=str(order.uuid))

        # There is some delay to create the label, so we make the user wait

    # A get is viewing a previous transaction, if it exists.
    return render(request, "shipping/transaction.html", {'order': order})


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def create_label(request, uuid):
    '''The shipment takes a small delay to process the transaction, so we
       first direct the user to the transaction page, and (given that the label
       is not generated) require them to push a button to generate it.
    '''
    try:
        # An order cannot be already processed (received is True)
        order = Order.objects.get(uuid=uuid)
    except Order.DoesNotExist:
        raise Http404

    if not order.label:

        # If we are successful, we can retrieve the shipping label
        label = shippo.Transaction.retrieve(order.transaction['object_id'], 
                                            api_key=SHIPPO_TOKEN)
        order.add_label(label)

        # Received flag indicates it was processed
        order.received = True
        order.save()

    # A get is viewing a previous transaction, if it exists.
    return render(request, "shipping/transaction.html", {'order': order})


# Helper Functions

def get_shippo_shipments():
    '''use the Shippo API to retrieve all (paginated) shipments
    '''
    url = "https://api.goshippo.com/v1/shipments/?results=25"
    return get_shippo_paginate(url)


def get_shippo_transactions():
    '''use the Shippo API to retrieve all (paginated) transactions
    '''
    url = "https://api.goshippo.com/v1/transactions/?results=25"
    return get_shippo_paginate(url)


def get_shippo_paginate(url):
    '''use the Shippo API to retrieve all (paginated) items
    '''
    results = []
    headers = {"Authorization": "ShippoToken %s" % SHIPPO_TOKEN}

    while url is not None:
        result = requests.get(url, headers=headers)
        if result.status_code == 200:
            result = result.json()
            results += result.get('results', [])
            url = result['next']
    return results


def convert_time(timestr):
    '''convert a datetime string to django timezone, we cut out just
       the year, month, date, and timestamp
    '''
    if timestr:
        timestr = timestr[0:19]
        return datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%S")


def create_shipment(addresses, data):
    '''create a shipment using the default parcel dimensions, and the valid
       addresses. The SHIPPO_TOKEN and parcel_default should be import into
       the module. We take again the original input data to see if the user 
       wants dry ice.
    '''
    extra = {}

    # Update the parcel attributes
    for attr in ['length', 'weight', 'height', 'width']:
        parcel_default[attr] = data.get('parcel_%s' % attr, parcel_default[attr])

    # Does the user have a customer reference?
    if SHIPPO_CUSTOMER_REFERENCE:
        extra['reference_1'] = SHIPPO_CUSTOMER_REFERENCE

    # Does the shipment need dry ice?
    if data.get('dryice_options', 'No') != 'No':
        extra['dry_ice'] = {"contains_dry_ice": True, "weight": data.get('dryice_options')}

    shipment = shippo.Shipment.create(
               address_from = addresses["From"],
               address_to = addresses["To"],
               parcels = [parcel_default],
               api_key = SHIPPO_TOKEN,
               extra = extra)

    # Important! Shippo's create API only returns 3 rates, usually wrong.
    rates = shippo.Shipment.get_rates(shipment.object_id, api_key=SHIPPO_TOKEN)['results']
    shipment['rates'] = rates
    return shipment


def create_addresses(data):
    '''create a shipment, where data is the cleaned data from the ShippingForm.
       If the shipment contains dry ice, the default weight is set to 2 (not
       sure what this means). We assume the country to be US.

       Parameters
       ==========
       data: the form.cleaned_data, expected to include:
	{'shipping_to': 'Mr. Bigglesworth',
	 'shipping_address': '2000 Campus Drive',
	 'shipping_zip': '94305',
         'shipping_state': "CA",
         'shipping_city': "Palo Alto",
	 'from_name': 'Dinosaur Labs',
	 'from_address': '2128 Roaring Ave Apt 410',
	 'from_zip': '12345',
	 'dryice_options': 'Yes'}
    '''
    # Create the address - it must be valid
    address_from = shippo.Address.create(
        name = data.get('from_name'),
        company = NODE_INSTITUTION,
        street1 = data.get('from_address'),
        street2 = data.get('from_address2'),
        state = data.get('from_state'),
        city = data.get('from_city'),
        zip = data.get('from_zip'),
        phone = HELP_CONTACT_PHONE,
        api_key=SHIPPO_TOKEN,
        country = "US", 
        email = HELP_CONTACT_EMAIL,
        validate = True
    )
    
    address_to = shippo.Address.create(
        name = data.get('shipping_to'),
        street1 = data.get('shipping_address'),
        street2 = data.get('shipping_address2'),
        state = data.get('shipping_state'),
        city = data.get('shipping_city'),
        zip = data.get('shipping_zip'),
        phone = data.get('shipping_phone'),
        api_key=SHIPPO_TOKEN,
        country = "US", 
        email = data.get('shipping_email'),
        validate = True
    )

    # Enforce that address is residential
    address_from['is_residential'] = False    
    address_to['is_residential'] = False    

    return {'To': address_to,
            'From': address_from}
