'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from rest_framework.permissions import BasePermission

class IsStaffOrSuperUser(BasePermission):
    '''Allows access to staff (admin) or superuser.
    '''
    def has_permission(self, request, view):

        # List and read are always allowed for non staff / superuser
        if view.action in ['list', 'read']:
            return True

        is_staff = request.user.is_staff or request.user.is_superuser
        return bool(request.user and is_staff)

