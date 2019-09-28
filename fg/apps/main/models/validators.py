'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from jsonschema import validate
from django.core.validators import BaseValidator
import re

def validate_direction_string(value):
    '''a direction string can only have < and > characters.
    '''
    if not re.search("^([<]|[>])+$", value):
        return False
    return True


def validate_dna_string(value):
    '''a validator to ensure that a sequence, primer, or barcode is valid.
    '''
    if not re.search("^[ATGC]*$", value):
        return False
    return True

def validate_name(value):
    '''helper function to validate the name of a container or robot'''
    if not re.search("^[^/ ]+$", value):
        return False
    return True

def validate_json_schema(instance, schema):
    return validate(instance=instance, schema=schema)

