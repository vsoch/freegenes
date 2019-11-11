
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
from fg.apps.main.models import *
from fg.apps.orders.models import *
from fg.apps.main.utils import load_json
from dateutil.parser import parse
import logging
import os
import requests
import shippo
import shutil
import sys

from fg.settings import LAB_NAME,TRASH_NAME

class Command(BaseCommand):
    '''Builds initial containers'''

    help = "Initialize containers"

    def handle(self,*args,**options):
        print('Initializing containers')
        Container.objects.get_or_create(name=LAB_NAME,
                container_type='lab',
                description='The root lab')
        Container.objects.get_or_create(name=TRASH_NAME,
                container_type='trash',
                description='The trash')
        print('Initialized containers')




