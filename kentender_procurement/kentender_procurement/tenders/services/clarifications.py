# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §4.9 / §5.1 / §7.4 — supplier clarifications (replaces
v0.8's addendum-only inquiry; TPR10-IMP-002/003).

`ReceiveTenderClarification` consumes one authenticated Bid Submission
event: the producer is the bidder-facing service identity, the asker is an
exact Active Tender-bound candidate registration (`candidate_gateway`),
never free text, and the inbound event is deduplicated on
`(producer, inbound_event_id)`. Receipt at or after the clarification
deadline creates nothing (`TND_CLARIFICATION_LATE`). A related addendum is
optional (a general question needs none). A question never changes the
Tender.

`RespondToTenderClarification` records the procurement professional's
classification and answer:

- no published change → sent as selected, to the asker only or to every
  registered candidate (a broadcast never identifies the asker);
- a published change → the clarification is **Awaiting addendum**
  (`TND_CLARIFICATION_ADDENDUM_REQUIRED`, the draft answer preserved) until
  an addendum linked to it is Issued and effective; only then may the answer
  go to every registered candidate.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.tenders.services import bid_definition, candidate_gateway, candidate_notices, clock, digest, draft_commands, envelope, events, handoffs, lifecycle
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER

DOCTYPE = "Tender Clarification"
AUDIENCES = ("Asker only", "All registered candidates")
AWAITING_RESPONSE = "Awaiting response"
AWAITING_ADDENDUM = "Awaiting addendum"
ANSWERED = "Answered"
CLOSED = "Closed with reason"


def _clean(text) -> str:
	return " ".join(cstr(text).split())


# --------------------------------------------------------------------------
# ReceiveTenderClarification
# --------------------------------------------------------------------------


def receive_tender_clarification(*, tender: str, candidate_registration_id: str, question: str, inbound_event_id: str, received_at=None, related_addendum: str = "", user: str | None = None) -> dict[str, Any]:
	producer = candidate_gateway.require_producer(user)
	inbound = cstr(inbound_event_id).strip()
	if not inbound:
		fail("TND_CONTROL_INVALID", "The inbound event identity is required.")
	existing = frappe.db.get_value(DOCTYPE, {"producer": producer, "inbound_event_id": inbound}, ["name", "status"], as_dict=True)
	if existing:
		return {"ok": True, "idempotent": True, "action": "duplicate", "clarification": existing.name, "status": existing.status}
	root, version = draft_commands.load(tender)
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	if root.overall_status != "Published — open":
		fail("TND_STALE_VERSION", "Clarifications are received only while the Tender is Published — open.")
	registration = candidate_gateway.candidate_registration(tender=root.name, candidate_registration_id=candidate_registration_id)
	if not registration:
		fail("TND_CLARIFICATION_CANDIDATE_REQUIRED")
	received = get_datetime(received_at) if received_at else clock.now()
	if root.clarification_deadline and received >= get_datetime(root.clarification_deadline):
		# §8: preserve receipt evidence (the producer keeps its event); create nothing here.
		frappe.logger("kentender.tenders").info("clarification rejected late | tender=%s | inbound=%s | received=%s", root.name, inbound, received)
		fail("TND_CLARIFICATION_LATE", detail={"clarification_deadline": cstr(root.clarification_deadline), "received_at": cstr(received)})
	text = _clean(question)
	if not (10 <= len(text) <= 2000):
		fail("TND_CONTROL_INVALID", "The question must be 10–2,000 characters.", {"fields": {"question": "Enter a question of 10–2,000 characters."}})
	related = cstr(related_addendum).strip()
	if related:
		row = frappe.db.get_value("Tender Addendum", related, ["tender", "status"], as_dict=True)
		if not row or row.tender != root.name or row.status != "Issued":
			fail("TND_CONTROL_INVALID", "A related addendum must be an issued addendum of this Tender.")
	effective = bid_definition.current(root.name)
	with envelope.atomic("receive-clarification"):
		doc = envelope.insert(
			frappe.get_doc(
				{
					"doctype": DOCTYPE, "tender": root.name, "publication": root.publication, "bid_definition_id": (effective or {}).get("bid_definition_id", ""),
					"related_addendum": related or None, "candidate_registration_id": cstr(registration["candidate_registration_id"]), "producer": producer,
					"inbound_event_id": inbound, "question": text, "received_at": received, "status": AWAITING_RESPONSE, "record_version": 0, "fixture_namespace": root.fixture_namespace,
				}
			)
		)
		task = handoffs.open_task(root, version, task_type=handoffs.CLARIFICATION_RESPONSE, subject_type=DOCTYPE, subject_id=doc.name)
		envelope.bump(root)
		events.emit(
			tender=root.name, event_type="ClarificationReceived", command="ReceiveTenderClarification", idempotency_key=inbound, actor=producer, previous_status="", resulting_status=AWAITING_RESPONSE,
			record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name,
			payload={"received_at": cstr(received), "related_addendum": related, "bid_definition_id": doc.bid_definition_id, "producer": producer, "inbound_event_id": inbound},
			fixture_namespace=root.fixture_namespace,
		)
	return {"ok": True, "idempotent": False, "action": "received", "clarification": doc.name, "status": doc.status, "task": task.name, "record_version": root.record_version}


# --------------------------------------------------------------------------
# RespondToTenderClarification
# --------------------------------------------------------------------------


def _addendum_effective(root, addendum: str) -> bool:
	row = frappe.db.get_value("Tender Addendum", addendum, ["tender", "status", "successor_bid_definition"], as_dict=True)
	if not row or row.tender != root.name or row.status != "Issued":
		return False
	if not row.successor_bid_definition:
		return True
	return cstr(frappe.db.get_value("Tender Bid Definition", row.successor_bid_definition, "status")) in ("Effective", "Superseded")


def respond_to_tender_clarification(*, tender: str, clarification: str, response: str, affects_published_tender, expected_record_version, idempotency_key: str, response_audience: str = "", required_addendum: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment, role = authz.require_any_site_role((ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION), actor)
	affects = affects_published_tender in (True, 1, "1", "true", "True", "Yes")
	payload = {"tender": tender, "clarification": clarification, "response": response, "affects_published_tender": affects, "response_audience": response_audience, "required_addendum": required_addendum}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	if root.overall_status != "Published — open":
		fail("TND_STALE_VERSION", "Clarifications are answered only while the Tender is Published — open.")
	doc = envelope.locked(DOCTYPE, clarification)
	if doc.tender != root.name:
		authz.not_found()
	if doc.status in (ANSWERED, CLOSED):
		fail("TND_STALE_VERSION", "This clarification has already been answered.")
	text = _clean(response)
	if not (5 <= len(text) <= 2000):
		fail("TND_CONTROL_INVALID", "Enter a response of 5–2,000 characters.", {"fields": {"response": "Enter a response of 5–2,000 characters."}})
	addendum = cstr(required_addendum).strip()
	if affects:
		if not addendum or not _addendum_effective(root, addendum):
			# §5.1 "Require addendum": the answer is preserved and nothing is sent.
			with envelope.atomic("clarification-awaiting-addendum"):
				envelope.bump(doc, response=text, affects_published_tender=1, required_addendum=addendum or None, status=AWAITING_ADDENDUM)
				envelope.bump(root)
				events.emit(
					tender=root.name, event_type="ClarificationAwaitingAddendum", command="RespondToTenderClarification", idempotency_key=idempotency_key, actor=actor,
					assignment_snapshot=authz.authority_snapshot(assignment), previous_status=AWAITING_RESPONSE, resulting_status=AWAITING_ADDENDUM, record_version=root.record_version,
					subject_type=DOCTYPE, subject_id=doc.name, payload={"required_addendum": addendum}, fixture_namespace=root.fixture_namespace,
				)
			result = {
				"ok": True, "idempotent": False, "action": "awaiting_addendum", "tender": root.name, "record_version": root.record_version, "clarification": doc.name, "status": AWAITING_ADDENDUM,
				"reason_code": "TND_CLARIFICATION_ADDENDUM_REQUIRED", "message": "This answer would change the published Tender. Issue an addendum before sending it.",
			}
			envelope.record_command(idempotency_key=idempotency_key, command="RespondToTenderClarification", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
			return result
		audience = "All registered candidates"
	else:
		audience = cstr(response_audience)
		if audience not in AUDIENCES:
			fail("TND_CONTROL_INVALID", "Choose who should receive this answer.", {"fields": {"response_audience": "Choose Only the supplier who asked or All registered candidates."}})
	responded_at = clock.now()
	content = {"tender_reference": root.tender_reference, "question": cstr(doc.question), "response": text, "responded_at": cstr(responded_at), "required_addendum": addendum}
	response_digest = digest.sha256_hex(content)
	with envelope.atomic("respond-clarification"):
		envelope.bump(
			doc, response=text, affects_published_tender=1 if affects else 0, required_addendum=addendum or None, response_audience=audience,
			responded_by=actor, responded_at=responded_at, status=ANSWERED, response_digest=response_digest,
		)
		notices = candidate_notices.freeze(
			root, notice_type="Clarification response", subject_type=DOCTYPE, subject_id=doc.name, subject_digest=response_digest, content=content,
			only=cstr(doc.candidate_registration_id) if audience == "Asker only" else "",
		)
		decision = lifecycle.record_decision(root, version, decision="Respond to clarification", actor=actor, business_role=role, assignment=assignment, idempotency_key=idempotency_key, subject_type=DOCTYPE, subject_id=doc.name)
		handoffs.close_open(root, task_types=(handoffs.CLARIFICATION_RESPONSE,), subject_id=doc.name, decision=decision.name)
		envelope.bump(root)
		events.emit(
			tender=root.name, event_type="ClarificationAnswered", command="RespondToTenderClarification", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status=doc.status, resulting_status=ANSWERED, record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name,
			payload={"response_audience": audience, "affects_published_tender": affects, "required_addendum": addendum, "response_digest": response_digest, "notices": [n.name for n in notices], "source_identity_included": audience == "Asker only"},
			fixture_namespace=root.fixture_namespace,
		)
	result = {"ok": True, "idempotent": False, "action": "answered", "tender": root.name, "record_version": root.record_version, "clarification": doc.name, "status": ANSWERED, "response_audience": audience, "notices": len(notices)}
	envelope.record_command(idempotency_key=idempotency_key, command="RespondToTenderClarification", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def close_open_for_cancellation(root, *, reason: str) -> int:
	"""A cancelled Tender closes every unanswered clarification with a reason
	(no answer is sent; the cancellation notice reaches every candidate)."""
	count = 0
	for name in frappe.get_all(DOCTYPE, filters={"tender": root.name, "status": ("in", (AWAITING_RESPONSE, AWAITING_ADDENDUM))}, pluck="name"):
		envelope.bump(frappe.get_doc(DOCTYPE, name), status=CLOSED, closed_reason=reason)
		count += 1
	return count
