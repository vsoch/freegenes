---
title: Export
description: Export data from the previous https://api.freegenes.org
---

In the [scripts folder](https://github.com/vsoch/freegenes/tree/master/scripts) you'll find 
a script, `export_flask.py`, that can be run to export (most) previous data from
the FreeGenes Flask version of the API. You should first get a username and password
from [Koeng101](https://www.github.com/Koeng101) and then export to the environment:

```bash
export FREEGENES_USER=myusername
export FREEGENES_PASSWORD=secretpassword
```

## 1. Export from Flask
To export from the Flask API, just run the script.

```bash
$ python scripts/export_flask.py
```

Note that there are a subset of files (ending in "pileup") that, at the time of writing
this script, persisted at the Files endpoint but were removed from storage (and this return
a 500 server error). The script passes over these files, so it shouldn't cause an error for
you to run it. Detail is provided [here](https://github.com/vsoch/freegenes/issues/15).

After running the script, it will create a subfolder in scripts, "data", that organizes data exported to json,
along with files, by the date:

```bash
scripts/data/
└── 2019-08-15
    ├── address-full.json
    ├── address.json
    ├── authors-full.json
    ├── authors.json
    ├── collections-full.json
    ├── collections.json
    ├── containers-full.json
    ├── containers.json
    ├── distribution-full.json
    ├── distribution.json
    ├── files
    │   ├── BioBlaze_openenzyme.pdf
    │   ├── BWB.pdf
    │   ├── cambridge_openmta_openenzyme.csv
    │   ├── ChiTown_openenzyme.pdf
    │   ├── larkin_openmta_pOpen_v3.pdf
    │   ├── Manifest_Biology_OpenMTA.pdf
    │   ├── Soundbio_openenzyme.pdf
    │   └── TheLab_openenzyme.pdf
    ├── files.json
    ├── institution-full.json
    ├── institution.json
    ├── materialtransferagreement-full.json
    ├── materialtransferagreement.json
    ├── modules-full.json
    ├── modules.json
    ├── operations-full.json
    ├── operations.json
    ├── order-full.json
    ├── order.json
    ├── organisms-full.json
    ├── organisms.json
    ├── parcel-full.json
    ├── parcel.json
    ├── parts-full.json
    ├── parts.json
    ├── plans-full.json
    ├── plans.json
    ├── plateset-full.json
    ├── plateset.json
    ├── plates-full.json
    ├── plates.json
    ├── protocols-full.json
    ├── protocols.json
    ├── robots-full.json
    ├── robots.json
    ├── samples-full.json
    ├── samples.json
    ├── schemas-full.json
    ├── schemas.json
    ├── shipment-full.json
    ├── shipment.json
    ├── wells-full.json
    └── wells.json

2 directories, 53 files
```

We will use this data to populate the FreeGenes Django database next.

## 2. Import into Django
 
At this point, you should [continue with setup]({{ site.baseurl }}/docs/development/) and return to this step
after you've started the containers with:

```bash
$ docker-compose up -d
```

When the containers are running, you can use `docker ps` to get their names, and
then you will want to shell in to the uwsgi container:

```bash
$ docker exec -it freegenes-django_uwsgi_1_ed95e258455c bash
```

If you know that the beginning starts with "freegenes-django_uwsgi*" you can
use tab to autocomplete the rest of the name. 
The script to import data simply takes the data folder as an argument, which
is bound to the container at `/code/scripts/data/<date>`. As an example:

```bash
$ python manage.py import_flask_json /code/scripts/data/2019-08-15
```

will import the json from those exports into the current database. There are
over 10K wells so the original import can take a minute.

