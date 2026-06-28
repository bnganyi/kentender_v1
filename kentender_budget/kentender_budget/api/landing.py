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
			"procuring_entity",
			"modified",
			"owner",
			"created_by",
			"rejection_reason",
			"rejected_by",
			"rejected_at",
			"submitted_by",
			"submitted_at",
			"approved_by",
			"approved_at",
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
				"reserved_sum": 0.0,
				"committed_sum": 0.0,
				"consumed_sum": 0.0,
				"available_sum": 0.0,
				"allocation_pct": 0.0,
			},
			"budgets": [],
		}

	names = [b.name for b in budgets]

	line_rows = frappe.db.sql(
		"""
		SELECT
			budget,
			COUNT(*) AS budget_line_total,
			SUM(CASE WHEN amount_allocated > 0 THEN 1 ELSE 0 END) AS budget_lines_allocated,
			SUM(amount_allocated)  AS allocated_amount,
			SUM(amount_reserved)   AS reserved_amount,
			SUM(COALESCE(amount_committed, 0)) AS committed_amount,
			SUM(COALESCE(amount_consumed, 0))  AS consumed_amount,
			SUM(amount_available)  AS available_amount
		FROM `tabBudget Line`
		WHERE budget IN %(names)s
			AND IFNULL(`is_active`, 1) = 1
		GROUP BY budget
		""",
		{"names": tuple(names)},
		as_dict=True,
	)
	line_by_budget = {r.budget: r for r in line_rows}

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
		flt(line_by_budget.get(b.name, {}).get("allocated_amount")) for b in budgets
	)
	# W1-02: portfolio KPI sums are scoped to Approved/Active budgets only
	_approved_active = frozenset(("Approved", "Active"))
	reserved_sum = sum(
		flt(line_by_budget.get(b.name, {}).get("reserved_amount"))
		for b in budgets if b.get("status") in _approved_active
	)
	committed_sum = sum(
		flt(line_by_budget.get(b.name, {}).get("committed_amount"))
		for b in budgets if b.get("status") in _approved_active
	)
	consumed_sum = sum(
		flt(line_by_budget.get(b.name, {}).get("consumed_amount"))
		for b in budgets if b.get("status") in _approved_active
	)
	available_sum = sum(
		flt(line_by_budget.get(b.name, {}).get("available_amount"))
		for b in budgets if b.get("status") in _approved_active
	)
	allocation_pct = (allocated_sum / total_budget_sum * 100.0) if total_budget_sum else 0.0

	plan_names = {b.strategic_plan for b in budgets if b.get("strategic_plan")}
	plan_titles: dict[str, str] = {}
	if plan_names:
		for row in frappe.get_all(
			"Strategic Plan",
			filters={"name": ["in", list(plan_names)]},
			fields=["name", "strategic_plan_name"],
			limit=5000,
		):
			plan_titles[row.name] = (row.strategic_plan_name or row.name or "").strip()

	entity_names_set = {b.get("procuring_entity") for b in budgets if b.get("procuring_entity")}
	entity_names: dict[str, str] = {}
	entity_codes: dict[str, str] = {}
	if entity_names_set:
		for row in frappe.get_all(
			"Procuring Entity",
			filters={"name": ["in", list(entity_names_set)]},
			fields=["name", "entity_name", "entity_code"],
			limit=5000,
		):
			entity_names[row.name] = (row.entity_name or row.name or "").strip()
			entity_codes[row.name] = (row.entity_code or "").strip()

	user_ids = set()
	for b in budgets:
		for key in ("submitted_by", "approved_by", "rejected_by"):
			if b.get(key):
				user_ids.add(b.get(key))
	user_labels: dict[str, str] = {}
	if user_ids:
		for row in frappe.get_all(
			"User",
			filters={"name": ["in", list(user_ids)]},
			fields=["name", "full_name"],
			limit=5000,
		):
			user_labels[row.name] = (row.full_name or row.name or "").strip()

	out_budgets = []
	for b in budgets:
		total = flt(b.get("total_budget_amount"))
		arow = line_by_budget.get(b.name)
		allocated_amount   = flt(arow.get("allocated_amount"))   if arow else 0.0
		reserved_amount    = flt(arow.get("reserved_amount"))    if arow else 0.0
		committed_amount   = flt(arow.get("committed_amount"))   if arow else 0.0
		consumed_amount    = flt(arow.get("consumed_amount"))    if arow else 0.0
		available_amount   = flt(arow.get("available_amount"))   if arow else 0.0
		budget_line_total       = int(arow.get("budget_line_total") or 0)     if arow else 0
		budget_lines_allocated  = int(arow.get("budget_lines_allocated") or 0) if arow else 0
		budget_lines_unallocated = max(0, budget_line_total - budget_lines_allocated)

		# Consumption = (reserved + committed + consumed) / allocated
		obligated = reserved_amount + committed_amount + consumed_amount
		consumption_pct = (obligated / allocated_amount * 100.0) if allocated_amount else 0.0
		consumption_pct = min(100.0, consumption_pct)

		# Derive health status for Approved/Active budgets
		status = b.get("status") or "Draft"
		if status in ("Approved", "Active"):
			if consumption_pct >= 90:
				health_status = "critical"
			elif consumption_pct >= 75:
				health_status = "reviewing"
			else:
				health_status = "healthy"
		elif status == "Submitted":
			health_status = "reviewing"
		elif status == "Rejected":
			health_status = "rejected"
		else:
			health_status = "draft"

		out_budgets.append(
			{
				"name": b.name,
				"budget_name": b.budget_name,
				"fiscal_year": b.fiscal_year,
				"status": status,
				"strategic_plan": b.get("strategic_plan"),
				"strategic_plan_title": plan_titles.get(b.get("strategic_plan"))
				or b.get("strategic_plan"),
				"currency": b.currency,
				"total_budget_amount": total,
			"procuring_entity": b.get("procuring_entity"),
			"procuring_entity_name": entity_names.get(b.get("procuring_entity"))
			or b.get("procuring_entity") or "",
			"procuring_entity_code": entity_codes.get(b.get("procuring_entity")) or "",
				"owner": b.get("owner"),
				"created_by": b.get("created_by"),
				"rejection_reason": b.get("rejection_reason"),
				"rejected_by": b.get("rejected_by"),
				"rejected_at": b.get("rejected_at"),
				"submitted_by": b.get("submitted_by"),
				"submitted_at": b.get("submitted_at"),
				"approved_by": b.get("approved_by"),
				"approved_at": b.get("approved_at"),
				"approved_by_label": user_labels.get(b.get("approved_by"))
				or b.get("approved_by"),
				"allocated_amount": allocated_amount,
				"reserved_amount": reserved_amount,
				"committed_amount": committed_amount,
				"consumed_amount": consumed_amount,
				"available_amount": available_amount,
				"remaining_amount": max(0.0, total - allocated_amount),
				"allocation_pct": (allocated_amount / total * 100.0) if total else 0.0,
				"consumption_pct": consumption_pct,
				"committed_pct": (committed_amount / allocated_amount * 100.0) if allocated_amount else 0.0,
				"reserved_pct": (reserved_amount / allocated_amount * 100.0) if allocated_amount else 0.0,
				"health_status": health_status,
				"budget_line_total": budget_line_total,
				"budget_lines_allocated": budget_lines_allocated,
				"budget_lines_unallocated": budget_lines_unallocated,
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
			"reserved_sum": reserved_sum,
			"committed_sum": committed_sum,
			"consumed_sum": consumed_sum,
			"available_sum": available_sum,
			"allocation_pct": allocation_pct,
		},
		"budgets": out_budgets,
	}
