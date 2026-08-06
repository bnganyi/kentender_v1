# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-SUP-005 — shared Funding Lifecycle read model (no separate journal DocType)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, get_datetime, getdate

from kentender_budget.services.budget_audit_contracts import (
	EVENT_COMMITMENT,
	EVENT_EXPENDITURE,
	EVENT_PARTIAL,
	EVENT_RESERVED,
)
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

# Audit event types that pair with domain DocTypes (dedup against domain rows).
_DOMAIN_AUDIT_TYPES = frozenset(
	{
		EVENT_RESERVED,
		EVENT_PARTIAL,
		EVENT_COMMITMENT,
		EVENT_EXPENDITURE,
	}
)

_AUDIT_TO_DOMAIN_DOCTYPE = {
	EVENT_RESERVED: "Funding Reservation",
	EVENT_PARTIAL: "Funding Reservation",
	EVENT_COMMITMENT: "Procurement Commitment",
	EVENT_EXPENDITURE: "Expenditure Snapshot",
}


def list_funding_lifecycle(
	budget: str,
	filters: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""Normalize authoritative lifecycle/audit records into one ordered event stream."""
	require_any_role(*_READ_ROLES)
	doc = _resolve_budget(budget)
	resolve_scoped_entity(doc.procuring_entity)
	if isinstance(filters, str):
		filters = frappe.parse_json(filters) if filters else {}
	filters = filters or {}

	currency = doc.currency or "KES"
	domain_events = _load_domain_events(doc.name, currency)
	audit_events = _load_audit_events(doc.name)
	events = _merge_dedup(domain_events, audit_events)
	events = _apply_filters(events, filters)
	events.sort(
		key=lambda e: (
			e.get("event_at_sort") or "",
			e.get("event_type") or "",
			e.get("source_code") or e.get("event_id") or "",
		),
		reverse=True,
	)

	return {
		"budget": {
			"id": doc.name,
			"code": doc.generated_reference,
			"name": doc.title,
			"title": doc.title,
			"status": doc.status,
			"status_label": "Under review" if doc.status == "Submitted" else doc.status,
			"currency": currency,
			"procuring_entity": doc.procuring_entity,
		},
		"events": events,
		"event_count": len(events),
	}


def _load_domain_events(budget_name: str, currency: str) -> list[dict[str, Any]]:
	events: list[dict[str, Any]] = []

	if frappe.db.exists("DocType", "Funding Reservation"):
		for r in frappe.get_all(
			"Funding Reservation",
			filters={"budget": budget_name},
			fields=[
				"name",
				"generated_reference",
				"budget_line",
				"demand_code",
				"demand_title",
				"plan_item_code",
				"original_amount",
				"remaining_reserved",
				"status",
				"event_date",
				"current_downstream_reference",
				"idempotency_key",
				"currency",
			],
		):
			ev_date = r.event_date
			sort = str(getdate(ev_date)) if ev_date else ""
			events.append(
				{
					"event_id": f"domain:Funding Reservation:{r.name}",
					"event_type": EVENT_RESERVED
					if (r.status or "") != "Partially converted"
					else EVENT_PARTIAL,
					"event_at": str(ev_date) if ev_date else "",
					"event_at_sort": sort,
					"budget": budget_name,
					"budget_line": r.budget_line or "",
					"source_doctype": "Funding Reservation",
					"source_name": r.name,
					"source_code": r.generated_reference or r.name,
					"downstream_module": "Demand",
					"downstream_reference": r.demand_code or "",
					"amount": flt(r.original_amount),
					"currency": r.currency or currency,
					"status": r.status or "",
					"actor": "",
					"actor_kind": "",
					"reason": "",
					"correlation_key": r.idempotency_key or "",
					"idempotency_key": r.idempotency_key or "",
					"audit_ref": None,
					"kind": "domain",
					"activity_type": "reservation",
					"domain_payload": dict(r),
				}
			)

	if frappe.db.exists("DocType", "Procurement Commitment"):
		for r in frappe.get_all(
			"Procurement Commitment",
			filters={"budget": budget_name},
			fields=[
				"name",
				"generated_reference",
				"budget_line",
				"reservation",
				"contract_code",
				"contract_title",
				"current_amount",
				"outstanding_amount",
				"status",
				"event_date",
				"currency",
			],
		):
			ev_date = r.event_date
			sort = str(getdate(ev_date)) if ev_date else ""
			events.append(
				{
					"event_id": f"domain:Procurement Commitment:{r.name}",
					"event_type": EVENT_COMMITMENT,
					"event_at": str(ev_date) if ev_date else "",
					"event_at_sort": sort,
					"budget": budget_name,
					"budget_line": r.budget_line or "",
					"source_doctype": "Procurement Commitment",
					"source_name": r.name,
					"source_code": r.generated_reference or r.name,
					"downstream_module": "Contract",
					"downstream_reference": r.contract_code or "",
					"amount": flt(r.current_amount),
					"currency": r.currency or currency,
					"status": r.status or "",
					"actor": "",
					"actor_kind": "",
					"reason": "",
					"correlation_key": "",
					"idempotency_key": "",
					"audit_ref": None,
					"kind": "domain",
					"activity_type": "commitment",
					"domain_payload": dict(r),
				}
			)

	if frappe.db.exists("DocType", "Expenditure Snapshot"):
		for r in frappe.get_all(
			"Expenditure Snapshot",
			filters={"budget": budget_name},
			fields=[
				"name",
				"generated_reference",
				"budget_line",
				"source_system",
				"source_reference",
				"amount",
				"reconciliation_status",
				"source_as_at",
				"contract_code",
				"currency",
			],
		):
			ev_date = r.source_as_at
			sort = str(getdate(ev_date)) if ev_date else ""
			events.append(
				{
					"event_id": f"domain:Expenditure Snapshot:{r.name}",
					"event_type": EVENT_EXPENDITURE,
					"event_at": str(ev_date) if ev_date else "",
					"event_at_sort": sort,
					"budget": budget_name,
					"budget_line": r.budget_line or "",
					"source_doctype": "Expenditure Snapshot",
					"source_name": r.name,
					"source_code": r.generated_reference or r.name,
					"downstream_module": "Finance",
					"downstream_reference": r.source_reference or r.contract_code or "",
					"amount": flt(r.amount),
					"currency": r.currency or currency,
					"status": r.reconciliation_status or "Matched",
					"actor": "",
					"actor_kind": "integration",
					"reason": "",
					"correlation_key": "",
					"idempotency_key": "",
					"audit_ref": None,
					"kind": "domain",
					"activity_type": "actual",
					"domain_payload": dict(r),
				}
			)

	return events


def _load_audit_events(budget_name: str) -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Budget Audit Event"):
		return []
	rows = frappe.get_all(
		"Budget Audit Event",
		filters={"budget": budget_name},
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
			"budget_line",
		],
	)
	events: list[dict[str, Any]] = []
	for r in rows:
		ea = get_datetime(r.event_at) if r.event_at else None
		sort = ea.isoformat(sep=" ") if ea else ""
		events.append(
			{
				"event_id": f"audit:{r.name}",
				"event_type": r.event_type or "",
				"event_at": str(r.event_at) if r.event_at else "",
				"event_at_sort": sort,
				"budget": budget_name,
				"budget_line": r.budget_line or "",
				"source_doctype": "Budget Audit Event",
				"source_name": r.name,
				"source_code": r.record_code or r.name,
				"downstream_module": "",
				"downstream_reference": r.source_reference or "",
				"amount": None,
				"currency": "",
				"status": "",
				"actor": r.actor or "",
				"actor_kind": r.actor_kind or "user",
				"reason": r.reason or "",
				"correlation_key": "",
				"idempotency_key": "",
				"audit_ref": r.name,
				"kind": "audit",
				"activity_type": "",
				"domain_payload": None,
				"audit_payload": dict(r),
			}
		)
	return events


def _merge_dedup(
	domain_events: list[dict[str, Any]],
	audit_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
	"""Attach matching audits onto domain rows; keep all audits for Audit projection.

	Activity must project domain rows only so amounts are not double-counted when a
	Budget Audit Event pairs with Funding Reservation / Commitment / Snapshot.
	"""
	by_key: dict[tuple[str, str], dict[str, Any]] = {}
	for ev in domain_events:
		key = (ev["source_doctype"], ev["source_code"])
		by_key[key] = ev

	for audit in audit_events:
		payload = audit.get("audit_payload") or {}
		etype = (audit.get("event_type") or "").strip()
		record_code = (payload.get("record_code") or audit.get("source_code") or "").strip()
		record_dt = (payload.get("record_doctype") or "").strip()
		if not record_dt and etype in _AUDIT_TO_DOMAIN_DOCTYPE:
			record_dt = _AUDIT_TO_DOMAIN_DOCTYPE[etype]
		key = (record_dt, record_code)
		paired = (
			etype in _DOMAIN_AUDIT_TYPES
			and record_dt
			and record_code
			and key in by_key
		)
		audit["paired_with_domain"] = paired
		if not paired:
			continue
		host = by_key[key]
		# Prefer EVENT_RESERVED as primary audit_ref when multiple audits pair.
		if not host.get("audit_ref") or etype == EVENT_RESERVED:
			host["audit_ref"] = audit["audit_ref"]
			host["audit_payload"] = payload
		if not host.get("actor") and audit.get("actor"):
			host["actor"] = audit["actor"]
			host["actor_kind"] = audit.get("actor_kind") or "user"
		if not host.get("reason") and audit.get("reason"):
			host["reason"] = audit["reason"]

	# Domain first (Activity/Downstream), then full audit stream (Audit History).
	return list(domain_events) + list(audit_events)


def _apply_filters(events: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
	types = filters.get("event_types") or filters.get("event_type")
	if isinstance(types, str) and types.strip():
		types = [types.strip()]
	line = (filters.get("budget_line") or "").strip()
	date_from = filters.get("date_from")
	date_to = filters.get("date_to")
	df = getdate(date_from) if date_from else None
	dt = getdate(date_to) if date_to else None
	kinds = filters.get("kinds")  # optional: domain / audit

	out: list[dict[str, Any]] = []
	for ev in events:
		if types and (ev.get("event_type") or "") not in types:
			continue
		if line and (ev.get("budget_line") or "") != line:
			# Also allow matching by line business code via domain payload later if needed.
			continue
		if kinds and (ev.get("kind") or "") not in kinds:
			continue
		ea = get_datetime(ev["event_at"]) if ev.get("event_at") else None
		if df and ea and ea.date() < df:
			continue
		if dt and ea and ea.date() > dt:
			continue
		out.append(ev)
	return out
