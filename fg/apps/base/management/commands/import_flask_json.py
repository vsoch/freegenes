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
from fg.apps.main.utils import load_json
from dateutil.parser import parse
import logging
import os
import shutil
import sys

def update_dates(instance, entry, create_field='time_created', update_field='time_updated'):
    '''a helper function to update an objects dates (to match what is in the
       import. For all models, the fields are consistently "time_created" and
       "time_updated" and the instance object is returned.
 
       Parameters
       ==========
       instance: the model to update
       create_field: the create field for entry
       update_field: the update field for entry
    '''
    for field in [create_field, update_field]:
        if entry.get(field):
            setattr(instance, field, parse(entry[field]))
    instance.save()
    return instance


def add_tags(instance, entry, tags_field="tags"):
    '''a helper function to generate Tag objects from a list of strings,
       and add to an instance.
    '''
    for name in entry['tags']:
        tag, created = Tag.objects.get_or_create(tag=name.lower())
        instance.tags.add(tag)
    instance.save()
    return instance


class Command(BaseCommand):
    '''import json that was exported from Flask into the database. It's a fairly
       concrete set of models, so we match models 1:1 with files.
    '''
    def add_arguments(self, parser):
        parser.add_argument(dest='input_folder', nargs=1, type=str)
    help = "Import data from an input folder with exported json"

    def handle(self, *args, **options):
        if options['input_folder'] is None:
            raise CommandError("Please provide an input folder to parse.")

        # The input folder must exist!
        folder = options['input_folder'][0]
        if not os.path.exists(folder):
            logging.error("Input folder %s does not exist." % folder)
            sys.exit(1)

        # TAGS are not exported as models, but defined with models (added as we go)

        # Institution ##########################################################
        institution_file = os.path.join(folder, 'institution-full.json')
        if os.path.exists(institution_file):
            institutions = load_json(institution_file)
            for entry in institutions:
                institution, created = Institution.objects.get_or_create(name=entry['name'],
                                                                         uuid=entry['uuid'],
                                                                         signed_master=entry['signed_master'])


        # Protocol #############################################################
        # need to get plates uuid from containers (add plates)

        protocols_file = os.path.join(folder, 'protocols-full.json')
        if os.path.exists(protocols_file):
            protocols = load_json(protocols_file)
            for entry in protocols:

                protocol, created = Protocol.objects.get_or_create(uuid=entry['uuid'],
                                                                   description=entry['description'],
                                                                   data=entry['data'])

                protocol = update_dates(protocol, entry)

        # Containers ###########################################################

        containers_file = os.path.join(folder, 'containers-full.json')
        if os.path.exists(containers_file):
            containers = load_json(containers_file)

            # First pass, create containers without parents
            for entry in containers:
                container, created = Container.objects.get_or_create(container_type=entry['container_type'].lower(),
                                                                     uuid=entry['uuid'],
                                                                     name=entry['name'],
                                                                     x=entry['x'],
                                                                     y=entry['y'],
                                                                     z=entry['z'],
                                                                     description=entry['description'],
                                                                     estimated_temperature=entry['estimated_temperature'])
                

                # Add plates
                for plate in entry['plates']:

                    # There are plates with protocol uuid that don't exist
                    try:
                        protocol = Protocol.objects.get(uuid=plate['protocol_uuid'])
                    except Protocol.DoesNotExist:
                        protocol = None

                    newplate, created = Plate.objects.get_or_create(plate_form=plate['plate_form'],
                                                                    name=plate['plate_name'],
                                                                    container=container,
                                                                    protocol=protocol,
                                                                    plate_type=plate['plate_type'],
                                                                    status=plate['status'],
                                                                    thaw_count=plate['thaw_count'],
                                                                    plate_vendor_id=plate['plate_vendor_id'],
                                                                    uuid=plate['uuid'])
                container.save()

            # Second pass, add parents
            for entry in containers:
                container = Container.objects.get(uuid=entry['uuid'])
                if entry['parent_uuid']:
                    parent = Container.objects.get(uuid=entry['parent_uuid'])
                    container.parent = Container.objects.get(uuid=entry['parent_uuid'])
                    container.save()


        # Organism #############################################################

        organism_file = os.path.join(folder, 'organisms-full.json')
        if os.path.exists(organism_file):
            organisms = load_json(organism_file)

            # There is only one organism!
            for entry in organisms:
                organism, created = Organism.objects.get_or_create(uuid=entry['uuid'],
                                                                   description=entry['description'],
                                                                   genotype=entry['genotype'],
                                                                   name=entry['name'])

                organism = update_dates(organism, entry)
                organism = add_tags(organism, entry)


        # Collections ##########################################################

        collections_file = os.path.join(folder, 'collections-full.json')
        if os.path.exists(collections_file):
            collections = load_json(collections_file)

            # First pass, create without parents
            for entry in collections:
                collection, created = Collection.objects.get_or_create(name=entry['name'],
                                                                       uuid=entry['uuid'],
                                                                       description=entry['readme'])
                collection = update_dates(collection, entry)
                collection = add_tags(collection, entry)


            # Second pass, add parent
            for entry in collections:
                if entry['parent_uuid']:
                    collection = Collection.objects.get(uuid=entry['uuid'])
                    print('Adding parent to %s' % collection)
                    collection.parent = Collection.objects.get(uuid=entry['parent_uuid'])
                    collection.save()


        # Modules ##############################################################

        modules_file = os.path.join(folder, 'modules-full.json')
        if os.path.exists(modules_file):
            modules = load_json(modules_file)

            for entry in modules:
                container = Container.objects.get(uuid=entry['container_uuid'])
                module, created = Module.objects.get_or_create(uuid=entry['uuid'],
                                                               data=entry['data'],
                                                               model_id=entry['model_id'],
                                                               name=entry['name'],
                                                               notes=entry['notes'],
                                                               module_type=entry['module_type'],
                                                               container=container)


        # Robots ###############################################################

        robots_file = os.path.join(folder, 'robots-full.json')
        if os.path.exists(robots_file):
            robots = load_json(robots_file)

            # There is only one robot!
            for entry in robots:
                container = container = Container.objects.get(uuid=entry['container_uuid'])
                left_mount = Module.objects.get(uuid=entry['left_mount'])
                right_mount = Module.objects.get(uuid=entry['right_mount'])
                robot, created = Robot.objects.get_or_create(uuid=entry['uuid'],
                                                             left_mount=left_mount,
                                                             right_mount=right_mount,
                                                             container=container,
                                                             notes=entry['notes'],
                                                             name=entry['name'],
                                                             robot_id=entry['robot_id'],
                                                             server_version=entry['server_version'],
                                                             robot_type=entry['robot_type'])

                robot = update_dates(robot, entry)
                robot.save()

        
        # Files ################################################################
        # Added to upload folder, and we will add logic to use storage when ready
 
        files_file = os.path.join(folder, 'files.json')

        # Keep a lookup of filenames for the MTAs
        files_lookup = {}

        if os.path.exists(files_file):
            files = load_json(files_file)
            for entry in files:
                files_lookup[entry['uuid']] = entry
                file_path = os.path.join(folder, 'files', entry['name'])
                if os.path.exists(file_path):
                    newfile, created = Files.objects.get_or_create(file_name=file_path)
                    original_path = newfile.file_name.name
                    upload_path = get_upload_to(newfile, newfile.file_name.name)
                    shutil.copyfile(original_path, upload_path)
                    newfile.file_name.name = upload_path
                    newfile.save()


        # Material Transfer Agreement ##########################################

        mta_file = os.path.join(folder, 'materialtransferagreement-full.json')
        if os.path.exists(mta_file):
            mtas = load_json(mta_file)
            for mta in mtas:
                if mta['file'] in files_lookup:
                    file_path = os.path.join(folder, 'files', files_lookup[mta['file']]['name'])
                    if os.path.exists(file_path):
                        institution = Institution.objects.get(uuid=mta['institution'])
                        newmta, created = MaterialTransferAgreement.objects.get_or_create(
                                               uuid=mta['uuid'],
                                               institution=institution,
                                               mta_type=mta['mta_type'])
                        if created:
                            newmta.agreement_file=file_path
                            original_path = newmta.agreement_file.name
                            upload_path = get_mta_upload_to(newmta, newmta.agreement_file.name)
                            shutil.copyfile(original_path, upload_path)
                            newmta.agreement_file.name = upload_path
                            newmta.save()
                        
        # Authors ##############################################################
        # data exported contains uuid for parts, but we will add authors to the parts
        # after they are created

        author_file = os.path.join(folder, 'authors-full.json')
        if os.path.exists(author_file):
            authors = load_json(author_file)

            # name and email are the only required
            for entry in authors:

                # Remove https://orcid
                orcid = None
                if entry['orcid']:
                    orcid = os.path.basename(entry['orcid'])
                author, created = Author.objects.get_or_create(uuid=entry['uuid'],
                                                               affiliation=entry['affiliation'],
                                                               name=entry['name'],
                                                               email=entry['email'],
                                                               orcid=orcid)
                author = add_tags(author, entry)                


        # Wells ################################################################

        wells_file = os.path.join(folder, 'wells-full.json')
        if os.path.exists(wells_file):
            wells = load_json(wells_file)

            for entry in wells:
                organism = Organism.objects.get(uuid=entry['organism_uuid'])
                well, created = Well.objects.get_or_create(uuid=entry['uuid'],
                                                           media=entry['media'],
                                                           organism=organism,
                                                           address=entry['address'],
                                                           volume=entry['volume'])
                if entry['quantity']:
                    well.quantity = entry['quantity']
                    well.save()                                                            

        # Plates ###############################################################
        # wells are added before initial save so they aren't generated automatically

        plates_file = os.path.join(folder, 'plates-full.json')
        if os.path.exists(plates_file):
            plates = load_json(plates_file)

            for entry in plates:

                # Get the wells we just generated
                container = Container.objects.get(uuid=entry['container_uuid'])
                plate, created = Plate.objects.get_or_create(uuid=entry['uuid'],
                                                             container=container,
                                                             plate_type=entry['plate_type'],
                                                             plate_vendor_id=entry['plate_vendor_id'],
                                                             plate_form=entry['plate_form'],
                                                             status=entry['status'],
                                                             name=entry['plate_name'],
                                                             thaw_count=entry['thaw_count'])

                for w in entry['wells']:
                    plate.wells.add(Well.objects.get(uuid=w))

                plate = update_dates(plate, entry)


        # PlateSet #############################################################

        plateset_file = os.path.join(folder, 'plateset-full.json')
        if os.path.exists(plateset_file):
            platesets = load_json(plateset_file)

            for entry in platesets:

                plateset, created = PlateSet.objects.get_or_create(uuid=entry['uuid'],
                                                                   description=entry['description'],
                                                                   name=entry['name'])

                for plate in entry['plates']:
                    plateset.plates.add(Plate.objects.get(uuid=plate))
                plateset = update_dates(plateset, entry)


        # Distribution #########################################################

        distribution_file = os.path.join(folder, 'distribution-full.json')
        if os.path.exists(distribution_file):
            distributions = load_json(distribution_file)

            for entry in distributions:
                distribution, created = Distribution.objects.get_or_create(uuid=entry['uuid'],
                                                                           name=entry['name'],
                                                                           description=entry['description'])
                for s in entry['platesets']:
                    distribution.platesets.add(PlateSet.objects.get(uuid=s))

                distribution = update_dates(distribution, entry)
                                                                             

        # Parts ################################################################

        parts_file = os.path.join(folder, 'parts-full.json')
        if os.path.exists(parts_file):
            parts = load_json(parts_file)

            for entry in parts:
                genbank = entry['genbank'] or {}
                author = Author.objects.get(uuid=entry['author_uuid'])
                collection = Collection.objects.get(uuid=entry['collection_id'])
                part, created = Part.objects.get_or_create(uuid=entry['uuid'],
                                                           author=author,
                                                           full_sequence=entry['full_sequence'],
                                                           optimized_sequence=entry['optimized_sequence'],
                                                           original_sequence=entry['original_sequence'],
                                                           synthesized_sequence=entry['synthesized_sequence'],
                                                           gene_id=entry['gene_id'],
                                                           vector=entry['vector'],
                                                           genbank=genbank,
                                                           description=entry['description'],
                                                           barcode=entry['barcode'],
                                                           part_type=entry['part_type'],
                                                           name=entry['name'],
                                                           translation=entry['translation'],
                                                           status=entry['status'])
                if entry['primer_for']:
                    part.primer_forward = entry['primer_for']
                if entry['primer_rev']:
                    part.primer_reverse = entry['primer_rev']
                if entry['ip_check_date']:
                    part.ip_check_date = parse(entry['ip_check_date'])
                if entry['ip_check']:
                    part.ip_check = True
                if entry['ip_check_ref']:
                    part.ip_check_ref = entry['ip_check_ref']

                part = update_dates(part, entry)
                part = add_tags(part, entry)                


        # Samples ##############################################################

        # Need to find associated wells from wells just created
        samples_file = os.path.join(folder, 'samples-full.json')
        if os.path.exists(samples_file):
            samples = load_json(samples_file)

            # First round, ignore derived from
            for entry in samples:
                part = Part.objects.get(uuid=entry['part_uuid'])
                sample, created = Sample.objects.get_or_create(uuid=entry['uuid'],
                                                               evidence=entry['evidence'],
                                                               sample_type=entry['sample_type'],
                                                               status=entry['status'],
                                                               vendor=entry['vendor'],
                                                               part=part)
 
                if entry['index_for']:
                    sample.index_forward = entry['index_for']
                if entry['index_rev']:
                    sample.index_reverse = entry['index_rev']

                for w in entry['wells']:
                    well = Well.objects.get(uuid=w)
                    sample.wells.add(well)
                
                sample = update_dates(sample, entry)


            # Secound round, add derived from
            for entry in samples:
                sample = Sample.objects.get(uuid=entry['uuid'])
                if entry['derived_from']:
                    sample.derived_from = Sample.objects.get(uuid=entry['derived_from'])
                    sample.save()


        # Schema ###############################################################
        # There aren't any schemas export from the API

        schemas_file = os.path.join(folder, 'schemas-full.json')
        if os.path.exists(schemas_file):
            schemas = load_json(schemas_file)


        # Operation ############################################################
        # no operations are exported from API

        operations_file = os.path.join(folder, 'operations-full.json')
        if os.path.exists(operations_file):
            operations = load_json(operations_file)
 
         
        # Plans ################################################################
        # no plans are exported from the API

        plans_file = os.path.join(folder, 'plans-full.json')
        if os.path.exists(plans_file):
            plans = load_json(plans_file)

        # Order ################################################################
        # no plans are exported from the API

        orders_file = os.path.join(folder, 'order-full.json')
        if os.path.exists(orders_file):
            orders = load_json(orders_file)

            for entry in orders:
                mta = MaterialTransferAgreement.objects.get(uuid=entry['materialtransferagreement'])
                order, created = Order.objects.get_or_create(uuid=entry['uuid'],
                                                             name=entry['name'],
                                                             material_transfer_agreement=mta,
                                                             notes=entry['notes'])

                for d in entry['distributions']:
                    order.distributions.add(Distribution.objects.get(uuid=d))
                order = update_dates(order, entry)
                                                             

    # We aren't representing address, shipment, parcel, need to have this linked
