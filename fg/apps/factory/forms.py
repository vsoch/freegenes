'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django import forms
from fg.apps.factory.models import FactoryOrder

class UploadTwistPlatesForm(forms.Form):
    '''a form to upload a plate csv for twist
    '''
    csv_file = forms.FileField(required=True, label="plate map (csv) file")
    factory_order = forms.ModelChoiceField(queryset=FactoryOrder.objects.all())
    generate_samples = forms.BooleanField(required=False)
    delimiter = forms.CharField(max_length=1,
                                initial=",",
                                label="Delimiter of file, defaults to ,")

