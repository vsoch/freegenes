'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django import forms
from fg.apps.main.models import MaterialTransferAgreement


class MTAForm(forms.ModelForm):
    '''Material Transfer Agreement Form - can be used by the user (in future)
       to upload their own MTA (orders/sign-mta.html) and currently used by
       staff to upload it after email from the user.
    '''
    class Meta:
        model = MaterialTransferAgreement
        fields = ['mta_type', 'agreement_file', 'institution']

#PAYMENT_CHOICES = (
#    ('S', 'Stripe'),
#    ('P', 'PayPal')
#)

class CheckoutForm(forms.Form):

    # Lab Name and Address
    lab_name = forms.CharField(required=True)
    lab_address = forms.CharField(required=True)
    lab_address2 = forms.CharField(required=False)
    lab_zip = forms.CharField(required=True)

    # PI Name and title (signing the MTA)
    recipient_name = forms.CharField(required=True)
    recipient_title = forms.CharField(required=True)

    # Are shipping address and lab address the same?
    same_shipping_address = forms.BooleanField(required=False)

    # If shipping address is different
    shipping_to = forms.CharField(required=False)
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_zip = forms.CharField(required=False)

    #payment_option = forms.ChoiceField(
    #    widget=forms.RadioSelect, choices=PAYMENT_CHOICES)
