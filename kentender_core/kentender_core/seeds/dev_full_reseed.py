# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Dev-only: wipe Procurement Planning rows + DIA seed demands + budgets + strategy seed,
then re-run core → strategy → budget → DIA → F1 planning stack.

bench --site kentender.midas.com execute kentender_core.seeds.dev_full_reseed.run
"""

from __future__ import annotations

import frappe

from kentender_core.seeds.reset_core_seed import run as reset_core_seed
from kentender_core.seeds.seed_budget_empty import run as run_budget_empty
from kentender_core.seeds.seed_budget_extended import run as run_budget_extended
from kentender_core.seeds.seed_core_minimal import run as run_core_minimal
from kentender_core.seeds.seed_strategy_basic import run as run_strategy_basic
from kentender_procurement.demand_intake.seeds.dia_seed_common import clear_dia_seed_demands
from kentender_procurement.demand_intake.seeds.seed_dia_basic import run as run_dia_basic
from kentender_procurement.demand_intake.seeds.seed_dia_planning_f1_prerequisites import (
	run as run_dia_f1_prereq,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_f1 import (
	run as run_pp_f1,
)


def _wipe_procurement_planning() -> dict[str, int]:
	frappe.only_for(("System Manager", "Administrator"))
	ln = frappe.db.sql("delete from `tabProcurement Package Line`")
	pk = frappe.db.sql("delete from `tabProcurement Package`")
	pl = frappe.db.sql("delete from `tabProcurement Plan`")
	return {"lines": ln or 0, "packages": pk or 0, "plans": pl or 0}


def run() -> dict:
	frappe.only_for(("System Manager", "Administrator"))
	out: dict = {}
	out["wiped_pp"] = _wipe_procurement_planning()
	out["cleared_dia"] = clear_dia_seed_demands()
	out["budget_empty"] = run_budget_empty()
	out["reset_core"] = reset_core_seed(dry_run=False)
	run_core_minimal()
	out["strategy_basic"] = run_strategy_basic()
	out["budget_extended"] = run_budget_extended()
	run_dia_basic()
	run_dia_f1_prereq()
	out["pp_f1"] = run_pp_f1(ensure_dia=True)
	frappe.db.commit()
	out["ok"] = True
	return out
