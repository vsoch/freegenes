---
title: Views and URLs
description: Notes about the design of the interface, including urls and views.
---

## Organization

FreeGenes django is organized into "apps" (Django modules or apps that are
part of FreeGenes) and plugins (Django modules or apps that add extra functionality
and must be added by an individual deployment.) For more on plugins, see [the plugins documentation]({{ site.baseurl }}/docs/plugins/). Both are organized under the main fg (freegenes) application folder (non
essential files removed from view):

```bash
$ tree fg -L 1
fg
├── apps        # (apps go here) 
├── plugins     # (plugins, or optional apps, here)
├── settings    # (configuration files)
├── urls.py 
└── wsgi.py
```

### Apps

The main apps provided include:

 - **users**: views for user accounts, logging in and out
 - **base**: primarily base templates (home, index, about, search) and static files
 - **main**: models and detail views for each
 - **api**: serialization of models to serve at the /api endpoint

The Django admin module is installed and in use, meaning that the models in the main
app are accessible via it.


### URLs

Across all apps, we honor the following namespaces to keep the url space (matched
based on regular expression) well organized.

 - **/u** corresponds to user or profile views (indicates "user")
 - **/o** external order and shipment views (under apps/orders)
 - **/l** lab (factory) views, correspond with "internal" module
 - **/c** catalog pages are under the letter c
   - **/c/<type>/** would correspond to a specific catalog
 - **/api** correponds to API endpoints
 - **/admin** administrative views
 - **/e** correspond to entity (e.g., a Model instance) views (indicates "entity")"
 - **/e/<type>** corresponds to a specific entity. For example, "container"
   - **/e/<type>/<uuid>/** would correspond to a details page for the specific uuid
   - **/e/<type>/<uuid>/<action>** would correspond to an action for the entity


If you need to inspect URLs further you can shell into the uwsgi container, and issue:

```bash
$ python manage.py show_urls
```

### Templates

Templates are organized in subfolders of each app's "templates" folder. Since they
are referred to based on the subfolder and file name, we again keep them organized
according to this standard. Generally, the subfolders are self explanatory (e.g.,
"details" under main templates is for the detail pages for each model.
