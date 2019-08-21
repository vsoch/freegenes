---
title: Using the API
description: The FreeGenes API allows for programmatic access to the server
---

# API

The Application Programming Interface (API) is available for browsing at "/api/docs".
For a development server, this means [http://127.0.0.1/api/docs](http://127.0.0.1/docs/api).
At this interface, you can browse endpoints (listed on the left side bar):

![freegenes-api.png]({{ site.baseurl }}/docs/usage/freegenes-api.png)

Along with testing them interactively, either to list entities, or to request a specific
entity based on it's unique id:

![freegenes-api-test.png]({{ site.baseurl }}/docs/usage/freegenes-api-test.png)

For endpoints with large listings or metadata (for example, some objects have descriptions or notes
that can be large, or lists of wells) the listed view removes these fields, and the user
is required to ask for a uuid directly to see the complete data.

## Clients

Under development (not a priority) will be [freegenes-python](https://www.github.com/vsoch/freegenes-python/) to allow
for easy, programmatic access to all endpoints from Python.

## Token

Once you are logged in, you can access your API token from your User Profile
dropdown menu, at the url "/token":

![token.png]({{ site.baseurl }}/docs/usage/token.png)

Further instructions will be added here (or to freegenes-python) for how to interact
with the API.
