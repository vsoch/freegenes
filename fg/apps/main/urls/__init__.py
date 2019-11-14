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
    url(r'^e/distribution/(?P<uuid>.+)/parts/?$', views.distribution_parts, name='distribution_parts'),
    url(r'^e/distribution/(?P<uuid>.+)/?$', views.distribution_details, name='distribution_details'),
    url(r'^e/institution/(?P<uuid>.+)/?$', views.institution_details, name='institution_details'),
    url(r'^e/module/(?P<uuid>.+)/?$', views.module_details, name='module_details'),
    url(r'^e/operation/(?P<uuid>.+)/?$', views.operation_details, name='operation_details'),
    url(r'^e/organism/(?P<uuid>.+)/?$', views.organism_details, name='organism_details'),
    url(r'^e/part/(?P<uuid>.+)/?$', views.part_details, name='part_details'),
    url(r'^e/plan/(?P<uuid>.+)/?$', views.plan_details, name='plan_details'),
    url(r'^e/plate/(?P<uuid>.+)/?$', views.plate_details, name='plate_details'),
    url(r'^e/plateset/(?P<uuid>.+)/?$', views.plateset_details, name='plateset_details'),
    url(r'^e/protocol/(?P<uuid>.+)/?$', views.protocol_details, name='protocol_details'),
    url(r'^e/robot/(?P<uuid>.+)/?$', views.robot_details, name='robot_details'),
    url(r'^e/sample/(?P<uuid>.+)/?$', views.sample_details, name='sample_details'),
    url(r'^e/schema/(?P<uuid>.+)/?$', views.schema_details, name='schema_details'),

    # Tags (filtered to types)
    url(r'^e/tag/(?P<uuid>.+)/organisms/?$', views.tag_organisms_details, name='tag_organisms_details'),
    url(r'^e/tag/(?P<uuid>.+)/parts/?$', views.tag_parts_details, name='tag_parts_details'),
    url(r'^e/tag/(?P<uuid>.+)/collections/?$', views.tag_collections_details, name='tag_collections_details'),
    url(r'^e/tag/(?P<uuid>.+)/authors/?$', views.tag_authors_details, name='tag_authors_details'),
    url(r'^e/tag/(?P<uuid>.+)/?$', views.tag_details, name='tag_details'),
    
    # Maps
    url(r'map/orders/?$', views.order_map_view, name='order_map'),

    # Catalog
    url(r'c/catalog/?$', views.catalog_view, name='catalog_view'),
    url(r'c/catalog/collections/?$', views.collections_catalog_view, name='collections_catalog'),
    url(r'c/catalog/containers/?$', views.containers_catalog_view, name='containers_catalog'),
    url(r'c/catalog/distributions/?$', views.distributions_catalog_view, name='distributions_catalog'),
    url(r'c/catalog/organisms/?$', views.organisms_catalog_view, name='organisms_catalog'),
    url(r'c/catalog/tags/?$', views.tags_catalog_view, name='tags_catalog'),
    url(r'c/catalog/tags/(?P<selection>.+)/?$', views.tags_catalog_view, name='tags_catalog_selection'),
    url(r'c/catalog/parts/?$', views.parts_catalog_view, name='parts_catalog'),
    url(r'c/catalog/platesets/?$', views.platesets_catalog_view, name='platesets_catalog'),
    url(r'c/catalog/plates/?$', views.plates_catalog_view, name='plates_catalog'),
    url(r'c/catalog/samples/?$', views.samples_catalog_view, name='samples_catalog'),

    # Download
    url(r'^download/mta/(?P<uuid>.+)/?$', views.download_mta, name='download_mta'),
    url(r'^download/plate/csv/(?P<uuid>.+)/?$', views.download_plate_csv, name='download_plate_csv'),
    url(r'^download/plateset/csv/(?P<uuid>.+)/?$', views.download_plateset_csv, name='download_plateset_csv'),
    url(r'^download/distribution/csv/(?P<uuid>.+)/?$', views.download_distribution_csv, name='download_distribution_csv'),

    # Export (for future import)
    url(r'^export/plate/(?P<uuid>.+)/?$', views.export_plate_json, name='export_plate_json'),
    url(r'^export/plateset/(?P<uuid>.+)/?$', views.export_plateset_json, name='export_plateset_json'),
    url(r'^export/distribution/(?P<uuid>.+)/?$', views.export_distribution_json, name='export_distribution_json'),
]
