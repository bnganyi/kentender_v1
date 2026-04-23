# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""G1 — seed_dia_extended: full DIA-MOH-2026-0001…0009 state coverage.

bench --site <site> execute kentender_procurement.demand_intake.seeds.seed_dia_extended.run
"""

from __future__ import annotations

import frappe

from kentender_procurement.demand_intake.seeds.dia_seed_common import (
	clear_dia_seed_demands,
	ensure_budget_line_prerequisites,
	ensure_core_prerequisites,
	seed_extended_demands,
)


def run():
	frappe.only_for(("System Manager", "Administrator"))
	ensure_core_prerequisites()
	ensure_budget_line_prerequisites()
	clear_dia_seed_demands()
	mapping = seed_extended_demands(exceptions_variant=False)
	frappe.db.commit()
	return {"demands": mapping, "pack": "seed_dia_extended"}
