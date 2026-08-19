# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Downstream Usage list contract — BUD-UI-10 / BUD-FR-105 / pack get_budget_usage.

Lineage rows project from the shared Funding Lifecycle read model (BUD-SUP-005).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

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
from kentender_budget.services.budget_authorization import CAP_BUDGET_EDIT, can_budget

_USAGE_ROLES = (ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_VIEWER, ROLE_AUDITOR)


def list_downstream_usage(budget: str) -> dict[str, Any]:
	"""Read-only Budget Line → Demand → Plan item → Tender → Contract lineage."""
	require_any_role(*_USAGE_ROLES)
	life = list_funding_lifecycle(budget)
	currency = life["budget"].get("currency") or "KES"
	rows = _usage_rows_from_lifecycle(life["events"], currency)
	bud = life["budget"]
	budget_doc = frappe.get_doc("Budget", bud["id"])
	return {
		"budget": {
			"id": bud["id"],
			"code": bud["code"],
			"name": bud["name"],
			"title": bud["title"],
			"status": bud["status"],
			"status_label": bud["status_label"],
			"currency": currency,
			"procuring_entity": bud["procuring_entity"],
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
			"primary_action": (
				"request_revision"
				if bud["status"] == "Active" and can_budget(CAP_BUDGET_EDIT, budget_doc)
				else ""
			),
			"primary_label": (
				"Request revision"
				if bud["status"] == "Active" and can_budget(CAP_BUDGET_EDIT, budget_doc)
				else ""
			),
			"view_funding_performance": True,
			"read_only": True,
		},
	}


def get_budget_usage(budget: str) -> dict[str, Any]:
	"""Pack §8 alias for list_downstream_usage."""
	return list_downstream_usage(budget)


def _usage_rows_from_lifecycle(events: list[dict[str, Any]], currency: str) -> list[dict[str, Any]]:
	reservations = [
		ev
		for ev in events
		if ev.get("kind") == "domain" and ev.get("source_doctype") == "Funding Reservation"
	]
	if not reservations:
		return []

	commitments_by_rsv: dict[str, list[dict[str, Any]]] = {}
	for ev in events:
		if ev.get("kind") != "domain" or ev.get("source_doctype") != "Procurement Commitment":
			continue
		payload = ev.get("domain_payload") or {}
		rsv = payload.get("reservation") or ""
		if rsv:
			commitments_by_rsv.setdefault(rsv, []).append(payload)

	line_ids = list(
		{
			(ev.get("domain_payload") or {}).get("budget_line")
			for ev in reservations
			if (ev.get("domain_payload") or {}).get("budget_line")
		}
	)
	line_titles: dict[str, str] = {}
	if line_ids:
		for row in frappe.get_all(
			"Budget Line",
			filters={"name": ("in", line_ids)},
			fields=["name", "title", "generated_reference"],
		):
			line_titles[row.name] = row.title or row.generated_reference or row.name

	# Preserve lifecycle order (already event_at desc); stable by source_code.
	rows: list[dict[str, Any]] = []
	for ev in reservations:
		rsv = ev.get("domain_payload") or {}
		coms = commitments_by_rsv.get(rsv.get("name") or "") or []
		commitment_total = sum(flt(c.get("current_amount")) for c in coms)
		primary = None
		for c in coms:
			if c.get("status") == "Active":
				primary = c
				break
		if primary is None and coms:
			primary = coms[0]

		contract_code = (primary.get("contract_code") if primary else "") or ""
		contract_title = (primary.get("contract_title") if primary else "") or ""
		reserved = flt(rsv.get("remaining_reserved"))
		requirement = (
			line_titles.get(rsv.get("budget_line") or "")
			or rsv.get("demand_title")
			or rsv.get("generated_reference")
		)
		tender = (rsv.get("current_downstream_reference") or "").strip()
		plan_item = (rsv.get("plan_item_code") or "").strip()

		rows.append(
			{
				"id": rsv.get("name"),
				"code": rsv.get("generated_reference"),
				"reservation_code": rsv.get("generated_reference"),
				"requirement": requirement,
				"demand_code": rsv.get("demand_code") or "",
				"demand_name": rsv.get("demand_title") or "",
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
				"status": rsv.get("status") or "",
				"status_kind": _status_kind(rsv.get("status") or ""),
				"original_amount": flt(rsv.get("original_amount")),
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
