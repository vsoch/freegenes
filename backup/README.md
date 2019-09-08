# Backup

This README contains information about backing up containers and the database.

## Static Files

If you use FreeGenes Django with the default storing static files and data
on the filesystem, both will be preserved on the host in [static](../static) and [data](../data),
respectively. This means that you can restore the node with previous uploads, given that
these folders on the host are bound at `/code` in the container.

## Database

This directory will be populated with a nightly backup.
It's run via a cron job that is scheduled in the
main uwsgi container:

```bash
RUN echo "0 1 * * * /bin/bash /code/scripts/backup_db.sh" >> /code/cronjob
```

It's a fairly simple strategy that will minimally allow you to restore your
database given that you accidentally remove and then recreate the db container.
For example, here we've started the containers, created some content, 
and then we (manually) create a backup:

```bash
$ docker exec -it freegenes-django_uwsgi_1_dc732361af2b bash
$ /bin/bash /code/scripts/backup_db.sh
$ exit
```

Then stop and remove your containers.

```bash
$ docker-compose stop
$ docker-compose rm
```

Bring up the containers, and check the interface if you like to verify your
previous data is gone. Again shell into the container,
but this time restore data.

```bash
$ docker exec -it sregistry_uwsgi_1_a5f868c10aa3 bash
$ /bin/bash /code/scripts/restore_db.sh
Loading table users
Installed 1 object(s) from 1 fixture(s)
Loading table api
Installed 1 object(s) from 1 fixture(s)
Loading table main
Installed 2 object(s) from 1 fixture(s)
Loading table logs
Installed 0 object(s) from 1 fixture(s)
```

If you browse to the interface, your content should then be restored.
