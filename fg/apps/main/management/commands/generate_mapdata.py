'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.core.management.base import (
    BaseCommand,
    CommandError
)
from fg.apps.main.utils import load_json
from fg.settings import SHIPPO_TOKEN

from uszipcode import SearchEngine
import logging
import os
import json
import requests
import shutil
import sys

class Command(BaseCommand):
    '''Generate data for the freegenes map, using the shippo API. The map
       generalizes the data to only include major geographic areas.

       usage: python manage.py generate_mapdata data/ordercoords.json

       Format is as follows:

	{
	    "00012": {
		"lat": 37.77,
		"long": -122.44,
		"count": 1
	    }
	}
    '''
    def add_arguments(self, parser):
        parser.add_argument(dest='output_file', nargs=1, type=str)
    help = "Generate an exported json of data for the shipping map."

    def handle(self, *args, **options):
        if options['output_file'] is None:
            raise CommandError("Please provide an output file as the only argument")

        # The input folder must exist!
        output_file = options['input_folder'][0]

        url="https://api.goshippo.com/orders/"
        headers={"Authorization": "ShippoToken %s" % SHIPPO_TOKEN}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            results = response.json()
            if "results" not in results:
                print("No results in response.")
                sys.exit(1)

        else:
            print("Error with request, %s:%s" %(response.status_code, response.reason))
            sys.exit(1)


        # If we get here, there are orders to parse!
        coords = dict()
        results = results['results']

        # First usage will download database to root (9MB)
        search = SearchEngine(simple_zipcode=True)

        # Assemble list of latitudes, longitudes
        for result in results:
            if "to_address" in result:
                if result['to_address']['zip']:
                    code = result['to_address']['zip']
                    zipcode = search.by_zipcode(code).to_dict()

                    # The radius of the circle will depend on the count
                    if code not in coords:
                        coords[code] = {"lat": zipcode['lat'],
                                        "long": zipcode['lng'],
                                        'count': 0}

                    coords[code]['count'] +=1
                    coords.append([zipcode['lat'], zipcode['lng']]) 
                    
        # Write to output file
        print('Writing to file...')
        with open(output_file, 'w') as filey:
            filey.writelines(json.dumps(coords, indent=4))
