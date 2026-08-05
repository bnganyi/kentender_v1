# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Funding Activity list contract — BUD-UI-07 / BUD-FR-107 / pack Phase 6."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, formatdate, getdate

from kentender_budget.services.budget_contracts import _line_totals, _resolve_budget, resolve_scoped_entity
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

	rows = _activity_rows(doc.name, currency)
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
	# Aggregate known amounts; Unavailable with no amount → Unknown display.
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


def _activity_rows(budget_name: str, currency: str) -> list[dict[str, Any]]:
	rows: list[dict[str, Any]] = []
	if frappe.db.exists("DocType", "Funding Reservation"):
		for r in frappe.get_all(
			"Funding Reservation",
			filters={"budget": budget_name},
			fields=[
				"name",
				"generated_reference",
				"demand_code",
				"demand_title",
				"original_amount",
				"remaining_reserved",
				"status",
				"event_date",
				"current_downstream_reference",
			],
		):
			rows.append(
				{
					"id": r.name,
					"code": r.generated_reference,
					"activity_type": "reservation",
					"activity_label": "Funding reservation",
					"source_code": r.demand_code,
					"source_name": r.demand_title,
					"amount": flt(r.original_amount),
					"amount_display": format_kes_full(r.original_amount, currency=currency),
					"status": r.status,
					"status_kind": "neutral",
					"event_date": formatdate(r.event_date) if r.event_date else "",
					"event_date_sort": str(getdate(r.event_date)) if r.event_date else "",
					"related_label": "Reserved balance:",
					"related_value": format_kes_full(r.remaining_reserved, currency=currency),
					"related_kind": "reserved",
					"action": "view_reservation",
					"action_label": "View reservation",
					"detail": {
						"title": r.demand_title,
						"code": r.generated_reference,
						"demand_code": r.demand_code,
						"original_amount_display": format_kes_full(r.original_amount, currency=currency),
						"remaining_display": format_kes_full(r.remaining_reserved, currency=currency),
						"status": r.status,
						"downstream": r.current_downstream_reference or "",
					},
				}
			)

	if frappe.db.exists("DocType", "Procurement Commitment"):
		for r in frappe.get_all(
			"Procurement Commitment",
			filters={"budget": budget_name},
			fields=[
				"name",
				"generated_reference",
				"contract_code",
				"contract_title",
				"current_amount",
				"status",
				"event_date",
				"outstanding_amount",
			],
		):
			rows.append(
				{
					"id": r.name,
					"code": r.generated_reference,
					"activity_type": "commitment",
					"activity_label": "Contract commitment",
					"source_code": r.contract_code,
					"source_name": r.contract_title,
					"amount": flt(r.current_amount),
					"amount_display": format_kes_full(r.current_amount, currency=currency),
					"amount_kind": "committed",
					"status": r.status,
					"status_kind": "active",
					"event_date": formatdate(r.event_date) if r.event_date else "",
					"event_date_sort": str(getdate(r.event_date)) if r.event_date else "",
					"related_label": "",
					"related_value": "—",
					"related_kind": "",
					"action": "view_commitment",
					"action_label": "View contract",
					"detail": {
						"title": r.contract_title,
						"code": r.generated_reference,
						"contract_code": r.contract_code,
						"amount_display": format_kes_full(r.current_amount, currency=currency),
						"outstanding_display": format_kes_full(r.outstanding_amount, currency=currency),
						"status": r.status,
					},
				}
			)

	if frappe.db.exists("DocType", "Expenditure Snapshot"):
		for r in frappe.get_all(
			"Expenditure Snapshot",
			filters={"budget": budget_name},
			fields=[
				"name",
				"generated_reference",
				"source_system",
				"source_reference",
				"amount",
				"reconciliation_status",
				"source_as_at",
				"contract_code",
			],
		):
			status = r.reconciliation_status or "Matched"
			has_amount = status != "Unavailable"
			rows.append(
				{
					"id": r.name,
					"code": r.generated_reference,
					"activity_type": "actual",
					"activity_label": "Actual expenditure snapshot",
					"source_code": r.source_reference or "",
					"source_name": r.source_system or "Finance system",
					"amount": flt(r.amount) if has_amount else None,
					"amount_display": format_kes_full(r.amount, currency=currency)
					if has_amount
					else "Unknown",
					"amount_kind": "actual",
					"status": status,
					"status_kind": "stale" if status == "Stale" else ("available" if status == "Matched" else "neutral"),
					"event_date": formatdate(r.source_as_at) if r.source_as_at else "",
					"event_date_sort": str(getdate(r.source_as_at)) if r.source_as_at else "",
					"related_label": "",
					"related_value": "—",
					"related_kind": "",
					"action": "view_reconciliation",
					"action_label": "View reconciliation",
					"detail": {
						"title": r.source_system or "Finance system",
						"code": r.generated_reference,
						"amount_display": format_kes_full(r.amount, currency=currency)
						if has_amount
						else "Unknown",
						"status": status,
						"source_as_at": formatdate(r.source_as_at) if r.source_as_at else "",
						"contract_code": r.contract_code or "",
					},
				}
			)
	return rows
