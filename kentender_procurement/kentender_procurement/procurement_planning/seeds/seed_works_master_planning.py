# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS master planning seed — bench execute entry (PP2 canonical).

Run::

    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_planning.seeds.seed_works_master_planning.run
"""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)


def run(**kwargs):
	checkpoint = kwargs.get("checkpoint") or "RELEASED_TO_TENDER"
	force_reset = bool(kwargs.get("force_reset"))
	result = seed_procurement_planning_works_master(
		checkpoint=checkpoint,
		force_reset=force_reset,
	)
	frappe.db.commit()
	return result
