'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.db.models import ProtectedError
from django.dispatch import receiver
from django.db.models.signals import (
    post_save,
    pre_delete
)
from fg.apps.main.models import (
    Plate,
    Plan,
    Container
)

@receiver(post_save, sender=Plate, dispatch_uid='plate_save_generate_wells_signal')
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
 

@receiver(pre_delete, sender=Container, dispatch_uid='container_pre_delete_signal')
def protect_containers(sender, instance, using, **kwargs):
    '''The root (container) may not be deleted. If a container is deleted, it's
       modules are moved to the parent.
    '''
    # Don't allow delete of the root container
    if not instance.parent: 
        raise ProtectedError('A root container may not be deleted')

    # Move any modules belonging to the container to parent container.
    for module in instance.module_set.all():
        module.container = instance.parent
        module.save()


@receiver(pre_delete, sender=Plan, dispatch_uid='plan_pre_delete_signal')
def protect_containers(sender, instance, using, **kwargs):
    '''Once a plan has been executed, it cannot be deleted.
    '''
    # Don't allow delete if plan is executed
    if instance.status == "Executed": 
        raise ProtectedError('An executed plan cannot be deleted.')
