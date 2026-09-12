# Copyright (c) 2026, KenTender and contributors
"""AUTH-ADR-001 v1.8 §8/§9 technical-read surface for Procurement Requisitions.

Registered through the `kt_technical_reference_resolvers` and
`kt_technical_read_probes` hooks (see kentender_procurement/hooks.py).

REQ-CHG-001 v1.6 §12 routes, all under the one "procurement-requisitions"
Page:
  - editor:              ["procurement-requisitions", requisition_reference]
  - authorised handoff:  ["procurement-requisitions", requisition_reference, "authorised"]
  - department task:     ["procurement-requisitions", "department-task", task_id]
  - procurement task:    ["procurement-requisitions", "procurement-task", task_id]

`Requisition Task` covers both the HoD and Procurement decision points; the
route depends on which business role the task was routed to
(`read.get_department_approval_task`/`get_procurement_authorisation_task`
distinguish the same way — "Head of User Department" vs the Head of
Procurement Function role).
"""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_requisitions import api

PAGE = "procurement-requisitions"
ROLE_HEAD_OF_USER_DEPARTMENT = "Head of User Department"


def _requisition_route(name: str) -> list[str]:
	reference = frappe.db.get_value("Procurement Requisition", name, "requisition_reference") or name
	return [PAGE, reference]


def _task_route(name: str) -> list[str]:
	business_role = frappe.db.get_value("Requisition Task", name, "business_role")
	segment = "department-task" if business_role == ROLE_HEAD_OF_USER_DEPARTMENT else "procurement-task"
	return [PAGE, segment, name]


def _handoff_route(name: str) -> list[str]:
	requisition = frappe.db.get_value("Authorised Requisition Handoff", name, "requisition")
	if not requisition:
		return [PAGE]
	reference = frappe.db.get_value("Procurement Requisition", requisition, "requisition_reference") or requisition
	return [PAGE, reference, "authorised"]


def reference_resolvers() -> list[dict]:
	return [
		{
			"doctype": "Procurement Requisition",
			"label": "Procurement Requisition",
			"reference_field": "requisition_reference",
			"title_field": "requisition_reference",
			"status_field": "current_state",
			"route": _requisition_route,
		},
		{
			"doctype": "Requisition Task",
			"label": "Requisition Task",
			"reference_field": "requisition",
			"title_field": "business_role",
			"status_field": "status",
			"route": _task_route,
		},
		{
			"doctype": "Authorised Requisition Handoff",
			"label": "Authorised Requisition Handoff",
			"reference_field": "requisition",
			"title_field": "handoff_digest",
			"status_field": None,
			"route": _handoff_route,
		},
	]


def _existing(doctype: str, filters: dict | None = None) -> str | None:
	rows = frappe.get_all(doctype, filters=filters or {}, limit=1, order_by="modified desc", pluck="name")
	return rows[0] if rows else None


def _first_where(doctype: str, filters: dict | None, probe_kwarg: str, probe_call) -> str | None:
	"""The single newest row of `doctype` matching `filters` can be one a
	test run left in a state the read contract masks as not-found (a
	since-wiped row, or one whose state has moved past that contract's own
	scope) — found live 2026-09-12, after a full Requisitions test run left
	the site's "newest" candidate in exactly that state on three separate
	probes. Self-validate against a few recent candidates, as Administrator
	already is at kwargs-computation time, rather than trusting the first
	one blindly."""
	for row in frappe.get_all(doctype, filters=filters or {}, order_by="modified desc", limit=20, pluck="name"):
		try:
			probe_call(**{probe_kwarg: row})
		except frappe.DoesNotExistError:
			continue
		return row
	return None


def _requisition_kwargs() -> dict | None:
	name = _first_where("Procurement Requisition", None, "requisition", api.get_requisition_editor)
	return {"requisition": name} if name else None


def _department_task_kwargs() -> dict | None:
	name = _first_where(
		"Requisition Task", {"business_role": ROLE_HEAD_OF_USER_DEPARTMENT}, "task", api.get_department_approval_task
	)
	return {"task": name} if name else None


def _procurement_task_kwargs() -> dict | None:
	name = _first_where(
		"Requisition Task", {"business_role": ["!=", ROLE_HEAD_OF_USER_DEPARTMENT]}, "task", api.get_procurement_authorisation_task
	)
	return {"task": name} if name else None


def _handoff_kwargs() -> dict | None:
	"""`get_authorised_requisition_handoff` is keyed by the owning
	Procurement Requisition, not the handoff record itself — find a
	Requisition whose `handoff` field is already populated."""
	name = _first_where(
		"Procurement Requisition", {"handoff": ["is", "set"]}, "requisition", api.get_authorised_requisition_handoff
	)
	return {"requisition": name} if name else None


def _plan_item_kwargs() -> dict | None:
	row = frappe.get_all("Annual Plan Item", fields=["plan_item_id"], limit=1, order_by="modified desc")
	return {"plan_item_id": row[0].plan_item_id} if row else None


def read_probes() -> list[dict]:
	return [
		{"label": "requisitions.get_requisition_workspace", "call": api.get_requisition_workspace, "kwargs": lambda: {}},
		{
			"label": "requisitions.get_eligible_plan_item_detail",
			"call": api.get_eligible_plan_item_detail,
			"kwargs": _plan_item_kwargs,
		},
		{"label": "requisitions.get_requisition_editor", "call": api.get_requisition_editor, "kwargs": _requisition_kwargs},
		{
			"label": "requisitions.get_department_approval_task",
			"call": api.get_department_approval_task,
			"kwargs": _department_task_kwargs,
		},
		{
			"label": "requisitions.get_procurement_authorisation_task",
			"call": api.get_procurement_authorisation_task,
			"kwargs": _procurement_task_kwargs,
		},
		{
			"label": "requisitions.get_authorised_requisition_handoff",
			"call": api.get_authorised_requisition_handoff,
			"kwargs": _handoff_kwargs,
		},
		{"label": "requisitions.get_requisition_history", "call": api.get_requisition_history, "kwargs": _requisition_kwargs},
		{"label": "requisitions.list_eligible_handoffs", "call": api.list_eligible_handoffs, "kwargs": lambda: {}},
	]
