# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Planning rows for the shared My Work queue (§10).

Planning has exactly one navigation entry; actionable decisions reach their
actors through the workspace, this My Work projection and notifications —
never a sidebar work-queue entry (PLN-AC-059, NDS FU-14 precedent). Core
collects providers through the `kt_my_work_providers` hook; core never
imports this app.

Eligibility mirrors the decision commands exactly (the read-offer parity
rule): a row appears only for an actor the command layer would accept.
Phase 3 projects DPP validation tasks; the Finance and governance task rows
are appended by their own slices (Phases 7–8) alongside their commands.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.procurement_planning.services.authority import (
	has_role,
	permitted_org_units,
	permitted_pes,
)
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_PROCUREMENT_PLANNER,
)


def _validation_rows(user: str) -> list[dict[str, Any]]:
	if not has_role(user, ROLE_PROCUREMENT_PLANNER):
		return []
	pes = permitted_pes(user)
	if not pes:
		return []
	ous = permitted_org_units(user)
	tasks = frappe.get_all(
		"Departmental Plan Validation Task",
		filters={"status": "Open", "procuring_entity": ("in", sorted(pes))},
		fields=[
			"name", "task_reference", "submission", "procuring_entity",
			"organisation_unit", "financial_year", "task_token", "creation",
		],
		order_by="creation asc",
		limit_page_length=0,
	)
	rows = []
	for task in tasks:
		if ous and cstr(task.organisation_unit) not in ous:
			continue
		submitted_by = cstr(
			frappe.db.get_value(
				"Departmental Plan Submission", task.submission, "submitted_by_user"
			)
		)
		if submitted_by == user:
			# §6.1 — the certifier never validates their own submission.
			continue
		department = cstr(
			frappe.db.get_value(
				"Organisation Unit", task.organisation_unit, "unit_name"
			)
			or task.organisation_unit
		)
		rows.append(
			{
				"task_id": task.name,
				"task_type": "planning.dpp_validation",
				"title": _("Validate {0} departmental plan").format(department),
				"reference": cstr(task.task_reference),
				"module": "Procurement Planning",
				"stage": _("Departmental plan validation"),
				"procuring_entity": cstr(task.procuring_entity),
				"financial_year": cstr(task.financial_year),
				"organisation_unit": cstr(task.organisation_unit),
				"assignment": _(ROLE_PROCUREMENT_PLANNER),
				"status": _("Assigned"),
				"received_at": cstr(task.creation),
				"due_at": "",
				"action_label": _("Review departmental plan"),
				"route": ["procurement-planning", "dpp-review", task.name],
				"route_options": {},
				"concurrency_token": cstr(task.task_token),
				"can_claim": False,
				"can_open": True,
			}
		)
	return rows


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	"""`kt_my_work_providers` entry: the caller's open Planning decisions."""
	return {"assigned": _validation_rows(user), "claimable": [], "waiting": []}
