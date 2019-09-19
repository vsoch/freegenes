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


class CheckoutForm(forms.Form):
    '''the checkout form is sent to the view, but currently not used -
       the information is sent via email to the lab. If we ever post to
       the server, this form can be used to validate fields.
    '''

    # Lab Name and Address
    lab_name = forms.CharField(required=True)
    lab_address = forms.CharField(required=True)
    lab_address2 = forms.CharField(required=False)
    lab_zip = forms.CharField(required=True)
    lab_phone = forms.CharField(required=True)

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
    shipping_phone = forms.CharField(required=False)


DRY_ICE_CHOICES = (
    ('Yes', 'Contains Dry Ice'),
    ('No', 'No Dry Ice')
)

class ShippingForm(forms.Form):
    '''the shipping form is filled out by the lab staff using the addresses
       sent via email. The institution (lab) name, and email are taken from
       settings.config (HELP_INSTITUTION_EMAIL and NODE_INSTITUTION) along
       with the phone number (HELP_INSTITUTION_PHONE)
    ''' 

    # If shipping address is different
    shipping_to = forms.CharField(required=True)
    shipping_address = forms.CharField(required=True)
    shipping_address2 = forms.CharField(required=False)
    shipping_zip = forms.CharField(required=True)
    shipping_phone = forms.CharField(required=True)

    # TO Lab Name and Address
    from_name = forms.CharField(required=True)
    from_address = forms.CharField(required=True)
    from_address2 = forms.CharField(required=False)
    from_zip = forms.CharField(required=True)

    parcel_length = forms.CharField(required=True, label="Length in inches")
    parcel_width = forms.CharField(required=True, label="Width in inches")
    parcel_height = forms.CharField(required=True, label="Height in inches")
    parcel_weight = forms.CharField(required=True, label="Weight in pounds")

    dryice_options = forms.ChoiceField(
        widget=forms.RadioSelect, choices=DRY_ICE_CHOICES)
