from __future__ import annotations

import frappe

from kentender_core.seeds import constants as C

PLAN_NAME = C.PLAN_BASIC_NAME
BUDGET_2026_NAME = "FY2026 Budget"
BUDGET_2027_NAME = "FY2027 Budget"


def _to_name(doc_or_name: str | object) -> str:
	if isinstance(doc_or_name, str):
		return doc_or_name
	return getattr(doc_or_name, "name")


def get_plan_name() -> str:
	plan_name = frappe.db.get_value(
		"Strategic Plan",
		{"strategic_plan_name": PLAN_NAME, "procuring_entity": C.ENTITY_MOH},
		"name",
	)
	if not plan_name:
		frappe.throw(f"Required Strategic Plan not found: {PLAN_NAME}")
	return plan_name


def get_program_name(plan_name: str, program_title: str) -> str:
	program_name = frappe.db.get_value(
		"Strategy Program",
		{"strategic_plan": plan_name, "program_title": program_title},
		"name",
	)
	if not program_name:
		frappe.throw(
			f"Required Strategy Program not found: {program_title} under plan {plan_name}"
		)
	return program_name


def upsert_budget(
	*,
	budget_name: str,
	fiscal_year: int,
	total_budget_amount: float,
	notes: str,
	strategic_plan: str,
) -> str:
	existing_name = frappe.db.get_value(
		"Budget",
		{
			"budget_name": budget_name,
			"procuring_entity": C.ENTITY_MOH,
			"fiscal_year": fiscal_year,
			"strategic_plan": strategic_plan,
			"is_current_version": 1,
		},
		"name",
	)
	fields = {
		"budget_name": budget_name,
		"procuring_entity": C.ENTITY_MOH,
		"fiscal_year": fiscal_year,
		"strategic_plan": strategic_plan,
		"currency": "KES",
		"total_budget_amount": total_budget_amount,
		"status": "Draft",
		"version_no": 1,
		"is_current_version": 1,
		"supersedes_budget": None,
		"notes": notes,
		"order_index": 0,
	}
	if existing_name:
		doc = frappe.get_doc("Budget", existing_name)
		# Do not reset approval status on re-seed (B5.6 extended pack may set Submitted/Approved).
		update_fields = {k: v for k, v in fields.items() if k != "status"}
		doc.update(update_fields)
		doc.save(ignore_permissions=True)
		return doc.name
	doc = frappe.get_doc({"doctype": "Budget", **fields})
	doc.insert(ignore_permissions=True)
	return doc.name


def upsert_budget_allocation(
	*,
	budget: str,
	program: str,
	amount: float,
	notes: str,
	order_index: int,
) -> str:
	budget_name = _to_name(budget)
	program_name = _to_name(program)
	existing = frappe.db.get_value(
		"Budget Allocation",
		{"budget": budget_name, "program": program_name},
		"name",
	)
	fields = {
		"budget": budget_name,
		"program": program_name,
		"amount": amount,
		"notes": notes,
		"order_index": order_index,
	}
	if existing:
		doc = frappe.get_doc("Budget Allocation", existing)
		doc.update(fields)
		doc.save(ignore_permissions=True)
		return doc.name
	doc = frappe.get_doc({"doctype": "Budget Allocation", **fields})
	doc.insert(ignore_permissions=True)
	return doc.name


def set_budget_status_for_seed(budget_id: str, status: str) -> None:
	"""Set Budget status using document save so validation runs (B5.6). Caller must be allowed to transition."""
	doc = frappe.get_doc("Budget", budget_id)
	if doc.status == status:
		return
	# Idempotent re-seed: do not overwrite Approved (or other final states) back to Submitted.
	if status == "Submitted" and doc.status != "Draft":
		return
	doc.status = status
	doc.save(ignore_permissions=True)


def clear_budget_data() -> dict[str, int]:
	alloc_deleted = frappe.db.delete("Budget Allocation", {})
	budget_deleted = frappe.db.delete("Budget", {})
	return {"budget_allocations_deleted": alloc_deleted, "budgets_deleted": budget_deleted}

