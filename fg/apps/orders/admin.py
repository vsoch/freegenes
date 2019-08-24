'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import admin
from fg.apps.orders.models import Order

def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)

make_refund_accepted.short_description = 'Update orders to refund granted'

class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'received', 'time_updated', 'time_created', 'material_transfer_agreement', )
    list_display_links = ('user', 'material_transfer_agreement', )
    list_filter = ['received']
    search_fields = [
        'user__username',
        'ref_code'
    ]
    actions = [make_refund_accepted]

admin.site.register(Order, OrderAdmin)
