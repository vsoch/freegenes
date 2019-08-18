'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.conf.urls import (
    url, 
    include
)
import rest_framework.authtoken.views as authviews
from rest_framework import routers
from fg.apps.api.urls.serializers import (

    # Viewsets (more than one entity)
    AuthorViewSet,
    ContainerViewSet,
    CollectionViewSet,
    DistributionViewSet,
    InstitutionViewSet,
    ModuleViewSet,
    TagViewSet
)



router = routers.DefaultRouter()
router.register(r'^authors', AuthorViewSet, base_name="author")
router.register(r'^collections', CollectionViewSet, base_name="collection")
router.register(r'^containers', ContainerViewSet, base_name="container")
router.register(r'^distributions', DistributionViewSet, base_name="distribution")
router.register(r'^institutions', InstitutionViewSet, base_name="institution")
router.register(r'^tags', TagViewSet, base_name="tag")

urlpatterns = [

    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token-auth/', authviews.obtain_auth_token),

    url(r'^modules/?$', ModuleViewSet.as_view()),
    url(r'^modules/(?P<id>.+?)/?$', ModuleViewSet.as_view()),


]
