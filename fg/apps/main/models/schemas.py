'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

MODULE_SCHEMAS = {

    "pipette": {
        'type': 'object',
        'schema': 'http://json-schema.org/draft-07/schema#',
        'required': ['upper_range_ul', 'lower_range_ul', 'channels', 'compatible_with'],
        'properties': {
            'upper_range_ul': {'type': 'number'},
            'lower_range_ul': {'type': 'number'},
            'channels': {'type': 'int'},
            'compatible_with': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': ['OT2', 'Human']
                }
            }
        }
    },
    "incubator": { 
        'type': 'object',
        'schema': 'http://json-schema.org/draft-07/schema#',
        'required': ['temperature', 'shaking', 'fits'],
        'properties': {
           'temperature': {'type': 'number'},
           'shaking': {'type': 'boolean'},
           'fits': {
               'type': 'array',
               'items': {
                    'type': 'string',
                    'enum': ['deep96', 'deep384', 'agar96']
               }
           }
        }
    },
    "magdeck": {
        'type': 'object',
        'schema': 'http://json-schema.org/draft-07/schema#',
        'required': ['fits', 'compatible_with'],
        'properties': {
            'fits': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': ['pcrhardshell96', 'pcrstrip8']
                }
            },
            'compatible_with': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': ['OT2', 'Human']
                }
            }
        }
    },
    "tempdeck": {
        'type': 'object',
        'schema': 'http://json-schema.org/draft-07/schema#',
        'required': ['upper_range_tm', 'lower_range_tm', 'default_tm', 'compatible_with', 'fits'],
        'properties': {
            'upper_range_tm': {'type': 'number'},
            'lower_range_tm': {'type': 'number'},
            'default_tm': {'type': 'number'},
            'channels': {'type': 'int'},
            'fits': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': ['pcrhardshell96', 'pcrstrip8', 'microcentrifuge2ml']
                }
            },
            'compatible_with': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'enum': ['OT2', 'Human']
                }
            }
        }
    }
}
