'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse

import os
import time
import uuid

################################################################################
# Factory Orders
################################################################################


class Vendor(models.Model):
    '''A vendor that can be associated with a FactoryOrder
    '''
    name = models.CharField(max_length=255, unique=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    def __str__(self):
        return "<Vendor:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "vendor"

    def get_absolute_url(self):
        return reverse('vendor_details', args=[self.uuid])

    class Meta:
        app_label = 'factory'


class FactoryOrder(models.Model):
    '''a factory order is an incoming order for gene parts
    '''

    ORDER_STATUS = [
        ('Planned', 'Planned'), 
        ('In-Production', 'In-Production'),
        ('Complete', 'Complete'), 
        ('Abandoned', 'Abandoned')
    ]

    name = models.CharField(max_length=255)
    order_number = models.CharField(max_length=255, null=True, blank=True, default=None)

    # Don't delete factory order if vendor is deleted.
    vendor = models.ForeignKey('factory.Vendor', on_delete=models.DO_NOTHING, blank=True, null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    # start and end dates are user defined, different from model create/update
    start_date = models.DateTimeField('start date', blank=True, null=True) 
    finish_date = models.DateTimeField('end date', blank=True, null=True) 
    status = models.CharField(max_length=32, choices=ORDER_STATUS, blank=True, null=True)

    # estimated and real prices must be greater than 0
    estimated_price = models.FloatField(validators=[MinValueValidator(0.0)], blank=True, null=True)
    real_price = models.FloatField(validators=[MinValueValidator(0.0)], blank=True, null=True)

    # When an invoice is deleted, don't touch the factory order
    invoices = models.ForeignKey('factory.Invoice', 
                                 on_delete=models.DO_NOTHING,
                                 blank=True, null=True)

    # One or more plates can be added to an order
    plates = models.ManyToManyField('main.Plate', blank=True, default=None,
                                    related_name="factoryorder_plates",
                                    related_query_name="factoryorder_plates")

    # One or more plates can be added to an order
    parts = models.ManyToManyField('main.Part', blank=True, default=None,
                                   related_name="factoryorder_parts",
                                   related_query_name="factoryorder_parts")

    def is_completed(self):
        '''determine if an order is completed based on having an end date.
        '''
        if self.finish_date is not None and self.start_date is not None:
            return True
        return False

    @property
    def duration_days(self):
        '''return the duration of the order (in days), 
           given that it is completed.
        '''
        if self.is_completed:
            return (self.finish_date - self.start_date).days

    # Counting Functions

    def count_parts_completed(self):
        '''determine parts completed based on having (or not having) a sample.
        '''
        count = 0
        for part in self.parts.all():
            if part.sample_set.count() > 0:
                count+=1

        return count

    def count_parts_failed(self):
        '''parts failed is total minus parts completed
        '''
        return self.parts.count() - self.count_parts_completed()

    # Get filtered parts

    def get_completed_parts(self):
        '''return completed parts'''
        parts = []
        for part in self.parts.all():
            if part.sample_set.count() > 0:
                parts.append(part)
        return parts

    def get_failed_parts(self):
        '''return completed parts'''
        parts = []
        for part in self.parts.all():
            if part.sample_set.count() == 0:
                parts.append(part)
        return parts
   

    def __str__(self):
        return "<FactoryOrder:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "factoryorder"

    def get_absolute_url(self):
        return reverse('factoryorder_details', args=[self.uuid])

    class Meta:
        app_label = 'factory'


def get_upload_to(instance, filename):
    '''given an instance and a filename, return the upload destination
    '''

    # The invoice folder is at /code/data/invoice
    upload_folder = os.path.join(settings.UPLOAD_PATH, "invoice")
    if not os.path.exists(upload_folder):
        os.mkdir(upload_folder)

    # Get the extension of the current filename
    _, ext = os.path.splitext(filename)
    filename = "%s/%s%s" % (upload_folder, instance.uuid, ext)
    return time.strftime(filename)


class Invoice(models.Model):
    '''An invoice contains a boolean for being paid, along with a file,
       and notes to keep about it.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    invoice_file = models.FileField(upload_to=get_upload_to)
    is_paid = models.BooleanField(default=False)
    notes = models.CharField(max_length=500)

    def __str__(self):
        return "<Invoice:%s>" % self.notes

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "invoice"

    def get_absolute_url(self):
        return reverse('invoice_details', args=[self.uuid])

    @property
    def name(self):
        if self.invoice_file:
            return os.path.basename(self.invoice_file)

    class Meta:
        app_label = 'factory'
