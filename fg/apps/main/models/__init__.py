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
from django.db.models.signals import post_save
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
from .schemas import MODULE_SCHEMAS
from .validators import (
    validate_dna_string,
    validate_name, 
    validate_json_schema
)

import string
import uuid

################################################################################
# Tags #########################################################################
################################################################################

class Tag(models.Model):
    '''A Tag object.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.CharField(max_length=250, blank=False, null=False)  # should this be unique?

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
    name = models.CharField(max_length=250, blank=False)
    description = models.CharField(max_length=500, blank=False)
    gene_id = models.CharField(max_length=250)
    part_type = models.CharField(max_length=250, choices=PART_TYPE)

    # Sequences (what are the maximum lengths here?)
    original_sequence = models.CharField(max_length=250, validators=[validate_dna_string])
    optimized_sequence = models.CharField(max_length=250, validators=[validate_dna_string])
    synthesized_sequence = models.CharField(max_length=250, validators=[validate_dna_string])
    full_sequence = models.CharField(max_length=250, blank=False, validators=[validate_dna_string])

    genbank = JSONField(default=dict)

    # It would be good to have descriptors for these fields
    vector = models.CharField(max_length=250)
    primer_for = models.CharField(max_length=250, validators=[validate_dna_string])
    primer_rev = models.CharField(max_length=250, validators=[validate_dna_string])
    barcode = models.CharField(max_length=250, validators=[validate_dna_string])
    translation = models.CharField(max_length=250)
    vdb = models.CharField(max_length=250, blank=False)

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

    # Can the same sample exist between parts?
    samples = models.ManyToManyField('main.Sample', blank=True, default=None,
                                    related_name="parts_samples",
                                    related_query_name="parts_samples")

    # When a collection is deleted, so are the parts
    # And assumes parts can only belong to one collection (is this true?)
    collection = models.ForeignKey('Collection', on_delete=models.CASCADE, blank=False)

    # When an author is deleted, his parts are deleted
    author = models.ForeignKey('Author', on_delete=models.CASCADE, blank=False)

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
    name = models.CharField(max_length=250, blank=False)

    # What is the difference between a readme and description? Should be consistent
    readme = models.CharField(max_length=500, blank=False)

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

    name = models.CharField(max_length=250, blank=False, validators=[validate_name])
    container_type = models.CharField(max_length=250, blank=False, choices=CONTAINER_TYPES)
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
    name = models.CharField(max_length=250, blank=False)

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
    container = models.ForeignKey('Container', on_delete=models.CASCADE, blank=False)
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
    '''A robot in the lab.
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
    mta_type = models.CharField(max_length=32, choices=MTA_TYPE, blank=False)

    # Are we sure we want all files hosted remote to server?
    # The agreement file is named based on the UUID here?
    agreement_file = models.ForeignKey('Files', on_delete=models.CASCADE)

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
        ('microcentrifuge2ml')
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plate_type = models.CharField(max_length=32, choices=PLATE_TYPE, blank=False)
    plate_form = models.CharField(max_length=32, choices=PLATE_FORM, blank=False)
    status = models.CharField(max_length=32, choices=PLATE_STATUS, blank=False)
    plate_name = models.CharField(max_length=250, blank=False)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    # What is this? Breadcrumb in a web page or something relevant to the plate?
    breadcrumb = models.CharField(max_length=32, choices=PLATE_STATUS, blank=False)
    plate_vendor_id = models.CharField(max_length=250)
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


def generate_plate_wells(sender, instance, **kwargs):
    '''After save of a plate, based on the width and length generate it's associated
       wells. This assumes that we want to model wells for a plate as soon as it's 
       generated (do we not?).

       Parameters
       ==========
       instance: is the instance of the Plate
       sender: is the plate model (we likely don't need)
    '''
    # Well positions are generated based on the plate dimensions
    positions = []
    
    for letter in list(string.ascii_uppercase[0:instance.height]):
        for number in range(instance.length):
            positions.append((letter, number+1))

    # Create wells, add to plate
    for location in [x[0]+str(x[1]) for x in positions]:
        well = Well.objects.create(address=location)
        well.save()
        instance.wells.add(well)

    instance.save()



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


# QUESTION: why have platesets and distributions? Why not just have platesets represented
#           in orders? Is there any other kind of entity that could be distributed (and would
#           warrant a more flexible model?


################################################################################
# Sample
################################################################################

class Sample(models.Model):
    '''A physical sample in the lab.
    '''

    SAMPLE_STATUS = [
        ('Confirmed','Confirmed'), 
        ('Mutated','Mutated')
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
    SAMPLE_EVIDENCE = [
        ('Twist_Confirmed', 'Twist_Confirmed'),
        ('NGS', 'NGS'),
        ('Sanger', 'Sanger'),
        ('Nanopore', 'Nanopore'),
        ('Derived', 'Derived')
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sample_type = models.CharField(max_length=32, choices=SAMPLE_TYPE)
    status = models.CharField(max_length=32, choices=SAMPLE_STATUS, blank=False)
    evidence = models.CharField(max_length=32, choices=SAMPLE_EVIDENCE, blank=False)
    vendor = models.CharField(max_length=250)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    # Confirm that a sample has one part, and delete part == delete sample?
    derived_from = models.ForeignKey('Sample', on_delete=models.CASCADE)
    part = models.ForeignKey('Part', on_delete=models.CASCADE, blank=False)

    index_for = models.CharField(max_length=250, validators=[validate_dna_string])
    index_rev = models.CharField(max_length=250, validators=[validate_dna_string])

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
    '''A physical well in the lab.
    '''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=32, blank=False)
    volume = models.FloatField()
    quantity = models.PositiveIntegerField()
    media = models.CharField(max_length=250)

    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    # If a plate is deleted, a well belonging to it is also deleted.
    plate = models.ForeignKey('Plate', on_delete=models.CASCADE, blank=False)

    # Why did original model code have uuid for organism (model) and organism string with this comment
    # organism = db.Column(db.String) # IMPLEMENT ORGANISM CONTROL
    organism = models.ForeignKey('Organism', on_delete=models.DO_NOTHING)

    # The original model had samples required for wells, but why is a sample required?
    # I modeled the Sample to have wells instead, and it shouldn't be required
    # in case we want to represent a sample that doesn't yet have a well.

    # Volume is listed as required - where does it come from? If it's added
    # when we fill a well, it shouldn't be required. If it's required,
    # it would need to be generated by plate post_save, so the plate would
    # need to include it's volume per well. The same is true for media.

    def get_label(self):
        return "well"

    class Meta:
        app_label = 'main'

# Distribution


################################################################################
# Protocol
################################################################################

class Protocol(models.Model):
    '''a set of plates combined with a schema (what is this exactly?)
    '''
    # Is there any reason to not store this as a boolean, potential for other states?
    PROTOCOL_STATUS = [
        ('Executed','Executed'), 
        ('Planned','Planned')
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=32, blank=False, choices=PROTOCOL_STATUS)
    description = models.CharField(max_length=500)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)

    data = JSONField(default=dict)

    # QUESTION: A schema is originally modeled as it's own object. Is this necessary?
    # Are schemas dynamic, or can we store templates somewhere?
    # If a schema is deleted, a protocol is deleted.
    # schema = models.ForeignKey('Schema', on_delete=models.CASCADE, blank=False)
    schema = JSONField(default=dict)

    plates = models.ManyToManyField('main.Well', blank=True, default=None,
                                    related_name="protocol_plates",
                                    related_query_name="protocol_plates")

    # protocol_required = ['protocol','schema_uuid']
    # QUESTION: for protocol required you had protocol but I don't see a field. Did you mean plates? or the data?
    def get_label(self):
        return "protocol"

    class Meta:
        app_label = 'main'


################################################################################
# Operation
################################################################################

class Operation(models.Model):
    '''A group of plans.
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
        ('Executed','Executed'), 
        ('Trashed','Trashed'),
        ('Planned','Planned')
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time_created = models.DateTimeField('date created', auto_now_add=True) 
    time_updated = models.DateTimeField('date modified', auto_now=True)
    name = models.CharField(max_length=250, blank=False)
    description = models.CharField(max_length=500)

    # Are these correct?
    parent = models.ForeignKey('Plan', on_delete=models.CASCADE)
    operation = models.ForeignKey('Operation', on_delete=models.DO_NOTHING)
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

    # What kind of information would go here?
    notes = models.CharField(max_length=500)

    # TODO: this was originally distributions. It should either be just platesets,
    # or a distribution modeled as a more generic object.
    platesets = models.ManyToManyField('main.Plan', blank=False,
                                       related_name="order_platesets",
                                       related_query_name="order_platesets")
 
    # Associated with an email that is looked up to get address
    # assumes that if a user deletes account, we delete orders
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, blank=False)
    material_transfer_agreement = models.ForeignKey('main.MaterialTransferAgreement', 
                                                    on_delete=models.DO_NOTHING)

    def get_label(self):
        return "order"

    class Meta:
        app_label = 'main'

# Schema

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

# signals
post_save.connect(generate_plate_wells, sender=Plate)
