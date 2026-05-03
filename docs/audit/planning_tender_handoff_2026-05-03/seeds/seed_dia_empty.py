# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""G1 — seed_dia_empty: remove reserved DIA-MOH-2026-0001…0009 demands (no inserts).

bench --site <site> execute kentender_procurement.demand_intake.seeds.seed_dia_empty.run
"""

from __future__ import annotations

import frappe

from kentender_procurement.demand_intake.seeds.dia_seed_common import clear_dia_seed_demands


def run():
	frappe.only_for(("System Manager", "Administrator"))
	removed = clear_dia_seed_demands()
	frappe.db.commit()
	return {"cleared_demand_ids": removed}
