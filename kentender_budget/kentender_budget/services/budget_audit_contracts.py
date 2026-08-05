# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget Audit History — BUD-UI-12 / Pack Phase 8 / get_budget_audit."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import format_datetime, get_datetime, getdate, now_datetime

from kentender_budget.services.budget_contracts import _resolve_budget, resolve_scoped_entity
from kentender_budget.services.budget_permissions import (
	ROLE_AUDITOR,
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_VIEWER,
	require_any_role,
)

_READ_ROLES = (ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_VIEWER, ROLE_AUDITOR)

EVENT_BASELINE = "Baseline registered"
EVENT_SUBMITTED = "Budget submitted"
EVENT_RETURNED = "Budget returned"
EVENT_REVIEWED = "Budget reviewed"
EVENT_ACTIVATED = "Budget activated"
EVENT_RESERVED = "Funding reserved"
EVENT_PARTIAL = "Reservation partially converted"
EVENT_COMMITMENT = "Contract commitment recorded"
EVENT_EXPENDITURE = "Expenditure snapshot recorded"
EVENT_REVISION = "Revision applied"


def record_event(
	*,
	budget: str,
	event_type: str,
	record_code: str,
	actor: str | None = None,
	actor_kind: str = "user",
	record_doctype: str = "",
	before_summary: str = "",
	after_summary: str = "",
	change_summary: str = "",
	source_reference: str = "",
	reason: str = "",
	event_at=None,
	budget_line: str | None = None,
	fixture_namespace: str = "",
) -> str | None:
	"""Insert an immutable Budget Audit Event. Returns name or None if DocType missing."""
	if not frappe.db.exists("DocType", "Budget Audit Event"):
		return None
	budget_name = budget
	if not frappe.db.exists("Budget", budget_name):
		# Allow business code.
		resolved = frappe.db.get_value("Budget", {"generated_reference": budget}, "name")
		if not resolved:
			return None
		budget_name = resolved

	summary = (change_summary or "").strip()
	if not summary:
		if before_summary and after_summary:
			summary = f"{before_summary} → {after_summary}"
		else:
			summary = after_summary or before_summary or event_type

	doc = frappe.get_doc(
		{
			"doctype": "Budget Audit Event",
			"budget": budget_name,
			"budget_line": budget_line or None,
			"event_type": event_type,
			"event_at": event_at or now_datetime(),
			"actor": (actor or frappe.session.user or "System").strip(),
			"actor_kind": actor_kind if actor_kind in ("user", "system", "integration") else "user",
			"record_code": (record_code or "").strip(),
			"record_doctype": (record_doctype or "").strip(),
			"before_summary": before_summary or "",
			"after_summary": after_summary or "",
			"change_summary": summary,
			"source_reference": source_reference or "",
			"reason": reason or "",
			"fixture_namespace": fixture_namespace or "",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def safe_record_event(**kwargs) -> str | None:
	"""Best-effort record; never break the calling mutation."""
	try:
		return record_event(**kwargs)
	except Exception:
		frappe.log_error(title="Budget audit record_event failed")
		return None


def get_budget_audit(
	budget: str,
	event_type: str | None = None,
	actor: str | None = None,
	date_from: str | None = None,
	date_to: str | None = None,
) -> dict[str, Any]:
	"""Return filtered read-only audit ledger for a Budget."""
	require_any_role(*_READ_ROLES)
	doc = _resolve_budget(budget)
	resolve_scoped_entity(doc.procuring_entity)

	if not frappe.db.exists("DocType", "Budget Audit Event"):
		return _empty_dto(doc)

	filters: dict[str, Any] = {"budget": doc.name}
	if (event_type or "").strip():
		filters["event_type"] = event_type.strip()
	if (actor or "").strip():
		filters["actor"] = ["like", f"%{actor.strip()}%"]

	rows = frappe.get_all(
		"Budget Audit Event",
		filters=filters,
		fields=[
			"name",
			"event_type",
			"event_at",
			"actor",
			"actor_kind",
			"record_code",
			"record_doctype",
			"before_summary",
			"after_summary",
			"change_summary",
			"source_reference",
			"reason",
		],
		order_by="event_at desc, creation desc",
	)

	# Date range filter in Python (Datetime compare).
	df = getdate(date_from) if date_from else None
	dt = getdate(date_to) if date_to else None
	out_rows = []
	for r in rows:
		ea = get_datetime(r.event_at) if r.event_at else None
		if df and ea and ea.date() < df:
			continue
		if dt and ea and ea.date() > dt:
			continue
		out_rows.append(_row_dto(r))

	actors = sorted({(r.get("actor") or "").strip() for r in out_rows if (r.get("actor") or "").strip()})
	event_types = sorted(
		{(r.get("event_type") or "").strip() for r in out_rows if (r.get("event_type") or "").strip()}
	)
	# Prefer full filter option lists from unfiltered set when filters applied.
	all_types = frappe.get_all(
		"Budget Audit Event",
		filters={"budget": doc.name},
		pluck="event_type",
		distinct=True,
	)
	all_actors = frappe.get_all(
		"Budget Audit Event",
		filters={"budget": doc.name},
		pluck="actor",
		distinct=True,
	)

	return {
		"budget": {
			"id": doc.name,
			"code": doc.generated_reference,
			"name": doc.title,
			"title": doc.title,
			"status": doc.status,
			"status_label": "Under review" if doc.status == "Submitted" else doc.status,
			"currency": doc.currency or "KES",
			"procuring_entity": doc.procuring_entity,
		},
		"rows": out_rows,
		"row_count": len(out_rows),
		"pagination": {
			"showing_from": 1 if out_rows else 0,
			"showing_to": len(out_rows),
			"total": len(out_rows),
			"label": (
				f"Showing 1 to {len(out_rows)} of {len(out_rows)} entries"
				if out_rows
				else "Showing 0 entries"
			),
		},
		"filters": {
			"event_types": sorted({(t or "").strip() for t in all_types if t}) or event_types,
			"actors": sorted({(a or "").strip() for a in all_actors if a}) or actors,
		},
		"capabilities": {
			"read_only": True,
			"can_export": True,
			"view_funding_performance": True,
			"primary_action": "request_revision" if doc.status == "Active" else "",
			"primary_label": "Request revision" if doc.status == "Active" else "",
		},
	}


def _empty_dto(doc) -> dict[str, Any]:
	return {
		"budget": {
			"id": doc.name,
			"code": doc.generated_reference,
			"name": doc.title,
			"title": doc.title,
			"status": doc.status,
			"status_label": doc.status,
			"currency": doc.currency or "KES",
			"procuring_entity": doc.procuring_entity,
		},
		"rows": [],
		"row_count": 0,
		"pagination": {
			"showing_from": 0,
			"showing_to": 0,
			"total": 0,
			"label": "Showing 0 entries",
		},
		"filters": {"event_types": [], "actors": []},
		"capabilities": {"read_only": True, "can_export": True},
	}


def _row_dto(r) -> dict[str, Any]:
	ea = get_datetime(r.event_at) if r.event_at else None
	change = (r.change_summary or "").strip()
	if not change and (r.before_summary or r.after_summary):
		change = f"{r.before_summary or '—'} → {r.after_summary or '—'}"
	return {
		"id": r.name,
		"event_type": r.event_type or "",
		"event_at": str(r.event_at) if r.event_at else "",
		"event_at_display": format_datetime(ea) if ea else "—",
		"actor": r.actor or "",
		"actor_kind": r.actor_kind or "user",
		"record_code": r.record_code or "",
		"record_doctype": r.record_doctype or "",
		"before_summary": r.before_summary or "",
		"after_summary": r.after_summary or "",
		"change_summary": change,
		"change_summary_display": change,
		"source_reference": r.source_reference or "",
		"reason": r.reason or "",
		"action_label": "View",
	}
