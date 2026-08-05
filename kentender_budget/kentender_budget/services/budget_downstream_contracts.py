# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Downstream Usage list contract — BUD-UI-10 / BUD-FR-105 / pack get_budget_usage."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_budget.services.budget_contracts import _resolve_budget, resolve_scoped_entity
from kentender_budget.services.budget_line_contracts import format_kes_full
from kentender_budget.services.budget_permissions import (
	ROLE_AUDITOR,
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_VIEWER,
	require_any_role,
)

_USAGE_ROLES = (ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_VIEWER, ROLE_AUDITOR)


def list_downstream_usage(budget: str) -> dict[str, Any]:
	"""Read-only Budget Line → Demand → Plan item → Tender → Contract lineage."""
	require_any_role(*_USAGE_ROLES)
	doc = _resolve_budget(budget)
	resolve_scoped_entity(doc.procuring_entity)
	currency = doc.currency or "KES"

	rows = _usage_rows(doc.name, currency)
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


def get_budget_usage(budget: str) -> dict[str, Any]:
	"""Pack §8 alias for list_downstream_usage."""
	return list_downstream_usage(budget)


def _usage_rows(budget_name: str, currency: str) -> list[dict[str, Any]]:
	if not frappe.db.exists("DocType", "Funding Reservation"):
		return []

	reservations = frappe.get_all(
		"Funding Reservation",
		filters={"budget": budget_name},
		fields=[
			"name",
			"generated_reference",
			"budget_line",
			"demand_code",
			"demand_title",
			"plan_item_code",
			"current_downstream_reference",
			"remaining_reserved",
			"original_amount",
			"status",
		],
		order_by="event_date desc, generated_reference asc",
	)
	if not reservations:
		return []

	line_ids = list({r.budget_line for r in reservations if r.budget_line})
	line_titles: dict[str, str] = {}
	if line_ids:
		for row in frappe.get_all(
			"Budget Line",
			filters={"name": ("in", line_ids)},
			fields=["name", "title", "generated_reference"],
		):
			line_titles[row.name] = row.title or row.generated_reference or row.name

	commitments_by_rsv: dict[str, list[Any]] = {}
	if frappe.db.exists("DocType", "Procurement Commitment"):
		rsv_names = [r.name for r in reservations]
		for com in frappe.get_all(
			"Procurement Commitment",
			filters={"budget": budget_name, "reservation": ("in", rsv_names)},
			fields=[
				"reservation",
				"generated_reference",
				"contract_code",
				"contract_title",
				"current_amount",
				"status",
			],
		):
			commitments_by_rsv.setdefault(com.reservation, []).append(com)

	rows: list[dict[str, Any]] = []
	for rsv in reservations:
		coms = commitments_by_rsv.get(rsv.name) or []
		commitment_total = sum(flt(c.current_amount) for c in coms)
		# Prefer first Active commitment for contract display; else first.
		primary = None
		for c in coms:
			if c.status == "Active":
				primary = c
				break
		if primary is None and coms:
			primary = coms[0]

		contract_code = (primary.contract_code if primary else "") or ""
		contract_title = (primary.contract_title if primary else "") or ""
		reserved = flt(rsv.remaining_reserved)
		requirement = line_titles.get(rsv.budget_line) or rsv.demand_title or rsv.generated_reference
		tender = (rsv.current_downstream_reference or "").strip()
		plan_item = (rsv.plan_item_code or "").strip()

		rows.append(
			{
				"id": rsv.name,
				"code": rsv.generated_reference,
				"reservation_code": rsv.generated_reference,
				"requirement": requirement,
				"demand_code": rsv.demand_code or "",
				"demand_name": rsv.demand_title or "",
				"plan_item_code": plan_item,
				"plan_item_display": plan_item or "—",
				"tender_code": tender,
				"tender_display": tender or "—",
				"contract_code": contract_code,
				"contract_name": contract_title,
				"contract_display": contract_code or ("Pending Award" if tender else "—"),
				"reserved_balance": reserved,
				"reserved_balance_display": format_kes_full(reserved, currency=currency),
				"commitment": commitment_total,
				"commitment_display": (
					format_kes_full(commitment_total, currency=currency)
					if commitment_total
					else "—"
				),
				"status": rsv.status or "",
				"status_kind": _status_kind(rsv.status or ""),
				"original_amount": flt(rsv.original_amount),
				"action": "view",
				"action_label": "View reservation",
			}
		)
	return rows


def _status_kind(status: str) -> str:
	s = (status or "").strip().lower()
	if s in ("active", "converted"):
		return "ok"
	if s in ("partially converted", "reserved"):
		return "warn"
	if s in ("released", "cancelled", "expired"):
		return "muted"
	return "ok"
