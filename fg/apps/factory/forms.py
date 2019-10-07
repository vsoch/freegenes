'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django import forms

class UploadTwistPlatesForm(forms.Form):
    '''a form to upload a plate csv for twist
    '''
    csv_file = forms.FileField(required=True, label="plate map (csv) file")
    delimiter = forms.CharField(max_length=1,
                                initial=",",
                                label="Delimiter of file, defaults to ,")
