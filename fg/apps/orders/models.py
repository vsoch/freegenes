'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse

import os
import time
import uuid

################################################################################
# Orders
################################################################################

class Address(models.Model):
    '''an address can correspond to a lab or shipping address. We collect
       both for an order, and then link to the order.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    # Either institution name or recipient name must be defined
    institution_name = models.CharField(max_length=250, blank=True, null=True)
    recipient_title = models.CharField(max_length=50, blank=True, null=True)
    recipient_name = models.CharField(max_length=250, blank=True, null=True)
    address1 = models.CharField(max_length=500, blank=False)
    address2 = models.CharField(max_length=500, blank=False)
    postal_code = models.CharField(max_length=500, blank=False)
    city = models.CharField(max_length=250, blank=False)
    state = models.CharField(max_length=250, blank=False)
    phone = models.CharField(max_length=500, blank=False)
    email = models.CharField(max_length=250, blank=True, null=True)
    country = models.CharField(max_length=250, blank=False, default="US")

    def clean(self):
        '''a recipient_name or institution name is required.
        '''
        if self.institution_name is None and self.recipient_name is None:
            message = "Either an institution or individual name needs to be provided."
            raise ValidationError(message)

    def __str__(self):
        return "<Address:%s>" % self.institution_name or self.recipient_name

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "address"

    class Meta:
        app_label = 'orders'


class Order(models.Model):
    '''A request by a user for a shipment. The address/ personal information
       is not stored here, but looked up elsewhere via the user address.
       A simple solution to start this off would be to have a form (only
       accessible with login) that feeds to a Google sheet (in Stanford
       Drive - check security level) that keeps the order information.
       Scripts / automation to generate order labels, etc. for addresses
       could be derived from there.
    '''
    # see https://github.com/vsoch/freegenes/issues/126#issue-520266580
    # and a status of None indicates not submit (still a cart)
    ORDER_STATUS = [
        ('Cart', 'Cart'),
        ('Rejected', 'Rejected'),  # add toggle to reject
        ('Awaiting Countersign', 'Awaiting Countersign'),
        ('Generating Label', 'Generating Label'),
        ('Waiting to Ship', 'Waiting to Ship'),
        ('Shipped', 'Shipped')
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    name = models.CharField(max_length=250, blank=False)

    date_ordered = models.DateTimeField('date ordered', null=True, blank=True) 
    date_shipped = models.DateTimeField('date shipped', null=True, blank=True)

    # Status of order, default is Awaiting Countersign, as the user can only have one Cart
    status = models.CharField(max_length=32, choices=ORDER_STATUS, blank=False, default='Awaiting Countersign')

    # Notes match to physical sticky notes in the lab
    notes = models.CharField(max_length=500)
    distributions = models.ManyToManyField('main.Distribution', blank=False,
                                           related_name="order_distribution",
                                           related_query_name="order_distribution")
 
    # When a user is deleted don't delete orders
    user = models.ForeignKey('users.User', on_delete=models.DO_NOTHING, blank=True, null=True)
    transaction = JSONField(default=dict)
    label = JSONField(default=dict)

    # Lab and Shipping Address
    lab_address = models.ForeignKey(Address, on_delete=models.DO_NOTHING, 
                                    related_name="order_lab_address",
                                    blank=True, null=True)
    shipping_address = models.ForeignKey(Address, on_delete=models.DO_NOTHING,
                                         related_name="order_shipping_address",
                                         blank=True, null=True)

    # When an MTA is deleted, we don't touch the order. We don't require an MTA
    # for the order object, however we require it to be present when checking out
    # (and we change ordered from False to True)
    material_transfer_agreement = models.ForeignKey('main.MaterialTransferAgreement', 
                                                    on_delete=models.DO_NOTHING,
                                                    blank=True, null=True)

    # Get status

    @property
    def summary_status(self):
        '''the status here corresponds to Complete or Processing depending
           on self.status, or Cart (which admins don't care to see)
        '''
        if self.status in ['Rejected', 'Shipped']:
            return "Completed"
        elif self.status == "Cart":
            return "Cart"
        return "Processing"

    # Save json functions

    def add_transaction(self, transaction):
        '''add a Shippo transaction to an order, meaning stripping any billing
           information and converting to dictionary
        '''
        data = dict(transaction)
        del data['billing']
        self.transaction = data
        self.save()

    def add_label(self, label):
        '''save a Shippo label to an order, meaning stripping any billing
           information and converting to dictionary
        '''
        data = dict(label)
        del data['billing']
        self.label = data
        self.save()


    def __str__(self):
        return "<Order:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "order"

    def get_absolute_url(self):
        return reverse('order_details', args=[self.uuid])

    def clean(self):
        '''a user is only allowed to have one order that isn't ordered (a cart)
           if staff puts a new order into the system (user None) this is allowed.
        '''
        if self.user is not None:
            message = 'User %s has a pending order, only one cart is allowed.' % self.user.username
            if Order.objects.filter(status="Cart", user=self.user).count() >= 1:
                raise ValidationError(message)

    class Meta:
        app_label = 'orders'
