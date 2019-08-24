'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse
import uuid

################################################################################
# Orders
################################################################################

#/o/	fg.apps.orders.views.HomeView	home
#/o/add-coupon/	fg.apps.orders.views.AddCouponView	add-coupon
#/o/add-to-cart/<slug>/	fg.apps.orders.views.add_to_cart	add-to-cart
#/o/checkout/	fg.apps.orders.views.CheckoutView	checkout
#/o/details/<uuid>/	fg.apps.orders.views.order_details	order_details
#/o/order-summary/	fg.apps.orders.views.OrderSummaryView	order-summary
#/o/payment/<payment_option>/	fg.apps.orders.views.PaymentView	payment
#/o/product/<slug>/	fg.apps.orders.views.ItemDetailView	product
#/o/remove-from-cart/<slug>/	fg.apps.orders.views.remove_from_cart	remove-from-cart
#/o/remove-item-from-cart/<slug>/	fg.apps.orders.views.remove_single_item_from_cart	remove-single-item-from-cart
#/o/request-refund/	fg.apps.orders.views.RequestRefundView	request-refund


class Order(models.Model):
    '''A request by a user for a shipment. The address/ personal information
       is not stored here, but looked up elsewhere via the user address.
       A simple solution to start this off would be to have a form (only
       accessible with login) that feeds to a Google sheet (in Stanford
       Drive - check security level) that keeps the order information.
       Scripts / automation to generate order labels, etc. for addresses
       could be derived from there.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    name = models.CharField(max_length=250, blank=False)

    # Status of order, ordered and received
    ordered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)

    # Notes match to physical sticky notes in the lab
    notes = models.CharField(max_length=500)
    distributions = models.ManyToManyField('main.Distribution', blank=False,
                                           related_name="order_distribution",
                                           related_query_name="order_distribution")
 
    # When a user is deleted don't delete orders
    user = models.ForeignKey('users.User', on_delete=models.DO_NOTHING, blank=True, null=True)

    # When an MTA is deleted, we don't touch the order
    material_transfer_agreement = models.ForeignKey('main.MaterialTransferAgreement', 
                                                    on_delete=models.DO_NOTHING)

    def __str__(self):
        return "<Order:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "order"

    class Meta:
        app_label = 'main'



# Thinking: holding the shipment information in the system is allocating too much
# responsibility to it - the farthest representation I think we should take
# is to represent an order, with a set of items and a number. The shipping
# details (addresses) along with status are out of scope for the FreeGenes
# database. We need to have another integration that can handle this, that doesn't
# require storing PI with FreeGenes. 

# The following should be represented elsewhere (personal information)
# Shipment
# Address
# Parcel
