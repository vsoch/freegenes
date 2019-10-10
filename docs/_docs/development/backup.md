---
title: Deployment backup
description: Deployment backup
tags: 
 - docker
---

# Backup

With changes to models and heavy development, there can be mistakes and errors
related to losing data. We can only do our best to back up the data locally,
back up the containers, and take snapshots of the server. This guide will provide 
detail to that.

## Snapshots

Google Cloud makes it easy to generate a snapshot schedule,
and then edit a Disk to associate it. Full instructions are [here](https://cloud.google.com/compute/docs/disks/scheduled-snapshots), and basically it comes down to:

 - Creating a snapshot schedule under Compute -> Snapshots. I chose daily, with snapshots expiring after 14 days
 - Editing the Disk under Compute -> Disks to use it.


## Containers

Since this is run directly on the server using Docker, it must be run with
the local cron. You can use crontab -e to edit the cron file, and crontab -l
to list and verify the edits. Specifically, you need to add this line:

```cron
0 1 * * * docker commit freegenes_uwsgi_1 quay.io/vsoch/freegenes:snapshot
0 1 * * * docker commit freegenes_db_1 quay.io/vsoch/freegenes-postgres:snapshot
0 1 * * * docker commit freegenes_redis_1 quay.io/vsoch/freegenes-redis:snapshot
```

This will run a docker commit at 1:00am, daily, using the container name
"freegenes_uwsgi_1" and saving to "quay.io/vsoch/freegenes:snapshot". When the snapshot
is saved for the disk (at 3-4am per the previous instructions) then
this container should be included.

## Database

There is a backup script in "scripts/backup_db.sh" that works when run manually,
but doesn't seem to work when run with cron. For this reason, we instead
run it via a scheduled task, defined in "fg/apps/main/utils/backup_db". If you
look at the worker container logs, you can see it running:

```bash
$ docker-compose logs --tail=30 worker
worker_1_41cb72457b36 | 12:50:07 Worker rq:worker:73375898a4f149408e68ec12bddd1ead: started, version 1.1.0
worker_1_41cb72457b36 | 12:50:07 *** Listening on default...
worker_1_41cb72457b36 | 12:51:07 default: fg.apps.main.utils.backup_db() (56867a75-9947-4a6d-bfd3-cfb764f7f66f)
```

It should run infinitely, every day.
