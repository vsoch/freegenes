---
title: Getting Started
tags: 
 - jekyll
 - github
 - freegenes
description: Getting started with FreeGenes
---

# Getting Started

The documentation here will get you started to use FreeGenes, developed
with Python and Django.

## Who is FreeGenes For?

FreeGenes is developed as an instance of a node in the [bionet](https://biobricks.org/bionet/). 
In that it's a set of microservices (web server, application, worker, database) it's expected
that a lab would deploy a node to provide the lab with an internal support system
to manage biological entities and orders, and the outside world a portal for
searching and requesting these entities. It is not expected that a single node
would be shared by more than one lab, as this would complicate the sharing of
data and permissions, but it's not technically impossible to do.

## Development

 - [Setup](development/setup): building containers and setting up.
