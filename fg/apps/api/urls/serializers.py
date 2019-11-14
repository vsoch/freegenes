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
    CompositePart,
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
    Tag,
    Well
)

from fg.apps.orders.models import Order
from .permissions import IsStaffOrSuperUser
from rest_framework import (
    generics,
    mixins,
    serializers,
    viewsets,
    status
)
from rest_framework.exceptions import (
    PermissionDenied,
    NotFound
)

from rest_framework.response import Response
from rest_framework.views import APIView


################################################################################
# Serializers paired with Viewsets
################################################################################

# Authors

class AuthorSerializer(serializers.ModelSerializer):

    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), required=False, many=True)
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Author
        fields = ('uuid', 'name', 'email', 'affiliation', 'orcid', 
                  'tags', 'label')

class AuthorViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Author.objects.all()

    serializer_class = AuthorSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Containers

class ContainerSerializer(serializers.ModelSerializer):

    plates = serializers.SerializerMethodField('plates_list')
    parent = serializers.PrimaryKeyRelatedField(queryset=Container.objects.all())
    label = serializers.SerializerMethodField('get_label')

    def plates_list(self, container):
        return [{"name": plate.name, "uuid": plate.uuid} for plate in container.plate_set.all()]

    def get_label(self, container):
        return container.get_label()
 
    class Meta:
        model = Container
        fields = ('uuid', 'time_created', 'time_updated', 'name', 'container_type', 'description',
                  'estimated_temperature', 'x', 'y', 'z', 'parent', 'plates', 'label')

class ContainerViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Container.objects.all()

    serializer_class = ContainerSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Collections

class CollectionSerializer(serializers.ModelSerializer):
    '''provide all fields, including notes
    '''
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), required=False, many=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all(), required=False)
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()
 
    class Meta:
        model = Collection
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'parent', 'tags', 'label')


class CollectionViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Collection.objects.all()

    serializer_class = CollectionSerializer
    permission_classes = (IsStaffOrSuperUser,)



# Composite Part

class CompositePartSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')
    parts = serializers.PrimaryKeyRelatedField(many=True, queryset=Part.objects.all())

    def get_label(self, instance):
        return "compositepart"

    class Meta:
        model = CompositePart

        # Extra keyword arguments for create
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'composite_id', 'composite_type',
                  'direction_string', 'sequence', 'parts', 'label')


class CompositePartViewSet(viewsets.ModelViewSet):
    permission_classes = (IsStaffOrSuperUser,)

    def get_queryset(self):
        return CompositePart.objects.all()

    def create(self, request, *args, **kwargs):
        '''create a new composite part! We require existing part ids, along
           with a name and direction string. The client should already have
           handled doing the processing to derive the direction string
           and part ids, we just validate that the parts are in the sequence.
        '''
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # We need at least one part
        parts = serializer.validated_data.get('parts')

        if len(parts) < 2:
            raise serializers.ValidationError('You must provide more than one part for a composite part') 

        # If no direction string provided, create default
        direction_string = serializer.validated_data.get('direction_string')
        sequence = serializer.validated_data.get('sequence')

        # Validate that length of part ids == length of direction string
        if len(parts) != len(direction_string):
            raise serializers.ValidationError('Direction string must be equal length to number of parts provided.') 

        # Ensure that each part is at least included in the sequence
        for i, part in enumerate(parts):
            direction = direction_string[i]

            # Check if forward and reverse isn't there.
            if part.optimized_sequence not in sequence and part.optimized_sequence[::-1] not in sequence:
                raise serializers.ValidationError('%s with direction %s not in sequence' %(part.uuid, direction)) 

        # Then perform create
        self.perform_create(serializer, sequence)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, sequence):
        serializer.save(sequence=sequence)

    serializer_class = CompositePartSerializer


# Distributions

class DistributionSerializer(serializers.ModelSerializer):

    platesets = serializers.PrimaryKeyRelatedField(many=True, queryset=PlateSet.objects.all())
    label = serializers.SerializerMethodField('get_label')
 
    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Distribution
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'platesets', 'label')


class DistributionViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Distribution.objects.all()

    serializer_class = DistributionSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Modules

class ModuleSerializer(serializers.ModelSerializer):
    '''a Module serializer provides all fields except for data and notes. The
       user is required to use the SingleModuleSerializer to get the extra data
    '''
    container = serializers.PrimaryKeyRelatedField(queryset=Container.objects.all())
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()
 
    class Meta:
        model = Module
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'container', 'notes', 'model_id',
                  'module_type', 'data', 'label')


class ModuleViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Module.objects.all()

    serializer_class = ModuleSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Institutions

class InstitutionSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Institution
        fields = ('uuid', 'name', 'signed_master', 'label')


class InstitutionViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Institution.objects.all()

    serializer_class = InstitutionSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Operations

class OperationSerializer(serializers.ModelSerializer):

    plans = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), required=False, many=True)
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


class OperationViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Operation.objects.all()

    serializer_class = OperationSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Orders


class OrderSerializer(serializers.ModelSerializer):

    distributions = serializers.PrimaryKeyRelatedField(queryset=Distribution.objects.all(), required=False, many=True)
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Order
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'notes', 'distributions', 'label')


class OrderViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Order.objects.all()

    serializer_class = OrderSerializer
    permission_classes = (IsStaffOrSuperUser,)



# Organisms

class OrganismSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Organism
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'genotype', 'label')


class OrganismViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Organism.objects.all()

    serializer_class = OrganismSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Part

class PartSerializer(serializers.ModelSerializer):
    '''a part serializer exposes all fields, meaning the user has
       looked up a part based on a uuid.
    '''
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), required=False, many=True)
    collections = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all(), required=False, many=True)
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())
    label = serializers.SerializerMethodField('get_label')

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


class PartViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Part.objects.all()

    serializer_class = PartSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Plans


class PlanSerializer(serializers.ModelSerializer):

    parent = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), required=False)
    operation = serializers.PrimaryKeyRelatedField(queryset=Operation.objects.all())
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Plan
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'parent', 'operation', 'status', 'label')


class PlanViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Plan.objects.all()

    serializer_class = PlanSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Plates

class PlateSerializer(serializers.ModelSerializer):

    container = serializers.PrimaryKeyRelatedField(queryset=Container.objects.all())
    protocol = serializers.PrimaryKeyRelatedField(queryset=Protocol.objects.all(), required=False)
    wells = serializers.PrimaryKeyRelatedField(queryset=Well.objects.all(), many=True, required=False)
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Plate
        fields = ('uuid', 'time_created', 'time_updated', 'plate_type', 
                  'plate_form', 'status', 'name', 'thaw_count',
                  'notes', 'height', 'length', 'container', 'protocol', 
                  'wells', 'label', 'plate_vendor_id')


class PlateViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Plate.objects.all()

    serializer_class = PlateSerializer
    permission_classes = (IsStaffOrSuperUser,)



# PlateSet

class PlateSetSerializer(serializers.ModelSerializer):
    '''platesets serializers
    '''

    plates = serializers.PrimaryKeyRelatedField(queryset=Plate.objects.all(), many=True)
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = PlateSet
        fields = ('uuid', 'description', 'name', 'time_created', 
                  'time_updated', 'plates', 'label')


class PlateSetViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return PlateSet.objects.all()

    serializer_class = PlateSetSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Protocol

class ProtocolSerializer(serializers.ModelSerializer):

    schema = serializers.PrimaryKeyRelatedField(queryset=Schema.objects.all(), required=False)
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()
 
    class Meta:
        model = Protocol
        fields = ('uuid', 'time_created', 'time_updated', 'data', 
                  'description', 'label', 'schema')


class ProtocolViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Protocol.objects.all()

    serializer_class = ProtocolSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Robot

class RobotSerializer(serializers.ModelSerializer):

    left_mount = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all())
    right_mount = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all())
    container = serializers.PrimaryKeyRelatedField(queryset=Container.objects.all())
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Robot
        fields = ('uuid', 'time_created', 'time_updated', 'container', 
                  'name', 'robot_id', 'robot_type', 'notes', 'server_version',
                  'right_mount', 'left_mount', 'label')


class RobotViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Robot.objects.all()

    serializer_class = RobotSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Sample


class SampleSerializer(serializers.ModelSerializer):

    part = serializers.PrimaryKeyRelatedField(queryset=Part.objects.all())
    derived_from = serializers.PrimaryKeyRelatedField(queryset=Sample.objects.all(), required=False)
    wells = serializers.PrimaryKeyRelatedField(queryset=Well.objects.all(), many=True)
    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Sample
        fields = ('uuid', 'outside_collaborator', 'sample_type', 'status',
                  'evidence', 'vendor', 'time_created', 'time_updated',
                  'derived_from', 'part', 'index_forward', 'index_reverse',
                  'label', 'wells')

class SampleViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Sample.objects.all()

    serializer_class = SampleSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Schema

class SchemaSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Schema
        fields = ('uuid', 'time_created', 'time_updated', 'name',
                  'description', 'schema', 'schema_version', 'label')

class SchemaViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Schema.objects.all()

    serializer_class = SchemaSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Tags

class TagSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Tag
        fields = ('uuid', 'tag', 'label')

class TagViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Tag.objects.all()

    serializer_class = TagSerializer
    permission_classes = (IsStaffOrSuperUser,)


# Wells

class WellSerializer(serializers.ModelSerializer):

    label = serializers.SerializerMethodField('get_label')
    organism = serializers.SerializerMethodField('get_organism')

    def get_organism(self, instance):
        return OrganismSerializer(instance.organism).data

    def get_label(self, instance):
        return instance.get_label()

    class Meta:
        model = Well
        fields = ('uuid', 'address', 'volume', 'quantity', 'media', 
                  'time_created', 'time_updated', 'organism', 'label')
