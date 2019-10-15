'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import admin
from fg.apps.factory.models import (
    Vendor,
    FactoryOrder,
    Invoice
)

# Actions

def reset_parts(modeladmin, request, queryset):
    '''reset parts for a selected factory order (remove but don't delete)'''
    for order in queryset:
        order.parts.clear()
        order.save()
reset_parts.short_description = "Reset Parts (empty but don't delete)"


# Admin Models

class FactoryOrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'finish_date', 'status', 'estimated_price', 
                    'real_price', 'time_updated', 'time_created')

    actions = [reset_parts,]

class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'time_updated', 'time_created',)

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('time_created', 'time_updated', 'is_paid', 'invoice_file', 'notes',)

admin.site.register(FactoryOrder, FactoryOrderAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Vendor, VendorAdmin)
