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
