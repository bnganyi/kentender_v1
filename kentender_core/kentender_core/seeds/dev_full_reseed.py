# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Dev-only: wipe legacy Planning rows + budgets + strategy seed, then re-run core stack.

PP2 Planning F1 seed retired (Planning MVP-1 pending).

bench --site kentender.midas.com execute kentender_core.seeds.dev_full_reseed.run
"""

from __future__ import annotations

import frappe

from kentender_core.seeds.reset_core_seed import run as reset_core_seed
from kentender_core.seeds.seed_budget_empty import run as run_budget_empty
from kentender_core.seeds.seed_budget_extended import run as run_budget_extended
from kentender_core.seeds.seed_core_minimal import run as run_core_minimal
from kentender_core.seeds.seed_strategy_basic import run as run_strategy_basic


def _wipe_procurement_planning() -> dict[str, int]:
	frappe.only_for(("System Manager", "Administrator"))
	out: dict[str, int] = {}
	for doctype in (
		"Procurement Package Line",
		"Procurement Package",
		"Procurement Plan",
	):
		if not frappe.db.exists("DocType", doctype):
			out[doctype] = 0
			continue
		out[doctype] = frappe.db.count(doctype) or 0
		frappe.db.delete(doctype)
	return out


def run() -> dict:
	frappe.only_for(("System Manager", "Administrator"))
	out: dict = {}
	out["wiped_pp"] = _wipe_procurement_planning()
	out["cleared_dia"] = {"skipped": True, "reason": "DEMAND_MODULE_RETIRED"}
	out["budget_empty"] = run_budget_empty()
	out["reset_core"] = reset_core_seed(dry_run=False)
	run_core_minimal()
	out["strategy_basic"] = run_strategy_basic()
	out["budget_extended"] = run_budget_extended()
	out["dia_basic"] = {"skipped": True, "reason": "DEMAND_MODULE_RETIRED"}
	out["dia_f1_prereq"] = {"skipped": True, "reason": "DEMAND_MODULE_RETIRED"}
	out["pp_f1"] = {"ok": True, "skipped": True, "reason": "PP2_PLANNING_RETIRED"}
	frappe.db.commit()
	out["ok"] = True
	out["notes"] = [
		"Demand Intake seed stages skipped — Demands MVP-1 rebuild pending.",
		"PP2 Planning F1 seed skipped — Planning MVP-1 pending.",
	]
	return out
