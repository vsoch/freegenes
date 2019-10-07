'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from io import StringIO
import csv


def read_csv(fileobj, delim):
    '''read the file object (a csv) into the file.
    '''
    csv_file = StringIO(fileobj.read().decode())
    reader = csv.reader(csv_file, delimiter=delim)
    rows = []
    for row in reader:
        rows.append(row)
    fileobj.close()
    return rows
