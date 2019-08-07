---
title: User Stories
description: User Stories and Interactions to help guide development
---

## User Stories

What is a user story? A user story is a small passage (a story) that describes
how a user would ideally interact with FreeGenes. We write User Stories to help
guide the early development of FreeGenes, including the interface and views
provided.

### Create an Order

I am a scientist at another institution, and I'm interested in creating an order
so that Endy Lab ships me some number of plate sets. I would typically want to:

 - Log into the interface at freegenes.org. This ideally would be an institution based login, but realistically I'd be okay with OAuth2. The OAuth2 login ensures that my email is used in the database as a unique id. No other personal information is stored.
 - I would then want to search or generally browse. I might want an "Add to Cart" experience, or an "Orders" page that has me select items in a single place with dropdowns (thoughts?)
 - I would want to select the items, and then submit.

The admins of FreeGenes would want to receive a notification about the order, and then
look up the requester in a local file with addresses (or a Google Sheet?). If the
shipping information isn't present, the user would need to be emailed to request it.
If it is present, a confirmation that the order was received should be sent.
This should be done in a somewhat automated fashion, but separate from FreeGenes
itself (will require thought / some research about how others do it).
The protocol for generating the actual order and shipment would be followed,
and the user sent a notification of shipment when it's shipped.

### View Current Orders

I'm an admin in the Endy Lab, and I want to log in to see existing orders.
I should have an admin interface to log in, and see a list of orders and their statuses.

