---
title: Using the API
description: The FreeGenes API allows for programmatic access to the server
---

# API

The Application Programming Interface (API) is available for browsing at "/api/docs".
For a development server, this means [http://127.0.0.1/api/docs](http://127.0.0.1/docs/api).
For the development server, it means [https://freegenes.dev](https://freegenes.dev).
You can use the [API Client](https://pypi.org/project/freegenes/) to more easily
interact with it (documentation [here](https://vsoch.github.io/freegenes-python/)).
At this interface, you can browse endpoints (listed on the left side bar):

![freegenes-api.png]({{ site.baseurl }}/docs/usage/img/freegenes-api.png)

Along with testing them interactively, either to list entities, or to request a specific
entity based on it's unique id:

![freegenes-api-test.png]({{ site.baseurl }}/docs/usage/img/freegenes-api-test.png)

For any endpoint that modified the database (e.g., POST to create, or PATCH, DELETE)
you are required to not only be authenticated, but also to be a staff or superuser.

## Clients

 - **Python**: [freegenes-python](https://www.github.com/vsoch/freegenes-python/) to allows
for easy, programmatic access to all endpoints from Python. We will be adding custom functions here as requested.

## Token

Once you are logged in, you can access your API token from your User Profile,
under the Settings tab.  You'll need to export this token as `FREEGENES_TOKEN` to use
the client. See the [getting started](https://vsoch.github.io/freegenes-python/docs/getting-started/) 
guide for more details.

## Permissions

All API views require authentication except for:

 - Parts
 - Composite Parts
 - Plates
 - Samples
 - Collections

Meaning that an unathenticated user can request the view GET.
