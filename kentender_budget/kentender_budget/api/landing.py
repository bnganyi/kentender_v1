# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def get_budget_landing_data():
	"""Portfolio KPIs + per-budget figures for Budget Management workspace."""
	if not frappe.has_permission("Budget", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	budgets = frappe.get_all(
		"Budget",
		filters={"is_current_version": 1},
		fields=[
			"name",
			"budget_name",
			"fiscal_year",
			"status",
			"strategic_plan",
			"currency",
			"total_budget_amount",
			"modified",
			"owner",
			"created_by",
			"rejection_reason",
			"rejected_by",
			"rejected_at",
		],
		order_by="modified desc",
		limit=2000,
	)

	session_user = frappe.session.user

	if not budgets:
		return {
			"portfolio": {
				"active_count": 0,
				"draft_count": 0,
				"submitted_count": 0,
				"approved_count": 0,
				"my_drafts_count": 0,
				"rejected_count": 0,
				"pending_approval_count": 0,
				"total_budget_sum": 0.0,
				"allocated_sum": 0.0,
				"allocation_pct": 0.0,
			},
			"budgets": [],
		}

	names = [b.name for b in budgets]

	alloc_rows = frappe.db.sql(
		"""
		SELECT budget, SUM(amount) AS allocated_amount, COUNT(DISTINCT program) AS programs_allocated
		FROM `tabBudget Allocation`
		WHERE budget IN %(names)s
		GROUP BY budget
		""",
		{"names": tuple(names)},
		as_dict=True,
	)
	alloc_by_budget = {r.budget: r for r in alloc_rows}

	plans = list({b.strategic_plan for b in budgets if b.get("strategic_plan")})
	prog_counts = {}
	if plans:
		for r in frappe.db.sql(
			"""
			SELECT strategic_plan, COUNT(*) AS cnt
			FROM `tabStrategy Program`
			WHERE strategic_plan IN %(plans)s
			GROUP BY strategic_plan
			""",
			{"plans": tuple(plans)},
			as_dict=True,
		):
			prog_counts[r.strategic_plan] = int(r.cnt or 0)

	active_count = sum(1 for b in budgets if b.get("status") == "Approved")
	draft_count = sum(1 for b in budgets if b.get("status") == "Draft")
	submitted_count = sum(1 for b in budgets if b.get("status") == "Submitted")
	rejected_count = sum(1 for b in budgets if b.get("status") == "Rejected")
	approved_count = active_count
	my_drafts_count = sum(
		1
		for b in budgets
		if b.get("status") in ("Draft", "Rejected")
		and (b.get("owner") == session_user or b.get("created_by") == session_user)
	)
	# MVP: org-wide pending (all Submitted), not scoped by entity.
	pending_approval_count = submitted_count

	total_budget_sum = sum(flt(b.get("total_budget_amount")) for b in budgets)
	allocated_sum = sum(
		flt(alloc_by_budget.get(b.name, {}).get("allocated_amount")) for b in budgets
	)
	allocation_pct = (allocated_sum / total_budget_sum * 100.0) if total_budget_sum else 0.0

	out_budgets = []
	for b in budgets:
		total = flt(b.get("total_budget_amount"))
		arow = alloc_by_budget.get(b.name)
		allocated_amount = flt(arow.get("allocated_amount")) if arow else 0.0
		programs_allocated = int(arow.get("programs_allocated") or 0) if arow else 0
		sp = b.get("strategic_plan")
		program_total = int(prog_counts.get(sp, 0)) if sp else 0
		programs_unallocated = max(0, program_total - programs_allocated)

		out_budgets.append(
			{
				"name": b.name,
				"budget_name": b.budget_name,
				"fiscal_year": b.fiscal_year,
				"status": b.status,
				"strategic_plan": sp,
				"currency": b.currency,
				"total_budget_amount": total,
				"owner": b.get("owner"),
				"created_by": b.get("created_by"),
				"rejection_reason": b.get("rejection_reason"),
				"rejected_by": b.get("rejected_by"),
				"rejected_at": b.get("rejected_at"),
				"allocated_amount": allocated_amount,
				"remaining_amount": max(0.0, total - allocated_amount),
				"allocation_pct": (allocated_amount / total * 100.0) if total else 0.0,
				"program_total": program_total,
				"programs_allocated": programs_allocated,
				"programs_unallocated": programs_unallocated,
			}
		)

	return {
		"portfolio": {
			"active_count": active_count,
			"draft_count": draft_count,
			"submitted_count": submitted_count,
			"approved_count": approved_count,
			"my_drafts_count": my_drafts_count,
			"rejected_count": rejected_count,
			"pending_approval_count": pending_approval_count,
			"total_budget_sum": total_budget_sum,
			"allocated_sum": allocated_sum,
			"allocation_pct": allocation_pct,
		},
		"budgets": out_budgets,
	}
