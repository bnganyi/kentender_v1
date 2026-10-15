# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What the evaluation gives the contract about the bid that won (CM-CHG-001 v0.8 section 19.4 S2 and S3; plan D20; tracker CM8-516).

Additive and read-only. Award lists these as the contract's accepted tender (S2) and price schedule (S3); Contract Management reads them back through the core source seam and verifies them against the
digest Award froze. Everything here is taken from the **frozen report version** the award rests on, so it cannot drift after the decision: the accepted bid's identity (its bid reference, submission
version, receipt, envelope and package digest, which name exactly the offer that was accepted), the priced lines it offered and the clarifications that were asked of it and answered. The offer's own text
stays with Bid Submission, referenced by the package digest; this module releases no sealed content."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr


class Unavailable(Exception):
	"""The evaluation owns this but cannot give it, and says why."""


def _report(report: str):
	if not report or not frappe.db.exists("Evaluation Report Version", report):
		raise Unavailable("The evaluation report the award rests on is not held.")
	return frappe.get_doc("Evaluation Report Version", report)


def _bid(bid: str):
	if not bid or not frappe.db.exists("Evaluation Bid", bid):
		raise Unavailable("The accepted bid is not held by the evaluation.")
	return frappe.get_doc("Evaluation Bid", bid)


def accepted_offer(*, report: str, bid: str) -> dict[str, Any]:
	"""S2: exactly which offer was accepted, and what was asked of it."""
	doc, row = _report(report), _bid(bid)
	content = json.loads(doc.content_json or "{}")
	clarifications = []
	for item in (content.get("clarifications_and_record") or {}).get("clarifications") or []:
		if frappe.db.get_value("Evaluation Clarification", item.get("name"), "evaluation_bid") != bid:
			continue
		reply = item.get("reply") or {}
		clarifications.append({"id": item.get("name"), "question": cstr(item.get("question")), "scope": cstr(item.get("reply_scope")), "sent_at": cstr(item.get("sent_at")), "reply": cstr(reply.get("body")),
			"received": cstr(reply.get("received")), "timeliness": cstr(reply.get("timeliness")), "disposition": cstr(item.get("disposition")), "result": cstr(item.get("disposition_result")),
			"reason": cstr(item.get("disposition_reason")), "closed_at": cstr(item.get("closed_at"))})
	return {"report": {"id": doc.name, "version": int(doc.version_number or 0), "digest": doc.content_digest},
		"bid": {"id": row.name, "reference": row.bid_reference, "tenderer": row.tenderer_name, "organisation": row.organisation_id, "submission_version": row.submission_version, "receipt": row.receipt_reference,
			"envelope": row.envelope_id, "package_digest": row.package_digest, "submitted_total": cstr(row.submitted_total), "currency": row.currency},
		"clarifications": clarifications}


def awarded_prices(*, report: str, bid: str) -> dict[str, Any]:
	"""S3: the priced lines of the accepted offer, as the evaluation froze them: quantity, unit price before tax, tax and the line total, with the evaluated arithmetic."""
	doc = _report(report)
	content = json.loads(doc.content_json or "{}")
	priced = next((p for p in (content.get("financial_comparison") or {}).get("prices") or [] if p.get("bid") == bid), None)
	if not priced or not priced.get("lines"):
		raise Unavailable("The report carries no priced lines for the accepted bid.")
	if priced.get("problems"):
		raise Unavailable("The accepted bid's priced lines carry unresolved arithmetic problems.")
	return {"report": {"id": doc.name, "digest": doc.content_digest}, "bid": bid, "currency": cstr(priced.get("currency")), "submitted_total": cstr(priced.get("submitted_total")),
		"calculated_total": cstr(priced.get("calculated_total")), "lines": [{k: cstr(v) for k, v in line.items()} for line in priced["lines"]]}
