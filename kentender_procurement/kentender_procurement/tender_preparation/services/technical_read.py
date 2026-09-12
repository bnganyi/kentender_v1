# Copyright (c) 2026, KenTender and contributors
"""AUTH-ADR-001 v1.8 §8/§9 technical-read surface for Tender Preparation.

Registered through the `kt_technical_reference_resolvers` and
`kt_technical_read_probes` hooks (see kentender_procurement/hooks.py).

The one "tender-preparation" Page carries every route:
  - editor:          ["tender-preparation", tender_reference]
  - approved view:   ["tender-preparation", tender_reference, "approved"]
  - approval task:   ["tender-preparation", "task", task_id]
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_preparation import api

PAGE = "tender-preparation"


def _tender_route(name: str) -> list[str]:
	reference = frappe.db.get_value("Prepared Tender", name, "tender_reference") or name
	return [PAGE, reference]


def _task_route(name: str) -> list[str]:
	return [PAGE, "task", name]


def reference_resolvers() -> list[dict]:
	return [
		{
			"doctype": "Prepared Tender",
			"label": "Prepared Tender",
			"reference_field": "tender_reference",
			"title_field": "tender_reference",
			"status_field": "current_state",
			"route": _tender_route,
		},
		{
			"doctype": "Tender Preparation Task",
			"label": "Tender Preparation Task",
			"reference_field": "tender",
			"title_field": "business_role",
			"status_field": "status",
			"route": _task_route,
		},
	]


def _existing(doctype: str, filters: dict | None = None) -> str | None:
	rows = frappe.get_all(doctype, filters=filters or {}, limit=1, order_by="modified desc", pluck="name")
	return rows[0] if rows else None


def _tender_kwargs() -> dict | None:
	name = _existing("Prepared Tender")
	return {"tender": name} if name else None


def _approved_tender_kwargs() -> dict | None:
	name = _existing("Prepared Tender", {"current_state": "Approved"})
	return {"tender": name} if name else None


def _task_kwargs() -> dict | None:
	name = _existing("Tender Preparation Task")
	return {"task": name} if name else None


def _preview_kwargs() -> dict | None:
	name = _existing("Prepared Tender")
	return {"tender": name, "output": "invitation"} if name else None


def _handoff_kwargs() -> dict | None:
	name = _existing("Authorised Requisition Handoff", {"consumed_at": ["is", "not set"]})
	return {"handoff": name} if name else None


def read_probes() -> list[dict]:
	return [
		{
			"label": "tender_preparation.get_tender_preparation_workspace",
			"call": api.get_tender_preparation_workspace,
			"kwargs": lambda: {},
		},
		{"label": "tender_preparation.get_tender_compatibility", "call": api.get_tender_compatibility, "kwargs": _handoff_kwargs},
		{"label": "tender_preparation.get_tender_editor", "call": api.get_tender_editor, "kwargs": _tender_kwargs},
		{"label": "tender_preparation.get_tender_approval_task", "call": api.get_tender_approval_task, "kwargs": _task_kwargs},
		{"label": "tender_preparation.get_approved_tender", "call": api.get_approved_tender, "kwargs": _approved_tender_kwargs},
		{"label": "tender_preparation.get_tender_history", "call": api.get_tender_history, "kwargs": _tender_kwargs},
		{"label": "tender_preparation.get_tender_preview", "call": api.get_tender_preview, "kwargs": _preview_kwargs},
	]
