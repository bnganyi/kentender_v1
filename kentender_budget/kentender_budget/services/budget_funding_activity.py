# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Funding Activity list contract — BUD-UI-07 / BUD-FR-107 / pack Phase 6.

Rows project from the shared Funding Lifecycle read model (BUD-SUP-005).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, formatdate, getdate

from kentender_budget.services.budget_contracts import _line_totals, _resolve_budget, resolve_scoped_entity
from kentender_budget.services.budget_funding_lifecycle import list_funding_lifecycle
from kentender_budget.services.budget_line_contracts import format_kes_full
from kentender_budget.services.budget_permissions import (
	ROLE_AUDITOR,
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_VIEWER,
	require_any_role,
)

_ACTIVITY_ROLES = (ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_VIEWER, ROLE_AUDITOR)
_ACTIVITY_TYPES = frozenset({"reservation", "commitment", "actual"})


def list_funding_activity(budget: str) -> dict[str, Any]:
	"""Return balance strip + chronological funding activity for a Budget."""
	require_any_role(*_ACTIVITY_ROLES)
	doc = _resolve_budget(budget)
	resolve_scoped_entity(doc.procuring_entity)
	currency = doc.currency or "KES"
	totals = _line_totals(doc.name)

	# Prefer Actual from expenditure snapshots when present (never fake zero for Unavailable).
	snap_actual, snap_status = _budget_actual_from_snapshots(doc.name)
	actual_value = snap_actual if snap_actual is not None else totals["actual"]
	actual_status = snap_status or ("Matched" if actual_value else "Unavailable")
	if snap_status == "Unavailable":
		actual_display = "Unknown"
		actual_amount = None
	else:
		actual_amount = actual_value
		actual_display = format_kes_full(actual_value, currency=currency)

	outstanding = max(0.0, totals["committed"] - flt(actual_amount or 0))

	life = list_funding_lifecycle(doc.name)
	rows = [
		_row_from_lifecycle(ev, currency)
		for ev in life["events"]
		if (ev.get("kind") == "domain" and (ev.get("activity_type") or "") in _ACTIVITY_TYPES)
	]
	rows.sort(key=lambda r: (r.get("event_date_sort") or "", r.get("code") or ""), reverse=True)

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
		"balances": {
			"reserved": totals["reserved"],
			"committed": totals["committed"],
			"actual": actual_amount,
			"outstanding": outstanding,
			"reserved_display": format_kes_full(totals["reserved"], currency=currency),
			"committed_display": format_kes_full(totals["committed"], currency=currency),
			"actual_display": actual_display,
			"outstanding_display": format_kes_full(outstanding, currency=currency),
			"actual_status": actual_status,
		},
		"rows": rows,
		"row_count": len(rows),
		"pagination": {
			"showing_from": 1 if rows else 0,
			"showing_to": len(rows),
			"total": len(rows),
			"label": f"Showing 1 to {len(rows)} of {len(rows)} entries" if rows else "Showing 0 entries",
		},
		"capabilities": {
			"primary_action": "request_revision" if doc.status == "Active" else "",
			"primary_label": "Request revision" if doc.status == "Active" else "",
			"view_funding_performance": True,
			"read_only": True,
		},
	}


def _budget_actual_from_snapshots(budget_name: str) -> tuple[float | None, str | None]:
	if not frappe.db.exists("DocType", "Expenditure Snapshot"):
		return None, None
	snaps = frappe.get_all(
		"Expenditure Snapshot",
		filters={"budget": budget_name},
		fields=["amount", "reconciliation_status"],
		order_by="source_as_at desc",
	)
	if not snaps:
		return None, None
	total = 0.0
	has_value = False
	statuses = {s.reconciliation_status for s in snaps}
	for s in snaps:
		if s.reconciliation_status == "Unavailable":
			continue
		total += flt(s.amount)
		has_value = True
	if not has_value:
		return None, "Unavailable"
	status = "Stale" if "Stale" in statuses else ("Exception" if "Exception" in statuses else "Matched")
	return total, status


def _row_from_lifecycle(ev: dict[str, Any], currency: str) -> dict[str, Any]:
	payload = ev.get("domain_payload") or {}
	atype = ev.get("activity_type") or ""
	if atype == "reservation":
		event_date = payload.get("event_date")
		return {
			"id": payload.get("name") or ev.get("source_name"),
			"code": ev.get("source_code") or payload.get("generated_reference"),
			"activity_type": "reservation",
			"activity_label": "Funding reservation",
			"source_code": payload.get("demand_code") or "",
			"source_name": payload.get("demand_title") or "",
			"amount": flt(payload.get("original_amount")),
			"amount_display": format_kes_full(payload.get("original_amount"), currency=currency),
			"status": payload.get("status") or ev.get("status") or "",
			"status_kind": "neutral",
			"event_date": formatdate(event_date) if event_date else "",
			"event_date_sort": str(getdate(event_date)) if event_date else "",
			"related_label": "Reserved balance:",
			"related_value": format_kes_full(payload.get("remaining_reserved"), currency=currency),
			"related_kind": "reserved",
			"action": "view_reservation",
			"action_label": "View reservation",
			"detail": {
				"title": payload.get("demand_title"),
				"code": payload.get("generated_reference"),
				"demand_code": payload.get("demand_code"),
				"original_amount_display": format_kes_full(
					payload.get("original_amount"), currency=currency
				),
				"remaining_display": format_kes_full(
					payload.get("remaining_reserved"), currency=currency
				),
				"status": payload.get("status"),
				"downstream": payload.get("current_downstream_reference") or "",
			},
		}

	if atype == "commitment":
		event_date = payload.get("event_date")
		return {
			"id": payload.get("name") or ev.get("source_name"),
			"code": ev.get("source_code") or payload.get("generated_reference"),
			"activity_type": "commitment",
			"activity_label": "Contract commitment",
			"source_code": payload.get("contract_code") or "",
			"source_name": payload.get("contract_title") or "",
			"amount": flt(payload.get("current_amount")),
			"amount_display": format_kes_full(payload.get("current_amount"), currency=currency),
			"amount_kind": "committed",
			"status": payload.get("status") or "",
			"status_kind": "active",
			"event_date": formatdate(event_date) if event_date else "",
			"event_date_sort": str(getdate(event_date)) if event_date else "",
			"related_label": "",
			"related_value": "—",
			"related_kind": "",
			"action": "view_commitment",
			"action_label": "View contract",
			"detail": {
				"title": payload.get("contract_title"),
				"code": payload.get("generated_reference"),
				"contract_code": payload.get("contract_code"),
				"amount_display": format_kes_full(payload.get("current_amount"), currency=currency),
				"outstanding_display": format_kes_full(
					payload.get("outstanding_amount"), currency=currency
				),
				"status": payload.get("status"),
			},
		}

	# actual / expenditure
	event_date = payload.get("source_as_at")
	status = payload.get("reconciliation_status") or "Matched"
	has_amount = status != "Unavailable"
	return {
		"id": payload.get("name") or ev.get("source_name"),
		"code": ev.get("source_code") or payload.get("generated_reference"),
		"activity_type": "actual",
		"activity_label": "Actual expenditure snapshot",
		"source_code": payload.get("source_reference") or "",
		"source_name": payload.get("source_system") or "Finance system",
		"amount": flt(payload.get("amount")) if has_amount else None,
		"amount_display": format_kes_full(payload.get("amount"), currency=currency)
		if has_amount
		else "Unknown",
		"amount_kind": "actual",
		"status": status,
		"status_kind": "stale" if status == "Stale" else ("available" if status == "Matched" else "neutral"),
		"event_date": formatdate(event_date) if event_date else "",
		"event_date_sort": str(getdate(event_date)) if event_date else "",
		"related_label": "",
		"related_value": "—",
		"related_kind": "",
		"action": "view_reconciliation",
		"action_label": "View reconciliation",
		"detail": {
			"title": payload.get("source_system") or "Finance system",
			"code": payload.get("generated_reference"),
			"amount_display": format_kes_full(payload.get("amount"), currency=currency)
			if has_amount
			else "Unknown",
			"status": status,
			"source_as_at": formatdate(event_date) if event_date else "",
			"contract_code": payload.get("contract_code") or "",
		},
	}
