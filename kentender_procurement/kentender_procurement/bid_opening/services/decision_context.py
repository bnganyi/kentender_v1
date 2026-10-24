# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening's published context for the Tender decision screen (`kt_tender_opening_decision_context`; TPR-CHG-001 v0.24 §10.13 POSTCLOSE, §10.19;
BOP-CHG-001 v0.16 §10.7, §10.8).

The Accounting Officer follows the exact decision item from the opening to `/app/tenders/{tender_id}`. The decision is Tenders' (its current verdict allows
Cancel Tender or names every blocker); this is only what Bid Opening can say about the opening — the item's reference and kind, the opening's state, the
latest support finding and the incident it concerns. References and states only: no bid count, name, price, envelope identifier or content. Everyone else
gets None (support cannot decide for the Accounting Officer, and a reader who is not the Accounting Officer has no decision here)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_opening.services import incidents, labels, people, records


def get(*, tender: str, user: str) -> dict[str, Any] | None:
	case = records.case_for(tender)
	if not case or not people.holds(user, people.ACCOUNTING_OFFICER):
		return None
	doc = frappe.get_doc(records.CASE, case)
	item_name = frappe.db.get_value("Opening Decision Item", {"opening_case": case, "status": "Open"}, "name") or \
		frappe.db.get_value("Opening Decision Item", {"opening_case": case}, "name", order_by="creation desc")
	item = frappe.get_doc("Opening Decision Item", item_name) if item_name else None
	finding = cstr(frappe.db.get_value(incidents.INCIDENT, {"opening_case": case, "incident_id": item.incident}, "current_finding")) if item and item.incident else ""
	return {
		"item": cstr(item.decision_item_id) if item else "", "kind": cstr(item.kind) if item else "", "status": cstr(item.status) if item else "", "state": doc.state,
		"incident": cstr(item.incident) if item else "", "finding": finding, "reason": cstr(item.reason) if item else "",
		"message": incidents.NOT_RECOVERED if item and item.kind in ("Paused opening", "Opening cannot proceed") else "",
		"recorded_label": labels.when(item.created_at) if item else "", "opening_route": ["tenders", doc.tender_reference, "opening"],
	}
