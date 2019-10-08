---
title: Admin Pages
description: FreeGenes administrative views
---

# Admin Pages

When you've added a user as staff or a superuser, he or she can access the 
admin views at `/admin`:

![admin-home.png]({{ site.baseurl }}/docs/usage/img/admin-home.png)

All of the models are viewable (and editable there). For example,
here is the table of plates that we see when we click on "plates":

![admin-table.png]({{ site.baseurl }}/docs/usage/img/admin-table.png)

The fields that are shown can be customized, and @vsoch has chosen the fields
and an order that makes sense (but it can be changed). Clicking on a single plate
will then show a detail view, where you could also edit fields:

![admin-change.png]({{ site.baseurl }}/docs/usage/img/admin-change.png)

or add a new entity entirely:

![admin-add.png]({{ site.baseurl }}/docs/usage/img/admin-add.png)

For some of these views, this "form click and add" approach would not
be most appropriate, and the views will be further customized, or additional
views added to the front end for administrators, or actions generated
to be run via an API endpoint. @vsoch hasn't delved into the user stories
yet to design this.
