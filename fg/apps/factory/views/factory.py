'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    Http404, 
    JsonResponse
)
from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from django.shortcuts import redirect

from fg.apps.factory.twist import get_client
from ratelimit.decorators import ratelimit
from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def factory_view(request):
    '''Show different factory operations to the user, including importing
       and managing orders from twist
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    context = {"twist_client": get_client()}
    return render(request, 'factory/incoming.html', context)
