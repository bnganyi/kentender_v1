# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Tenders side of the Award contract (AWD-CHG-001 v0.4 §3, AWD-IF-02;
Award plan D5). Read-only facts Award needs about a Tender — its identity and
title, its validity end with the counting rule, and its authoritative status
events — plus the serialised issue/cancellation boundary: `cancel_tender`
asks every registered guard (`kt_tender_cancellation_guards`) before it
cancels, so a cancellation cannot race an award notice that has been, or is
being, issued (§5.4). Tenders owns cancellation and validity extension; Award
never writes a Tender."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import evaluation_seam


def tender_facts(tender: str) -> dict[str, Any] | None:
	fact = evaluation_seam.publication_fact(tender)
	if not fact:
		return None
	pe = cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_name")) if frappe.db.exists("DocType", "Site Procuring Entity") else ""
	return {"tender": fact["tender"], "tender_reference": fact["tender_reference"], "title": fact["title"], "lot": "1", "procuring_entity": pe, "requesting_unit": requesting_unit(tender),
		"status": fact.get("status"), "cancelled": bool(fact.get("cancelled")), "product_key": fact.get("product_key"),
		"award_method": "Lowest evaluated responsive tender", "currency": "KES"}


def requesting_unit(tender: str) -> str:
	"""The organisation unit that asked for the goods (the requisition's lead unit): the unit that will manage the contract."""
	requisition = frappe.db.get_value("Tender", tender, "requisition")
	return cstr(frappe.db.get_value("Procurement Requisition", requisition, "lead_org_unit_id")) if requisition else ""


def validity(tender: str) -> dict[str, Any]:
	rules = evaluation_seam.dated_rules(tender) or {}
	return {"validity_end": rules.get("validity_end"), "rule": rules.get("validity_rule")}


def funding_reservations(tender: str) -> list[str]:
	"""The Budget reservations this Tender draws on, for Award's decision-time
	funding read (AWD-IF-07). Award reads their amounts through Budget's
	published contract; this only names them."""
	return list(evaluation_seam.funding_reservations(tender)["reservation_ids"] or [])


def funding_sources(tender: str, definition_version: Any) -> dict[str, Any]:
	"""The item → drawdown line → reservation mapping an award's price is traced through (AWD-CHG-001 v0.7 §7.1), read from what Tenders holds: the Requisition the approved Tender Version consumed, and the
	published bid definition's price rows with the source items each covers. Read-only; nothing is inferred. Award never reads a Tender record; it asks this and verifies the answer against Requisitions.

	Returns `{}` when the Tender holds no consumed Requisition or the definition version, so the caller reports a missing mapping rather than a guess."""
	from kentender_procurement.tenders.services import bid_definition
	from kentender_procurement.tenders.services import snapshot as snap

	root = evaluation_seam._root(tender)
	name = (root.approved_version or root.current_version) if root else None
	stored = bid_definition.definition_for(tender, definition_version) if definition_version else None
	if not name or not stored:
		return {}
	loaded = snap.load(frappe.get_doc("Tender Version", name))
	lines = {}
	for line in loaded.get("drawdown_lines") or []:
		if line.get("drawdown_line_id"):
			lines[line["drawdown_line_id"]] = {key: line.get(key) for key in ("plan_item_line_id", "source_line_id", "contributing_org_unit", "budget_line", "requested_quantity", "requested_value", "reservation_id", "reservation_reference")}
	rows = []
	for row in (stored["definition"] or {}).get("price_rows") or []:
		if row.get("kind") != "Goods":
			continue
		lineage = ((row.get("source_lineage") or {}).get("source_lineage")) or []
		rows.append({"line": cstr(row.get("line")), "price_row_id": cstr(row.get("price_row_id")), "quantity": cstr(row.get("quantity")), "unit": cstr(row.get("unit")), "description": cstr(row.get("description")),
			"sources": [{key: cstr(item.get(key)) for key in ("requisition_item_id", "drawdown_line_id", "quantity")} for item in lineage]})
	return {
		"tender_version": name,
		"requisition": {"id": cstr(loaded.get("requisition_id")), "version": cstr(loaded.get("requisition_version")), "content_digest": cstr(loaded.get("content_digest")), "handoff_digest": cstr(loaded.get("handoff_digest"))},
		"definition": {"id": stored["bid_definition_id"], "version": stored["definition_version"], "digest": stored["definition_digest"]},
		"drawdown_lines": lines,
		"items": [{key: cstr(item.get(key)) for key in ("requisition_item_id", "drawdown_line_id", "quantity")} for item in loaded.get("items") or []],
		"price_rows": rows,
	}


def status_events(tender: str) -> list[dict[str, Any]]:
	return evaluation_seam.status_events(tender)


def cancellation_refusals(tender: str) -> list[str]:
	"""Every registered guard's reason to refuse cancelling `tender` now."""
	out: list[str] = []
	for path in frappe.get_hooks("kt_tender_cancellation_guards") or []:
		reason = frappe.get_attr(path)(tender=tender)
		if reason:
			out.append(cstr(reason))
	return out
