'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

*Models are stil being written*

'''

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.postgres.fields import JSONField
from taggit.managers import TaggableManager

from .validators import (
    validate_dna_string,
    validate_name, 
    validate_json_schema
)

import uuid

################################################################################
# Tags #########################################################################
################################################################################

class Tag(models.Model):
    '''A Tag object.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.CharField(max_length=250, blank=False, null=False)  # should this be unique?
    add_date = models.DateTimeField('date published', auto_now_add=True) # Do we need to keep track of dates?
    modify_date = models.DateTimeField('date modified', auto_now=True)

    def get_absolute_url(self):
        return reverse('tag_details', args=[self.uuid])

    def get_label(self):
        return "tag"

    class Meta:
        app_label = 'main'


################################################################################
# Authors ######################################################################
################################################################################

class Author(models.Model):
    '''An author coincides with an individual responsible for creation of an
       object.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=250, blank=False, required=True)
    email = models.EmailField(max_length=250, blank=False, unique=True)

    affiliation = models.CharField(max_length=250, blank=False, null=False)

    # Maximum length is only 19, but might as well prepare for future extension
    orcid = models.CharField(max_length=32, blank=False, unique=True)

    # What purpose do tags serve? What is a tag?
    tags = models.ManyToManyField('main.Tag', blank=True, default=None,
                                   related_name="author_tags",
                                   related_query_name="author_tags")
    def get_absolute_url(self):
        return reverse('author_details', args=[self.uuid])

    def get_label(self):
        return "author"

    class Meta:
        app_label = 'main'


################################################################################
# Parts ########################################################################
################################################################################

class Part(models.Model):
    '''A parts object
    '''
    PART_STATUS = [
        ('null', None),
        ('optimized', 'optimized'),
        ('fixed','fixed'),
        ('sites_applied', 'sites_applied'),
        ('syn_checked', 'syn_checked'),
        ('syn_checked_failed', 'syn_checked_failed')
    ]

    PART_TYPE = [
        ('full_promoter', 'full_promoter'),
        ('promoter', 'promoter'),  
        ('rbs', 'rbs'),  
        ('cds', 'cds'),
        ('vector', 'vector'),
        ('partial_seq', 'partial_seq'),
        ('linear_dna', 'linear_dna'),
        ('plasmid', 'plasmid'),
        ('terminator', 'terminator'),    
    ]

    IP_CHECKED_CHOICES = [
        ('NOT_CHECKED', False),
        ('CHECKED', True) 
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Why do these fields use time, and others use date (e.g., see ip_check*)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    status = models.CharField(max_length=250, choices=PART_STATUS, default='null')
    name = models.CharField(max_length=250, required=True)
    description = models.CharField(max_length=500, required=True)
    gene_id = models.CharField(max_length=250)
    part_type = models.CharField(max_length=250, choices=PART_TYPE)

    # Sequences (what are the maximum lengths here?)
    original_sequence = models.CharField(max_length=250, validators=[validate_dna_string])
    optimized_sequence = models.CharField(max_length=250, validators=[validate_dna_string])
    synthesized_sequence = models.CharField(max_length=250, validators=[validate_dna_string])
    full_sequence = models.CharField(max_length=250, required=True, validators=[validate_dna_string])

    genbank = JSONField(default=dict)

    # It would be good to have descriptors for these fields
    vector = models.CharField(max_length=250)
    primer_for = models.CharField(max_length=250, validators=[validate_dna_string])
    primer_rev = models.CharField(max_length=250, validators=[validate_dna_string])
    barcode = models.CharField(max_length=250, validators=[validate_dna_string])
    translation = models.CharField(max_length=250)
    vdb = models.CharField(max_length=250, required=True)

    # What is an ip check?
    ip_check_date = models.DateTimeField('date ip checked')
    ip_check = models.BooleanField(choices=IP_CHECKED_CHOICES, default='NOT_CHECKED')
    ip_check_ref = models.CharField(max_length=250, required=True)

    ## Foreign Keys and Relationships

    # The assumption here is that tags and files can be shared between models
    tags = models.ManyToManyField('main.Tag', blank=True, default=None,
                                   related_name="parts_tags",
                                   related_query_name="parts_tags")

    files = models.ManyToManyField('main.Files', blank=True, default=None,
                                   related_name="parts_files",
                                   related_query_name="parts_files")

    # Can the same sample exist between parts?
    samples = models.ManyToManyField('main.Sample', blank=True, default=None,
                                    related_name="parts_samples",
                                    related_query_name="parts_samples")

    # When a collection is deleted, so are the parts
    # And assumes parts can only belong to one collection (is this true?)
    collection = models.ForeignKey('Collection', on_delete=models.CASCADE, required=True)

    # When an author is deleted, his parts are deleted
    author = models.ForeignKey('Author', on_delete=models.CASCADE, required=True)

    # Note: there was a to_json function here, but if this is for API, better
    # to do this with a serializer.

    #tags = TaggableManager()
    
    def get_absolute_url(self):
        return reverse('part_details', args=[self.uuid])

    def get_label(self):
        return "part"

    class Meta:
        app_label = 'main'


################################################################################
# Collections and Containers ###################################################
################################################################################

class Collection(models.Model):
    '''A collection of things (more details?)
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    name = models.CharField(max_length=250, required=True)

    # What is the difference between a readme and description? Should be consistent
    readme = models.CharField(max_length=500, required=True)

    # When a parent is deleted, so are the children
    parent = models.ForeignKey('Collection', on_delete=models.CASCADE)

    tags = models.ManyToManyField('main.Tag', blank=True, default=None,
                                   related_name="collection_tags",
                                   related_query_name="collection_tags")

    def get_absolute_url(self):
        return reverse('collection_details', args=[self.uuid])

    def get_label(self):
        return "collection"

    class Meta:
        app_label = 'main'

class Container(models.Model):
    '''A physical container in the lab space
    '''

     CONTAINER_TYPES = [ # TODO: need better descriptions here
         ('trash', 'trash'),
         ('lab', 'lab'),
         ('room', 'room'),
         ('bay', 'bay'),
         ('bench', 'bench'),
         ('desk', 'desk'),
         ('cabinet', 'cabinet'),
         ('robot', 'robot'),
         ('freezer', 'freezer'),
         ('fridge', 'fridge'),
         ('shelf', 'shelf'),
         ('rack', 'rack'),
         ('incubator', 'incubator'),
         ('shaking_incubator', 'shaking incubator'),

     ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    name = models.CharField(max_length=250, required=True, validators=[validate_name])
    container_type = models.CharField(max_length=250, required=True, choices=CONTAINER_TYPES)
    description = models.CharField(max_length=500)
    estimated_temperature = models.FloatField()

    # What are these coordinates for? (no default?)
    x = models.FloatField()
    y = models.FloatField()
    z = models.FloatField()

    # When a parent is deleted, so are the children. If a file is deleted, do nothing
    parent = models.ForeignKey('Container', on_delete=models.CASCADE)
    image = models.ForeignKey('Files', on_delete=models.DO_NOTHING)
 
    plates = models.ManyToManyField('main.Plate', blank=True, default=None,
                                    related_name="container_plates",
                                    related_query_name="container_plates")
    # What exactly is a module?
    modules = models.ManyToManyField('main.Robot', blank=True, default=None,
                                    related_name="container_modules",
                                    related_query_name="container_modules")

    def get_absolute_url(self):
        return reverse('container_details', args=[self.uuid])

    def get_label(self):
        return "container"

    class Meta:
        app_label = 'main'



################################################################################
# Organisms ####################################################################
################################################################################

class Organism(models.Model):
    '''A representation of an organism (more details?)
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    name = models.CharField(max_length=250, required=True)

    description = models.CharField(max_length=500, null=False)
    genotype = models.CharField(max_length=250, null=False)

    tags = models.ManyToManyField('main.Tag', blank=True, default=None,
                                   related_name="organism_tags",
                                   related_query_name="organism_tags")

    files = models.ManyToManyField('main.Files', blank=True, default=None,
                                   related_name="organism_files",
                                   related_query_name="organism_files")

    def get_absolute_url(self):
        return reverse('organism_details', args=[self.uuid])

    def get_label(self):
        return "organism"

    class Meta:
        app_label = 'main'


################################################################################
# Modules
################################################################################

class Module(models.Model):
    '''A module base, can have define a pipette, tempdeck, magdeck, or incubator
    '''
    MODULE_TYPE = [
        ('pipette', 'pipette'),
        ('tempdeck', 'tempdeck'),
        ('magdeck', 'magdeck'),
        ('incubator', 'incubator'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    container = models.ForeignKey('Container', on_delete=models.CASCADE, required=True)
    name = models.CharField(max_length=250, required=True, validators=[validate_name])

    # This is generally bad practice to have a notes field - what is this for?
    notes = models.CharField(max_length=500)
    model_id = models.CharField(max_length=250, required=True)
    module_type = models.CharField(max_length=250, required=True, choices=MODULE_TYPE)

    # This will be validated with clean according to module_type
    data = JSONField(default=dict)

    def clean(self):
        '''clean provides a custom validation function for a module. We check
           the json data against the known schemas
        '''
        schema = self.SCHEMAS.get(self.module_type)
        if schema:
            if not validate(self.data, schema):
                raise ValidationError('Invalid schema for %s type %s' % (self.uuid, self.module_type))

    SCHEMAS = { 
        "pipette": { 
            'type': 'object',
            'schema': 'http://json-schema.org/draft-07/schema#',
            'properties': {
                'upper_range_ul': {
                'type': 'float'
              },{
                'lower_range_ul': {
                'type': 'float'
              },{
                'channels': {
                'type': 'int'
              },{
                'channels': {
                'type': 'int'
              }
            },
           'required': ['my_key']
        }

        #TODO: stopped here, need to look up how to do arrays with json validator
        # Pipette
#        schema_generator({'upper_range_ul': generic_num, 'lower_range_ul': generic_num, 'channels': generic_num, 'compatible_with': {'type': 'array', 'items': {'type': 'string', 'enum': ['OT2','Human']}}}, # Pipette
#            ['upper_range_ul','lower_range_ul','channels','compatible_with']),

        # Incubator
#        schema_generator({'temperature': generic_num, 'shaking': {'type': 'boolean'}, 'fits': {'type': 'array', 'items': {'type':'string','enum':['deep96','deep384','agar96']}}}, # Incubator
#            ['temperature','shaking','fits']),
        # Magdeck

#       schema_generator({'compatible_with': {'type': 'array', 'items': {'type': 'string', 'enum': ['OT2','Human']}}, 'fits': {'type': 'array', 'items': {'type':'string','enum':['pcrhardshell96','pcrstrip8']}}},
#           ['compatible_with','fits']),

        # Tempdeck
#        schema_generator({'upper_range_tm': generic_num, 'lower_range_tm': generic_num, 'default_tm': generic_num,
#            'compatible_with': {'type': 'array', 'items': {'type': 'string', 'enum': ['OT2','Human']}}, 'fits': {'type': 'array', 'items':{'type':'string','enum':['pcrhardshell96','pcrstrip8','microcentrifuge2ml']}}},
#            ['upper_range_tm','lower_range_tm','default_tm','compatible_with','fits'])
#       ]},


    def get_absolute_url(self):
        return reverse('module_details', args=[self.uuid])

    def get_label(self):
        return "module"

    class Meta:
        app_label = 'main'



################################################################################
# Robots
################################################################################


class Robot(models.Model):
    '''A robot in the lab.
    '''
    ROBOT_TYPES = [
        ('OT2','OT2')
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    container = models.ForeignKey('Container', on_delete=models.CASCADE, required=True)
    name = models.CharField(max_length=250, required=True, validators=[name_validator])
    robot_id = models.CharField(max_length=250, required=True)
    robot_type = models.CharField(max_length=250, required=True, choices=ROBOT_TYPES, default='OT2')

    # This is generally bad practice to have a notes field - what is this for?
    notes = models.CharField(max_length=500)
    server_version = models.CharField(max_length=32)

    # What is a mount?
    right_mount = models.ForeignKey('Module', on_delete=models.CASCADE)
    left_mount = models.ForeignKey('Module', on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('robot_details', args=[self.uuid])

    def get_label(self):
        return "robot"

    class Meta:
        app_label = 'main'



################################################################################
# Files and Agreements
################################################################################

class Files(models.Model):
    '''A file associated with an organism or part. The file_name field
       is the path to storage, which should be chosen to minimize egress
       depending on where the application is served from. Signed URLs
       should be used to manage access to private objects, if possible.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    file_name = models.CharField(max_length=500, null=True, blank=True)

    description = models.CharField(max_length=500, null=False)
    genotype = models.CharField(max_length=250, null=False)

    tags = models.ManyToManyField('main.Tag', blank=True, default=None,
                                   related_name="organism_tags",
                                   related_query_name="organism_tags")

    files = models.ManyToManyField('main.Files', blank=True, default=None,
                                   related_name="organism_files",
                                   related_query_name="organism_files")

    def download(self):
        # Need to set up connection to some storage, this would be best
        # handled by the API
        print('WRITE ME')

    @property
    def name(self):
        if self.file_name:
            return os.path.basename(self.file_name)

    def get_absolute_url(self):
        return reverse('file_details', args=[self.uuid])

    def get_label(self):
        return "files"

    class Meta:
        app_label = 'main'



class MaterialTransferAgreement(models.Model):
    '''A material transfer agreement (MTA) is an agreement between two parties.
    '''
    MTA_TYPE = [
        ('OpenMTA', 'Open Material Transfer Agreement (OpenMTA)'),
        ('UBMTA', 'Uniform Biological Material Transfer Agreement')
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mta_type = models.CharField(max_length=32, choices=PART_TYPE, required=True)

    # Are we sure we want all files hosted remote to server?
    # The agreement file is named based on the UUID here?
    agreement_file = models.ForeignKey('Files', on_delete=models.CASCADE)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    institution = models.CharField(max_length=250, required=True)

    def get_label(self):
        return "materialtransferagreement"

    class Meta:
        app_label = 'main'




# Plate
# Sample
# Well
# Protocol
# Operation
# Plan
# PlateSet
# Distribution
# Order (how much of this should be kept in database? We don't want to house PI)
# Shipment
# Address
# Parcel
# Institution
# Schema
