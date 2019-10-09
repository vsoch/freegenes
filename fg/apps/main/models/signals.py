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
    Container,
    Well
)
 
@receiver(pre_delete, sender=Plate, dispatch_uid='plate_pre_delete_signal')
def delete_wells(sender, instance, using, **kwargs):
    '''Delete all wells for a container that is to be deleted.
    '''
    # Move any modules belonging to the container to parent container.
    for well in instance.wells.all():
        if well.plate_wells.count() == 1:
            well.delete()


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
def protect_plan(sender, instance, using, **kwargs):
    '''Once a plan has been executed, it cannot be deleted.
    '''
    # Don't allow delete if plan is executed
    if instance.status == "Executed": 
        raise ProtectedError('An executed plan cannot be deleted.')
