---
title: Deployment start containers
description: Start containers to deploy your FreeGenes node
tags: 
 - docker
 - docker-compose
---

# Docker Compose

At this point you should have cloned the repository to your server, edited the settings files to select the authentication, rate limits, and other settings, generated the secrets file with credentials for third party services, and set up networking. Personally, I like to have https ready to go before turning anything on - if you haven't done this yet
go back to [here](https://vsoch.github.io/freegenes/docs/development/setup#domain-name). After those steps, you should be ready to start your node. 

## Containers

If you haven't built the primary container yet:

```bash
$ docker build -t vanessa/freegenes .
```

Additionally, the application container is built at [quay.io/vsoch/freegenes](https://quay.io/repository/vsoch/freegenes) and can be pulled and tagged appropriately:

```bash
$ docker pull quay.io/vsoch/freegenes:devel
$ docker tag quay.io/vsoch/freegenes:devel vanessa/freegenes
```

Specifically, we build the following tags via the [.circleci recipe](https://github.com/vsoch/freegenes/blob/master/.circleci/config.yml):

 - devel: is built on any push to master
 - vM.M.M: is a version built on a release or tag
 - Opening a pull request tests a build

Once you have your container (pull or build) you can start the containers with:

```bash
$ docker-compose up -d
```

And likely you'll want to look at logs of containers to make sure everything looks OK:

```bash
$ docker-compose logs uwsgi
$ docker-compose logs db
$ docker-compose logs worker
$ docker-compose logs scheduler
$ docker-compose logs nginx
```

If you want to have logs streaming live in a window, add "-f":

```bash
$ docker-compose logs -f uwsgi
```

## Logging in

Next you should be able to go to the interface at either [127.0.0.1](127.0.0.1) (for development)
or your domain (for deployment). You'll want to log in to create your account, and remember
your username. For example, when I log in with GitHub my username is @vsoch.

### Adding Staff and Superusers

Django has two roles for administrators of the site. A superuser is an all powerful, can
edit / delete / do anything role, and a staff is a limited subset of that role. To add or remove
staff, after the users have added their accounts you can shell into the main uwsgi container:

```bash
# press tab to autocomplete
# docker exec -it freegenes-django_uwsgi_[TAB]
$ docker exec -it freegenes-django_uwsgi_1_ed95e258455c bash
```

And then add or remove a superuser or staff.

```bash
$ python manage.py add_superuser vsoch
vsoch is now a superuser.
$ python manage.py remove_superuser vsoch
vsoch is no longer a superuser.
```
```bash
$ python manage.py add_staff vsoch
vsoch is now FreeGenes staff.
$ python manage.py remove_staff vsoch
vsoch is not longer staff.
```

> **Important** a user must be a staff and a superuser to access the Django default admin interfaces. If you don't want to create an account with a social backend, you can also do so on the command line interactively:

```bash
$ python manage.py createsuperuser
```

