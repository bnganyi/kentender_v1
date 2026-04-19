# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""seed_strategy_basic — MOH Strategic Plan 2026–2030 with full hierarchy (seed spec §8)."""

from __future__ import annotations

import frappe

from kentender_core.seeds import constants as C
from kentender_core.seeds.seed_core_minimal import run as run_core


def run():
	frappe.only_for(("System Manager", "Administrator"))
	run_core()
	out = _ensure_basic_plan()
	frappe.db.commit()
	return out


def _wipe_plan_content(plan_name: str):
	frappe.db.delete("Strategy Target", {"strategic_plan": plan_name})
	frappe.db.delete("Strategy Objective", {"strategic_plan": plan_name})
	frappe.db.delete("Strategy Program", {"strategic_plan": plan_name})


def _ensure_basic_plan():
	moh = C.ENTITY_MOH
	existing = frappe.db.get_value(
		"Strategic Plan",
		{"strategic_plan_name": C.PLAN_BASIC_NAME, "procuring_entity": moh},
		"name",
	)
	if existing:
		_wipe_plan_content(existing)
		frappe.delete_doc("Strategic Plan", existing, force=True, ignore_permissions=True)

	plan = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"strategic_plan_name": C.PLAN_BASIC_NAME,
			"procuring_entity": moh,
			"start_year": 2026,
			"end_year": 2030,
			"status": "Draft",
			"version_no": 1,
			"is_current_version": 1,
		}
	)
	plan.insert(ignore_permissions=True)
	pn = plan.name

	# Programs
	p1 = frappe.get_doc(
		{
			"doctype": "Strategy Program",
			"strategic_plan": pn,
			"program_title": "Healthcare Access",
			"program_code": "P001",
			"description": "Expand equitable access to essential healthcare services across underserved areas.",
			"order_index": 1,
		}
	)
	p1.insert(ignore_permissions=True)
	p2 = frappe.get_doc(
		{
			"doctype": "Strategy Program",
			"strategic_plan": pn,
			"program_title": "Workforce Development",
			"program_code": "P002",
			"description": "Strengthen health workforce capacity, deployment, and specialist availability.",
			"order_index": 2,
		}
	)
	p2.insert(ignore_permissions=True)

	# Objectives
	o1 = frappe.get_doc(
		{
			"doctype": "Strategy Objective",
			"strategic_plan": pn,
			"program": p1.name,
			"objective_title": "Increase rural healthcare coverage",
			"objective_code": "O001",
			"description": "Improve population access to healthcare services in rural and underserved counties.",
			"order_index": 1,
		}
	)
	o1.insert(ignore_permissions=True)
	o2 = frappe.get_doc(
		{
			"doctype": "Strategy Objective",
			"strategic_plan": pn,
			"program": p1.name,
			"objective_title": "Improve maternal health service access",
			"objective_code": "O002",
			"description": "Expand access to maternal care infrastructure and referral capability.",
			"order_index": 2,
		}
	)
	o2.insert(ignore_permissions=True)
	o3 = frappe.get_doc(
		{
			"doctype": "Strategy Objective",
			"strategic_plan": pn,
			"program": p2.name,
			"objective_title": "Expand nursing and clinical workforce capacity",
			"objective_code": "O003",
			"description": "Increase trained personnel and improve workforce deployment.",
			"order_index": 1,
		}
	)
	o3.insert(ignore_permissions=True)

	# Targets (§8.5)
	targets = [
		{
			"strategic_plan": pn,
			"program": p1.name,
			"objective": o1.name,
			"target_title": "Rural healthcare coverage reaches 65 percent",
			"description": "Increase national rural healthcare service coverage by 2027.",
			"order_index": 1,
			"measurement_type": "Percentage",
			"target_period_type": "Annual",
			"target_year": 2027,
			"target_value_numeric": 65,
			"target_unit": "Percent",
			"baseline_value_numeric": 52,
			"baseline_year": 2025,
		},
		{
			"strategic_plan": pn,
			"program": p1.name,
			"objective": o1.name,
			"target_title": "Rural healthcare coverage reaches 85 percent",
			"description": "Achieve broad rural healthcare access by end of plan period.",
			"order_index": 2,
			"measurement_type": "Percentage",
			"target_period_type": "End of Plan",
			"target_value_numeric": 85,
			"target_unit": "Percent",
			"baseline_value_numeric": 52,
			"baseline_year": 2025,
		},
		{
			"strategic_plan": pn,
			"program": p1.name,
			"objective": o2.name,
			"target_title": "Additional maternal health facilities operational",
			"description": "Expand operational maternal health facilities across priority counties.",
			"order_index": 1,
			"measurement_type": "Numeric",
			"target_period_type": "Annual",
			"target_year": 2028,
			"target_value_numeric": 40,
			"target_unit": "Facilities",
			"baseline_value_numeric": 18,
			"baseline_year": 2025,
		},
		{
			"strategic_plan": pn,
			"program": p2.name,
			"objective": o3.name,
			"target_title": "Nurses trained and deployed",
			"description": "Train and deploy additional nurses to underserved facilities.",
			"order_index": 1,
			"measurement_type": "Numeric",
			"target_period_type": "Annual",
			"target_year": 2026,
			"target_value_numeric": 500,
			"target_unit": "Staff",
			"baseline_value_numeric": 0,
			"baseline_year": 2025,
		},
	]
	for t in targets:
		frappe.get_doc({"doctype": "Strategy Target", **t}).insert(ignore_permissions=True)

	return {
		"plan": pn,
		"programs": 2,
		"objectives": 3,
		"targets": 4,
	}
