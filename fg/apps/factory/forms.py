'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django import forms
from fg.apps.factory.models import FactoryOrder
from fg.apps.main.models import Container

class UploadTwistPlatesForm(forms.Form):
    '''a form to upload a plate csv for twist
    '''
    csv_file = forms.FileField(required=True, label="plate map (csv) file")
    factory_order = forms.ModelChoiceField(queryset=FactoryOrder.objects.all())
    delimiter = forms.CharField(max_length=1,
                                initial=",",
                                label="Delimiter of file, defaults to ,")


class UploadFactoryPlateJsonForm(forms.Form):
    '''a form to upload a plate json export from another node. The user
       must selected a container and json file.
    '''
    container = forms.ModelChoiceField(queryset=Container.objects.all())
    json_file = forms.FileField(required=True, label="plate (json) export")


class UploadTwistPartsForm(forms.Form):
    '''a form to upload a csv of parts from twist
    '''
    csv_file = forms.FileField(required=True, label="parts (csv) file")
    factory_order = forms.ModelChoiceField(queryset=FactoryOrder.objects.all())
    delimiter = forms.CharField(max_length=1,
                                initial=",",
                                label="Delimiter of file, defaults to ,")

