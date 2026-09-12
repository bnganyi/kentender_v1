# Copyright (c) 2026, KenTender and contributors
"""AUTH-ADR-001 v1.8 §8/§9 technical-read surface for Departmental Needs.

Registered through the `kt_technical_reference_resolvers` and
`kt_technical_read_probes` hooks (see kentender_procurement/hooks.py).
Resolvers cover `Departmental Need` (identity, autonamed by its own
`need_reference`), `Departmental Need Revision` (a version — no route of
its own, resolves to the parent Need's detail page, KT-STD-001 v1.5 §3A.6)
and `Departmental Need Review Task`. §10's one Page ("departmental-needs")
carries every route.
"""

from __future__ import annotations

import frappe

from kentender_procurement.departmental_needs import api

PAGE = "departmental-needs"


def _need_route(name: str) -> list[str]:
	return [PAGE, name]


def _revision_route(name: str) -> list[str]:
	need = frappe.db.get_value("Departmental Need Revision", name, "departmental_need")
	return [PAGE, need] if need else [PAGE]


def _task_route(name: str) -> list[str]:
	return [PAGE, "review", name]


def reference_resolvers() -> list[dict]:
	return [
		{
			"doctype": "Departmental Need",
			"label": "Departmental Need",
			"reference_field": "need_reference",
			"title_field": "need_reference",
			"status_field": "current_state",
			"route": _need_route,
		},
		{
			"doctype": "Departmental Need Revision",
			"label": "Departmental Need Revision",
			"reference_field": "need_revision_id",
			"title_field": "title",
			"status_field": "revision_status",
			"route": _revision_route,
		},
		{
			"doctype": "Departmental Need Review Task",
			"label": "Departmental Need Review Task",
			"reference_field": "review_task_id",
			"title_field": "review_task_id",
			"status_field": "status",
			"route": _task_route,
		},
	]


def _existing(doctype: str, filters: dict | None = None) -> str | None:
	rows = frappe.get_all(doctype, filters=filters or {}, limit=1, order_by="modified desc", pluck="name")
	return rows[0] if rows else None


def _need_kwargs() -> dict | None:
	name = _existing("Departmental Need")
	return {"need": name} if name else None


def _accepted_need_kwargs() -> dict | None:
	name = _existing("Departmental Need", {"current_accepted_revision": ["is", "set"]})
	return {"need": name} if name else None


def _task_kwargs() -> dict | None:
	name = _existing("Departmental Need Review Task")
	return {"task": name} if name else None


def _withdrawal_dependency_kwargs() -> dict | None:
	row = frappe.get_all(
		"Departmental Need",
		filters={"current_accepted_revision": ["is", "set"]},
		fields=["name", "current_accepted_revision"],
		limit=1,
		order_by="modified desc",
	)
	if not row:
		return None
	return {"need": row[0].name, "accepted_revision": row[0].current_accepted_revision}


def read_probes() -> list[dict]:
	return [
		{"label": "needs.resolve_needs_scope", "call": api.resolve_needs_scope, "kwargs": lambda: {}},
		{"label": "needs.list_needs_financial_years", "call": api.list_needs_financial_years, "kwargs": lambda: {}},
		{"label": "needs.list_need_create_targets", "call": api.list_need_create_targets, "kwargs": lambda: {}},
		{"label": "needs.get_needs_workspace", "call": api.get_needs_workspace, "kwargs": lambda: {}},
		{"label": "needs.get_departmental_need", "call": api.get_departmental_need, "kwargs": _need_kwargs},
		{"label": "needs.get_departmental_review_task", "call": api.get_departmental_review_task, "kwargs": _task_kwargs},
		{"label": "needs.get_needs_submission_state", "call": api.get_needs_submission_state, "kwargs": lambda: {}},
		{"label": "needs.get_current_accepted_need", "call": api.get_current_accepted_need, "kwargs": _accepted_need_kwargs},
		{
			"label": "needs.check_accepted_need_withdrawal_dependency",
			"call": api.check_accepted_need_withdrawal_dependency,
			"kwargs": _withdrawal_dependency_kwargs,
		},
	]
