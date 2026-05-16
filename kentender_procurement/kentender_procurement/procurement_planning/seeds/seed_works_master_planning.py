# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-007 bench execute entry point.

Run::

    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_planning.seeds.seed_works_master_planning.run
"""

import frappe

from kentender_procurement.procurement_planning.seeds.works_master_planning_seed import (
    upsert_works_master_planning,
)


def run(**kwargs):
    result = upsert_works_master_planning()
    frappe.db.commit()
    return result
