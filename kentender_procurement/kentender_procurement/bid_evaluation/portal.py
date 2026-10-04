# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Evaluation's answer inside Bid Submission's supplier portal
(EVL-CHG-001 v0.4 §9.7, §10 "Correspondence subroute"; plan D14; boards
D06-SUPPLIER, D06-RECEIVED, D06-LATE, D06-LATE-RECEIVED, D06-CLOSED,
D06-FINAL-CLOSED, D06-FINAL-CLOSED-NR).

Bid Submission owns /tenders; it asks `kt_tender_evaluation_portal` for
/tenders/{ref}/bid/evaluation-clarifications/{request}, and
`kt_tender_portal_links` for the supplier's own requests on the Tender page.
A supplier sees only their own organisation's request and reply: never a
finding, a ranking or another bidder."""

from __future__ import annotations

from typing import Any

import frappe


def resolve(*, tender_reference: str, clarification: str, organisation: str, user: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import reads

	try:
		data = reads.own_clarification(tender_reference=tender_reference, clarification=clarification, organisation=organisation, user=user)
	except frappe.DoesNotExistError:
		return {"verdict": "NOT_FOUND", "title": "Not found", "payload": {"screen": "not-found"}}
	return {"verdict": "OK", "title": "Reply to clarification", "payload": {"screen": "evaluation-clarification", "data": data}}


def tender_links(*, tender_reference: str, user: str) -> list[dict[str, str]]:
	"""The supplier's own clarification requests on this Tender (sent, not yet
	withdrawn), each linking to its reply page. Nothing for anyone else."""
	from kentender_procurement.bid_evaluation.services import clarification, records

	if not user or user == "Guest":
		return []
	tender = frappe.db.get_value("Tender", {"tender_reference": tender_reference}, "name")
	case = records.case_for(tender) if tender else None
	if not case:
		return []
	out = []
	for request in frappe.get_all("Evaluation Clarification", filters={"evaluation_case": case, "status": ("in", ("Sent", "Closed", "Withdrawn"))},
			fields=["name", "status", "reply_deadline"], order_by="creation asc"):
		try:
			clarification._supplier_request(tender, request.name, user)
		except frappe.DoesNotExistError:
			continue
		from kentender_procurement.bid_evaluation.services import next_steps

		out.append({"label": "Evaluation clarification", "value": "Reply by " + next_steps.when(request.reply_deadline) if request.status == "Sent" else request.status,
			"href": f"/tenders/{tender_reference}/bid/evaluation-clarifications/{request.name}",
			"text": "The evaluation committee asked a question about your bid" if request.status == "Sent" else "A question from the evaluation committee"})
	return out
