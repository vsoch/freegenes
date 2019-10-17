---
title: Deployment setup
description: Deployment setup
tags: 
 - docker
---

# Setup

You'll first need to clone the repository to your local machine, or where you
intend to deploy it.

```bash
$ git clone https://github.com/vsoch/freegenes
```

Ensure that you have both [Docker](https://docs.docker.com/install/) and 
[Docker Compose](https://docs.docker.com/compose/install/) installed. To make
this entire process easier, we've provided a [script](https://github.com/vsoch/freegenes/blob/master/scripts/prepare_instance.sh) that will handle installing Docker, docker-compose, cloning,
and building the FreeGenes container. Note that you'll need to log in and out after
adding your user to the Docker group for Docker to function properly without needing sudo.

## Google Cloud

For development deployment on Google Cloud, you will want to first log in to your project and [create an instance](https://console.cloud.google.com/compute/instances). Notes are in
[script](https://github.com/vsoch/freegenes/blob/master/scripts/prepare_instance.sh), and repeated here for clarity:

 - **Region** you want to be as close to where your main operations are as possible. For CA, this typically means us-west1, and then choose a,b, or c. The actual instances for a/b/c vary by project, so your choice of A isn't equal to another project's, so don't worry too much about your choice.
 - **Machine Family** I typically choose General purpose, because we just need a basic linux base.
 - You don't need to select that we are deploying a container to the instance - we are, but we don't need the special "Container OS" that Google Cloud offers.
 - **Machine Type** It's best to choose a smaller (but not too small) size, typically I choose n1-standard-2 (2 vCPUs, 7.5 GB memory).
 - **Boot Disk** Even for development, you always want to chose an image with long term support. E.g., for now I would choose Ubuntu 18.04 LTS (long term support). There is a minimal image that works well.
 - **API Access** you generally want to limit to only those endpoints that are needed. For the current FreeGenes we don't need additional, however I anticipate using Google Storage and possibly Big Query.
 - You want to allow both http/https traffic - this server will be exposed to the web.
 - Under management, I like to enable "Delete protection." You never know if/when someone might click a button by accident.
 - Under management-> networking, you can click on the "default" interface to ensure that you have a static (and not ephemeral) ip address. This is important so that if we ever need to re-create the server, we can use the same DNS settings and have confidence that we have the ip address.

### Billing

Under billing, it's good practice to also set up billing alerts - unintended charges to a project that you don't know about can have dire consequences. A small server of this size shouldn't cost more than $10 a day (this would be a LOT) so I generally would start with a lower monthly limit (possibly $300) with alerts at 25, 50, 75, and 100, and adjust as needed.

> We will be adding production deployment specific clones and setup once they are determined, for now this is assumed to be local development or deployment on a server. This setup could very well serve in production.

## Settings

By the time you get here, you should be sitting on a server, have dependencies installed via the [prepare instance script](https://github.com/vsoch/freegenes/blob/master/scripts/prepare_instance.sh), and have cloned the FreeGenes repository to your $HOME (or a shared location where you want to install it).

The primary workings of your FreeGenes node are determined by how you configure
it in the application settings, which are located in the [settings folder](https://github.com/vsoch/freegenes/blob/master/fg/settings). In that folder are a group of different files with default settings for your application. 
In this guide, we will walk through how you can customize them for your needs. Generally, these changes
come down to making updates in two files:

 1. We will generate a `settings/secrets.py` from a dummy template [settings/dummy_secrets.py](https://github.com/vsoch/freegenes/blob/master/fg/settings/dummy_secrets.py) for application secrets. 
 2. The file [settings/config.py](https://github.com/{{ site.github_user }}/{{ site.github_repo }}/blob/master/fg/settings/config.py) has values to configure your database and FreeGenes server.

### Secrets

There should be a file called `secrets.py` in the FreeGenes settings folder (it won't exist in the repo, you have to make it), in which you will store the application secret and other social login credentials.

An template to work from is provided in the settings folder called `dummy_secrets.py`. You can copy this template:

```bash
cp fg/settings/dummy_secrets.py fg/settings/secrets.py
```

Or, if you prefer a clean secrets file, create a blank one as below:

```bash
touch fg/settings/secrets.py
```

and inside you want to add a `SECRET_KEY`. You can use the [secret key generator](http://www.miniwebtool.com/django-secret-key-generator/) to make a new secret key, and call it `SECRET_KEY` in your `secrets.py` file, like this:

```python
SECRET_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

### Shipping Secrets

We will use [shippo](https://goshippo.com/docs) to generate labels for orders. The only requirement after you create
an account is to export a `SHIPPO_TOKEN` in your secrets.py:

```python
SHIPPO_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Shippo usually can provide a test and a live token, so you can first test with the testing token. Additionally,
if you use FedEx and want to add a Customer_Reference field, define this in your secrets:

```python
SHIPPO_CUSTOMER_REFERENCE="1111111-1-DENRC"
```

### SendGrid Secrets

To send PDFs (and other emails) from the server, we use SendGrid. This means
that you need to [sign up](https://app.sendgrid.com/) for an account (the basic account with 100 emails
per day is free) and then add the `SENDGRID_API_KEY` to your settings/config.py:

```python
SENDGRID_API_KEY=xxxxxxxxxxxxxxx
```

To create your key:

 1. Go to [SendGrid](https://app.sendgrid.com/) and click on Settings -> Api keys in the left bar
 2. Click the blue button to "Create API key"
 3. Give your key a meaningful name (e.g., freegenes_dev_test)
 4. Choose "Restricted Access" and give "Full Access" to mail send by clicking the bar on the far right circle.
 5. Copy it to a safe place, likely your settings/config.py (it is only shown once!)

If the value is found to be None, emails will not be sent.

### Twist Import

The Twist API is buggy and getting tokens is challenging, so we use a simple
strategy of importing Plate Maps (export from Twist) to import plates.
You don't need any secrets here.


### Map Tokens

The Orders Map (a map of all historical orders found at the route /map/orders) is generated using Mapbox GL JS (https://docs.mapbox.com/mapbox-gl-js/api/).

In order for the JS library to generate the map, you need to supply a valid Mapbox access token ("mapboxgl.accessToken" in the JavaScript that creates the map). This variable is populated from the MAPBOX_ACCESS_TOKEN in your settings/config.py or in settings/secrets.py as follows:

```python
MAPBOX_ACCESS_TOKEN = 'XXXXX'
```

This token is passed from the server to the Orders Map template and can be set as a configuration variable.

Once you log in to your account, you can click on "tokens" in the settings bar and write your
token to your secrets.py file.

### Authentication Secrets

One thing that cannot be donein advance is to produce application keys and secrets to give your FreeGenes node for each social provider that you want to allow users (and yourself) to login with. We are going to use a framework called [python social auth](https://python-social-auth-docs.readthedocs.io/en/latest/configuration/django.html) to achieve this, and in fact you can add a [number of providers](http://python-social-auth-docs.readthedocs.io/en/latest/backends/index.html).

For special cases like SAML or LDAP, see the [plugins]({{ site.baseurl }}/docs/plugins/) section as they are slightly more complicated and have been done in advance for you. If there is a backend that you want to add, please <a href="https://www.github.com/{{ site.github_user }}/{{ site.github_repo }}/isses" target="_blank">submit an issue</a>.

Using OAuth2 with a token-->refresh flow gives the user power to revoke permission at any point, and also
allows you as the provider to revoke all tokens if necessary. This is a better strategy than storing a database
of usernames and passwords. To choose the authentication backends that you want to use (outside of plugins)
just set them to True in the `settings/config.py`:

```python
# Which social auths do you want to use?
ENABLE_GOOGLE_AUTH = False
ENABLE_ORCID_AUTH = False
ENABLE_ORCID_AUTH_SANDBOX = False
ENABLE_TWITTER_AUTH = False
ENABLE_GITHUB_AUTH = True
ENABLE_GITLAB_AUTH = False
ENABLE_BITBUCKET_AUTH = False
```

You will need at least one to log in. I've found that Github works the fastest and easiest, and then Google. Twitter now requires an actual server name and won't work with localost, but if you are deploying on a server with a proper domain go ahead and use it. All avenues are extremely specific with regard to callback urls, so you should be very careful in setting them up. 

## Plugins

As mentioned previously, other authentication methods, such as LDAP, are implemented as [plugins]({{ site.baseurl }}/docs/plugins/). See the [plugins documentation]({{ site.baseurl }}/docs/plugins/) for details on how to configure these. You should also now look here to see which plugins you will want to set up (and then build into your container).

For authentication plugins, we will walk through the setup of each in detail here. 
For other plugins, you should look at the [plugins]({{ site.baseurl }}/docs/plugins/) documentation now before proceeding. For all of the below, you should put the content in your `secrets.py` under settings. Note that if you are deploying locally, you will need to put localhost (127.0.0.1) as your domain, and Github is now the only one that worked reliably without an actual domain for me.

### Globus OAuth2

Complete instructions for Globus are [here](https://globus-integration-examples.readthedocs.io/en/latest/django.html#develop-web-application). You'll need to go to [https://developers.globus.org/](https://developers.globus.org/) to get your client key and secret, and also designate the redirect urls:

```
https://<your_server_host_name/<prefix>/complete/globus/
``` 

For scopes, I chose:

```
Profile
View identity Set
Email
Openid
View identities on Globus Auth
```

And then add the key, secret, and extra args to your secrets.py in the settings folder.

```python
SOCIAL_AUTH_GLOBUS_KEY = '<your_Globus_Auth_Client_ID>'
SOCIAL_AUTH_GLOBUS_SECRET = '<your_Globus_Auth_Client_Secret>'
SOCIAL_AUTH_GLOBUS_AUTH_EXTRA_ARGUMENTS = {
    'access_type': 'offline',
}
```

### Orcid OAuth2

[Orcid](https://python-social-auth.readthedocs.io/en/latest/backends/orcid.html) allows for
a user to login with their orcid id. It also supports a "sandbox" mode for local
development. For each, define these variables in your `settings/config.py`:

```python
SOCIAL_AUTH_ORCID_KEY = ''
SOCIAL_AUTH_ORCID_SECRET = ''

# or 

SOCIAL_AUTH_ORCID_SANDBOX_KEY = ''
SOCIAL_AUTH_ORCID_SANDBOX_SECRET = ''
```

All keys can be generated in the [Orcid Developer Tools](https://orcid.org/developer-tools).
The callback uri should be `http://<your-server>/complete/orcid/`

### Google OAuth2

You first need to [follow the instructions](https://developers.google.com/identity/protocols/OpenIDConnect) and setup an OAuth2 API credential. The redirect URL should be every variation of having http/https, and www. and not. (Eg, change around http-->https and with and without www.) of `https://<your-server>/complete/google-oauth2/`. Google has good enough debugging that if you get this wrong, it will give you an error message with what is going wrong. You should store the credential in `secrets.py`, along with the complete path to the file for your application:

```python
GOOGLE_CLIENT_FILE='/code/.grilledcheese.json'

# http://psa.matiasaguirre.net/docs/backends/google.html?highlight=google
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'xxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'xxxxxxxxxxxxxxxxx'
# The scope is not needed, unless you want to develop something new.
#SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['https://www.googleapis.com/auth/drive']
SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS = {
    'access_type': 'offline',
    'approval_prompt': 'auto'
}
```

Google is great in letting you specify multiple acceptable callback urls, so you should set every version of `http://127.0.0.1/complete/google-oauth2` (I did with and without http/https, along with the ending and without the ending slash, just in case). Note that `1.` extra arguments have been added to ensure that users can refresh tokens, and `2.` in testing I was using `http` and not `https`, and I eventually added `https` (and so the url was adjusted accordingly). Next, we need to follow instructions for [web applications](https://developers.google.com/identity/protocols/OAuth2WebServer). 

### Setting up Github OAuth

For users to connect to Github, you need to [register a new application](https://github.com/settings/applications/new), and add the key and secret to your `secrets.py` file like this: 

```python
# http://psa.matiasaguirre.net/docs/backends/github.html?highlight=github
SOCIAL_AUTH_GITHUB_KEY = ''
SOCIAL_AUTH_GITHUB_SECRET = ''

SOCIAL_AUTH_GITHUB_SCOPE = ["user:email"]
```

The callback url should be in the format `http://127.0.0.1/complete/github`, and replace the localhost address with your domain. See the [Github Developers](https://github.com/settings/developers) pages to browse more information on the Github APIs.

### Gitlab OAuth2

Instructions are provided [here](https://github.com/python-social-auth/social-docs/blob/master/docs/backends/gitlab.rst). Basically:

 1. You need to [register an application](https://gitlab.com/profile/applications), be sure to add the `read_user` scope. If you need `api`, add it to (you shouldn't).
 2. Set the callback URL to `http://<your-server>/complete/gitlab/`. The URL **must** match the value sent. If you are having issues, try adjusting the trailing slash or http/https/. 
 3. In your `secrets.py` file under settings, add:

```
SOCIAL_AUTH_GITLAB_SCOPE = ['api', 'read_user']
SOCIAL_AUTH_GITLAB_KEY = ''
SOCIAL_AUTH_GITLAB_SECRET = ''
```

Where the key and secret are replaced by the ones given to you. If you have a private Gitlab, you need to add it's url too:

```
SOCIAL_AUTH_GITLAB_API_URL = 'https://example.com'
```

### Bitbucket OAuth2

We will be using the [bitbucket](https://python-social-auth.readthedocs.io/en/latest/backends/bitbucket.html) backend for Python Social Auth.

First, register a new OAuth Consumer by following the instructions in the [Bitbucket documentation](https://confluence.atlassian.com/bitbucket/oauth-on-bitbucket-cloud-238027431.html). Overall, this means registering a new consumer, and making sure to add the "account" scope to it. You can find the button to add a consumer in your BitBucket profile (click your profile image from the bottom left of [the dashboard](https://bitbucket.org/dashboard/overview).

![{{ site.baseurl }}/assets/img/bitbucket-consumer.png]({{ site.baseurl }}/assets/img/bitbucket-consumer.png)

After clicking the button, fill in the following values:

 - Name: choose a name that will be easy to link and remember like "FreeGenes Node MyLab"
 - Callback URL: should be `http://[your-domain]/complete/bitbucket` For localhost, this is usually `http://127.0.0.1/complete/bitbucket`
 - Keep the button "This is a private consumer" checked.
 - Under Permissions (the scope) click on Account (email, read, write).


Then, when you click to add the consumer, it will take you back to the original pacge. To get the key and secret, you should click on the name of the consumer. Then add the following variables to your `secrets.py` file under settings:

```python
SOCIAL_AUTH_BITBUCKET_OAUTH2_KEY = '<your-consumer-key>'
SOCIAL_AUTH_BITBUCKET_OAUTH2_SECRET = '<your-consumer-secret>'
```

 3. Optionally, if you want to limit access to only users with verified e-mail addresses, add the following:

```python
SOCIAL_AUTH_BITBUCKET_OAUTH2_VERIFIED_EMAILS_ONLY = True
```

Finally, don't forget to enable the bitbucket login in settings/config.py:

```python
ENABLE_BITBUCKET_AUTH=True
```

### Setting up Twitter OAuth2

You can go to the [Twitter Apps](https://apps.twitter.com/) dashboard, register an app, and add secrets, etc. to your `secrets.py`:

```bash
SOCIAL_AUTH_TWITTER_KEY = ''
SOCIAL_AUTH_TWITTER_SECRET = ''
```

Note that Twitter now does not accept localhost urls. Thus, 
the callback url here should be `http://[your-domain]/complete/twitter`.



## Config

In the [config.py](https://github.com/{{ site.github_user }}/{{ site.github_repo }}/blob/master/fg/settings/config.py) you need to define the following:


### Domain Name

A FreeGenes server should have a domain. It's not required for local development.
Thus, the first thing you should do is change the `DOMAIN_NAME_*` variables in your settings [settings/config.py](https://github.com/{{ site.github_user }}/{{ site.github_repo }}/blob/master/fg/settings/config.py).

For local testing, you will want to change `DOMAIN_NAME` and `DOMAIN_NAME_HTTP` to be localhost. Also note that I've set the regular domain name (which should be https) to just http because I don't have https locally:

```python
DOMAIN_NAME = "http://127.0.0.1"
DOMAIN_NAME_HTTP = "http://127.0.0.1"
```

When you deploy, you should [obtain https certificates](https) and set up your DNS, along with
ensuring that the `DOMAIN_NAME` above uses https. It's up to the deployer to set one up a domain or subdomain for the server. Typically this means going into the hosting account to add the A and CNAME records, and then update the DNS servers. Since every host is a little different, I'll leave this up to you, but [here is how it's done on Google Cloud](https://cloud.google.com/dns/quickstart).


### FreeGenes Node Contact

You need to define a FreeGenes node uri, and different contact information:

> **Important** The `HELP_CONTACT_EMAIL` and `HELP_CONTACT_PHONE` are used for the Shippo API, and the `HELP_CONTACT_EMAIL` is used for SendGrid (if you provide an api key for it). Ensure that both are valid contacts that can be received by lab personell. The `NODE_INSTITUTION` is also used for the company field.

```python
HELP_CONTACT_EMAIL = 'vsochat@stanford.edu'
HELP_CONTACT_PHONE = '123-456-7890'
HELP_INSTITUTION_SITE = 'https://srcc.stanford.edu'
NODE_INSTITUTION = 'Stanford University'
NODE_URI = "srcc"
NODE_NAME = "Stanford Research Computing Center"
```

The `HELP_CONTACT_EMAIL` should be an email address that you want your users (and/or visitors to your registry site, if public) to find if they need help. The `HELP_INSTITUTION_SITE` is any online documentation that you want to be found in that same spot. Finally, `NODE_NAME` is the long (human readable with spaces) name for your FreeGenes node, and `NODE_URI` is a string, all lowercase, 12 or fewer characters to describe your node.


### Database

By default, the database itself will be deployed as a postgres image called `db`. You probably don't want this for production (for example, I use a second instance with postgres and a third with a hot backup, but it's an ok solution for a small cluster or single user. Either way, we recommend backing it up every so often.

When your database is set up, you can define it in your `secrets.py` and it will override the Docker image one in the `settings/main.py file`. It should look something like this

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dbname',
        'USER': 'dbusername',
        'PASSWORD':'dbpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Rate Limits

It's hard to believe that anyone would want to maliciously issue requests to your server,
but it's unfortunately a way of life. For this reason, all views have a rate limit, along
with blocking ip addresses that exceed it (for the duration of the limit, one day). You
can customize this:

```python
VIEW_RATE_LIMIT="50/1d"  # The rate limit for each view, django-ratelimit, "50 per day per ipaddress)
VIEW_RATE_LIMIT_BLOCK=True # Given that someone goes over, are they blocked for the period?
```

And see the [django-ratelimit](https://django-ratelimit.readthedocs.io/en/v1.0.0/usage.html) documentation
for other options. 

Next, you might want to [start your containers]({{ site.baseurl }}/docs/development/start)
