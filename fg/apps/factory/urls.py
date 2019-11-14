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

    # Twist
    url(r'^twist/plates/import/?$', views.twist_import_plates, name='twist_import_plates'),
    url(r'^twist/parts/import/?$', views.twist_import_parts, name='twist_import_parts'),

    # Bionet Server Import
    url(r'^factory/plate/import/?$', views.import_factory_plate, name='import_factory_plate'),

    # Completed and Failed Parts
    url(r'^factoryorder/parts/completed/(?P<uuid>.+)/?$', views.view_factoryorder_parts_completed, name='view_factoryorder_parts_completed'),
    url(r'^factoryorder/parts/failed/(?P<uuid>.+)/?$', views.view_factoryorder_parts_failed, name='view_factoryorder_parts_failed'),
    url(r'^factoryorder/parts/(?P<uuid>.+)/?$', views.view_factoryorder_parts, name='view_factoryorder_parts'),

    # Lab Map
    url(r'map/?$', views.lab_map_view, name='lab_map'),

]
