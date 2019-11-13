'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

def get_part_available_query(gene_ids):
    '''a custom query to return if a part is available based on being associated
       with a distribution. You can provide a single gene_id to look for,
       or a list of more then one (which will run a query to return more
       than one result for those available.
    '''
    query = """SELECT DISTINCT p.uuid AS uuid, p.name AS part_name, p.description AS part_description, p.gene_id AS part_gene_id
FROM main_part AS p
JOIN main_sample as s on s.part_id=p.uuid
JOIN main_sample_wells AS sw on sw.sample_id=s.uuid
JOIN main_well AS w on w.uuid=sw.well_id
JOIN main_plate_wells AS pw on pw.well_id=w.uuid
JOIN main_plate AS pl on pl.uuid=pw.plate_id
JOIN main_plateset_plates AS pp on pp.plate_id=pl.uuid
JOIN main_plateset AS ps on ps.uuid=pp.plateset_id
JOIN main_distribution_platesets AS dp on dp.plateset_id=ps.uuid
JOIN main_distribution AS d on d.uuid=dp.distribution_id
WHERE '' LIKE p.name OR '' LIKE p.description OR '' LIKE p.part_type"""

    # If we're given one string, just for one part
    if isinstance(gene_ids, str):
        return query + " OR '%s' LIKE p.gene_id" % gene_ids

    # If we're given a list, assemble a LIKE for each one
    for gene_id in gene_ids:
        query += " OR '%s' LIKE p.gene_id" % gene_id

    return query
