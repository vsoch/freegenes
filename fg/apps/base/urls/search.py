'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.conf.urls import url
import fg.apps.base.views as views

urlpatterns = [

    # Non parts search is not primary search
    url(r'^search/detailed/?$', views.search_view, name="detailed_search"),
    url(r'^searching/detailed/?$', views.run_search, name="running_detailed_search"),
    url(r'^search/detailed/(?P<query>.+?)/?$', views.search_view, name="detailed_search_query"),

    # primary search provides parts
    url(r'^search/?$', views.parts_search_view, name="search"),
    url(r'^searching/?$', views.run_parts_search, name="running_search"),
    url(r'^search/(?P<query>.+?)/?$', views.parts_search_view, name="search_query"),

]
