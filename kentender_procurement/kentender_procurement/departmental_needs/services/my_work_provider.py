"""Departmental Needs rows for the shared My Work queue.

The reviewer's open decisions (§4.4 review tasks) reach them through the
established My Work queue and notification mechanism, not through a module
sidebar entry (§10). The protected review-task record, its permissions and
the decision screens are unchanged — this module only *projects* the open
tasks into My Work via kentender_core's `kt_my_work_providers` hook, which is
the sanctioned direction (core collects, this app publishes; core never
imports this app).

Eligibility mirrors the workspace's row actions exactly (§12.2 via
`workspace._actions`): the caller holds an active Head of User Department
responsibility assignment (AUTH-ADR-001 v1.6) covering the task's exact
Organisation Unit, and is not the Need's own author (maker-checker, NDS-AC-042).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.departmental_needs.constants import (
	ROLE_HEAD_OF_USER_DEPARTMENT,
	TASK_OPEN,
	TASK_WITHDRAWAL,
)
from kentender_procurement.departmental_needs.services.permissions import in_scope


def _row(task: Any, need: Any) -> dict[str, Any]:
	withdrawal = task.task_type == TASK_WITHDRAWAL
	title = (
		cstr(frappe.db.get_value("Departmental Need Version", task.need_version, "title"))
		if task.need_version
		else ""
	)
	route = ["departmental-needs", "review", task.name]
	if withdrawal:
		route.append("withdrawal")
	return {
		"task_id": task.name,
		"task_type": "needs.withdrawal" if withdrawal else "needs.review",
		"title": title or cstr(need.need_reference),
		"reference": cstr(need.need_reference),
		"module": "Departmental Needs",
		"stage": _("Withdrawal review") if withdrawal else _("Departmental review"),
		"financial_year": cstr(task.financial_year),
		"organisation_unit": cstr(task.organisation_unit or ""),
		"assignment": _(ROLE_HEAD_OF_USER_DEPARTMENT),
		"status": _("Assigned"),
		"received_at": cstr(task.opened_at),
		"due_at": "",
		"action_label": _("Review withdrawal") if withdrawal else _("Review need"),
		"route": route,
		"route_options": {},
		"concurrency_token": cstr(task.decision_token),
		"can_claim": False,
		"can_open": True,
	}


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	"""`kt_my_work_providers` entry: the caller's open departmental decisions.

	Role-assigned work has no claim step — any in-scope HoD may decide, and the
	task's decision token already serialises concurrent decisions — so every
	row lands in the "assigned" bucket.
	"""
	empty: dict[str, list[dict[str, Any]]] = {"assigned": [], "claimable": [], "waiting": []}
	if user in ("Guest", ""):
		return empty
	if ROLE_HEAD_OF_USER_DEPARTMENT not in frappe.get_roles(user):
		return empty
	tasks = frappe.get_all(
		"Departmental Need Review Task",
		filters={"status": TASK_OPEN},
		fields=[
			"name",
			"departmental_need",
			"need_version",
			"task_type",
			"organisation_unit",
			"financial_year",
			"decision_token",
			"opened_at",
		],
		order_by="opened_at asc",
	)
	rows = []
	for task in tasks:
		if not in_scope(
			user,
			business_role=ROLE_HEAD_OF_USER_DEPARTMENT,
			organisation_unit=task.organisation_unit,
		):
			continue
		need = frappe.db.get_value(
			"Departmental Need",
			task.departmental_need,
			["name", "need_reference", "owner"],
			as_dict=True,
		)
		if not need or cstr(need.owner) == cstr(user):
			continue
		rows.append(_row(task, need))
	empty["assigned"] = rows
	return empty
