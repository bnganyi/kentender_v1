# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The bidder receipt (BDS-CHG-001 v0.8 §4.10, §10.14, §11.6; BDS01-AC-066/067).

A receipt exists only because the tender box accepted the exact signed
envelope. Its read, print view and PDF carry the human-readable facts — the
receipt reference; the Tender reference and title; the bidder; the bid and
its Submitted bid Version; who submitted it; when the tender-box service
received it and when it was accepted, to the second in EAT; its status; the
earlier receipt it replaced — and the summary recorded at acceptance, and
nothing technical: no digest, key, certificate detail, schema, database
identity or storage location. Only people of the bid's lead organisation
can read it; anyone else is told it does not exist."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, escape_html

from kentender_procurement.bid_submission.services import bid_context, clock, labels

RECEIPT = "Bid Receipt"
NOT_A_RESULT = "This receipt confirms submission only. It is not an opening, evaluation or award result."
SIMULATION_NOTE = "Test environment: this receipt comes from the simulated Test Tender Box, not a production tender box."


def _load(receipt_reference: str, *, actor: str, organisation: str):
	name = frappe.db.get_value(RECEIPT, {"receipt_reference": cstr(receipt_reference).strip()}, "name") if cstr(receipt_reference).strip() else None
	if not name:
		raise frappe.DoesNotExistError("This receipt is unavailable or you do not have permission to view it.")
	receipt = frappe.get_doc(RECEIPT, name)
	try:
		bid_context.workspace_for(receipt.bid_workspace, actor=actor, organisation=organisation, at=clock.now())
	except frappe.DoesNotExistError:
		raise frappe.DoesNotExistError("This receipt is unavailable or you do not have permission to view it.")
	return receipt


def _status(receipt) -> str:
	return cstr(frappe.db.get_value("Bid Submission Version", receipt.submission_version, "status")) or "Submitted"


def facts(receipt) -> dict[str, Any]:
	summary = json.loads(receipt.summary_json or "{}")
	predecessor = cstr(receipt.predecessor_receipt)
	return {
		"receipt_reference": receipt.receipt_reference, "tender_reference": receipt.tender_reference, "tender_title": receipt.tender_title, "bidder": receipt.bidder_name,
		"bid_reference": receipt.bid_workspace, "submitted_version": f"Submitted bid Version {int(receipt.version_number)}", "submitted_by": receipt.submitted_by_name,
		"received_at": labels.datetime_seconds_label(receipt.received_at), "accepted_at": labels.datetime_seconds_label(receipt.accepted_at), "status": _status(receipt),
		"replaces_receipt": predecessor,
		"summary": {"bid_total": cstr(summary.get("bid_total")), "offered_item": cstr(summary.get("offered_item")), "quantity": cstr(summary.get("quantity")), "delivery_date": cstr(summary.get("delivery_date"))},
		"deadline": labels.datetime_label(frappe.db.get_value("Tender", receipt.tender, "submission_deadline")),
		"notice": NOT_A_RESULT, "simulation_note": SIMULATION_NOTE if receipt.simulation else "",
	}


def get_bid_receipt(*, receipt_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""The receipt facts and, for its bid, the viewer's next step (§5.12)."""
	from kentender_procurement.bid_submission.services import guidance

	actor = cstr(user or frappe.session.user)
	receipt = _load(receipt_reference, actor=actor, organisation=organisation)
	at = clock.now()
	ctx = bid_context.load(receipt.bid_workspace, actor=actor, organisation=organisation, at=at)
	guided = guidance.for_bid(ctx, actor=actor, at=at)
	return {**facts(receipt), "next_step": guided["next_step"], "journey": guided["journey"]}


ROWS = (
	("Receipt reference", "receipt_reference"), ("Tender", "tender_reference"), ("Tender title", "tender_title"), ("Bidder", "bidder"), ("Bid", "bid_reference"),
	("Submitted bid version", "submitted_version"), ("Submitted by", "submitted_by"), ("Received by tender-box service", "received_at"),
	("Accepted into tender box", "accepted_at"), ("Status", "status"), ("Replaces receipt", "replaces_receipt"),
)
SUMMARY_ROWS = (("Bid total", "bid_total"), ("Offered item", "offered_item"), ("Quantity", "quantity"), ("Delivery date", "delivery_date"))


def receipt_html(data: dict[str, Any]) -> str:
	"""The accessible print view (also the PDF source): a heading, two
	definition lists and the notice. Plain HTML, no scripts."""

	def rows(pairs, source):
		return "".join(f"<dt>{escape_html(label)}</dt><dd>{escape_html(cstr(source.get(key)))}</dd>" for label, key in pairs if cstr(source.get(key)))

	return (
		"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>Bid receipt " + escape_html(data["receipt_reference"]) + "</title>"
		"<style>body{font-family:sans-serif;margin:32px;color:#1d2433}h1{font-size:22px}dl{display:grid;grid-template-columns:260px 1fr;gap:6px 16px}"
		"dt{color:#4a5468}dd{margin:0;font-weight:600}p{max-width:640px}</style></head><body>"
		"<h1>Bid submitted</h1><p>Your bid was accepted into the electronic tender box.</p>"
		f"<dl>{rows(ROWS, data)}</dl><h2>Submission summary</h2><dl>{rows(SUMMARY_ROWS, data['summary'])}<dt>Current deadline</dt><dd>{escape_html(data['deadline'])}</dd></dl>"
		f"<p>{escape_html(data['notice'])}</p>" + (f"<p>{escape_html(data['simulation_note'])}</p>" if data.get("simulation_note") else "") + "</body></html>"
	)


def receipt_pdf(*, receipt_reference: str, organisation: str = "", user: str | None = None) -> tuple[str, bytes]:
	"""(file name, PDF bytes) of the immutable receipt (§11.6 Download receipt)."""
	from frappe.utils.pdf import get_pdf

	data = get_bid_receipt(receipt_reference=receipt_reference, organisation=organisation, user=user)
	return f"{data['receipt_reference']}.pdf", get_pdf(receipt_html(data))
