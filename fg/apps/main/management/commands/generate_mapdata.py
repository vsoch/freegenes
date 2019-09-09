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
from geopy.geocoders import Nominatim

import logging
import os
import json
import requests
import shutil
import sys

def address_lookup(lookup):
    '''a helper function to use a lookup (a to_address or from_address
       returned from the Shippo API) to return a location object.
       If the address is not found, returns None
    '''
    address = lookup.get('street1','')
    geolocator = Nominatim(user_agent="freegenes")
    
    # City
    if lookup.get('city'):
        address = "%s, %s" %(address, lookup['city'])
  
    # State
    if lookup.get('state'):
        address = "%s %s" %(address, lookup['state'])

    # Zip
    if lookup.get('zip'):
        address = "%s %s" %(address, lookup['zip'])

    # Country
    if lookup.get('country'):
        address = "%s, %s" %(address, lookup['country'])
         
    return geolocator.geocode(address) 



class Command(BaseCommand):
    '''Generate data for the freegenes map, using the shippo API. The map
       generalizes the data to only include major geographic areas.

       usage: python manage.py generate_mapdata data/ordercoords.json

       Format is as follows:

	{
	    "11217": {
		"lat": 40.68,
		"long": -73.98,
		"count": 1
	    },
	    "60660": {
		"lat": 41.98,
		"long": -87.66,
		"count": 1
	    },
	    "60177": {
		"lat": 41.99,
		"long": -88.31,
		"count": 1
	    },
	    "V6A 1M3": {
		"lat": 49.2818536,
		"long": -123.0876828,
		"count": 1
	    },
	    "02135": {
		"lat": 42.35,
		"long": -71.15,
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
        output_file = options['output_file'][0]

        url="https://api.goshippo.com/orders/"
        headers={"Authorization": "ShippoToken %s" % SHIPPO_TOKEN}

        # If we get here, there are orders to parse!
        coords = dict()

        # First usage will download database to root (9MB)
        search = SearchEngine(simple_zipcode=True)
        geolocator = Nominatim(user_agent="freegenes")

        response = requests.get(url, headers=headers)

        # Continue parsing until we don't have next
        while response.status_code == 200:

            results = response.json()
            if "results" not in results:
                print("No results in response.")
                sys.exit(1)

            listing = results['results']

            # Assemble list of latitudes, longitudes
            for result in listing:

                if "to_address" in result:

                    zipcode = result['to_address']['zip'].split('-')[0]
                    lat = None
                    lng = None

                    # If the country is the US, this is most accurage
                    if result['to_address']['country'] in ['US', 'USA']:
                        location = search.by_zipcode(zipcode).to_dict()
                        lat = location.get('lat')
                        lng = location.get('lng')

                    # Second try use entire address with geopy
                    if not lat or not lng:
                        location = address_lookup(result['to_address'])
                        if location:
                            lat = location.latitude
                            lng = location.longitude

                    # Third try, use zip code / country only
                    if not lat or not lng:
                        country = result['to_address']['country']
                        location = geolocator.geocode("%s %s" %(zipcode, country))
                        if location:
                            lat = location.latitude
                            lng = location.longitude
                   
                    if lat and lng:

                        # The radius of the circle will depend on the count
                        if zipcode not in coords:
                            coords[zipcode] = {"lat": lat,
                                               "long": lng,
                                               'count': 0}

                        coords[zipcode]['count'] +=1

            # Get the next page
            response = requests.get(results['next'], headers=headers)

        # Write to output file
        print('Writing to file...')
        with open(output_file, 'w') as filey:
            filey.writelines(json.dumps(coords, indent=4))
