# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-008 bench execute entry point.

Run::

    bench --site kentender.midas.com execute \\
        kentender_procurement.tender_management.seeds.seed_works_master_std.run
"""

import frappe

from kentender_procurement.tender_management.seeds.works_master_std_seed import (
    upsert_works_master_std,
)


def run(**kwargs):
    result = upsert_works_master_std()
    frappe.db.commit()
    return result
