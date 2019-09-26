---
title: Background
description: Background about FreeGenes before this application
---

# Background

FreeGenes was a longer term project that unfortunately didn't result in an intended outcome.
[flask_freegenes](https://github.com/Koeng101/flask_freegenes) was created
to minimally serve a databased backed API to support Endy Lab. The original
schema is shown below:

![{{ site.baseurl }}/assets/img/original-database.png]({{ site.baseurl }}/assets/img/original-database.png)

## Design

Conceptually there are two different "things" - the Node and the Factory. 
Since the software here is monolithic, we can conceptually define "Node" and "Factory" into
different views for different types of users.

The six different functions we're looking at overall include:

 1. DNA design software
 2. DNA ordering system (This is the Twist stuff)
 3. Factory - > Node import 
 4. Browse
 5. Shipments / requests
 6. Overall status views

Where 1-3 are included in the Factory set, and 4-5 in the Node set. The last
function (overall status views) are shared between the sets, as getting a status
for an order could be relevant for an incoming order to the factory, or an outgoing
user of lab product to another lab. The Endy Lab has designed the following diagram to outline
these relationships:

![{{ site.baseurl }}/assets/img/freegenes-design.png]({{ site.baseurl }}/assets/img/freegenes-design.png)
