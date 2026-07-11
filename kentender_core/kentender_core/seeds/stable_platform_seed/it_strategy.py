# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT strategy supplement under the existing MOH strategic plan."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.stable_platform_seed.constants import (
	IT_OBJECTIVE_CODE,
	IT_OBJECTIVE_DESCRIPTION,
	IT_OBJECTIVE_TITLE,
	IT_PROGRAM_CODE,
	IT_PROGRAM_DESCRIPTION,
	IT_PROGRAM_TITLE,
	IT_SUB_PROGRAM_CODE,
	IT_SUB_PROGRAM_TITLE,
	IT_TARGET_CODE,
	IT_TARGET_METRIC,
	IT_TARGET_TITLE,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	PLAN_TITLE,
	PROGRAM_CODE as WORKS_PROGRAM_CODE,
	START_YEAR,
	END_YEAR,
	resolve_procuring_entity_moh,
)


def _find_strategic_plan(pe_name: str) -> str | None:
	rows = frappe.get_all(
		"Strategic Plan",
		filters={
			"procuring_entity": pe_name,
			"start_year": START_YEAR,
			"end_year": END_YEAR,
		},
		fields=["name", "strategic_plan_name"],
		order_by="modified desc",
		limit=50,
	)
	for row in rows:
		if (row.get("strategic_plan_name") or "").strip() == PLAN_TITLE:
			return row.name
		if frappe.db.exists(
			"Strategy Program",
			{"strategic_plan": row.name, "program_code": WORKS_PROGRAM_CODE},
		):
			return row.name
	return None


def _ensure_draft_for_mutation(plan_name: str) -> None:
	plan = frappe.get_doc("Strategic Plan", plan_name)
	if (plan.status or "").strip() != "Draft":
		plan.status = "Draft"
		plan.save(ignore_permissions=True)


def _ensure_program(plan_name: str) -> str:
	existing = frappe.db.get_value(
		"Strategy Program",
		{"strategic_plan": plan_name, "program_code": IT_PROGRAM_CODE},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Strategy Program", existing)
		changed = False
		for field, value in (
			("program_title", IT_PROGRAM_TITLE),
			("description", IT_PROGRAM_DESCRIPTION),
		):
			if (getattr(doc, field) or "").strip() != value:
				setattr(doc, field, value)
				changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return existing
	child = frappe.get_doc(
		{
			"doctype": "Strategy Program",
			"strategic_plan": plan_name,
			"program_title": IT_PROGRAM_TITLE,
			"program_code": IT_PROGRAM_CODE,
			"description": IT_PROGRAM_DESCRIPTION,
			"order_index": 20,
		}
	)
	child.insert(ignore_permissions=True)
	return child.name


def _ensure_sub_program(plan_name: str, program_name: str) -> str:
	existing = frappe.db.get_value(
		"Sub Program",
		{"program": program_name, "sub_program_code": IT_SUB_PROGRAM_CODE},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Sub Program", existing)
		changed = False
		if doc.strategic_plan != plan_name:
			doc.strategic_plan = plan_name
			changed = True
		if (doc.title or "").strip() != IT_SUB_PROGRAM_TITLE:
			doc.title = IT_SUB_PROGRAM_TITLE
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return existing
	child = frappe.get_doc(
		{
			"doctype": "Sub Program",
			"strategic_plan": plan_name,
			"program": program_name,
			"title": IT_SUB_PROGRAM_TITLE,
			"sub_program_code": IT_SUB_PROGRAM_CODE,
		}
	)
	child.insert(ignore_permissions=True)
	return child.name


def _ensure_objective(plan_name: str, program_name: str, sub_program_name: str) -> str:
	existing = frappe.db.get_value(
		"Strategy Objective",
		{"sub_program": sub_program_name, "objective_code": IT_OBJECTIVE_CODE},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Strategy Objective", existing)
		changed = False
		for field, value in (
			("strategic_plan", plan_name),
			("program", program_name),
			("sub_program", sub_program_name),
			("objective_title", IT_OBJECTIVE_TITLE),
			("description", IT_OBJECTIVE_DESCRIPTION),
		):
			if getattr(doc, field) != value:
				setattr(doc, field, value)
				changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return existing
	child = frappe.get_doc(
		{
			"doctype": "Strategy Objective",
			"strategic_plan": plan_name,
			"program": program_name,
			"sub_program": sub_program_name,
			"objective_title": IT_OBJECTIVE_TITLE,
			"objective_code": IT_OBJECTIVE_CODE,
			"description": IT_OBJECTIVE_DESCRIPTION,
			"order_index": 20,
		}
	)
	child.insert(ignore_permissions=True)
	return child.name


def _ensure_target(plan_name: str, program_name: str, objective_name: str) -> str:
	existing = frappe.db.get_value(
		"Strategy Target",
		{"objective": objective_name, "target_code": IT_TARGET_CODE},
		"name",
	)
	desc = f"{IT_TARGET_METRIC} (stable platform IT supplement)."
	if existing:
		doc = frappe.get_doc("Strategy Target", existing)
		changed = False
		for field, value in (
			("strategic_plan", plan_name),
			("program", program_name),
			("target_title", IT_TARGET_TITLE),
			("description", desc),
		):
			if getattr(doc, field) != value:
				setattr(doc, field, value)
				changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return existing
	child = frappe.get_doc(
		{
			"doctype": "Strategy Target",
			"strategic_plan": plan_name,
			"program": program_name,
			"objective": objective_name,
			"target_title": IT_TARGET_TITLE,
			"target_code": IT_TARGET_CODE,
			"description": desc,
			"order_index": 20,
			"measurement_type": "Numeric",
			"target_value_numeric": 3,
			"target_unit": "hospitals",
			"target_period_type": "Annual",
			"target_year": START_YEAR,
		}
	)
	child.insert(ignore_permissions=True)
	return child.name


def upsert_it_strategy_supplement() -> dict[str, Any]:
	"""Add the digital health strategy chain to the existing MOH strategic plan."""
	frappe.only_for(("System Manager", "Administrator"))
	pe = resolve_procuring_entity_moh()
	if not pe:
		return {
			"ok": False,
			"error_code": "MISSING_PROCURING_ENTITY",
			"message": "Procuring Entity PE-MOH not found. Run core seed first.",
		}

	plan_name = _find_strategic_plan(pe)
	if not plan_name:
		return {
			"ok": False,
			"error_code": "MISSING_STRATEGIC_PLAN",
			"message": (
				f"Strategic plan '{PLAN_TITLE}' ({START_YEAR}-{END_YEAR}) not found. "
				"Run WORKS strategy seed first."
			),
		}

	_ensure_draft_for_mutation(plan_name)
	program = _ensure_program(plan_name)
	sub_program = _ensure_sub_program(plan_name, program)
	objective = _ensure_objective(plan_name, program, sub_program)
	target = _ensure_target(plan_name, program, objective)

	plan = frappe.get_doc("Strategic Plan", plan_name)
	if (plan.status or "").strip() != "Active":
		plan.status = "Active"
		plan.save(ignore_permissions=True)

	return {
		"ok": True,
		"strategic_plan": plan_name,
		"strategy_program": program,
		"strategy_objective": objective,
		"strategy_target": target,
		"codes": {
			"program_code": IT_PROGRAM_CODE,
			"objective_code": IT_OBJECTIVE_CODE,
			"target_code": IT_TARGET_CODE,
		},
	}
