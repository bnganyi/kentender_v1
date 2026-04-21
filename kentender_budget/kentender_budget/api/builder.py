import frappe
from frappe import _
from frappe.utils import flt


def _get_builder_payload(budget_name: str):
	budget = frappe.db.get_value(
		"Budget",
		budget_name,
		[
			"name",
			"budget_name",
			"currency",
			"total_budget_amount",
			"strategic_plan",
			"status",
			"rejection_reason",
			"rejected_by",
			"rejected_at",
		],
		as_dict=True,
	)
	if not budget:
		frappe.throw(_("Budget not found."))

	programs = frappe.get_all(
		"Strategy Program",
		filters={"strategic_plan": budget.strategic_plan},
		fields=["name", "program_title", "order_index"],
		order_by="order_index asc, modified asc",
		limit=2000,
	)

	alloc_rows = frappe.get_all(
		"Budget Allocation",
		filters={"budget": budget.name},
		fields=["name", "program", "amount", "notes"],
		limit=2000,
	)
	alloc_by_program = {r.program: r for r in alloc_rows}

	program_rows = []
	for p in programs:
		allocation = alloc_by_program.get(p.name)
		amount = flt(allocation.amount) if allocation else 0.0
		label = p.program_title or p.name
		program_rows.append(
			{
				"name": p.name,
				"program_title": label,
				"allocated_amount": amount,
				"notes": allocation.notes if allocation else "",
				"allocation_name": allocation.name if allocation else None,
				"is_allocated": bool(allocation),
			}
		)

	total_budget = flt(budget.total_budget_amount)
	allocated_sum = sum(flt(r.get("allocated_amount")) for r in program_rows)
	remaining_amount = max(0.0, total_budget - allocated_sum)

	return {
		"budget": {
			"name": budget.name,
			"budget_name": budget.budget_name,
			"currency": budget.currency,
			"total_budget_amount": total_budget,
			"strategic_plan": budget.strategic_plan,
			"status": budget.status or "Draft",
			"rejection_reason": budget.get("rejection_reason"),
			"rejected_by": budget.get("rejected_by"),
			"rejected_at": budget.get("rejected_at"),
		},
		"totals": {
			"total_budget_amount": total_budget,
			"allocated_sum": allocated_sum,
			"remaining_amount": remaining_amount,
		},
		"programs": program_rows,
	}


@frappe.whitelist()
def get_budget_builder_data(budget_name: str):
	"""Return shell data for Budget Builder (B3.1, read-only)."""
	if not budget_name:
		frappe.throw(_("Budget is required."))
	if not frappe.has_permission("Budget", "read", budget_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return _get_builder_payload(budget_name)


@frappe.whitelist()
def upsert_budget_allocation(
	budget_name: str, program_name: str, amount: float, notes: str | None = None
):
	if not budget_name:
		frappe.throw(_("Budget is required."))
	if not program_name:
		frappe.throw(_("Program is required."))
	if not frappe.has_permission("Budget", "write", budget_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	existing = frappe.db.get_value(
		"Budget Allocation",
		{"budget": budget_name, "program": program_name},
		"name",
	)
	allocation_doc = (
		frappe.get_doc("Budget Allocation", existing)
		if existing
		else frappe.new_doc("Budget Allocation")
	)
	allocation_doc.budget = budget_name
	allocation_doc.program = program_name
	allocation_doc.amount = flt(amount)
	allocation_doc.notes = notes or ""
	allocation_doc.save(ignore_permissions=False)

	return _get_builder_payload(budget_name)
