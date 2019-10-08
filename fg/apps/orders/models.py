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
    ordered = models.BooleanField(default=False)  # The user submit the order
    received = models.BooleanField(default=False) # FreeGenes staff has processed it

    # Notes match to physical sticky notes in the lab
    notes = models.CharField(max_length=500)
    distributions = models.ManyToManyField('main.Distribution', blank=False,
                                           related_name="order_distribution",
                                           related_query_name="order_distribution")
 
    # When a user is deleted don't delete orders
    user = models.ForeignKey('users.User', on_delete=models.DO_NOTHING, blank=True, null=True)
    transaction = JSONField(default=dict)
    label = JSONField(default=dict)

    # When an MTA is deleted, we don't touch the order. We don't require an MTA
    # for the order object, however we require it to be present when checking out
    # (and we change ordered from False to True)
    material_transfer_agreement = models.ForeignKey('main.MaterialTransferAgreement', 
                                                    on_delete=models.DO_NOTHING,
                                                    blank=True, null=True)

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
            if Order.objects.filter(ordered=False, user=self.user.username).count() >= 1:
                raise ValidationError(message)

    class Meta:
        app_label = 'orders'
