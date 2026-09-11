# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget & Funding rows for the shared My Work queue.

BUD-CHG-001 v1.6 §10 names an "Approval tasks" entry visible only to a
Budget Approver. Work queues are never module sidebar entries in this
product (NDS FU-14, the same decision Departmental Needs and Procurement
Planning already follow): the Approver's open decisions reach them through
the shared My Work queue, published via kentender_core's
`kt_my_work_providers` hook — core collects, this app publishes, core never
imports this app — and through the Budget workspace's own server-decided
`pending_version` action.

Eligibility mirrors the approval-task screen exactly: the caller holds an
Enabled Site-wide Budget Approver assignment (AUTH-ADR-001 v1.6) and is not
the version's own submitter (§6 no-self-approval, read from the submission
audit event). A version a caller may not decide is not disclosed.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_budget.services.budget_authorization import (
	CAP_APPROVE,
	ROLE_BUDGET_APPROVER,
	has_budget_version_capability,
)


def _row(version: Any, budget: Any) -> dict[str, Any]:
	successor = bool(version.based_on_budget_version)
	return {
		"task_id": version.name,
		"task_type": "budget.approve",
		"title": _("Approve budget version — {0}").format(cstr(budget.title)),
		"reference": cstr(version.generated_reference),
		"module": "Budget & Funding",
		"stage": _("Revision approval") if successor else _("Initial baseline approval"),
		"financial_year": cstr(budget.fiscal_year),
		"organisation_unit": "",
		"assignment": _(ROLE_BUDGET_APPROVER),
		"status": _("Assigned"),
		"received_at": cstr(version.submitted_at or ""),
		"due_at": "",
		"action_label": _("Open approval task"),
		"route": ["budget-funding", "review", version.name],
		"route_options": {},
		"concurrency_token": cstr(version.modified),
		"can_claim": False,
		"can_open": True,
	}


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	"""`kt_my_work_providers` entry: the caller's open Budget approval
	decisions. Role-assigned work has no claim step — any Budget Approver may
	decide, and `approve_budget_version`'s own record-version check
	serialises concurrent decisions — so every row lands in "assigned"."""
	empty: dict[str, list[dict[str, Any]]] = {"assigned": [], "claimable": [], "waiting": []}
	if user in ("Guest", ""):
		return empty
	if ROLE_BUDGET_APPROVER not in frappe.get_roles(user):
		return empty
	versions = frappe.get_all(
		"Procurement Budget Version",
		filters={"status": "Submitted for approval"},
		fields=["name", "generated_reference", "budget", "based_on_budget_version", "submitted_at", "modified"],
		order_by="submitted_at asc, creation asc",
	)
	rows = []
	for version in versions:
		# Real assignment + no-self-approval, the same gate the task screen's
		# Approve button uses.
		if not has_budget_version_capability(user, CAP_APPROVE, version.name):
			continue
		budget = frappe.db.get_value(
			"Procurement Budget", version.budget, ["title", "fiscal_year"], as_dict=True
		)
		if not budget:
			continue
		rows.append(_row(version, budget))
	empty["assigned"] = rows
	return empty
