"""Downstream selector APIs — expose hierarchy from Active strategic plans only."""

from __future__ import annotations

import frappe
from frappe import _


def _active_plan_names() -> list[str]:
	return frappe.get_all(
		"Strategic Plan",
		filters={"status": "Active", "is_current_version": 1},
		pluck="name",
	)


def _reference_rows(rows: list[dict], *, id_field: str, code_field: str, name_field: str) -> list[dict]:
	out = []
	for row in rows:
		out.append(
			{
				"id": row.get(id_field),
				"code": row.get(code_field) or "",
				"name": row.get(name_field) or row.get(id_field) or "",
			}
		)
	return out


def _require_read() -> None:
	if not frappe.has_permission("Strategic Plan", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_active_strategy_programs():
	"""Programs belonging to Active strategic plans (downstream dropdowns)."""
	_require_read()
	plans = _active_plan_names()
	if not plans:
		return []
	rows = frappe.get_all(
		"Strategy Program",
		filters={"strategic_plan": ["in", plans]},
		fields=["name", "program_code", "program_title"],
		order_by="program_title asc",
		limit=5000,
	)
	return _reference_rows(rows, id_field="name", code_field="program_code", name_field="program_title")


@frappe.whitelist()
def get_active_strategy_sub_programs(program: str | None = None):
	"""Sub-programs belonging to Active strategic plans."""
	_require_read()
	plans = _active_plan_names()
	if not plans:
		return []
	filters: dict = {"strategic_plan": ["in", plans]}
	if program:
		filters["program"] = program
	rows = frappe.get_all(
		"Sub Program",
		filters=filters,
		fields=["name", "sub_program_code", "title", "program"],
		order_by="title asc",
		limit=5000,
	)
	return _reference_rows(rows, id_field="name", code_field="sub_program_code", name_field="title")


@frappe.whitelist()
def get_active_strategy_indicators(sub_program: str | None = None):
	"""Indicators (Strategy Objectives) belonging to Active strategic plans."""
	_require_read()
	plans = _active_plan_names()
	if not plans:
		return []
	filters: dict = {"strategic_plan": ["in", plans]}
	if sub_program:
		filters["sub_program"] = sub_program
	rows = frappe.get_all(
		"Strategy Objective",
		filters=filters,
		fields=["name", "objective_code", "objective_title", "sub_program"],
		order_by="objective_title asc",
		limit=5000,
	)
	return _reference_rows(rows, id_field="name", code_field="objective_code", name_field="objective_title")


@frappe.whitelist()
def get_active_strategy_targets(objective: str | None = None):
	"""Targets belonging to Active strategic plans."""
	_require_read()
	plans = _active_plan_names()
	if not plans:
		return []
	filters: dict = {"strategic_plan": ["in", plans]}
	if objective:
		filters["objective"] = objective
	rows = frappe.get_all(
		"Strategy Target",
		filters=filters,
		fields=["name", "target_code", "target_title", "objective"],
		order_by="target_title asc",
		limit=5000,
	)
	return _reference_rows(rows, id_field="name", code_field="target_code", name_field="target_title")
