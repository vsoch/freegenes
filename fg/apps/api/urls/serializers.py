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
    Order,
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
# Serializers paired with Viewsets
################################################################################

# Containers

class ContainerSerializer(serializers.ModelSerializer):

    plates = serializers.SerializerMethodField('plates_list')
    parent = serializers.SerializerMethodField('get_parent')

    def plates_list(self, container):
        return [{"name": plate.name, "uuid": plate.uuid} for plate in container.plate_set.all()]

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
                  'estimated_temperature', 'x', 'y', 'z', 'parent', 'plates')

class ContainerViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Container.objects.all()

    serializer_class = ContainerSerializer


# Collections

class CollectionSerializer(serializers.ModelSerializer):

    tags = serializers.SerializerMethodField('tags_list')
    parent = serializers.SerializerMethodField('get_parent')

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
                  'description', 'parent', 'tags')


class CollectionViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Collection.objects.all()

    serializer_class = CollectionSerializer


# Distributions

class DistributionSerializer(serializers.ModelSerializer):

    platesets = serializers.SerializerMethodField('get_platesets')

    def get_platesets(self, distribution):
        return [{"name": p.name, "uuid": p.uuid} for p in distribution.platesets.all()]
 
    class Meta:
        model = Distribution
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'description', 'platesets',)


class DistributionViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Distribution.objects.all()

    serializer_class = DistributionSerializer


# Modules

class ModuleSerializer(serializers.ModelSerializer):
    '''a Module serializer provides all fields except for data. The user
       is required to use the SingleModuleSerializer to get the extra data
    '''
    container = serializers.SerializerMethodField('get_container')

    def get_container(self, module):
        container = None
        if module.container:
            container = {'uuid': module.container.uuid,
                         'name': module.container.name}
        return container
 
    class Meta:
        model = Module
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'container', 'notes', 'model_id',
                  'module_type')


class SingleModuleSerializer(ModuleSerializer):
    '''a SingleModule serializer provides all fields
    '''
    class Meta:
        model = Module
        fields = ('uuid', 'time_created', 'time_updated', 'name', 
                  'container', 'notes', 'model_id',
                  'module_type', 'data')


class ModuleViewSet(ListModelMixin, generics.GenericAPIView):
    '''Retrieve a single module instance based on it's uuid
    '''
    remove_data = False

    def get_object(self, uuid):
        try:
            module = Module.objects.get(uuid=uuid)
        except Module.DoesNotExist:
            module = None
        return module

    def get_queryset(self):
        return Module.objects.all()

    def get_serializer_class(self):
        '''check if remove_data is True, if so, a listing is being called and
           we return the ModuleSerializer without. If remove_data is False,
           we are returning a single Module
        '''
        if self.remove_data:
            return ModuleSerializer
        return SingleModuleSerializer

    def list(self, request, *args, **kwargs):
        '''we need to override list in order to remove data
           the user must request an individual module to see the data.
        '''
        self.remove_data = True
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get(self, request, *args, **kwargs):

        # If we don't have an id, return a listing
        if "id" not in kwargs:
            return self.list(request, *args, **kwargs)

        # Otherwise return a single view
        module = self.get_object(uuid=kwargs['id'])
        if not module:
            raise NotFound(detail="Module not found")

        serializer = SingleModuleSerializer(module)
        return Response(serializer.data)


# Institutions

class InstitutionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Institution
        fields = ('uuid', 'name', 'signed_master')


class InstitutionViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Institution.objects.all()

    serializer_class = InstitutionSerializer


# Tags

class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('uuid', 'tag', )

class TagViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Tag.objects.all()

    serializer_class = TagSerializer


# Authors

class AuthorSerializer(serializers.ModelSerializer):

    tags = serializers.SerializerMethodField('tags_name')

    def tags_name(self, author):
        return [x.tag for x in author.tags.all()]

    class Meta:
        model = Author
        fields = ('uuid', 'name', 'email', 'affiliation', 'orcid', 'tags')

class AuthorViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return Author.objects.all()

    serializer_class = AuthorSerializer
