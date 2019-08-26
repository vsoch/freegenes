---
title: Interacting with FreeGenes
description: A typical user might want to search, or create an order
---

# Interface

 - [Search](#search) and catalog views.
 - [Maps](#maps) for finding plates.
 - [Profile](#profile) include account management and API tokens.
 - [Admin]({{ site.baseurl }}/docs/usage/admin) views
 - [API]({{ site.baseurl }}/docs/usage/api) views

FreeGenes has general functionality for non authenticated users to search,
and detail is provided after a user has created an account.

## Search

The main entrypoint for finding content is via search. A basic search (from the
home page or the search endpoint) will search across all models in the database,
and return a list of results:

![search-result.png]({{ site.baseurl }}/docs/usage/search-result.png)

The results currently don't link to detail views (but will). The user will
need to be authenticated to see the details (or it could be they can
see some derivative). Under development is also a category based view,
where a user that knows what he or she is looking for can browse the category
directly:

![catalog.png]({{ site.baseurl }}/docs/usage/catalog.png)

And then view a listing of entities for a particular catalog of interest. For
example, here is the Collections catalog.

![catalog-collections.png]({{ site.baseurl }}/docs/usage/catalog-collections.png)

Since the size of collections is small, this single table provides all entities
that are sortable and searchable. A larger catalog (e.g. parts) would be paginated
on the server, and provide a custom search box for searching (server side). 
Front end rendering and search of the table would be inexusibly slow.

To zoom in further to a detail page, here is an example for a tag detail -
in the case of a tag, a tab is rendered with subtypes (e.g., collections, organisms,
parts, or other) only if the tag is associated with said subtype.

![tags.png]({{ site.baseurl }}/docs/usage/tags.png)

## Maps

If you are a staff in the lab, you can click on your username in the top right
and select "Map" to see an expanded, lab map view:

![lab-map.png]({{ site.baseurl }}/docs/usage/lab-map.png)

Any of the plates or containers can be clicked to go to their specific view.
If you are browsing a container, you can also quickly see it's immediate children:

![container-map.png]({{ site.baseurl }}/docs/usage/container-map.png)

The breadcrumb at the top shows the direct address of the container, and the
map tab shows the nested plates within. If you are browsing a plate and want
to quickly find a location, if you want more detail than the breadcrumb
you can click on "Locate" in the interface:

![locate-from.png]({{ site.baseurl }}/docs/usage/locate-from.png)

And it will take you to the Lab map, with the selected plate highlighted in
red.

![locate-to.png]({{ site.baseurl }}/docs/usage/locate-to.png)

## Profile

The user profile is accessible from the top right after the user is logged in:

![profile-menu.png]({{ site.baseurl }}/docs/usage/profile-menu.png)

Currently, profile views are limited to simple account management and
getting access to an API token. 

![profile.png]({{ site.baseurl }}/docs/usage/profile.png)

When users can create others (and do other actions) this view will be extended.
