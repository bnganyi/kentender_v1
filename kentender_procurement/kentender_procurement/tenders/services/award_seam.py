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
	return {"tender": fact["tender"], "tender_reference": fact["tender_reference"], "title": fact["title"], "lot": "1", "procuring_entity": pe,
		"status": fact.get("status"), "cancelled": bool(fact.get("cancelled")), "product_key": fact.get("product_key"),
		"award_method": "Lowest evaluated responsive tender", "currency": "KES"}


def validity(tender: str) -> dict[str, Any]:
	rules = evaluation_seam.dated_rules(tender) or {}
	return {"validity_end": rules.get("validity_end"), "rule": rules.get("validity_rule")}


def funding_reservations(tender: str) -> list[str]:
	"""The Budget reservations this Tender draws on, for Award's decision-time
	funding read (AWD-IF-07). Award reads their amounts through Budget's
	published contract; this only names them."""
	return list(evaluation_seam.funding_reservations(tender)["reservation_ids"] or [])


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
