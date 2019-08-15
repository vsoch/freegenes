'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

import hashlib
import json

def generate_sha256(content):
    '''Generate a sha256 hex digest for a string or dictionary. If it's a 
       dictionary, we dump as a string (with sorted keys) and encode for utf-8.
       The intended use is for a Schema Hash

       Parameters
       ==========
       content: a string or dict to be hashed.
    '''
    if isinstance(content, dict):
        content = json.dumps(content, sort_keys=True).encode('utf-8')
    return "sha256:%s" % hashlib.sha256().hexdigest()


def save_json(input_dict, output_file):
    '''save dictionary to file as json. Returns the output file written.

       Parameters
       ==========
       content: the dictionary to save
       output_file: the output_file to save to
    '''
    with open(output_file, 'w') as filey:
        filey.writelines(json.dumps(input_dict, indent=4))
    return output_file


def load_json(input_file):
    '''load json from a filename.

       Parameters
       ==========
       input_file: the input file to load
    '''
    with open(input_file, 'r') as filey:
        content = json.loads(filey.read())
    return content

