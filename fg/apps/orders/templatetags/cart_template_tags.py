'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django import template
from fg.apps.orders.models import Order

register = template.Library()

@register.filter
def cart_item_count(user):
    if user.is_authenticated:
        try:
            cart = Order.objects.get(user=user, status="Cart")
        except Order.DoesNotExist:
            return 0
        return cart.distributions.count()

