'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.conf.urls import url
import fg.apps.orders.views as views

urlpatterns = [
    url(r'^$', views.orders_view, name='orders'),
    url(r'^cart/add/(?P<uuid>.+)$', views.add_to_cart, name='add-to-cart'),
    url(r'^cart/remove/(?P<uuid>.+)$', views.remove_from_cart, name='remove-from-cart'),
    url(r'^checkout$', views.CheckoutView.as_view(), name='checkout'),
    url(r'^submit/(?P<uuid>.+)$', views.submit_order, name='submit_order'),

    # Material Transfer Agreement
    url(r'^mta/upload/(?P<uuid>.+)$', views.upload_mta, name='sign-mta'),
    url(r'^mta/admin-upload/(?P<uuid>.+)$', views.admin_upload_mta, name='upload-mta'),

    # Details (e corresponds for entity)
    url(r'^details/(?P<uuid>.+)$', views.order_details, name='order_details'),

]
