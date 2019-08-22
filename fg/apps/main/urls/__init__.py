'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.conf.urls import url
import fg.apps.main.views as views

urlpatterns = [

    # Details (e corresponds for entity)
    url(r'^e/author/(?P<uuid>.+)/?$', views.author_details, name='author_details'),
    url(r'^e/container/(?P<uuid>.+)/?$', views.container_details, name='container_details'),
    url(r'^e/collection/(?P<uuid>.+)/?$', views.collection_details, name='collection_details'),
    url(r'^e/distribution/(?P<uuid>.+)/?$', views.distribution_details, name='distribution_details'),
    url(r'^e/institution/(?P<uuid>.+)/?$', views.institution_details, name='institution_details'),
    url(r'^e/module/(?P<uuid>.+)/?$', views.module_details, name='module_details'),
    url(r'^e/operation/(?P<uuid>.+)/?$', views.operation_details, name='operation_details'),
    url(r'^e/organism/(?P<uuid>.+)/?$', views.organism_details, name='_details'),
    url(r'^e/order/(?P<uuid>.+)/?$', views.order_details, name='order_details'),
    url(r'^e/part/(?P<uuid>.+)/?$', views.part_details, name='part_details'),
    url(r'^e/plan/(?P<uuid>.+)/?$', views.plan_details, name='plan_details'),
    url(r'^e/plate/(?P<uuid>.+)/?$', views.plate_details, name='plate_details'),
    url(r'^e/plateset/(?P<uuid>.+)/?$', views.plateset_details, name='plateset_details'),
    url(r'^e/protocol/(?P<uuid>.+)/?$', views.protocol_details, name='protocol_details'),
    url(r'^e/robot/(?P<uuid>.+)/?$', views.robot_details, name='robot_details'),
    url(r'^e/sample/(?P<uuid>.+)/?$', views.sample_details, name='sample_details'),
    url(r'^e/schema/(?P<uuid>.+)/?$', views.schema_details, name='schema_details'),
    url(r'^e/tag/(?P<uuid>.+)/?$', views.tag_details, name='tag_details')

]
