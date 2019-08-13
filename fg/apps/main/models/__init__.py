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
from fg.apps.main.utils import generate_sha256
from fg.settings import (
    DEFAULT_PLATE_HEIGHT,
    DEFAULT_PLATE_LENGTH
)
from .schemas import MODULE_SCHEMAS
from .validators import (
    validate_dna_string,
    validate_name, 
    validate_json_schema
)

import string
import uuid
import re

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

    def save(self, *args, **kwargs):
        '''tags are enforced as all lowercase to avoid duplication, along
           with removing all special characters except for dashes and :.
           Dashes and : are allowed. 
        '''
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

    affiliation = models.CharField(max_length=250, blank=False, null=False)

    # Maximum length is only 19, but might as well prepare for future extension
    orcid = models.CharField(max_length=32, blank=False, unique=True)

    # Tags are shared between models
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

    IP_CHECKED_CHOICES = [
        ('NOT_CHECKED', False),
        ('CHECKED', True) 
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Why do these fields use time, and others use date (e.g., see ip_check*)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    status = models.CharField(max_length=250, choices=PART_STATUS, default='null')
    name = models.CharField(max_length=250, blank=False)
    description = models.CharField(max_length=500, blank=False)
    gene_id = models.CharField(max_length=250)
    part_type = models.CharField(max_length=250, choices=PART_TYPE)

    # Sequences - we would want 10K to 100K, can go up to 4 million (but not practical)
    original_sequence = models.TextField(validators=[validate_dna_string])
    optimized_sequence = models.TextField(validators=[validate_dna_string])
    synthesized_sequence = models.TextField(validators=[validate_dna_string])
    full_sequence = models.TextField(blank=False, validators=[validate_dna_string])

    genbank = JSONField(default=dict)

    # It would be good to have descriptors for these fields
    vector = models.CharField(max_length=250)
    primer_forward = models.CharField(max_length=250, validators=[validate_dna_string])
    primer_reverse = models.CharField(max_length=250, validators=[validate_dna_string])
    barcode = models.CharField(max_length=250, validators=[validate_dna_string])
    translation = models.CharField(max_length=250)

    # What is an ip check?
    ip_check_date = models.DateTimeField('date ip checked')
    ip_check = models.BooleanField(choices=IP_CHECKED_CHOICES, default='NOT_CHECKED')
    ip_check_ref = models.CharField(max_length=250, blank=False)

    ## Foreign Keys and Relationships

    # The assumption here is that tags and files can be shared between models
    tags = models.ManyToManyField('main.Tag', blank=True, default=None,
                                   related_name="parts_tags",
                                   related_query_name="parts_tags")

    files = models.ManyToManyField('main.Files', blank=True, default=None,
                                   related_name="parts_files",
                                   related_query_name="parts_files")

    # The same sample can exist between parts
    samples = models.ManyToManyField('main.Sample', blank=True, default=None,
                                    related_name="parts_samples",
                                    related_query_name="parts_samples")

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
    name = models.CharField(max_length=250, blank=False)

    # This was originally the collection "README"
    description = models.CharField(max_length=500, blank=False)

    # When a parent is deleted, the children remain
    parent = models.ForeignKey('Collection', on_delete=models.DO_NOTHING)

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
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    name = models.CharField(max_length=250, blank=False, validators=[validate_name])
    container_type = models.CharField(max_length=250, blank=False, choices=CONTAINER_TYPES)
    description = models.CharField(max_length=500)
    estimated_temperature = models.FloatField()

    # Meter coordinates for the locations of things in lab
    # https://github.com/vsoch/freegenes/issues/10
    x = models.FloatField()
    y = models.FloatField()
    z = models.FloatField()

    # When a parent is deleted, so are the children. If a file is deleted, do nothing
    parent = models.ForeignKey('Container', on_delete=models.CASCADE)
    image = models.ForeignKey('Files', on_delete=models.DO_NOTHING)
 
    plates = models.ManyToManyField('main.Plate', blank=True, default=None,
                                    related_name="container_plates",
                                    related_query_name="container_plates")

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
    name = models.CharField(max_length=250, blank=False, validators=[validate_name])

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


def get_upload_to(instance, filename):
    '''upload to a filename named based on the MTA uuid.
       UPLOAD_FOLDER is data or /code/data in the container.
    '''
    # The upload folder is the MTA subfolder of /code/data
    upload_folder = os.path.join(settings.UPLOAD_PATH, 'MTA')
    if not os.path.exists(upload_folder):
        os.mkdir(upload_folder)

    # Get the extension of the current filename
    _, ext = os.path.splitext(filename)
    filename = os.path.join(upload_folder, instance.uuid + ext)
    return time.strftime(filename)


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
    agreement_file = models.FileField(upload_to=get_upload_to)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    institution = models.CharField(max_length=250, blank=False)

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
    plate_name = models.CharField(max_length=250, blank=False)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    # legacy implementation of a "lab tree" (see container) with information stored as a string
    breadcrumb = models.CharField(max_length=500, blank=False)
    plate_vendor_id = models.CharField(max_length=250)

    # Track the number of times a plate has been frozen and thawed, each freeze damages the cells
    thaw_count = models.IntegerField(default=0)

    # This is generally bad practice to have a notes field - what is this for?
    notes = models.CharField(max_length=500)

    # This is a proposed addition so we generate wells from plates with known dimensions
    height = models.IntegerField(blank=False, default=DEFAULT_PLATE_HEIGHT)
    length = models.IntegerField(blank=False, default=DEFAULT_PLATE_LENGTH)

    container = models.ForeignKey('Container', on_delete=models.CASCADE)
    protocol = models.ForeignKey('Protocol', on_delete=models.CASCADE)
   
    def get_label(self):
        return "plate"

    class Meta:
        app_label = 'main'

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

    COLLABORATOR_CHOICES = [
        ('OUTSIDE', True), 
        ('WITHIN_INSTITUTION', False)
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
    outside_collaborator = models.BooleanField(choices=COLLABORATOR_CHOICES, default='OUTSIDE')

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sample_type = models.CharField(max_length=32, choices=SAMPLE_TYPE)
    status = models.CharField(max_length=32, choices=SAMPLE_STATUS, blank=False)

    # Each sequencing method is different (Sanger kind of sucks, and so I barely trust it, 
    # while NGS is very strong, and so I completely trust it) which is important.
    evidence = models.CharField(max_length=32, choices=SAMPLE_EVIDENCE, blank=False)
    vendor = models.CharField(max_length=250)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    # A sample with derivations cannot be deleted, a part with samples cannot be deleted
    # If we have some frozen bacteria, and scrape a little off and put it into 
    # a new tube to grow overnight, the new growth is not the same sample as the 
    # frozen bacteria (maybe there was some contamination, or maybe we bottlenecked 
    # the population so there are more mutations). We think it's status is 
    # confirmed, but the only evidence we have is that it was "Derived" from a confirmed sample.
    derived_from = models.ForeignKey('Sample', on_delete=models.PROTECT)
    part = models.ForeignKey('Part', on_delete=models.PROTECT, blank=False)

    # needed to automate sequencing
    index_forward = models.CharField(max_length=250, validators=[validate_dna_string])
    index_reverse = models.CharField(max_length=250, validators=[validate_dna_string])

    wells = models.ManyToManyField('main.Well', blank=True, default=None,
                                   related_name="sample_wells",
                                   related_query_name="sample_wells")

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
    volume = models.FloatField()
    quantity = models.PositiveIntegerField()
    media = models.CharField(max_length=250)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    # A plate with wells cannot be deleted
    plate = models.ForeignKey('Plate', on_delete=models.PROTECT, blank=False)

    # organism with wells cannot be deleted
    organism = models.ForeignKey('Organism', on_delete=models.PROTECT)

    # Volume is listed as required - where does it come from? If it's added
    # when we fill a well, it shouldn't be required. If it's required,
    # it would need to be generated by plate post_save, so the plate would
    # need to include it's volume per well. The same is true for media.

    def get_label(self):
        return "well"

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
    schema = models.ForeignKey('Schema', on_delete=models.DO_NOTHING)

    plates = models.ManyToManyField('main.Plate', blank=True, default=None,
                                    related_name="%(class)s_protocol")

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
    parent = models.ForeignKey('Plan', on_delete=models.CASCADE)

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

    def get_label(self):
        return "plandata"

    class Meta:
        app_label = 'main'


################################################################################
# Orders
################################################################################

class Order(models.Model):
    '''A request by a user for a shipment. The address/ personal information
       is not stored here, but looked up elsewhere via the user address.
       A simple solution to start this off would be to have a form (only
       accessible with login) that feeds to a Google sheet (in Stanford
       Drive - check security level) that keeps the order information.
       Scripts / automation to generate order labels, etc. for addresses
       could be derived from there.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    name = models.CharField(max_length=250, blank=False)

    # Notes match to physical sticky notes in the lab
    notes = models.CharField(max_length=500)
    distributions = models.ManyToManyField('main.Distribution', blank=False,
                                           related_name="order_distribution",
                                           related_query_name="order_distribution")
 
    # When a user is deleted don't delete orders
    user = models.ForeignKey('users.User', on_delete=models.DO_NOTHING, blank=False)

    # When an MTA is deleted, we don't touch the order
    material_transfer_agreement = models.ForeignKey('main.MaterialTransferAgreement', 
                                                    on_delete=models.DO_NOTHING)

    def get_label(self):
        return "order"

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
    schema = JSONField(default=dict, blank=False)
    schema_version = models.CharField(max_length=250)

    schema_hash = models.CharField(max_length=250)

    def save(self, *args, **kwargs):
        '''Calculate the schema_hash on save (sha256). The schema is required,
           so it will throw an error by the super if not defined, so we check
           just in case.
        '''
        if self.schema:
            self.schema_version = generate_sha256(self.schema)
        return super(Schema, self).save(*args, **kwargs)


    def get_label(self):
        return "schema"

    class Meta:
        app_label = 'main'


# Thinking: holding the shipment information in the system is allocating too much
# responsibility to it - the farthest representation I think we should take
# is to represent an order, with a set of items and a number. The shipping
# details (addresses) along with status are out of scope for the FreeGenes
# database. We need to have another integration that can handle this, that doesn't
# require storing PI with FreeGenes. 

# The following should be represented elsewhere (personal information)
# Shipment
# Address
# Parcel
# Institution
