#!/bin/bash

# **Important** run this command from inside the container, where you have
# Django and dependencies installed. This is typically run automatically 
# (nightly) via a cron job. See the Dockerfile, or shell into the uwsgi container:
# > service cron status
# > crontab -l
# > crontab -e

for db in "users" "main" "orders" "factory"
  do
    echo "Backing up $db"

    # Keep 1 day previous
    if [ -f "/code/backup/$db.json" ]; then
        mv /code/backup/$db.json /code/backup/$db1.json
    fi
    python /code/manage.py dumpdata $db --output /code/backup/$db.json
done

# All models in one file, for loading with loaddata
if [ -f "/code/backup/models.json" ]; then
    mv /code/backup/models.json /code/backup/models1.json
fi

python /code/manage.py dumpdata main users orders factory --output /code/backup/models.json

# Everything
if [ -f "/code/backup/db.json" ]; then
    mv /code/backup/db.json /code/backup/db1.json
fi

python /code/manage.py dumpdata --output /code/backup/db.json
