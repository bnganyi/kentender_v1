# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`SubmitTenderClarification` (BDS-CHG-001 v0.8 §5.4, §7.2 and §8).

A registered candidate (an Active bidder arrangement) asks a question before
the clarification deadline, by trusted time. The exact question goes to
Tenders idempotently through the bidder-facing producer identity; Tenders'
identity and receipt time come back. Bid Submission keeps no copy of the
question. After the deadline nothing is created and the entered text is the
screen's to keep for copying only.

The producer identity is a service user holding the Tenders inquiry-producer
role, named in site_config `kt_bds_clarification_producer` (tests set
`frappe.flags.kt_bds_clarification_producer`)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services import clock, labels, records, tenders_gateway
from kentender_procurement.bid_submission.services.errors import fail, field_errors

ARRANGEMENT = "Bidder Arrangement"
MIN_LENGTH, MAX_LENGTH = 10, 2000
# what the asker reads for each state of their own question (Tenders owns the state)
OWN_STATUS = {"Received": ("Received · waiting for an answer", "pending"), "Answered": ("Answered", "live"), "Closed": ("Closed", "draft")}
ANSWERED_ALERT = "Your question was answered"


def _producer() -> str:
	producer = cstr(frappe.flags.get("kt_bds_clarification_producer") or frappe.conf.get("kt_bds_clarification_producer") or "")
	if not producer:
		frappe.throw("Bid Submission's clarification producer is not configured (site_config kt_bds_clarification_producer).")
	return producer


def submit_tender_clarification(*, tender_reference: str, question: str, organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.require_person(cstr(user or frappe.session.user))
	payload = {"tender_reference": cstr(tender_reference).strip(), "question": cstr(question), "organisation": cstr(organisation).strip()}
	return records.idempotent(idempotency_key, "SubmitTenderClarification", payload, lambda: _submit(actor=actor, key=idempotency_key, **payload), actor=actor, organisation=payload["organisation"])


def _submit(*, actor: str, key: str, tender_reference: str, question: str, organisation: str) -> dict[str, Any]:
	at = clock.now()
	root = tenders_gateway.tender_root(tender_reference)
	if not root:
		fail("BDS_TENDER_NOT_FOUND")
	lead = authz.acting_assignment(actor, organisation, at=at)["organisation_id"]
	authz.active_account(lead)
	arrangement = frappe.db.get_value(ARRANGEMENT, {"tender": root.name, "lead_organisation": lead, "status": "Active"}, "name")
	if not arrangement:
		fail("BDS_CLARIFICATION_NOT_REGISTERED")
	if tenders_gateway.availability(tender_reference, at=at) != "open":
		fail("BDS_TENDER_NOT_OPEN")
	if not root.clarification_deadline or at >= get_datetime(root.clarification_deadline):
		fail("BDS_CLARIFICATION_DEADLINE_PASSED", detail={"clarification_deadline": labels.datetime_label(root.clarification_deadline)})
	text = " ".join(cstr(question).split())
	if not (MIN_LENGTH <= len(text) <= MAX_LENGTH):
		return field_errors({"question": "Enter a question of 10 to 2,000 characters."})
	from kentender_procurement.tenders.services.errors import TendersError

	try:
		received = tenders_gateway.submit_clarification(
			tender=root.name, candidate_registration_id=arrangement, question=text, inbound_event_id=f"BDS-{cstr(key).strip()}", received_at=at, producer=_producer(),
		)
	except TendersError as exc:
		mapped = {"TND_CLARIFICATION_LATE": "BDS_CLARIFICATION_DEADLINE_PASSED", "TND_CLARIFICATION_CANDIDATE_REQUIRED": "BDS_CLARIFICATION_NOT_REGISTERED", "TND_CANCELLED": "BDS_TENDER_NOT_OPEN", "TND_STALE_VERSION": "BDS_TENDER_NOT_OPEN"}
		if exc.code == "TND_CONTROL_INVALID":
			return field_errors({"question": "Enter a question of 10 to 2,000 characters."})
		fail(mapped.get(exc.code, "BDS_TENDER_NOT_OPEN"))
	records.emit("ClarificationSubmitted", tender=root.name, arrangement=arrangement, organisation=lead, actor=actor, at=at, payload={"clarification": received["clarification"]})
	return {"ok": True, "clarification_id": received["clarification"], "received_at": labels.datetime_label(at), "status": received.get("status", "")}


def my_questions(bid_reference: str) -> list[dict[str, Any]]:
	"""This bid's own questions, read from Tenders' projection of the
	asking candidate (nothing is kept here): the text, when it was received,
	where it stands and, once answered, the answer — including an answer sent
	to the asker only, which no public list carries. Another bidder's
	questions are never read: the projection is keyed by this bid's own
	candidate registration."""
	ws = frappe.db.get_value("Bid Workspace", bid_reference, ["tender", "bidder_arrangement"], as_dict=True)
	view = tenders_gateway.candidate_view(ws.tender, ws.bidder_arrangement) if ws else None
	rows = []
	for q in (view or {}).get("questions") or []:
		label, tone = OWN_STATUS.get(q["status"], OWN_STATUS["Received"])
		answered = q["status"] == "Answered"
		rows.append({
			"key": q["key"], "question": q["question"], "received": f"Received {labels.datetime_label(q['received_at'])}", "status": q["status"], "status_label": label, "tone": tone,
			"answer": q["answer"] if answered else "", "answered": f"Answered {labels.datetime_label(q['answered_at'])}" if answered else "", "private": answered and q["audience"] == "Asker only",
		})
	return rows


def answered_alert(bid_reference: str, tender_reference: str) -> list[dict[str, str]]:
	"""The My bids line when any of this bid's questions has been answered."""
	if not any(q["status"] == "Answered" for q in my_questions(bid_reference)):
		return []
	return [{"title": ANSWERED_ALERT, "href": f"/tenders/{tender_reference}/bid/documents"}]
