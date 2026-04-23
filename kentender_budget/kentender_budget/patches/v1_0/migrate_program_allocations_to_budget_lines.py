# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint, flt


def execute():
	"""Backfill Budget Lines from legacy Budget Allocation rows (idempotent)."""
	alloc_rows = frappe.get_all(
		"Budget Allocation",
		fields=["name", "budget", "program", "amount", "notes", "order_index"],
		order_by="modified asc",
		limit=10000,
	)
	for idx, row in enumerate(alloc_rows, start=1):
		_upsert_line_for_allocation(row, idx)


def _upsert_line_for_allocation(row, seq: int):
	budget = frappe.get_doc("Budget", row.budget)
	program_title = frappe.db.get_value("Strategy Program", row.program, "program_title") or row.program
	entity = (budget.procuring_entity or "GEN").strip().upper()
	year = cint(budget.fiscal_year) or 0
	code = f"BL-{entity}-{year}-{str(seq).zfill(3)}"
	existing = frappe.db.get_value(
		"Budget Line",
		{"budget": row.budget, "program": row.program, "amount_allocated": flt(row.amount)},
		"name",
	)
	if not existing:
		existing = frappe.db.get_value("Budget Line", {"budget": row.budget, "budget_line_code": code}, "name")
	obj = frappe.db.get_value(
		"Strategy Objective",
		{"strategic_plan": budget.strategic_plan, "program": row.program},
		"name",
	)
	target = frappe.db.get_value("Strategy Target", {"objective": obj}, "name") if obj else None
	doc = frappe.get_doc("Budget Line", existing) if existing else frappe.new_doc("Budget Line")
	doc.budget_line_code = code
	doc.budget_line_name = program_title
	doc.budget = budget.name
	doc.procuring_entity = budget.procuring_entity
	doc.fiscal_year = budget.fiscal_year
	doc.currency = budget.currency
	doc.strategic_plan = budget.strategic_plan
	doc.program = row.program
	doc.output_indicator = obj
	doc.performance_target = target
	doc.amount_allocated = flt(row.amount)
	doc.amount_reserved = flt(doc.amount_reserved or 0)
	doc.amount_consumed = flt(doc.amount_consumed or 0)
	doc.funding_source = doc.funding_source or None
	doc.notes = row.notes or ""
	doc.is_active = 1
	doc.save(ignore_permissions=True)
