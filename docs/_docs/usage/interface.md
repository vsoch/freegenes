---
title: Interacting with FreeGenes
description: A typical user might want to search, or create an order
---

# Interface

 - [Dashboard](#dashboard) for user and staff navigation
 - [Orders](#orders) to sign an MTA and request distributions
 - [Shipments](#shipments) for the label to receive and process orders
 - [Search](#search) and catalog views
 - [Maps](#maps) for finding plates.
 - [Profile](#profile) include account management and API tokens.
 - [Admin]({{ site.baseurl }}/docs/usage/admin) views
 - [API]({{ site.baseurl }}/docs/usage/api) views

FreeGenes has general functionality for non authenticated users to search,
and detail is provided after a user has created an account.

## Dashboard

The primary dashboard for FreeGenes shows overall statistics at the top:

![dashboard.png]({{ site.baseurl }}/docs/usage/dashboard.png)

> Question: should the orders / dashboard be moved into a tabbed interface? Should the chart be moved into a 50% column, and then the four statistic boxes stacked on the right?

Larger values are shown in boxes, others are shown in a standard box plot.
Directly below, an admin or staff user sees a table of all orders:

![dashboard-orders.png]({{ site.baseurl }}/docs/usage/dashboard-orders.png)

And a logged in user that isn't admin or staff only sees his or her current and
previous orders.

## Orders

When a user adds one or more distributions to his or her cart, they appear
on the "Cart" page that is available by clicking the shopping cart in the top
right:

![order.png]({{ site.baseurl }}/docs/usage/order.png)

Checkout first checks if the user has signed a material transfer agreement for
the order. In the case of not, the user is redirected to a page to read,
fill out fields, and then download the form as a PDF.

![sign-mta.png]({{ site.baseurl }}/docs/usage/sign-mta.png)

Once the form is signed, the user can re-upload it in the same interface.

![upload-mta.png]({{ site.baseurl }}/docs/usage/upload-mta.png)

A successful upload redirects the user to the actual Checkout form.

![checkout.png]({{ site.baseurl }}/docs/usage/checkout.png)

The checkout form itself doesn't save personal information to the server,
but rather sends an email with the form to the lab. This is done for three reasons -

 1. It's an easy way to notify the lab of an order
 2. It eliminates the need to store personal information on the server
 3. We can have better certainty of having the latest shipping information.

## Shipments

The lab can then receive the email, click a link to go directly to the order
and download the MTA:

![download-mta.png]({{ site.baseurl }}/docs/usage/download-mta.png)

And then use a similar form to re-upload, finish processing on their side, and continue with
preparing the order. The interface for creating the shipment is what you would expect -
the lab enters the addresses needed to create the shipment, along with
the dimensions of the parcel:

![create-shipment.png]({{ site.baseurl }}/docs/usage/create-shipment.png)

The requester can also decide to include dry ice or not. If either of the addresses aren't valid,
the user is returned to the page with instructions to fix. In the case that the
user is returned to the page, a button is presented that will re-load the addresses
information from local storage so the user doesn't need to re-enter it. 
If the shipment is valid, the user is then presented with the shipping rate options:

![shipment-details.png]({{ site.baseurl }}/docs/usage/shipment-details.png)

Selecting a rate first needs to create and validate the transaction. The user is
taken to a page that shows it's valid, and then (for the first round, given that
there is no label) the user can click a button to generate one when ready. Once
the label is generated, the user can choose to print it, or track the package:

![transaction.png]({{ site.baseurl }}/docs/usage/transaction.png)

The label prints as a PDF that opens in a new window:

![label.png]({{ site.baseurl }}/docs/usage/label.png)

And the tracking url is standard, provided by the service selected (the testing
api appears to return an already used number):

![tracking.png]({{ site.baseurl }}/docs/usage/tracking.png)


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

### Lab Map

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

### Orders Map

When you are logged in as a superuser or staff, on the main page there is a link
for a map above the orders table. Clicking it will show a map of orders, with
circles representing number of orders located above a zip code:

![shipping-map.png]({{ site.baseurl }}/docs/usage/shipping-map.png)

We don't store anything but the zip codes with counts on the server, and the
data is obtained as a nightly task using the Shippo api. The current map
is generated from testing data, as only a real Shippo token (not a testing one)
will return real order data.

## Profile

The user profile is accessible from the top right after the user is logged in:

![profile-menu.png]({{ site.baseurl }}/docs/usage/profile-menu.png)

Currently, profile views are limited to simple account management and
getting access to an API token. 

![profile.png]({{ site.baseurl }}/docs/usage/profile.png)

When users can create others (and do other actions) this view will be extended.
