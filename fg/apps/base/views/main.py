'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.shortcuts import render
 
from ratelimit.decorators import ratelimit

from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def index_view(request):
    return render(request, 'main/index.html')

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def about_view(request):
    return render(request, 'main/about.html')

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def dashboard_view(request):
    return render(request, 'main/dashboard.html')

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def contact_view(request):
    return render(request, 'main/contact.html')

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def tools_view(request):
    return render(request, 'main/tools.html')
