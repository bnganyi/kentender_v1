# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""Critical Guardrails — proactive budget health checks for the hub panel.

Three checks (per W3-02 spec):
  low_balance       (error)   — active line with available < 15% of allocated
  unlinked_strategy (warning) — active lines missing Strategic Program link
  expiry            (warning) — budgets whose closing_date falls within 30 days

Each result item carries:
  severity     : "error" | "warning"
  check_type   : "low_balance" | "unlinked_strategy" | "expiry"
  title        : human label
  description  : one-line explanation with numbers
  action_label : CTA text for the action button
  budget_line  : Budget Line name (str | None)
  budget       : Budget name (str | None)
"""
from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, today

_LOW_BALANCE_THRESHOLD = 0.15  # < 15% available triggers error
_EXPIRY_DAYS = 30              # closing_date within N days triggers warning
_MAX_LOW_BALANCE = 10          # cap individual low-balance cards


@frappe.whitelist()
def compute_budget_guardrails() -> dict:
	"""Evaluate active budget health and return guardrail items sorted by severity."""
	if not frappe.has_permission("Budget", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	guardrails: list[dict] = []

	# ── 1. Low balance: active lines on current-version budgets ───────────────
	low_rows = frappe.db.sql(
		"""
		SELECT
			bl.name         AS budget_line,
			bl.budget_line_name,
			bl.amount_allocated,
			bl.amount_available,
			bl.budget,
			b.budget_name
		FROM `tabBudget Line` bl
		INNER JOIN `tabBudget` b ON b.name = bl.budget
		WHERE bl.is_active = 1
		  AND bl.amount_allocated > 0
		  AND (bl.amount_available / bl.amount_allocated) < %(threshold)s
		  AND b.is_current_version = 1
		ORDER BY (bl.amount_available / bl.amount_allocated) ASC
		LIMIT %(limit)s
		""",
		{"threshold": _LOW_BALANCE_THRESHOLD, "limit": _MAX_LOW_BALANCE},
		as_dict=True,
	)
	for r in low_rows:
		avail_pct = flt(r.amount_available) / flt(r.amount_allocated) * 100.0
		guardrails.append({
			"severity": "error",
			"check_type": "low_balance",
			"title": f"Low Balance: {r.budget_line_name or r.budget_line}",
			"description": (
				f"Available funds at {avail_pct:.0f}% of allocation "
				f"(threshold: {_LOW_BALANCE_THRESHOLD * 100:.0f}%). "
				"Planned tender releases may be blocked."
			),
			"action_label": "Review",
			"budget_line": r.budget_line,
			"budget": r.budget,
		})

	# ── 2. Unlinked strategy: active lines missing program link ───────────────
	unlinked_rows = frappe.db.sql(
		"""
		SELECT
			bl.name         AS budget_line,
			bl.budget_line_name,
			bl.budget,
			b.budget_name
		FROM `tabBudget Line` bl
		INNER JOIN `tabBudget` b ON b.name = bl.budget
		WHERE bl.is_active = 1
		  AND (bl.program IS NULL OR bl.program = '')
		  AND b.is_current_version = 1
		ORDER BY bl.creation ASC
		LIMIT 100
		""",
		as_dict=True,
	)
	if unlinked_rows:
		count = len(unlinked_rows)
		if count == 1:
			r = unlinked_rows[0]
			title = f"Unlinked Strategy: {r.budget_line_name or r.budget_line}"
			desc = (
				f"Budget line lacks a Strategic Program mapping. "
				"Audit compliance risk detected."
			)
			budget_line = r.budget_line
			budget = r.budget
		else:
			title = f"Unlinked Strategy: {count} Budget Lines"
			desc = (
				f"{count} active budget line(s) lack a Strategic Program mapping. "
				"Audit compliance risk detected."
			)
			budget_line = unlinked_rows[0].budget_line
			budget = unlinked_rows[0].budget
		guardrails.append({
			"severity": "warning",
			"check_type": "unlinked_strategy",
			"title": title,
			"description": desc,
			"action_label": "Fix Link",
			"budget_line": budget_line,
			"budget": budget,
		})

	# ── 3. Budget expiry: closing_date within the next N days ─────────────────
	today_date = getdate(today())
	deadline   = add_days(today_date, _EXPIRY_DAYS)
	expiry_rows = frappe.db.sql(
		"""
		SELECT
			b.name,
			b.budget_name,
			b.closing_date,
			b.status
		FROM `tabBudget` b
		WHERE b.closing_date IS NOT NULL
		  AND b.closing_date >= %(today)s
		  AND b.closing_date <= %(deadline)s
		  AND b.is_current_version = 1
		ORDER BY b.closing_date ASC
		LIMIT 10
		""",
		{"today": today_date, "deadline": deadline},
		as_dict=True,
	)
	for r in expiry_rows:
		days_left = (getdate(r.closing_date) - today_date).days
		guardrails.append({
			"severity": "warning",
			"check_type": "expiry",
			"title": f"Expiring Soon: {r.budget_name}",
			"description": (
				f"Budget expires in {days_left} day(s) "
				f"(closing date: {r.closing_date}). "
				"Ensure all obligations are finalised."
			),
			"action_label": "Review",
			"budget_line": None,
			"budget": r.name,
		})

	# errors first, then warnings
	guardrails.sort(key=lambda g: (0 if g["severity"] == "error" else 1))
	return {"guardrails": guardrails}
