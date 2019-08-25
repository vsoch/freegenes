'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import admin
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

class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'affiliation', 'orcid')
    
class ContainerAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'container_type', 'description', 
                    'estimated_temperature',)

class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'time_updated', 'time_created',)

class DistributionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'time_updated', 'time_created', )

class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'signed_master', )

class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'container', 'model_id', 'module_type', 'time_updated', 'time_created', )

class OperationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'time_updated', 'time_created', )

class OrganismAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'time_updated', 'time_created')

class PartAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'gene_id', 'part_type', 'description', 'time_updated', 'time_created')

class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'description', 'parent', 'time_updated', 'time_created', )

class PlateAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'breadcrumb', 'plate_type', 'plate_form', 'thaw_count', 'height', 'length')

class PlateSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'time_updated', 'time_created', )

class ProtocolAdmin(admin.ModelAdmin):
    list_display = ('description', 'time_updated', 'time_created')

class RobotAdmin(admin.ModelAdmin):
    list_display = ('name', 'container', 'robot_id', 'robot_type', 'server_version',
                    'notes', 'right_mount', 'left_mount')

class SampleAdmin(admin.ModelAdmin):
    list_display = ('sample_type', 'status', 'vendor', 'evidence', 'part', 'derived_from', 'outside_collaborator' )

class SchemaAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'schema_version', 'time_updated', 'time_created')

class TagAdmin(admin.ModelAdmin):
    list_display = ('tag', )

admin.site.register(Author, AuthorAdmin)
admin.site.register(Container, ContainerAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Distribution, DistributionAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(Operation, OperationAdmin)
admin.site.register(Organism, OrganismAdmin)
admin.site.register(Part, PartAdmin)
admin.site.register(Plan, PlanAdmin)
admin.site.register(Plate, PlateAdmin)
admin.site.register(PlateSet, PlateSetAdmin)
admin.site.register(Protocol, ProtocolAdmin)
admin.site.register(Robot, RobotAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(Schema, SchemaAdmin)
admin.site.register(Tag, TagAdmin)
