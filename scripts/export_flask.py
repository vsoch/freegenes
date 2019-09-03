#!/usr/bin/env python

# This script will use the api.freegenes.org to export current data, saved 
# in a folder here as json to import into the new database.
# FREEGENES_USER and FREEGENES_PASSWORD should be export to the environment.

from datetime import datetime
import json
import os
import re
import requests
import sys

username = os.environ.get('FREEGENES_USER')
password = os.environ.get('FREEGENES_PASSWORD')
api_base = "https://api.freegenes.org"

# Organize data based on when downloaded
today = datetime.now().strftime('%Y-%m-%d')

# Endpoints to download json, excluding files
endpoints = ["collections", "collections/full", 
             "parts", "parts/full",
             "authors", "authors/full",
             "organisms", "organisms/full",
             "protocols", "protocols/full",
             "plates", "plates/full",
             "samples", "samples/full",
             "wells", "wells/full",
             "files",
             "operations", "operations/full",
             "plans", "plans/full",
             "plateset", "plateset/full",
             "distribution", "distribution/full",
             "order", "order/full",
             "institution", "institution/full",
             "materialtransferagreement", "materialtransferagreement/full",
             "shipment", "shipment/full",
             "address", "address/full",
             "parcel", "parcel/full",
             "containers", "containers/full",
             "robots", "robots/full",
             "modules", "modules/full",
             "schemas", "schemas/full"]

if not username or not password:
    print('Please export FREEGENES_USER and FREEGENES_PASSWORD to the environment')
    sys.exit(1)

# Save to data folder in the scripts directory, organized by date
save_base = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
save_to = os.path.join(save_base, today)
files = os.path.join(save_to, 'files')
for folder in [save_base, save_to, files]:
    if not os.path.exists(folder):
        print('Creating output directory %s' % folder)
        os.mkdir(folder)

# Helper Functions #############################################################

def save_json(content, output_file):
    '''save dictionary to file as json
    '''
    with open(output_file, 'w') as filey:
        filey.writelines(json.dumps(content, indent=4))
    return output_file

def get_auth_token(username, password):
    token_url = 'https://auth.services.freegenes.org/users/admin/token/11111'
    response = requests.get(token_url, auth=(username, password))
    if response.status_code != 200:
        print('Error with %s' % token_url)
        sys.exit(1)
    return response.json()['token']


def download_file(url, output_file, mode='wb'):
    '''stream a file to download'''
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(output_file, mode) as filey:
            for chunk in response.iter_content(chunk_size=8192): 
                if chunk: 
                    filey.write(chunk)
        return output_file


################################################################################

for endpoint in endpoints:

    # For each endpoint, save to data
    output_file = os.path.join(save_to, "%s.json" % endpoint.replace('/', '-'))
    url = "%s/%s" %(api_base, endpoint)

    # Make request if not done yet
    if not os.path.exists(output_file):
        print("GET %s" % url)
 
        if re.search('(shipment|address|parcel)', endpoint):
            try:
                token = get_auth_token(username, password)
                response = requests.get(url, json={'token': token})
            except:
                continue
        else:
            response = requests.get(url)

        if response.status_code != 200:
            print('Error with %s' % url)
            sys.exit(1)

        # Save to json file in data, pretty printed
        save_json(response.json(), output_file)


# Separately download files
files_url = "%s/files" % api_base
response = requests.get(files_url)
for entry in response.json():
    url = "%s/download/%s" % (files_url, entry['uuid'])
    output_file = os.path.join(files, entry['name'])
    if not os.path.exists(output_file):
        print('Downloading %s' % output_file)

        # Internal server error
        if output_file.endswith('pileup'):
            continue
        else:
            download_file(url, output_file)
