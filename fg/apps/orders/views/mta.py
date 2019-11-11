'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from fg.apps.orders.forms import MTAForm
from fg.apps.orders.models import Order
from fg.apps.orders.email import send_email
from ratelimit.decorators import ratelimit
from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block,
    SENDGRID_API_KEY,
    NODE_NAME,
    HELP_CONTACT_EMAIL
)

def _upload_mta(request, uuid, 
                template="orders/sign-mta.html",
                redirect_checkout=True,
                updated_status=None,
                email_to=None):

    '''a general view to handle uploading the MTA form, is used for both the
       admin and user upload forms, but each return different templates.

       Parameters
       ==========
       uuid: the unique id of the order associated with the MTA
       template: the template to return
       redirect_checkout: redirect to checkout, otherwise to order details
       updated_status: when the lab re-uploads the countersigned MTA,
                       we change the status to "Generating Label"
       email_to: if defined, and SENDGRID_API_KEY too, send PDF attached 
                 to email to this contact.
    '''
    # The order must exist, we look up based on uuid
    try:
        order = Order.objects.get(uuid=uuid)
    except Order.DoesNotExist:
        messages.info(request, "We can't find an order with that identifier.")
        return redirect('orders')        

    if request.method == 'POST':
        form = MTAForm(request.POST, request.FILES)

        # If the form is valid, save to the order and continue checkout
        if form.is_valid():
            mta = form.save()
            order.material_transfer_agreement = mta

            # If a new status is requested, countersigned MTA letter has been uploaded
            if updated_status is not None:
                order.status = "Generating Label"
            order.save()

            # If a to email is provided, and the sendgrid api key present
            if email_to and SENDGRID_API_KEY:
                subject = "Material Transfer Agreement (test)"
                message = '''<strong>Attached, please find the signed MTA. 
                            This will (eventually) be emailed to an institution contact
                            when protocol is established.</strong>'''
                filename = ("signed-mta-%s.pdf" % NODE_NAME).lower()
                send_email(email_to=email_to,
                           subject=subject,
                           message=message,
                           attachment=mta.agreement_file.path,
                           filename=filename)

            if redirect_checkout:
                return redirect('checkout')
            return redirect('order_details', uuid=order.uuid)
    else:
        form = MTAForm()
    context = {'form': form, 'order': order}
    return render(request, template, context)


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def upload_mta(request, uuid):
    '''a specific view to handle uploading the MTA form, redirected from the
       view to checkout in the case that an order is missing an MTA. The
       uuid corresponds to the UUID for the order
    '''
    # In this case, if a user re-uploads an MTA (and it needs to again be
    # countersigned) we revert the status back to Awaiting Countersign
    return _upload_mta(request, uuid, updated_status="Awaiting Countersign")


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def admin_upload_mta(request, uuid):
    '''the admin view to upload the MTA - the same variables and functionality,
       but a different template. For this view, if a SendGrid key is defined,
       we also send the MTA to the Bionet Server admin (and in the future, 
       when a user email is available, to them).
    '''
    if request.user.is_staff or request.user.is_superuser:

        # Upload, and send email attachment (testing) back to lab
        # This is when a countersigned MTA letter has been uploaded
        # and we update the order status to reflect that
        return _upload_mta(request, uuid, 
                           template='orders/upload-mta.html',
                           redirect_checkout=False,
                           updated_status="Generating label",
                           email_to=HELP_CONTACT_EMAIL)

    messages.warning(request, 'You are not allowed to perform this action.')
    redirect('orders')
