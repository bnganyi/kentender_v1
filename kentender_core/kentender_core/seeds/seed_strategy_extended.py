# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""seed_strategy_extended — second plan (seed spec §9) after basic scenario."""

from __future__ import annotations

import frappe

from kentender_core.seeds import constants as C
from kentender_core.seeds.seed_core_minimal import run as run_core
from kentender_core.seeds.seed_strategy_basic import _ensure_basic_plan


def run():
	frappe.only_for(("System Manager", "Administrator"))
	run_core()
	basic = _ensure_basic_plan()
	frappe.db.commit()
	ext = _ensure_extended_plan()
	frappe.db.commit()
	return {"basic": basic, "extended": ext}


def _ensure_extended_plan():
	moh = C.ENTITY_MOH
	existing = frappe.db.get_value(
		"Strategic Plan",
		{"strategic_plan_name": C.PLAN_EXTENDED_NAME, "procuring_entity": moh},
		"name",
	)
	if existing:
		frappe.db.delete("Strategy Target", {"strategic_plan": existing})
		frappe.db.delete("Strategy Objective", {"strategic_plan": existing})
		frappe.db.delete("Strategy Program", {"strategic_plan": existing})
		frappe.delete_doc("Strategic Plan", existing, force=True, ignore_permissions=True)

	plan = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"strategic_plan_name": C.PLAN_EXTENDED_NAME,
			"procuring_entity": moh,
			"start_year": 2027,
			"end_year": 2031,
			"status": "Draft",
			"version_no": 1,
			"is_current_version": 0,
		}
	)
	plan.insert(ignore_permissions=True)
	pn = plan.name

	pg = frappe.get_doc(
		{
			"doctype": "Strategy Program",
			"strategic_plan": pn,
			"program_title": "Service Delivery",
			"program_code": "P201",
			"description": "Extended seed program.",
			"order_index": 1,
		}
	)
	pg.insert(ignore_permissions=True)
	ob = frappe.get_doc(
		{
			"doctype": "Strategy Objective",
			"strategic_plan": pn,
			"program": pg.name,
			"objective_title": "Improve service delivery metrics",
			"objective_code": "O201",
			"description": "Placeholder objective for multi-plan testing.",
			"order_index": 1,
		}
	)
	ob.insert(ignore_permissions=True)
	tg = frappe.get_doc(
		{
			"doctype": "Strategy Target",
			"strategic_plan": pn,
			"program": pg.name,
			"objective": ob.name,
			"target_title": "Service delivery index baseline",
			"description": "Single target for extended plan smoke tests.",
			"order_index": 1,
			"measurement_type": "Numeric",
			"target_period_type": "Annual",
			"target_year": 2028,
			"target_value_numeric": 100,
			"target_unit": "Index",
			"baseline_value_numeric": 0,
			"baseline_year": 2025,
		}
	)
	tg.insert(ignore_permissions=True)
	return {"plan": pn, "programs": 1, "objectives": 1, "targets": 1}
