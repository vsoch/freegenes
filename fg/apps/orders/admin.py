'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import admin
from fg.apps.orders.models import Order

class OrderAdmin(admin.ModelAdmin):
    exclude = ('transaction', 'label', 'user', )
    list_display = ('name', 'user', 'status', 'summary_status', 'date_ordered', 'date_shipped', 'material_transfer_agreement', )
    list_display_links = ('user', 'material_transfer_agreement', )
    list_filter = ['status']
    search_fields = [
        'user__username',
        'ref_code'
    ]

admin.site.register(Order, OrderAdmin)
