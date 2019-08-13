---
title: Models
description: Details and notes about models
---

These are compiled notes from discussion in email, and on GitHub issues.
Some details are kept alongside the Models as well.

## General Fields

These are notes on fields shared across models.

### Notes vs. Description

Notes are on physical objects in lab, and basically function to replace sticky notes (if you look at modules it has some examples). A description field (like a Readme) doesn't really change too much over time.

## Tags

Proper tagging of genes is perhaps one of the most important pieces of information we can create. Tags are little bits of information that come from experience / science. For example, we may tag a plasmid part as conferring ampicillin resistance, so it would include the tag ```resistance:ampicillin```. That same part could also be tagged as an ```essential_gene``` - and so basically the tags are ways to organize the different categories they are associated with.

Tags should be stored between models. We may want to find all things associated with ```mesoplasma florum```. That may include the collections that are associated with Mesoplasma florum, the parts associated with Mesoplasma florum, or even perhaps the authors associated with that category.


## Sequence

- Sequence at MINIMIUM needs to be ~10,000. Preferably this would be much larger, and we would want at least ~100,000. Nearly none of our genes will fit in 250. In the most ideal world, sequence field on an organism would be ~4,000,000, but this isn't very practical.
- Genbank is a bit odd, it's just some JSON generated from previous genbank files about each part. The goal is to go back later and implement JSON <-> genbank format (not done yet). It can be considered historical data.
- ip_check has some odd wording that is required for legal reasons
- A part can belong to many collections.


## Containers and modules

- The x,y,z coordinates are the meter coordinates for the locations of things in lab. You can imagine that on an overlay of the lab, so a new person can figure out where things live.
- A container module basically represents a tree view of lab. Inside of a lab is a room, inside of that room is a freezer, inside of that freezer are shelves, inside of those shelves are racks, and inside those racks are plates. For example, see here https://api.freegenes.org/containers/tree_view_full/ . The idea is to be able to tell an end user "please grab this plate from this specific location and move it to this other specific location"
- Modules are physical lab capabilities. From a protocol-generation perspective side (protocol in terms of a lab protocol, or lab procedure), you can query for a lab's capabilities and then generate a protocol that fits their capabilities. If I have an OpenTrons available with a pipette, it will make a protocol for an opentrons, if there is a human available, it will make a protocol for a human. This is important further down the line to have for general-use protocols, and so have some simple implementations here. Right now, there are magdeck modules, pipette modules, and tempdeck modules, each of which have a different JSON schema.

## Plates and samples

- Breadcrumb is the legacy implementation of the lab "tree view" storing the information as a string. It is used as navigation just like in a web page, except in the real world.
- It is very important to track the number of times a plate has been frozen and thawed. Each freeze thaw damages the cells, until eventually the plate is unusable. 
- "index_for" and "index_rev" have a pretty specific meaning. They are used for samples we want to sequence, and although we don't need them often, we do need them to automate sequencing. They do stand for "Index forward" and "Index reverse".


## Samples

In the biological world, we can have a piece of DNA that is hypothetically matches what we have on a computer, but most of the time we don't really know. A sample is simply a part that we have some level of confidence exists in the real world. 

For example, if we have some frozen bacteria, and scrape a little off and put it into a new tube to grow overnight, the new growth is not the same sample as the frozen bacteria (maybe there was some contamination, or maybe we bottlenecked the population so there are more mutations). We think it's status is confirmed, but the only evidence we have is that it was "Derived" from a confirmed sample. 

However, if now we take that new growth and split it between 10 wells and freeze them, all those new frozen bacteria are the same sample (they theoretically are all the same). 

### Evidence

At very best, we have sequencing data for a sample in our lab. This is the "evidence" we have for the state of a sample. The next best is someone else sequencing the sample (in which we are often not privy to the data), and the worst is if the evidence of the state of a sample is just that it is Derived from something else. 

Importance: Each sequencing method is different (Sanger kind of sucks, and so it isn't well trusted, while NGS is very strong, and we completely trust it) which is important. Sequencing providers we also have more or less confidence in: In my professional experience (of both ordering and watching others order) sometimes we get samples that just aren't that we asked for. If we decide to resequence some samples from X and see a 50% mutation rate, we know that we should probably check out the rest of the samples from X.

## PlateSet vs Distribution

A plateset is actually just a collection of identical plates. A distribution is a collection of platesets.  When you order a distribution, you are technically ordering one plate from each one of the platesets in the distribution. Only once a shipment comes around does it become concrete which plates are physically getting sent out. A the minimium, a distribution can be a single plateset. At most, a distribution can be all platesets (and there may be overlap) The only thing that is being sent out is 1 or more plates, but the abstraction is useful.


## Schemas

Schemas are shared between types of protocols, and so aren't supposed to be special snowflakes. For this
reason, we model them as an object that can be shared between others.
