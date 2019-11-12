

# Dokku setup
SSH into your new Dokku server.

# Install redis on dokku
The FreeGenes app uses redis for caching. Dokku has a convenient 

dokku plugin:install https://github.com/dokku/dokku-redis.git redis

dokku redis:create fg-django-redis

dokku redis:link fg-django-redis freegenes-django-stage


# Install postgres on dokku
sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git postgres

dokku postgres:create fg-django-pg

dokku postgres:link fg-django-pg freegenes-django-stage

[
    postgres:backup <service> <bucket-name> [-u|--use-iam-optional]                 creates a backup of the Postgres service to an existing s3 bucket
    postgres:backup-auth <service> <aws-access-key-id> <aws-secret-access-key>...   sets up authentication for backups on the Postgres service
    postgres:backup-deauth <service>                                                removes backup authentication for the Postgres service
    postgres:backup-schedule <service> <schedule> <bucket-name>...                  schedules a backup of the Postgres service
    postgres:backup-schedule-cat <service>                                          cat the contents of the configured backup cronfile for the service
    postgres:backup-set-encryption <service> <passphrase>                           sets encryption for all future backups of Postgres service
]



# letsencrypt

dokku plugin:update letsencrypt

dokku config:set --no-restart freegenes-django-stage DOKKU_LETSENCRYPT_EMAIL=koeng101@gmail.com

dokku letsencrypt freegenes-django-stage

dokku letsencrypt:cron-job --add

