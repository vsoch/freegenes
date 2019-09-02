'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib.postgres.fields import JSONField
from django.conf import settings
from django.urls import reverse

from fg.apps.main.models import (
    Author,
    Container,
    Collection,
    Distribution,
    Institution,
    Module,
    Operation,
    Organism,
    Part,
    Plan,
    Plate,
    PlateSet,
    Protocol,
    Robot,
    Sample,
    Schema,
    Tag
)

from fg.apps.orders.models import Order
from rest_framework import (
    generics,
    serializers,
    viewsets,
    status
)
from rest_framework.exceptions import (
    PermissionDenied,
    NotFound
)
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView


################################################################################
# Custom ViewSet Functions
# In many cases, we need to provide a limited view when the user requests all
# paginated entities, versus lookup by id. These base functions allows for that.
################################################################################

def limited_get_object(self, uuid):
    '''get an object, or return None. Should be used as the function get_object
       for an APIViewSet 
    '''
    try:
        instance = self.Model.objects.get(uuid=uuid)
    except self.Model.DoesNotExist:
        instance = None
    return instance


def limited_get_queryset(self):
    '''get a queryset from the APIViewSet Model. Should be used as the 
       function get_queryset for an APIViewSet 
    '''
    return self.Model.objects.all()


def limited_get_serializer_class(self):
    '''this function is the main controller for returning a limited view. When
       list is called by the APIViewSet based on a get request that doesn't have
       an id (indicating a request for more than one) the class remove_data is
       set to True, and a limited Serializer is returned here.
    '''
    if self.remove_data:
        return self.regularSerializer
    return self.detailedSerializer


def limited_list(self, request, *args, **kwargs):
    '''this function is the same as the parent, but we set self.remove_data
       to True first to indicate the user is listing.
    '''
    self.remove_data = True
    queryset = self.filter_queryset(self.get_queryset())

    page = self.paginate_queryset(queryset)
    if page is not None:
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    serializer = self.get_serializer(queryset, many=True)
    return Response(serializer.data)


def limited_get(self, request, *args, **kwargs):
    '''get an object. If the request provides an id, this indicates we are
       requesting one entity, and a single (more detailed) entry is returned.
       If not, we return a call to list.
    '''

    # If we don't have an id, return a listing
    if "id" not in kwargs:
        return self.list(request, *args, **kwargs)

    # Otherwise return a single view
    instance = self.get_object(uuid=kwargs['id'])
    if not instance:
        raise NotFound(detail="Instance not found")

    serializer = self.detailedSerializer(instance)
    return Response(serializer.data)



################################################################################
# Serializers paired with Viewsets
################################################################################

# Authors

class AuthorSerializer(serializers.ModelSerializer):

    tags = serializers.SerializerMethodField('tags_name')
    label = serializers.SerializerMethodField('get_label')

    def tags_name(self, author):
        return [x.tag for x in author.tags.all()]

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Author
        fields = ('uuid', 'name', 'email', 'affiliation', 'orcid', 
                  'tags', 'label')

class AuthorViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Author.objects.all()

    serializer_class = AuthorSerializer

# Containers

class ContainerSerializer(serializers.ModelSerializer):

    plates = serializers.SerializerMethodField('plates_list')
    parent = serializers.SerializerMethodField('get_parent')
    label = serializers.SerializerMethodField('get_label')

    def plates_list(self, container):
        return [{"name": plate.name, "uuid": plate.uuid} for plate in container.plate_set.all()]

    def get_label(self, container):
        return container.get_label()

    def get_parent(self, container):
        '''return the parent name, if it exists. Otherwise return None.'''
        parent = None
        if container.parent:
            parent = {"name": container.parent.name,
                      "uuid": container.parent.uuid}
        return parent
 
    class Meta:
        model = Container
        fields = ('uuid', 'time_created', 'time_updated', 'name', 'container_type', 'description',
                  'estimated_temperature', 'x', 'y', 'z', 'parent', 'plates', 'label')

class ContainerViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Container.objects.all()

    serializer_class = ContainerSerializer


# Collections

class SingleCollectionSerializer(serializers.ModelSerializer):
    '''provide all fields, including notes
    '''
    tags = serializers.SerializerMethodField('tags_list')
    parent = serializers.SerializerMethodField('get_parent')
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    def tags_list(self, collection):
        return [tag.tag for tag in collection.tags.all()]

    def get_parent(self, collection):
        '''return the parent name, if it exists. Otherwise return None.'''
        parent = None
        if collection.parent:
            parent = {"name": collection.parent.name,
                      "uuid": collection.parent.uuid}
        return parent
 
    class Meta:
        model = Collection
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'parent', 'tags', 'label')

class CollectionSerializer(SingleCollectionSerializer):
    '''provide all fields except for description, which can be lengthy
    '''
    class Meta:
        model = Collection
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'parent', 'tags', 'label')


class CollectionViewSet(ListModelMixin, generics.GenericAPIView):
    '''Retrieve a single detailed instance with a uuid, or a more generic list
    '''   
    remove_data = False

    # These fields are required and should be instantiated by subclass
    Model = Collection
    detailedSerializer = SingleCollectionSerializer
    regularSerializer = CollectionSerializer

CollectionViewSet.get_object = limited_get_object
CollectionViewSet.get_queryset = limited_get_queryset
CollectionViewSet.get_serializer_class = limited_get_serializer_class
CollectionViewSet.list = limited_list
CollectionViewSet.get = limited_get


# Distributions

class DistributionSerializer(serializers.ModelSerializer):

    platesets = serializers.SerializerMethodField('get_platesets')
    label = serializers.SerializerMethodField('get_label')

    def get_platesets(self, distribution):
        return [{"name": p.name, "uuid": p.uuid} for p in distribution.platesets.all()]
 
    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Distribution
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'platesets', 'label')


class DistributionViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Distribution.objects.all()

    serializer_class = DistributionSerializer


# Modules

class ModuleSerializer(serializers.ModelSerializer):
    '''a Module serializer provides all fields except for data and notes. The
       user is required to use the SingleModuleSerializer to get the extra data
    '''
    container = serializers.SerializerMethodField('get_container')
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    def get_container(self, module):
        container = None
        if module.container:
            container = {'uuid': module.container.uuid,
                         'name': module.container.name}
        return container
 
    class Meta:
        model = Module
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'container', 'model_id',
                  'module_type', 'label')


class SingleModuleSerializer(ModuleSerializer):
    '''a SingleModule serializer provides all fields
    '''
    class Meta:
        model = Module
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'container', 'notes', 'model_id',
                  'module_type', 'data', 'label')


class ModuleViewSet(ListModelMixin, generics.GenericAPIView):
    '''Retrieve a single detailed module with a uuid, or a more generic list
    '''   
    remove_data = False

    # These fields are required and should be instantiated by subclass
    Model = Module
    detailedSerializer = SingleModuleSerializer
    regularSerializer = ModuleSerializer

ModuleViewSet.get_object = limited_get_object
ModuleViewSet.get_queryset = limited_get_queryset
ModuleViewSet.get_serializer_class = limited_get_serializer_class
ModuleViewSet.list = limited_list
ModuleViewSet.get = limited_get


# Institutions

class InstitutionSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Institution
        fields = ('uuid', 'name', 'signed_master', 'label')


class InstitutionViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Institution.objects.all()

    serializer_class = InstitutionSerializer


# Operations

class OperationSerializer(serializers.ModelSerializer):

    plans = serializers.SerializerMethodField('plans_list')
    label = serializers.SerializerMethodField('get_label')

    def plans_list(self, operation):
        plans = []
        for plan in operation.plans.all():
            plans.append({"name": plan.name,
                          "uuid": plan.uuid})
        return plans

    def get_label(self, instance):
        return instance.get_label()
 
    class Meta:
        model = Operation
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'plans', 'label')


class OperationViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Operation.objects.all()

    serializer_class = OperationSerializer


# Orders


class OrderSerializer(serializers.ModelSerializer):

    distributions = serializers.SerializerMethodField('distributions_list')
    label = serializers.SerializerMethodField('get_label')

    def distributions_list(self, order):
        distributions = []
        for distribution in order.distributions.all():
            distributions.append({"name": distribution.name,
                                  "uuid": distribution.uuid})
        return distributions

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Order
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'notes', 'distributions', 'label')


class OrderViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Order.objects.all()

    serializer_class = OrderSerializer



# Organisms

class OrganismSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Organism
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'genotype', 'label')


class OrganismViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Organism.objects.all()

    serializer_class = OrganismSerializer


# Part

class SinglePartSerializer(serializers.ModelSerializer):
    '''a single part serializer exposes all fields, meaning the user has
       looked up a part based on a uuid. If we are listing all parts, we
       remove the heavier / longer fields (sequences, etc.). Neither
       expose any information about ip checks or files.
    '''

    tags = serializers.SerializerMethodField('tags_list')
    collections = serializers.SerializerMethodField('collections_list')
    author = serializers.SerializerMethodField('get_author')
    label = serializers.SerializerMethodField('get_label')

    def tags_list(self, part):
        tags = []
        for tag in part.tags.all():
            tags.append({"name": tag.tag,
                         "uuid": tag.uuid})
        return tags

    def collections_list(self, part):
        collections = []
        for collection in part.collections.all():
            collections.append({'name': collection.name,
                                'uuid': collection.uuid})
        return collections

    def get_author(self, part):
        author = None
        if part.author:
            author = {'name': part.author.name, 'uuid': part.author.uuid}
        return author

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Part
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'status', 'gene_id', 'part_type',
                  'genbank', 'original_sequence', 'optimized_sequence',
                  'synthesized_sequence', 'full_sequence', 'vector',
                  'primer_forward', 'primer_reverse', 'barcode', 
                  'label', 'translation', 'tags', 'collections', 
                  'author')

class PartSerializer(SinglePartSerializer):
    '''Don't include more extensive data files.
    '''

    class Meta:
        model = Part
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'status', 'gene_id', 'part_type', 
                  'label', 'vector', 'barcode', 'tags', 'collections', 
                  'author')


class PartViewSet(ListModelMixin, generics.GenericAPIView):
    '''Retrieve a single detailed instance with a uuid, or a more generic list
    '''   
    remove_data = False

    # These fields are required and should be instantiated by subclass
    Model = Part
    detailedSerializer = SinglePartSerializer
    regularSerializer = PartSerializer

PartViewSet.get_object = limited_get_object
PartViewSet.get_queryset = limited_get_queryset
PartViewSet.get_serializer_class = limited_get_serializer_class
PartViewSet.list = limited_list
PartViewSet.get = limited_get


# Plans


class PlanSerializer(serializers.ModelSerializer):

    parent = serializers.SerializerMethodField('get_parent')
    operation = serializers.SerializerMethodField('get_operation')
    label = serializers.SerializerMethodField('get_label')

    def get_parent(self, plan):
        parent = None
        if plan.parent:
            parent = {'name': plan.parent.name, 'uuid': plan.parent.uuid}
        return parent

    def get_operation(self, plan):
        operation = None
        if plan.operation:
            operation = {'name': plan.operation.name, 'uuid': plan.operation.uuid}
        return operation

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Plan
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'parent', 'operation', 'status', 'label')


class PlanViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Plan.objects.all()

    serializer_class = PlanSerializer


# Plates

class SinglePlateSerializer(serializers.ModelSerializer):

    container = serializers.SerializerMethodField('get_container')
    protocol = serializers.SerializerMethodField('get_protocol')
    wells = serializers.SerializerMethodField('get_wells')
    label = serializers.SerializerMethodField('get_label')

    def get_container(self, plate):
        container = None
        if plate.container:
            container = {'name': plate.container.name, 'uuid': plate.container.uuid}
        return container

    def get_protocol(self, plate):
        protocol = None
        if plate.protocol:
            protocol = {'uuid': plate.protocol.uuid}
        return protocol

    def get_wells(self, plate):
        wells = []
        for well in plate.wells.all():
            wells.append({'address': well.address, 'uuid': well.uuid})
        return wells

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Plate
        fields = ('uuid', 'time_created', 'time_updated', 'plate_type', 
                  'plate_form', 'status', 'name', 'thaw_count',
                  'notes', 'height', 'length', 'container', 'protocol', 
                  'wells', 'label')


class PlateSerializer(SinglePlateSerializer):
    '''dont return wells when we are listing plates'''

    class Meta:
        model = Plate
        fields = ('uuid', 'time_created', 'time_updated', 'plate_type', 
                  'plate_form', 'status', 'name', 'thaw_count',
                  'notes', 'height', 'length', 'protocol', 'label')


class PlateViewSet(ListModelMixin, generics.GenericAPIView):
    '''Retrieve a single detailed instance with a uuid, or a more generic list
    '''   
    remove_data = False

    # These fields are required and should be instantiated by subclass
    Model = Plate
    detailedSerializer = SinglePlateSerializer
    regularSerializer = PlateSerializer

PlateViewSet.get_object = limited_get_object
PlateViewSet.get_queryset = limited_get_queryset
PlateViewSet.get_serializer_class = limited_get_serializer_class
PlateViewSet.list = limited_list
PlateViewSet.get = limited_get


# PlateSet

class SinglePlateSetSerializer(serializers.ModelSerializer):
    '''platesets can be large, so only the Single serializer returns the
       list of plates.
    '''

    plates = serializers.SerializerMethodField('get_plates')
    label = serializers.SerializerMethodField('get_label')

    def get_plates(self, plateset):
        plates = []
        for plate in plateset.plates.all():
            plates.append({'name': plate.name, 'uuid': plate.uuid})
        return plates

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = PlateSet
        fields = ('uuid', 'description', 'name', 'time_created', 
                  'time_updated', 'plates', 'label')


class PlateSetSerializer(SinglePlateSetSerializer):
    '''when serializing a list, don't return the plates
    '''
    class Meta:
        model = PlateSet
        fields = ('uuid', 'description', 'name', 'time_created', 
                  'time_updated', 'label')


class PlateSetViewSet(ListModelMixin, generics.GenericAPIView):
    '''Retrieve a single detailed instance with a uuid, or a more generic list
    '''   
    remove_data = False

    # These fields are required and should be instantiated by subclass
    Model = PlateSet
    detailedSerializer = SinglePlateSetSerializer
    regularSerializer = PlateSetSerializer

PlateSetViewSet.get_object = limited_get_object
PlateSetViewSet.get_queryset = limited_get_queryset
PlateSetViewSet.get_serializer_class = limited_get_serializer_class
PlateSetViewSet.list = limited_list
PlateSetViewSet.get = limited_get


# Protocol

class SingleProtocolSerializer(serializers.ModelSerializer):

    schema = serializers.SerializerMethodField('get_schema')
    label = serializers.SerializerMethodField('get_label')

    def get_schema(self, protocol):
        schema = None
        if protocol.schema:
            schema = {'name': protocol.schema.name, 'uuid': protocol.schema.uuid}
        return schema

    def get_label(self, instance):
        return instance.get_label()
 
    class Meta:
        model = Protocol
        fields = ('uuid', 'time_created', 'time_updated', 'data', 
                  'description', 'label', 'schema')

class ProtocolSerializer(SingleProtocolSerializer):
    '''dont include the data when listing'''

    class Meta:
        model = Protocol
        fields = ('uuid', 'time_created', 'time_updated', 
                  'description', 'label', 'schema')


class ProtocolViewSet(ListModelMixin, generics.GenericAPIView):
    '''Retrieve a single detailed instance with a uuid, or a more generic list
    '''   
    remove_data = False

    # These fields are required and should be instantiated by subclass
    Model = Protocol
    detailedSerializer = SingleProtocolSerializer
    regularSerializer = ProtocolSerializer

ProtocolViewSet.get_object = limited_get_object
ProtocolViewSet.get_queryset = limited_get_queryset
ProtocolViewSet.get_serializer_class = limited_get_serializer_class
ProtocolViewSet.list = limited_list
ProtocolViewSet.get = limited_get


# Robot

class RobotSerializer(serializers.ModelSerializer):

    left_mount = serializers.SerializerMethodField('get_left_mount')
    right_mount = serializers.SerializerMethodField('get_right_mount')
    container = serializers.SerializerMethodField('get_container')
    label = serializers.SerializerMethodField('get_label')

    def get_field_instance(self, robot, instance_name):
        '''a shared class to get a field instance (based on attribute name)
           and return a dictionary with its name and uuid
        '''
        entity = None
        if getattr(robot, instance_name):
            instance = getattr(robot, instance_name)
            entity = {'name': instance.name, 'uuid': instance.uuid}
        return entity

    def get_left_mount(self, robot):
        return self.get_field_instance(robot, 'left_mount')

    def get_right_mount(self, robot):
        return self.get_field_instance(robot, 'right_mount')

    def get_container(self, robot):
        return self.get_field_instance(robot, 'container')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Robot
        fields = ('uuid', 'time_created', 'time_updated', 'container', 
                  'name', 'robot_id', 'robot_type', 'notes', 'server_version',
                  'right_mount', 'left_mount', 'label')


class RobotViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Robot.objects.all()

    serializer_class = RobotSerializer


# Sample

class SingleSampleSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')
    derived_from = serializers.SerializerMethodField('get_derived_from')
    part = serializers.SerializerMethodField('get_part')
    wells = serializers.SerializerMethodField('get_wells')

    def get_derived_from(self, sample):
        derived_from = None
        if sample.derived_from:
            derived_from = {'uuid': sample.derived_from.uuid}
        return derived_from

    def get_part(self, sample):
        part = None
        if sample.part:
            part = {'name': sample.part.name, 'uuid': sample.part.uuid}
        return part

    def get_wells(self, sample):
        wells = []
        for well in sample.wells.all():
            wells.append({'address': well.address, 'uuid': well.uuid})
        return wells

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Sample
        fields = ('uuid', 'outside_collaborator', 'sample_type', 'status',
                  'evidence', 'vendor', 'time_created', 'time_updated',
                  'derived_from', 'part', 'index_forward', 'index_reverse',
                  'label', 'wells')


class SampleSerializer(SingleSampleSerializer):

    class Meta:
        model = Sample
        fields = ('uuid', 'outside_collaborator', 'sample_type', 'status',
                  'evidence', 'vendor', 'time_created', 'time_updated',
                  'derived_from', 'part', 'index_forward', 'index_reverse',
                  'label')


class SampleViewSet(ListModelMixin, generics.GenericAPIView):
    '''Retrieve a single detailed instance with a uuid, or a more generic list
    '''   
    remove_data = False

    # These fields are required and should be instantiated by subclass
    Model = Sample
    detailedSerializer = SingleSampleSerializer
    regularSerializer = SampleSerializer

SampleViewSet.get_object = limited_get_object
SampleViewSet.get_queryset = limited_get_queryset
SampleViewSet.get_serializer_class = limited_get_serializer_class
SampleViewSet.list = limited_list
SampleViewSet.get = limited_get


# Schema

class SchemaSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Schema
        fields = ('uuid', 'time_created', 'time_updated', 'name',
                  'description', 'schema', 'schema_version', 'label')

class SchemaViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Schema.objects.all()

    serializer_class = SchemaSerializer


# Tags

class TagSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Tag
        fields = ('uuid', 'tag', 'label')

class TagViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Tag.objects.all()

    serializer_class = TagSerializer
