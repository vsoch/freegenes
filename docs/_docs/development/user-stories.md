---
title: User Stories
description: User Stories and Interactions to help guide development
---

## User Stories

What is a user story? A user story is a small passage (a story) that describes
how a user would ideally interact with FreeGenes. We write User Stories to help
guide the early development of FreeGenes, including the interface and views
provided.


There are 4 categories of views that we need: 
1. Inventory
2. Ordering and shipping
3. Operations status
4. Gene design 

# Inventory
Inventory refers to our virtual inventory (what parts we have) as well as our
physical inventory (what samples of parts we have). The intended audience for 
our virtual inventory is any visitor of the site, while the intended audience 
for our physical inventory is our lab technicians. 

## The site visitor 
I am a synthetic biology student currently in iGEM (unaffiliated with EndyLab). I am used to the organization 
of the [iGEM parts catalog](http://parts.igem.org/Catalog) in finding materials.

While browsing the registry, I have found [a part](http://parts.igem.org/wiki/index.php?title=Part:BBa_J97001) that I think is really cool
that was created by the Endylab in 2014. I want to see if this part is also in 
the FreeGenes repository!

I want to have a couple of different options: I could browse collections to see
if there is a fluorescent protein collection, or I might want to browse commonly
used (or requested) CDSs to see if it is there, or finally I might want to BLAST
the sequence to see if it is represented anywhere in the system right now.

(A simplified view similar to iGEM is exactly what we need)

## The lab technician
I am a lab technician in Endy lab. Our PI / lab manager has just initiated a
new operation to build a new genome. Exciting!

For the first step, I need to take a plate named 'OpenEnzyme' out of the freezer.
However, I am fairly new to the lab, and so don't exactly know where it is. I use
the FreeGenes website to find out where this plate is exactly (similar to [this view](https://api.freegenes.org/containers/tree_view_full/).)


I am a different lab technician in Endy lab. A new extremely important protein
is needed pronto for a graduate students experiment. It is somewhere in lab, but
I don't know where. Since I am a lab technician, I can go to the part's page, and view
the samples currently available for that part. I see there are 3 samples in lab that are 
sequence confirmed, but one that is currently sequence verified by NGS in house. I decide
that sample is the best for the graduate student. I click a button to find that particular 
sample, and I'm given a similar map to the one above, telling me to go into the FreezerHall->
FearlessWanderer->Shelf_4->Rack_2->23w->A1. I go scrape a little bit of glycerol stock from 
that location, and give it to the graduate student.

# Ordering and shipping
Ordering and shipping are two different but closely related topics. On one side, 
people should be able to come onto our website and order distributions, and on the 
other side, we need to fulfill those requests by shipping those distributions 
physically.

## Ordering
I am the "site visitor" from the Invetory section. I have found the part I was looking for, JuniperGFP!
It turns out that that part is part of 3 different distributions - "OpenEnzyme", "Fluorescent proteins", 
and "Reporters". I open all those 3 distribution links to take a look at which one would work for me. 
OpenEnzyme has mostly irrelevant enzymes, reporters is too broad, but fluorescent proteins distribution 
has exactly what I'm looking for.

On the fluorescent protein distribution page, I click "add to cart". 

(After this point, a demonstration of what an actual plasmid order page looks like
would be appropriate. For this example, we'll use Addgene. This includes
getting the OpenMTA signed)

## Shipping
I am the lab Shipper! Taking mostly from email example:

I check to make sure the MTA has been signed correctly from the previous steps.

If the MTAs have been properly signed, I generate a shipping label through shippo 
or through our system. 

I then pull out the actual plates from the freezer and scan their respective QR codes. Our system
confirms the plates that are going out using the QR codes. Once all the plates are packed,
the system confirms that the shipment is complete / packed, and forwards a confirmation email
to the recipient. 

# Operations status

# Gene design







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

