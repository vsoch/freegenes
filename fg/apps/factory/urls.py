'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
import fg.apps.factory.views as views

urlpatterns = [
    url(r'^$', views.factory_view, name='factory'),
    url(r'^twist/orders?/$', views.twist_orders, name='twist_orders'),
    url(r'^twist/order/import/(?P<uuid>.+)$', views.twist_order_import, name='twist_order_import'),
    url(r'^twist/order/(?P<uuid>.+)$', views.twist_order, name='twist_order'),

    # Lab Map
    url(r'map/?$', views.lab_map_view, name='lab_map'),

]
