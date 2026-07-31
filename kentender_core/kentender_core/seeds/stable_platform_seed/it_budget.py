# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT budget line supplement on the existing MOH FY 2026/2027 budget cycle."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_budget.seeds.works_master_budget_seed import (
	BUDGET_NAME,
	FISCAL_YEAR,
	FUNDING_SOURCE_TITLE,
	PLAN_END_YEAR,
	PLAN_START_YEAR,
	PLAN_TITLE,
	_ensure_funding_source,
	resolve_procuring_entity_moh,
)
from kentender_core.seeds._common import ensure_currency_kes
from kentender_core.seeds.stable_platform_seed.constants import (
	IT_AMOUNT_ALLOCATED,
	IT_AMOUNT_RESERVED,
	IT_BUDGET_LINE_CODE,
	IT_BUDGET_LINE_NOTES,
	IT_BUDGET_LINE_TITLE,
	IT_OBJECTIVE_CODE,
	IT_PROGRAM_CODE,
	IT_SUB_PROGRAM_CODE,
	IT_TARGET_CODE,
)


def _resolve_strategic_plan(pe_name: str) -> str | None:
	rows = frappe.get_all(
		"Strategic Plan",
		filters={
			"procuring_entity": pe_name,
			"start_year": PLAN_START_YEAR,
			"end_year": PLAN_END_YEAR,
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
			{"strategic_plan": row.name, "program_code": IT_PROGRAM_CODE},
		):
			return row.name
	return None


def _resolve_it_strategy_refs(plan_name: str) -> dict[str, str | None]:
	program = frappe.db.get_value(
		"Strategy Program",
		{"strategic_plan": plan_name, "program_code": IT_PROGRAM_CODE},
		"name",
	)
	sub_program = (
		frappe.db.get_value(
			"Sub Program",
			{"program": program, "sub_program_code": IT_SUB_PROGRAM_CODE},
			"name",
		)
		if program
		else None
	)
	objective = (
		frappe.db.get_value(
			"Strategy Objective",
			{"sub_program": sub_program, "objective_code": IT_OBJECTIVE_CODE},
			"name",
		)
		if sub_program
		else None
	)
	target = (
		frappe.db.get_value(
			"Strategy Target",
			{"objective": objective, "target_code": IT_TARGET_CODE},
			"name",
		)
		if objective
		else None
	)
	return {
		"program": program,
		"sub_program": sub_program,
		"objective": objective,
		"target": target,
	}


def _find_budget(pe_name: str) -> str | None:
	return frappe.db.get_value(
		"Budget",
		{"budget_name": BUDGET_NAME, "procuring_entity": pe_name, "fiscal_year": FISCAL_YEAR},
		"name",
	)


def _sync_budget_total_from_lines(budget_name: str) -> float:
	"""Keep Budget.total_budget_amount equal to active line allocations.

	The IT supplement adds BUD-MOH-IT-2026-001 on top of the WORKS line. Without
	this sync, Home/Budget portfolio shows allocated > approved.
	"""
	total = flt(
		frappe.db.sql(
			"""
			SELECT COALESCE(SUM(amount_allocated), 0)
			FROM `tabBudget Line`
			WHERE budget = %s AND IFNULL(is_active, 1) = 1
			""",
			budget_name,
		)[0][0]
	)
	frappe.db.set_value(
		"Budget",
		budget_name,
		"total_budget_amount",
		total,
		update_modified=False,
	)
	return total


def upsert_it_budget_supplement() -> dict[str, Any]:
	"""Add BUD-MOH-IT-2026-001 to the existing MOH budget cycle."""
	frappe.only_for(("System Manager", "Administrator"))

	entity = resolve_procuring_entity_moh()
	if not entity:
		return {
			"ok": False,
			"error_code": "MISSING_PROCURING_ENTITY",
			"message": "Procuring Entity PE-MOH not found.",
		}

	budget_name = _find_budget(entity)
	if not budget_name:
		return {
			"ok": False,
			"error_code": "MISSING_BUDGET",
			"message": f"Budget cycle {BUDGET_NAME} not found. Run WORKS budget seed first.",
		}

	plan_name = _resolve_strategic_plan(entity)
	if not plan_name:
		return {
			"ok": False,
			"error_code": "MISSING_STRATEGIC_PLAN",
			"message": "MOH strategic plan not found.",
		}

	refs = _resolve_it_strategy_refs(plan_name)
	if not all(refs.values()):
		return {
			"ok": False,
			"error_code": "MISSING_IT_STRATEGY",
			"message": "IT strategy supplement not found. Run IT strategy seed first.",
			"missing_refs": refs,
		}

	if frappe.db.exists("Budget Line", IT_BUDGET_LINE_CODE):
		frappe.db.set_value(
			"Budget Line",
			IT_BUDGET_LINE_CODE,
			{
				"budget_line_name": IT_BUDGET_LINE_TITLE,
				"notes": IT_BUDGET_LINE_NOTES,
				"amount_allocated": IT_AMOUNT_ALLOCATED,
				"amount_reserved": IT_AMOUNT_RESERVED,
				"sub_program": refs["sub_program"],
				"output_indicator": refs["objective"],
				"performance_target": refs["target"],
				"is_active": 1,
			},
			update_modified=False,
		)
		available = flt(IT_AMOUNT_ALLOCATED) - flt(IT_AMOUNT_RESERVED)
		frappe.db.set_value(
			"Budget Line",
			IT_BUDGET_LINE_CODE,
			"amount_available",
			available,
			update_modified=False,
		)
		budget_total = _sync_budget_total_from_lines(budget_name)
		return {
			"ok": True,
			"budget_line": IT_BUDGET_LINE_CODE,
			"budget_line_code": IT_BUDGET_LINE_CODE,
			"created": False,
			"amount_available": available,
			"budget_total": budget_total,
		}

	ensure_currency_kes()
	funding_source = _ensure_funding_source()

	doc = frappe.get_doc(
		{
			"doctype": "Budget Line",
			"budget_line_code": IT_BUDGET_LINE_CODE,
			"budget_line_name": IT_BUDGET_LINE_TITLE,
			"budget": budget_name,
			"procuring_entity": entity,
			"fiscal_year": FISCAL_YEAR,
			"amount_allocated": IT_AMOUNT_ALLOCATED,
			"amount_reserved": IT_AMOUNT_RESERVED,
			"amount_consumed": 0.0,
			"currency": "KES",
			"funding_source": funding_source,
			"strategic_plan": plan_name,
			"program": refs["program"],
			"sub_program": refs["sub_program"],
			"output_indicator": refs["objective"],
			"performance_target": refs["target"],
			"economic_classification": "Goods",
			"is_active": 1,
			"line_status": "Active",
			"notes": IT_BUDGET_LINE_NOTES,
		}
	)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	available = flt(IT_AMOUNT_ALLOCATED) - flt(IT_AMOUNT_RESERVED)
	frappe.db.set_value(
		"Budget Line",
		doc.name,
		{
			"amount_allocated": IT_AMOUNT_ALLOCATED,
			"amount_reserved": IT_AMOUNT_RESERVED,
			"amount_available": available,
		},
		update_modified=False,
	)
	budget_total = _sync_budget_total_from_lines(budget_name)

	return {
		"ok": True,
		"budget_line": doc.name,
		"budget_line_code": IT_BUDGET_LINE_CODE,
		"created": True,
		"amount_available": available,
		"budget_total": budget_total,
	}
