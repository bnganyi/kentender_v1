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
				"alignment_score_pct": 0.0,
				"previous_fy": None,
				"previous_period_available": None,
				"previous_period_reserved": None,
				"previous_period_committed": None,
				"previous_period_consumed": None,
				"delta_available_pct": None,
				"delta_reserved_pct": None,
				"delta_committed_pct": None,
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

	# W2-04: highest-allocated active Budget Line name per budget (for table subtitle)
	primary_line_rows = frappe.db.sql(
		"""
		SELECT budget, budget_line_name, amount_allocated
		FROM `tabBudget Line`
		WHERE budget IN %(names)s
			AND IFNULL(`is_active`, 1) = 1
			AND amount_allocated > 0
		ORDER BY budget, amount_allocated DESC
		""",
		{"names": tuple(names)},
		as_dict=True,
	)
	# Take the first (highest) row per budget — ORDER BY already sorted DESC
	primary_line_by_budget: dict[str, str] = {}
	for row in primary_line_rows:
		if row.budget not in primary_line_by_budget:
			primary_line_by_budget[row.budget] = row.budget_line_name or ""

	# W3-04: Portfolio alignment score — active lines with full hierarchy
	# (plan + program + sub_program all non-null) ÷ total active lines.
	alignment_row = frappe.db.sql(
		"""
		SELECT
		    COUNT(*)                                                        AS total_active,
		    SUM(CASE
		            WHEN strategic_plan IS NOT NULL AND strategic_plan != ''
		             AND program        IS NOT NULL AND program        != ''
		             AND sub_program    IS NOT NULL AND sub_program    != ''
		            THEN 1 ELSE 0
		        END)                                                        AS fully_aligned
		FROM `tabBudget Line`
		WHERE is_active = 1
		""",
		as_dict=True,
	)
	_alr = alignment_row[0] if alignment_row else {}
	_total_al   = int(_alr.get("total_active", 0) or 0)
	_aligned_al = int(_alr.get("fully_aligned", 0) or 0)
	alignment_score_pct = round((_aligned_al / _total_al) * 100.0, 1) if _total_al else 0.0


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

	# W3-05: Previous-period (FY − 1) aggregates for trend delta badges.
	# Determine current FY from the loaded budgets; stub all delta fields with
	# None when no matching lines exist for the prior year.
	_current_fy = max((b.get("fiscal_year") or 0) for b in budgets) if budgets else 0
	_prev_fy = _current_fy - 1 if _current_fy else None

	previous_fy              = None
	previous_period_available = None
	previous_period_reserved  = None
	previous_period_committed = None
	previous_period_consumed  = None
	delta_available_pct  = None
	delta_reserved_pct   = None
	delta_committed_pct  = None

	if _prev_fy:
		_prev_rows = frappe.db.sql(
			"""
			SELECT
			    COUNT(*)                                AS line_count,
			    SUM(amount_available)                   AS available_sum,
			    SUM(amount_reserved)                    AS reserved_sum,
			    SUM(COALESCE(amount_committed, 0))      AS committed_sum,
			    SUM(COALESCE(amount_consumed,  0))      AS consumed_sum
			FROM `tabBudget Line`
			WHERE fiscal_year = %s
			  AND is_active    = 1
			""",
			(_prev_fy,),
			as_dict=True,
		)
		_pr = _prev_rows[0] if _prev_rows else {}
		if (_pr.get("line_count") or 0) > 0:
			previous_fy               = _prev_fy
			previous_period_available = float(_pr.get("available_sum") or 0)
			previous_period_reserved  = float(_pr.get("reserved_sum")  or 0)
			previous_period_committed = float(_pr.get("committed_sum") or 0)
			previous_period_consumed  = float(_pr.get("consumed_sum")  or 0)

			def _delta_pct(curr, prev_v):
				return round((curr - prev_v) / prev_v * 100.0, 1) if prev_v else None

			delta_available_pct = _delta_pct(available_sum, previous_period_available)
			delta_reserved_pct  = _delta_pct(reserved_sum,  previous_period_reserved)
			delta_committed_pct = _delta_pct(committed_sum, previous_period_committed)


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

		# W2-03: health_status — available ÷ allocated ratio with defined thresholds.
		# Thresholds: < 8% → exhausted, 8–20% → reviewing, > 20% → healthy.
		# Non-Approved/Active statuses use their workflow state.
		status = b.get("status") or "Draft"
		if status in ("Approved", "Active"):
			if allocated_amount > 0:
				avail_pct = available_amount / allocated_amount * 100.0
			else:
				avail_pct = 100.0  # no lines yet → treat as fully available
			if avail_pct < 8.0:
				health_status = "exhausted"
			elif avail_pct <= 20.0:
				health_status = "reviewing"
			else:
				health_status = "healthy"
		elif status == "Submitted":
			health_status = "submitted"
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
			"avail_pct": (available_amount / allocated_amount * 100.0) if allocated_amount else 100.0,
			"committed_pct": (committed_amount / allocated_amount * 100.0) if allocated_amount else 0.0,
			"reserved_pct": (reserved_amount / allocated_amount * 100.0) if allocated_amount else 0.0,
			"health_status": health_status,
			"budget_line_total": budget_line_total,
			"budget_lines_allocated": budget_lines_allocated,
			"budget_lines_unallocated": budget_lines_unallocated,
			"primary_line_name": primary_line_by_budget.get(b.name, ""),
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
			"alignment_score_pct": alignment_score_pct,
			"previous_fy": previous_fy,
			"previous_period_available": previous_period_available,
			"previous_period_reserved": previous_period_reserved,
			"previous_period_committed": previous_period_committed,
			"previous_period_consumed": previous_period_consumed,
			"delta_available_pct": delta_available_pct,
			"delta_reserved_pct": delta_reserved_pct,
			"delta_committed_pct": delta_committed_pct,
		},
		"budgets": out_budgets,
	}
