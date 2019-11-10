'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

*Note*: We could use an abstract model for shared attributes (less code,
        and the same result) but in past cases when I've done this (and
        something needs to change for a model) it makes it more difficult.
        The current approach to redefine the fields is more redundant, but
        produces the same result and doesn't risk this future issue.
'''

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from taggit.managers import TaggableManager
from fg.settings import (
    DEFAULT_PLATE_HEIGHT,
    DEFAULT_PLATE_LENGTH
)
from sortedm2m.fields import SortedManyToManyField
from .schemas import MODULE_SCHEMAS
from .validators import (
    validate_direction_string,
    validate_dna_string,
    validate_name, 
    validate_json_schema
)

from itertools import chain
import os
import string
import uuid
import re
import time


################################################################################
# Tags #########################################################################
################################################################################

class Tag(models.Model):
    '''tags are ways to organize the different categories they are associated with. 
       As an example, we may tag a plasmid part as conferring ampicillin 
       resistance, so it would include the tag resistance:ampicillin. 
       That same part could also be tagged as an essential_gene.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.CharField(max_length=250, blank=False, null=False, unique=True)

    def __str__(self):
        return "<Tag:%s>" % self.tag

    def __repr__(self):
        return self.__str__()

    @property
    def total_count(self):
        '''Return a total count of all associated entities.
        '''
        return (self.author_tags.count() +
                self.organism_tags.count() +
                self.collection_tags.count() +
                self.part_tags.count())

    def save(self, *args, **kwargs):
        '''tags are enforced as all lowercase to avoid duplication, along
           with removing all special characters except for dashes and :.
           Dashes and : are allowed. 
        '''
        if self.pk is None:
            self.tag = self.tag.replace(' ', '-') # replace space with -
            self.tag = re.sub('[^A-Za-z0-9:-]+', '', self.tag).lower()
        return super(Tag, self).save(*args, **kwargs)

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
    name = models.CharField(max_length=250, blank=False)
    email = models.EmailField(max_length=250, blank=False, unique=True)

    affiliation = models.CharField(max_length=250, null=False)

    # Maximum length is only 19, but might as well prepare for future extension
    orcid = models.CharField(max_length=32, unique=True, blank=True, null=True)

    # Tags are shared between models
    tags = models.ManyToManyField('main.Tag', blank=True, default=None,
                                   related_name="author_tags",
                                   related_query_name="author_tags")
    def __str__(self):
        return "<Author:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_absolute_url(self):
        return reverse('author_details', args=[self.uuid])

    def get_label(self):
        return "author"

    def get_tags(self):
        '''a helper to return a list of tags (strings)'''
        return [x.tag for x in self.tags.all()]

    def json(self):
        '''return a list of fields (dict) for the object. The format returned
           is standard across models so it can be used in templates 
           to render fields into a table. Fields include key, value, 
           and auth and admin required (booleans)

           auth: indicates authorization required (True or False)
           admin: indicates admin (superusers) only
        '''
        fields = [
            {"key": "Name", "value": self.name, "auth": True}, 
            {"key": "Email", "value": self.email, "admin": True}, 
            {"key": "Affiliation", "value": self.affiliation, "auth": False},
            {"key": "orcid", "value": self.orcid, "auth": True}]

        return fields

    class Meta:
        app_label = 'main'


class Institution(models.Model):
    '''An institution is an organization of people. An institution can optionally
       sign a master agreement, the default is set to False to indicate not signed.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=250, blank=False)

    # Master MTAs are available on biobricks, if signed_master False need to look up
    signed_master = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('institution_details', args=[self.uuid])

    def get_label(self):
        return "institution"

    def __str__(self):
        return "<Institution:%s>" % self.name

    def __repr__(self):
        return self.__str__()



################################################################################
# Parts ########################################################################
################################################################################

class CompositePart(models.Model):
    '''a composite part is a virtual representation of a group of parts.
    '''
    COMPOSITE_TYPE = [
        ('base_part_plasmid', 'base_part_plasmid'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    name = models.CharField(max_length=250, blank=False, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)

    # to differentiate between composite_ids and gene_ids
    composite_id = models.CharField(max_length=250, null=True, blank=True) 
    composite_type = models.CharField(max_length=250, choices=COMPOSITE_TYPE, null=True, blank=True)

    # Must be same length as parts, e.g., ABC might correspond with any of <<> <>< >>> etc.
    # < means reversed
    # > means no change or forwardd (current direction)
    direction_string = models.CharField(max_length=250, null=False, blank=False,
                                        validators=[validate_direction_string],
                                        help_text="String of equal length to parts to designate directions (<<>)")

    sequence = models.TextField(validators=[validate_dna_string], default=None)
    parts = SortedManyToManyField("main.Part")

    def get_absolute_url(self):
        return reverse('compositepart_details', args=[self.uuid])

    def get_label(self):
        return "compositepart"

    class Meta:
        app_label = 'main'


class Part(models.Model):
    '''A parts object is a virtual representation of genetic element(s).
       A part may be created from other parts, or synthesized from scratch.
       It may be several different types of genetic elements, such as a 
       promoter, rbs, cds, or terminator. Typically, these parts are 
       in a standardized format, such as the FreeGenes MoClo format.
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

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Why do these fields use time, and others use date (e.g., see ip_check*)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    status = models.CharField(max_length=250, choices=PART_STATUS, default='null', blank=True, null=True)
    name = models.CharField(max_length=250, blank=False)
    description = models.CharField(max_length=500, blank=True, null=True)
    gene_id = models.CharField(max_length=250)
    part_type = models.CharField(max_length=250, choices=PART_TYPE)

    # Sequences - we would want 10K to 100K, can go up to 4 million (but not practical)
    original_sequence = models.TextField(validators=[validate_dna_string], blank=True, null=True)
    optimized_sequence = models.TextField(validators=[validate_dna_string], blank=True, null=True)
    synthesized_sequence = models.TextField(validators=[validate_dna_string], blank=True, null=True)
    full_sequence = models.TextField(validators=[validate_dna_string], blank=True, null=True)

    genbank = JSONField(default=dict)

    # It would be good to have descriptors for these fields
    vector = models.CharField(max_length=250, blank=True, null=True)
    primer_forward = models.TextField(validators=[validate_dna_string])
    primer_reverse = models.TextField(validators=[validate_dna_string])
    barcode = models.CharField(max_length=250, validators=[validate_dna_string], blank=True, null=True)
    translation = models.TextField(validators=[validate_dna_string], blank=True, null=True)

    # What is an ip check?
    ip_check_date = models.DateTimeField('date ip checked', blank=True, null=True)
    ip_check = models.BooleanField(default=False)
    ip_check_ref = models.CharField(max_length=250)

    ## Foreign Keys and Relationships

    # The assumption here is that tags and files can be shared between models
    tags = models.ManyToManyField('main.Tag', blank=True, default=None,
                                   related_name="part_tags",
                                   related_query_name="part_tags")

    files = models.ManyToManyField('main.Files', blank=True, default=None,
                                   related_name="parts_files",
                                   related_query_name="parts_files")

    # samples point to their parts (not defined here)

    # Parts can belong to many collections, when collection deleted, all parts remain
    collections = models.ManyToManyField('main.Collection', blank=True, default=None,
                                         related_name="parts_collections",
                                         related_query_name="parts_collections")

    # Authors cannot be deleted if there is a part
    author = models.ForeignKey('Author', on_delete=models.PROTECT, blank=False)

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
    '''A collection object represents a collection of parts. A collection
       may contain several subcollections containing more parts. For example,
       the "Mesoplasma florum" collection may have a subcollection of
       "Mesoplasma florum promoters" and "Mesoplasma florum vectors".
       This object is used for organizing groups of parts.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    name = models.CharField(max_length=250, blank=False, unique=True)

    # This was originally the collection "README"
    description = models.CharField(max_length=5000, blank=False)

    # When a parent is deleted, the children remain
    parent = models.ForeignKey('Collection', on_delete=models.DO_NOTHING, blank=True, null=True)

    tags = models.ManyToManyField('main.Tag', blank=True, default=None,
                                   related_name="collection_tags",
                                   related_query_name="collection_tags")

    def __str__(self):
        return "<Collection:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_absolute_url(self):
        return reverse('collection_details', args=[self.uuid])

    def get_label(self):
        return "collection"

    class Meta:
        app_label = 'main'


class Container(models.Model):
    '''A physical container in the lab space. Put together, forms a tree view of 
      a lab. Inside of a lab is a room, inside of that room is a freezer, 
      inside of that freezer are  shelves, inside of those shelves are racks, 
      and inside those racks are plates. For example, see 
      https://api.freegenes.org/containers/tree_view_full/. 
      The idea is to be able to tell an end user "please grab this plate from 
      this specific location and move it to this other specific location"
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
         ('world', 'world'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    name = models.CharField(max_length=250, blank=False, validators=[validate_name])
    container_type = models.CharField(max_length=250, blank=False, choices=CONTAINER_TYPES)
    description = models.CharField(max_length=500)
    estimated_temperature = models.FloatField(null=True, blank=True, default=None)

    # Meter coordinates for the locations of things in lab
    # https://github.com/vsoch/freegenes/issues/10
    x = models.FloatField(null=True, blank=True, default=None)
    y = models.FloatField(null=True, blank=True, default=None)
    z = models.FloatField(null=True, blank=True, default=None)

    # When a parent is deleted, so are the children. If a file is deleted, do nothing
    parent = models.ForeignKey('Container', on_delete=models.CASCADE, blank=True, null=True)
    image = models.ForeignKey('Files', on_delete=models.DO_NOTHING, blank=True, null=True)

    @property
    def breadcrumb(self):
        '''a breadcrumb is a trace of the plate up to the parent container.
           we start at the child and trace up to the parent, so the order
           is first child to parent, and we reverse to give user parent
           to child.
        '''
        breadcrumb = []
        container = self
        while container:
            breadcrumb.append(container)
            container = container.parent

        # Reverse, give to user parent to child
        breadcrumb = breadcrumb[::-1]
        return breadcrumb
 
    def __str__(self):
        return "<Container:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_absolute_url(self):
        return reverse('container_details', args=[self.uuid])

    def get_label(self):
        return "container"

    def json(self):
        '''return a list of fields (dict) for the object. The format returned
           is standard across models so it can be used in templates 
           to render fields into a table. Fields include key, value, 
           and auth and admin required (booleans)

           auth: indicates authorization required (True or False)
           admin: indicates admin (superusers) only
        '''
        fields = [
            {"key": "Name", "value": self.name}, 
            {"key": "Container Type", "value": self.container_type},
            {"key": "Description", "value": self.description},
            {"key": "Estimated Temperature", "value": self.estimated_temperature}]

        # Only add coordinates if defined
        if self.x and self.y and self.z:
            coordinate = "%s %s %s" %(self.x, self.y, self.z)
            fields.append({"key": "Coordinate", "value": coordinate})

        return fields

    class Meta:
        app_label = 'main'


################################################################################
# Organisms ####################################################################
################################################################################

class Organism(models.Model):
    '''A representation of an organism. Includes tags and genotype
       information. It is assumed if a well contains a sample and 
       an organism, the sample is within the organism.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    name = models.CharField(max_length=250, blank=False)

    description = models.CharField(max_length=500, null=False)
    genotype = models.CharField(max_length=250, null=False)

    tags = models.ManyToManyField('main.Tag', blank=True, default=None,
                                   related_name="organism_tags",
                                   related_query_name="organism_tags")

    files = models.ManyToManyField('main.Files', blank=True, default=None,
                                   related_name="%(class)s_organism")

    def __str__(self):
        return "<Organism:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_absolute_url(self):
        return reverse('organism_details', args=[self.uuid])

    def get_label(self):
        return "organism"

    def json(self):
        '''return a list of fields (dict) for the object. The format returned
           is standard across models so it can be used in templates 
           to render fields into a table. Fields include key, value, 
           and auth and admin required (booleans)

           auth: indicates authorization required (True or False)
           admin: indicates admin (superusers) only
        '''
        fields = [
            {"key": "Name", "value": self.name}, 
            {"key": "Description", "value": self.description},
            {"key": "Genotype", "value": self.genotype}]

        return fields
 
    class Meta:
        app_label = 'main'


################################################################################
# Modules
################################################################################

class Module(models.Model):
    '''Physical lab capabilities. From a protocol-generation perspective side 
       (protocol in terms of a lab protocol, or lab procedure), you can query 
       for a lab's capabilities and then generate a protocol that fits their 
       capabilities. If I have an OpenTrons available with a pipette, it will 
       make a protocol for an opentrons, if I have a human available, 
       it will make a protocol for a human. This, I believe, is important further 
       down the line to have for general-use protocols, and so have some simple 
       implementations here.
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

    # We do nothing here because there is a pre_delete signal on the container to
    # move any associated modules to belong to the container parent. The root
    # container is not allowed to be deleted.
    container = models.ForeignKey('Container', on_delete=models.DO_NOTHING, blank=False)
    name = models.CharField(max_length=250, blank=False, validators=[validate_name], unique=True)

    # This is generally bad practice to have a notes field - what is this for?
    notes = models.CharField(max_length=500)
    model_id = models.CharField(max_length=250, blank=False)
    module_type = models.CharField(max_length=250, blank=False, choices=MODULE_TYPE)

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

    SCHEMAS = MODULE_SCHEMAS

    def __str__(self):
        return "<Module:%s>" % self.name

    def __repr__(self):
        return self.__str__()
    
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
    '''A robot in the lab. Right now, this is presumed to be 
       and only supports OpenTrons 2 robots.
    '''
    ROBOT_TYPES = [
        ('OT2','OT2')
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    container = models.ForeignKey('Container', on_delete=models.CASCADE, blank=False)
    name = models.CharField(max_length=250, blank=False, validators=[validate_name])
    robot_id = models.CharField(max_length=250, blank=False)
    robot_type = models.CharField(max_length=250, blank=False, choices=ROBOT_TYPES, default='OT2')

    # This is generally bad practice to have a notes field - what is this for?
    notes = models.CharField(max_length=500)
    server_version = models.CharField(max_length=32)

    # If a module gets deleted, it is removed from the mount. This doesn't mean we delete the robot.
    right_mount = models.ForeignKey('Module', on_delete=models.DO_NOTHING, related_name="robot_right_mount")
    left_mount = models.ForeignKey('Module', on_delete=models.DO_NOTHING, related_query_name="robot_left_mount")

    def __str__(self):
        return "<Robot:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_absolute_url(self):
        return reverse('robot_details', args=[self.uuid])

    def get_label(self):
        return "robot"

    class Meta:
        app_label = 'main'



################################################################################
# Files and Agreements
################################################################################

def get_upload_to(instance, filename, subfolder="files"):
    '''upload to a filename named based on the MTA uuid.
       UPLOAD_FOLDER is data or /code/data in the container.
    '''
    # The upload folder is the MTA subfolder of /code/data
    upload_folder = os.path.join(settings.UPLOAD_PATH, subfolder)
    if not os.path.exists(upload_folder):
        os.mkdir(upload_folder)

    # Get the extension of the current filename
    _, ext = os.path.splitext(filename)
    filename = "%s/%s%s" % (upload_folder, instance.uuid, ext)
    return time.strftime(filename)


class Files(models.Model):
    '''A file associated with an organism or part. The file_name field
       is the path to storage, which should be chosen to minimize egress
       depending on where the application is served from. Signed URLs
       should be used to manage access to private objects, if possible.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    file_name = models.FileField(upload_to=get_upload_to)

    def download(self):
        # Need to set up connection to some storage, this would be best
        # handled by the API
        print('WRITE ME')

    def __str__(self):
        return "<Files:%s>" % self.file_name

    def __repr__(self):
        return self.__str__()

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


def get_mta_upload_to(instance, filename):
    '''upload to a filename named based on the MTA uuid.
       UPLOAD_FOLDER is data or /code/data in the container.
    '''
    return get_upload_to(instance, filename, "MTA")


class MaterialTransferAgreement(models.Model):
    '''A material transfer agreement (MTA) is an agreement between two parties
       on the terms in which the biological materials will be transfered.
    '''
    MTA_TYPE = [
        ('OpenMTA', 'Open Material Transfer Agreement (OpenMTA)'),
        ('UBMTA', 'Uniform Biological Material Transfer Agreement')
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mta_type = models.CharField(max_length=32, choices=MTA_TYPE, blank=False)

    # The agreement file is named based on the UUID
    # We never want to delete an agreement file, but if we absolutely have to, the MTA is deleted.
    agreement_file = models.FileField(upload_to=get_mta_upload_to)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    institution = models.ForeignKey('Institution', help_text="The recipient institution", on_delete=models.DO_NOTHING)

    def __str__(self):
        return "<MTA:%s>" % self.agreement_file.name

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "materialtransferagreement"

    class Meta:
        app_label = 'main'


################################################################################
# Plates
################################################################################

class Plate(models.Model):
    '''A physical plate in the lab.
    '''
    PLATE_STATUS = [
        ('Planned','Planned'),
        ('Stocked','Stocked'),
        ('Trashed','Trashed')
    ]

    PLATE_TYPE = [
        ('archive_glycerol_stock','archive_glycerol_stock'),
        ('plasmid_plate','plasmid_plate'),
        ('glycerol_stock','glycerol_stock'),
        ('culture','culture'),
        ('distro','distro'),
    ]

    PLATE_FORM = [
        ('standard96', 'standard96'),
        ('deep96', 'deep96'),
        ('standard384', 'standard384'),
        ('deep384', 'deep384'),
        ('pcrhardshell96', 'pcrhardshell96'),
        ('pcrstrip8', 'pcrstrip8'),
        ('agar96', 'agar96'),
        ('microcentrifuge2ml', 'microcentrifuge2ml')
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plate_type = models.CharField(max_length=32, choices=PLATE_TYPE, blank=False)
    plate_form = models.CharField(max_length=32, choices=PLATE_FORM, blank=False)
    status = models.CharField(max_length=32, choices=PLATE_STATUS, blank=False)
    name = models.CharField(max_length=250, blank=False)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    plate_vendor_id = models.CharField(max_length=250, blank=True, null=True, unique=True)

    # Track the number of times a plate has been frozen and thawed, each freeze damages the cells
    thaw_count = models.IntegerField(default=0)

    # This is generally bad practice to have a notes field - what is this for?
    notes = models.CharField(max_length=500)

    # This is a proposed addition so we generate wells from plates with known dimensions
    height = models.IntegerField(blank=False, default=DEFAULT_PLATE_HEIGHT)
    length = models.IntegerField(blank=False, default=DEFAULT_PLATE_LENGTH)

    container = models.ForeignKey('Container', on_delete=models.CASCADE)
    protocol = models.ForeignKey('Protocol', on_delete=models.CASCADE, blank=True, null=True)

    @property
    def breadcrumb(self):
        '''a breadcrumb is a trace of the plate up to the parent container.
           we start at the child and trace up to the parent, so the order
           is first child to parent, and we reverse to give user parent
           to child.
        '''
        breadcrumb = []
        container = self.container
        while container:
            breadcrumb.append(container)
            container = container.parent

        # Reverse, give to user parent to child
        breadcrumb = breadcrumb[::-1]
        return breadcrumb


    def json(self):
        '''return a list of fields (dict) for the object. The format returned
           is standard across models so it can be used in templates 
           to render fields into a table. Fields include key, value, 
           and auth and admin required (booleans)

           auth: indicates authorization required (True or False)
           admin: indicates admin (superusers) only
        '''
        fields = [
            {"key": "Plate Type", "value": self.plate_type},
            {"key": "Plate Vendor", "value": self.plate_vendor_id},
            {"key": "Plate Form", "value": self.plate_form},
            {"key": "Status", "value": self.status},
            {"key": "Time Updated", "value": self.time_updated},
            {"key": "Time Created", "value": self.time_created},
            {"key": "Thaw Count", "value": self.thaw_count},
            {"key": "Notes", "value": self.notes},
            {"key": "Height", "value": self.height},
            {"key": "Length", "value": self.length}]
        return fields

    def generate_wells(self):
        '''Given a set length and height, generate plate wells, but only
           if the plate does not have any. We return the number of wells
           created.
        '''
        # Imported data will already have wells added, skip this
        if self.wells.count() > 0:
            print("Plate already has wells.")
            return 0

        # Well positions are generated based on the plate dimensions
        positions = []
    
        for letter in list(string.ascii_uppercase[0:self.height]):
            for number in range(self.length):
                positions.append((letter, number+1))

        # Create wells, add to plate
        for location in [x[0]+str(x[1]) for x in positions]:
            well = Well.objects.create(address=location, volume=0)
            well.save()
            self.wells.add(well)

        self.save()

    def get_absolute_url(self):
        return reverse('plate_details', args=[self.uuid])

    def __str__(self):
        return "<Plate:%s,%s>" % (self.container, self.name)

    def __repr__(self):
        return self.__str__()
   
    def get_label(self):
        return "plate"

    class Meta:
        app_label = 'main'

    # wells are deleted with a pre_delete signal
    wells = models.ManyToManyField('main.Well', blank=True, default=None,
                                   related_name="plate_wells",
                                   related_query_name="plate_wells")

class PlateSet(models.Model):
    '''One or more plates associated with an order (or similar).
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField(max_length=500)
    name = models.CharField(max_length=250, blank=False)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    plates = models.ManyToManyField('main.Plate', blank=False,
                                    related_name="plateset_plates",
                                    related_query_name="plateset_plates")

    def __str__(self):
        return "<PlateSet:%s,%s>" %(self.name, self.plates.count())

    def __repr__(self):
        return self.__str__()

    def get_absolute_url(self):
        return reverse('plateset_details', args=[self.uuid])

    def get_label(self):
        return "plateset"

    class Meta:
        app_label = 'main'


class Distribution(models.Model):
    '''One or more platesets (an additional level of abstraction)
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField(max_length=500)
    name = models.CharField(max_length=250, blank=False)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    platesets = models.ManyToManyField('main.PlateSet', blank=False,
                                       related_name="distribution_plateset",
                                       related_query_name="distribution_plateset")

    def get_absolute_url(self):
        return reverse('distribution_details', args=[self.uuid])

    def get_plates(self, only_first=False):
        '''return a list of plates belonging to the distribution (meaning
           unwrapping the platesets. If only_first is True, we are returning
           only a representative sample (the first plate) for each plateset.
        '''
        plates = []
        for plateset in self.platesets.all():
            if not only_first:
                plates = list(chain(plates, plateset.plates.all()))
            else:
                if plateset.plates.count() > 0:
                    plates = list(chain(plates, [plateset.plates.first()]))
        return plates

    def gene_ids(self):
        '''return a list of unique part gene_ids for the distribution
        '''
        gene_ids = set()
        for plateset in self.platesets.all():
            # Each plate should be the same, so we look at the first
            plate = plateset.plates.first()          
            for well in plate.wells.all():
                gene_ids.add(well.sample_wells.first().part.gene_id)
        return gene_ids

    def parts(self):
        '''return unique list of part objects'''
        return Part.objects.filter(gene_id__in=self.gene_ids())


    def unique_parts(self):
        '''return the count of unique parts (intended for the distribution 
           catalog view or the function in views to count parts
        '''
        return len(self.gene_ids())

    def __str__(self):
        return "<Distribution:%s,%s>" %(self.name, self.platesets.count())

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "distribution"

    class Meta:
        app_label = 'main'



################################################################################
# Sample
################################################################################

class Sample(models.Model):
    '''In the biological world, we can have a piece of DNA that hypothetically 
       matches what we have on a computer, but most of the time we don't really 
       know. A sample is simply a piece of DNA that we have some level of confidence 
       exists in the real world. We could take a piece of DNA and derive a sample of
       it (that we have confidence is the "same thing" and then take that 
       new growth and split it between 10 wells and freeze them, all those new 
       frozen bacteria are the same sample (they theoretically are all the same).
    '''

    SAMPLE_STATUS = [
        ('Confirmed', 'Confirmed'), 
        ('Mutated', 'Mutated')
    ]

    SAMPLE_TYPE = [
        ('Plasmid', 'Plasmid'),
        ('Illumina_Library', 'Illumina_Library')
    ]

    # What is sample evidence?
    # The labels here don't match what is commented about outside folks, e.g.,
    # Are all options valid, either lowercase or uppercase? Should there be boolean instead?
    # Why is this important to know?
    # ngs, sanger, TWIST - capitals denote outside folks

    # At very best, we have sequencing data for a sample in our lab. 
    # This is the "evidence" we have for the state of a sample. The next best is 
    # someone else sequencing the sample (in which we are often not privy to the data), 
    # and the worst is if the evidence of the state of a sample is just that it is Derived from something else.
    SAMPLE_EVIDENCE = [
        ('Twist_Confirmed', 'Twist_Confirmed'),
        ('NGS', 'NGS'),
        ('Sanger', 'Sanger'),
        ('Nanopore', 'Nanopore'),
        ('Derived', 'Derived')
    ]

    # Default is outside collaborator (more conservative)
    outside_collaborator = models.BooleanField(default=True)

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sample_type = models.CharField(max_length=32, choices=SAMPLE_TYPE, blank=True, null=True)
    status = models.CharField(max_length=32, choices=SAMPLE_STATUS, blank=True, null=True)

    # Each sequencing method is different (Sanger kind of sucks, and so I barely trust it, 
    # while NGS is very strong, and so I completely trust it) which is important.
    evidence = models.CharField(max_length=32, choices=SAMPLE_EVIDENCE, blank=True, null=True)
    vendor = models.CharField(max_length=250, blank=True, null=True)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    # A sample with derivations cannot be deleted, a part with samples cannot be deleted
    # If we have some frozen bacteria, and scrape a little off and put it into 
    # a new tube to grow overnight, the new growth is not the same sample as the 
    # frozen bacteria (maybe there was some contamination, or maybe we bottlenecked 
    # the population so there are more mutations). We think it's status is 
    # confirmed, but the only evidence we have is that it was "Derived" from a confirmed sample.
    derived_from = models.ForeignKey('Sample', on_delete=models.PROTECT, blank=True, null=True)

    # Parts, not required since it could be composite or part
    part = models.ForeignKey('Part', on_delete=models.PROTECT, blank=True, null=True)
    composite_part = models.ForeignKey('CompositePart', on_delete=models.PROTECT, blank=True, null=True)

    # needed to automate sequencing
    index_forward = models.TextField(validators=[validate_dna_string], blank=True, null=True)
    index_reverse = models.TextField(validators=[validate_dna_string], blank=True, null=True)

    wells = models.ManyToManyField('main.Well', blank=True, default=None,
                                   related_name="sample_wells",
                                   related_query_name="sample_wells")

    def get_absolute_url(self):
        return reverse('sample_details', args=[self.uuid])

    def get_label(self):
        return "sample"

    class Meta:
        app_label = 'main'


################################################################################
# Wells
################################################################################


class Well(models.Model):
    '''A physical well in the lab. A sample is not required for a well.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=32, blank=False)

    # Volume is defined at plate import (required)
    volume = models.FloatField()
    quantity = models.PositiveIntegerField(default=0, null=True, blank=True)
    media = models.CharField(max_length=250)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    # organism with wells cannot be deleted
    organism = models.ForeignKey('Organism', on_delete=models.PROTECT, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('well_details', args=[self.uuid])

    def __str__(self):
        if self.address and self.organism:
            return "<Well:%s,%s>" %(self.address, self.organism.name)
        elif self.organism:
            return "<Well:%s>" %(self.organism.name)
        else:
            return "<Well:%s>" %(self.address)

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "well"

    class Meta:
        app_label = 'main'


################################################################################
# Schemas
################################################################################

class Schema(models.Model):
    '''A JSON Schema to validate JSON information, usually
       protocol data.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    name = models.CharField(max_length=250, blank=False)
    description = models.CharField(max_length=500, blank=False)
    schema = JSONField(default=dict, blank=False, unique=True)
    schema_version = models.CharField(max_length=250)

    def get_absolute_url(self):
        return reverse('schema_details', args=[self.uuid])

    def __str__(self):
        return "<Schema:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "schema"

    class Meta:
        app_label = 'main'


################################################################################
# Protocol
################################################################################

class Protocol(models.Model):
    '''A protocol associated with a plan. Status is represented with the Plan.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField(max_length=500)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    data = JSONField(default=dict, blank=False)

    # Protocols exist without schemas. Schema deletion is technically allowed
    # but not unless an admin does it or something
    schema = models.ForeignKey('Schema', on_delete=models.DO_NOTHING, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('schema_details', args=[self.uuid])

    def get_label(self):
        return "protocol"

    class Meta:
        app_label = 'main'


################################################################################
# Operation
################################################################################

class Operation(models.Model):
    '''An operation is a series of plans required to complete
       a lab objective, such as 'clone x genes into y vector'.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    description = models.CharField(max_length=500)
    name = models.CharField(max_length=250, blank=False)

    plans = models.ManyToManyField('main.Plan', blank=True, default=None,
                                   related_name="operation_plans",
                                   related_query_name="operation_plans")

    def get_absolute_url(self):
        return reverse('operation_details', args=[self.uuid])

    def __str__(self):
        return "<Operation:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "operation"

    class Meta:
        app_label = 'main'



################################################################################
# Plans
################################################################################

class Plan(models.Model):
    '''A collection of protocols, plates, samples, and wells to be done.
    '''
    # These are similar to plate statuses - are these global statuses that should
    # be present across protocols, plates, samples, wells?
    PLAN_STATUS = [
        ('Executed', 'Executed'), 
        ('Trashed', 'Trashed'),
        ('Planned','Planned'),
        ('Failed', 'Failed'),
        ('Interrupted', 'Interrupted'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    name = models.CharField(max_length=250, blank=False)
    description = models.CharField(max_length=500)

    # If a parent plan is deleted, it's children are meaningless, however
    # a plan that is executed cannot be deleted (see plan pre_delete signal).
    # a plan does not necessarily require a parent
    parent = models.ForeignKey('Plan', on_delete=models.CASCADE, blank=True, null=True)

    # An operation with plans cannot be deleted
    operation = models.ForeignKey('Operation', on_delete=models.PROTECT)
    status = models.CharField(max_length=32, blank=False, choices=PLAN_STATUS)

    def add_item(self, item):
        '''can be used to add a well, protocol, plate, or sample. We don't
           currently validate the type, so a plan can include any type.
        '''
        data_content_type = ContentType.objects.get_for_model(item)

        return PlanData.objects.create(
            plan=self,
            data_content_type=data_content_type,
            data_object_id=item.pk,
        )

    def get_absolute_url(self):
        return reverse('plan_details', args=[self.uuid])

    def __str__(self):
        return "<Plan:%s>" % self.name

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "plan"

    class Meta:
        app_label = 'main'


class PlanData(models.Model):
    '''plan data can hold protocols, plates, samples, or wells. The PlanData is
       represented under a plan as plan_data, e.g., plan.plan_data.all()
    '''
    plan = models.ForeignKey('main.Plan', on_delete=models.CASCADE, related_name="plan_data")
    data_object_id = models.IntegerField()
    data_content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    data = GenericForeignKey(
        'data_content_type',
        'data_object_id',
    )

    def __str__(self):
        if self.plan:
            return "<PlanData:%s>" % self.plan.name
        return "<PlanData: (empty)>"

    def get_absolute_url(self):
        return reverse('plandata_details', args=[self.uuid])

    def __repr__(self):
        return self.__str__()

    def get_label(self):
        return "plandata"

    class Meta:
        app_label = 'main'

from .signals import protect_containers, delete_wells, protect_plan
