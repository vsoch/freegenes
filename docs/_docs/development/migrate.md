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

and then run the script.

```bash
$ python scripts/export_flask.py
```

It will create a subfolder in scripts, "data", that organizes data exported to json,
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
