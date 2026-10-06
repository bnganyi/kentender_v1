# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD v1.12 §6 / BUD18-AC-062 (AUD-BUD-002) — the immutable per-attempt
submission record. `submit_budget_version` opens one `Budget Submission
Attempt` carrying the evidence and every line as submitted; Return or Approve
records the single decision on it. Re-editing the same Draft and resubmitting
opens the next attempt, so no earlier attempt's content, attachment or
decision is overwritten. No-self-approval reads the latest attempt."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_budget.services.budget_locking import locked_doc


def _lines_snapshot(version_name: str) -> list[dict[str, Any]]:
	rows = frappe.db.sql(
		"select budget_line, title, owner_org_unit, funding_source, approved_amount "
		"from `tabProcurement Budget Line Version` where budget_version = %s order by budget_line for update",
		(version_name,),
		as_dict=True,
	)
	return [
		{
			"budget_line": r.budget_line,
			"title": r.title,
			"owner_org_unit": r.owner_org_unit or "",
			"funding_source": r.funding_source,
			"approved_amount": flt(r.approved_amount),
		}
		for r in rows
	]


def open_attempt(version) -> Any:
	"""Record this submission of `version` (call inside the Budget lock)."""
	number = (
		frappe.db.sql(
			"select coalesce(max(attempt_number), 0) from `tabBudget Submission Attempt` where budget_version = %s for update",
			(version.name,),
		)[0][0]
		+ 1
	)
	doc = frappe.get_doc(
		{
			"doctype": "Budget Submission Attempt",
			"budget_version": version.name,
			"budget": version.budget,
			"attempt_number": number,
			"submitted_by": frappe.session.user,
			"submitted_at": version.submitted_at or now_datetime(),
			"approval_reference": version.approval_reference,
			"approval_date": version.approval_date,
			"authorised_total": version.authorised_total,
			"currency": version.currency,
			"revision_type": version.revision_type,
			"approval_document": version.approval_document,
			"lines_snapshot": json.dumps(_lines_snapshot(version.name), sort_keys=True),
			"outcome": "Submitted",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def latest_attempt(version_name: str, *, for_update: bool = False) -> Any | None:
	suffix = " for update" if for_update else ""
	rows = frappe.db.sql(
		"select name from `tabBudget Submission Attempt` where budget_version = %s order by attempt_number desc limit 1" + suffix,
		(version_name,),
	)
	return frappe.get_doc("Budget Submission Attempt", rows[0][0], for_update=for_update) if rows else None


def record_decision(version, outcome: str, reason: str = "") -> None:
	"""Set the one decision on the version's open (latest, undecided) attempt."""
	attempt = latest_attempt(version.name, for_update=True)
	if not attempt or attempt.outcome != "Submitted":
		return
	attempt = locked_doc("Budget Submission Attempt", attempt.name)
	attempt.outcome = outcome
	attempt.decided_by = frappe.session.user
	attempt.decided_at = now_datetime()
	attempt.return_reason = reason or ""
	attempt.save(ignore_permissions=True)


def attempts_for_history(version_name: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Budget Submission Attempt",
		filters={"budget_version": version_name},
		fields=[
			"name", "attempt_number", "submitted_by", "submitted_at", "approval_reference", "approval_date",
			"authorised_total", "approval_document", "lines_snapshot", "outcome", "decided_by", "decided_at", "return_reason",
		],
		order_by="attempt_number desc",
	)
	out = []
	for r in rows:
		try:
			lines = json.loads(r.lines_snapshot or "[]")
		except ValueError:
			lines = []
		out.append({**r, "submitted_at": cstr(r.submitted_at), "decided_at": cstr(r.decided_at), "approval_date": cstr(r.approval_date), "lines": lines})
		out[-1].pop("lines_snapshot", None)
	return out
