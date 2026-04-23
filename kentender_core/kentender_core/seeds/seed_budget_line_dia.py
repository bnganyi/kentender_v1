# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""BX4 — DIA Budget Line seed (mini-PRD §14): BL-MOH-2026-001/002, BL-MOH-2027-001."""

from __future__ import annotations

import frappe

from kentender_core.seeds import constants as C
from kentender_core.seeds._budget_seed_common import (
	BUDGET_2026_NAME,
	BUDGET_2027_NAME,
	get_plan_name,
	get_program_name,
)
from kentender_core.seeds.seed_budget_extended import run as run_budget_extended


def verify_prerequisites_for_dia() -> dict:
	"""G2 — report whether BL-MOH-2026-001/002 and BL-MOH-2027-001 exist (no writes)."""
	frappe.only_for(("System Manager", "Administrator"))
	codes = ("BL-MOH-2026-001", "BL-MOH-2026-002", "BL-MOH-2027-001")
	found: dict[str, str | None] = {}
	missing: list[str] = []
	for code in codes:
		name = frappe.db.get_value("Budget Line", {"budget_line_code": code}, "name")
		found[code] = name
		if not name:
			missing.append(code)
	return {"ok": len(missing) == 0, "budget_lines": found, "missing": missing}


def run(include_budget_extended: bool = True):
	frappe.only_for(("System Manager", "Administrator"))
	if include_budget_extended:
		run_budget_extended()
	out = _seed_budget_lines()
	frappe.db.commit()
	return out


def _ensure_sub_program(program: str, title: str) -> str:
	existing = frappe.db.get_value("Sub Program", {"program": program, "title": title}, "name")
	if existing:
		return existing
	doc = frappe.get_doc({"doctype": "Sub Program", "program": program, "title": title})
	doc.insert(ignore_permissions=True)
	return doc.name


def _target_for_objective(objective_name: str) -> str | None:
	rows = frappe.get_all(
		"Strategy Target",
		filters={"objective": objective_name},
		pluck="name",
		order_by="order_index asc",
		limit=1,
	)
	return rows[0] if rows else None


def _objective_by_title(plan: str, program: str, title: str) -> str | None:
	return frappe.db.get_value(
		"Strategy Objective",
		{"strategic_plan": plan, "program": program, "objective_title": title},
		"name",
	)


def upsert_budget_line(
	*,
	code: str,
	line_name: str,
	budget: str,
	fiscal_year: int,
	allocated: float,
	strategic_plan: str,
	program: str,
	output_indicator: str | None,
	performance_target: str | None,
	sub_program: str,
) -> str:
	entity = frappe.db.get_value("Budget", budget, "procuring_entity")
	currency = frappe.db.get_value("Budget", budget, "currency")
	if not entity or not currency:
		frappe.throw(f"Budget {budget} is missing entity or currency.")

	fields = {
		"budget_line_code": code,
		"budget_line_name": line_name,
		"budget": budget,
		"procuring_entity": entity,
		"fiscal_year": fiscal_year,
		"amount_allocated": allocated,
		"amount_reserved": 0,
		"amount_consumed": 0,
		"currency": currency,
		"strategic_plan": strategic_plan,
		"program": program,
		"sub_program": sub_program,
		"output_indicator": output_indicator,
		"performance_target": performance_target,
		"is_active": 1,
	}
	existing = frappe.db.get_value("Budget Line", {"budget_line_code": code}, "name")
	if existing:
		doc = frappe.get_doc("Budget Line", existing)
		doc.update(fields)
		doc.save(ignore_permissions=True)
		return doc.name
	doc = frappe.get_doc({"doctype": "Budget Line", **fields})
	doc.insert(ignore_permissions=True)
	return doc.name


def _seed_budget_lines():
	plan = get_plan_name()
	healthcare = get_program_name(plan, "Healthcare Access")
	workforce = get_program_name(plan, "Workforce Development")

	b2026 = frappe.db.get_value(
		"Budget",
		{
			"budget_name": BUDGET_2026_NAME,
			"strategic_plan": plan,
			"procuring_entity": C.ENTITY_MOH,
			"is_current_version": 1,
		},
		"name",
	)
	b2027 = frappe.db.get_value(
		"Budget",
		{
			"budget_name": BUDGET_2027_NAME,
			"strategic_plan": plan,
			"procuring_entity": C.ENTITY_MOH,
			"is_current_version": 1,
		},
		"name",
	)
	if not b2026 or not b2027:
		frappe.throw("FY2026 and FY2027 budgets must exist before seeding budget lines.")

	obj_rural = _objective_by_title(plan, healthcare, "Increase rural healthcare coverage")
	obj_maternal = _objective_by_title(
		plan, healthcare, "Improve maternal health service access"
	)
	obj_nursing = _objective_by_title(plan, workforce, "Expand nursing and clinical workforce capacity")
	if not obj_rural or not obj_maternal or not obj_nursing:
		frappe.throw("Required Strategy Objective rows not found for DIA budget line seed.")

	t_rural = _target_for_objective(obj_rural)
	t_nursing = _target_for_objective(obj_nursing)
	t_maternal = _target_for_objective(obj_maternal)
	if not t_rural or not t_nursing or not t_maternal:
		frappe.throw("Required Strategy Target rows not found for DIA budget line seed.")

	sub_hc_primary = _ensure_sub_program(healthcare, "Primary Care Infrastructure")
	sub_wf_training = _ensure_sub_program(workforce, "Clinical Training Delivery")

	lines = [
		upsert_budget_line(
			code="BL-MOH-2026-001",
			line_name="Medical Equipment Capex",
			budget=b2026,
			fiscal_year=2026,
			allocated=5_000_000,
			strategic_plan=plan,
			program=healthcare,
			sub_program=sub_hc_primary,
			output_indicator=obj_rural,
			performance_target=t_rural,
		),
		upsert_budget_line(
			code="BL-MOH-2026-002",
			line_name="Clinical Workforce Training",
			budget=b2026,
			fiscal_year=2026,
			allocated=3_000_000,
			strategic_plan=plan,
			program=workforce,
			sub_program=sub_wf_training,
			output_indicator=obj_nursing,
			performance_target=t_nursing,
		),
		upsert_budget_line(
			code="BL-MOH-2027-001",
			line_name="Rural Facility Expansion",
			budget=b2027,
			fiscal_year=2027,
			allocated=9_000_000,
			strategic_plan=plan,
			program=healthcare,
			sub_program=sub_hc_primary,
			output_indicator=obj_maternal,
			performance_target=t_maternal,
		),
	]
	return {"budget_lines": lines}
