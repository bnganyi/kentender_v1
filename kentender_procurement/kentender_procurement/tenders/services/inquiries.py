# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.9 / §7.4 — addendum inquiries (plan D8).

Tenders creates no inquiry on behalf of a candidate: `ReceiveAddendumInquiry`
consumes an authenticated bidder-facing event from a registered producer
identity (a service user carrying the `Tender Inquiry Producer` role —
never a business responsibility) and deduplicates it on
`(producer, inbound_event_id)`. An inquiry received after the inquiry
deadline (the later of the clarification deadline and the addendum's
effective instant plus the governed inquiry window) is preserved as `Late` and cannot be answered. The
responding professional classifies the response; a requirement-affecting
response is broadcast to every registered candidate through an outbox
event that never carries the source identity (TPR08-AC-063..065)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.tenders.services import clock, digest, draft_commands, envelope, events, lifecycle
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import INQUIRY_PRODUCER_ROLE, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER

DOCTYPE = "Tender Addendum Inquiry"
TASK_RESPONSE = "Inquiry response"
BROADCAST_EVENT = "AddendumInquiryBroadcast"
DIRECT_EVENT = "AddendumInquiryAnswered"
# Governed inquiry window: an issued addendum re-opens clarification for this
# many days from its effective instant, never beyond the effective deadline.
INQUIRY_WINDOW_DAYS = 7


def inquiry_deadline(root, addendum_row):
	"""The later of the Tender's clarification deadline and the addendum's
	effective instant plus the inquiry window, capped at the effective
	submission deadline."""
	candidates = []
	if root.clarification_deadline:
		candidates.append(get_datetime(root.clarification_deadline))
	if addendum_row and addendum_row.get("effective_at"):
		candidates.append(get_datetime(addendum_row.effective_at) + timedelta(days=INQUIRY_WINDOW_DAYS))
	if not candidates:
		return None
	deadline = max(candidates)
	if root.submission_deadline:
		deadline = min(deadline, get_datetime(root.submission_deadline))
	return deadline


def ensure_producer_role() -> None:
	if not frappe.db.exists("Role", INQUIRY_PRODUCER_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": INQUIRY_PRODUCER_ROLE, "desk_access": 0}).insert(ignore_permissions=True)


def require_producer(user: str | None = None) -> str:
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest" or INQUIRY_PRODUCER_ROLE not in set(frappe.get_roles(principal)):
		fail("TND_RESPONSIBILITY_REQUIRED", "Only the registered bidder-facing service may deliver an inquiry.")
	return principal


def receive_addendum_inquiry(*, tender: str, addendum: str, candidate_identity: str, question: str, received_at, inbound_event_id: str, user: str | None = None) -> dict[str, Any]:
	producer = require_producer(user)
	inbound = cstr(inbound_event_id).strip()
	if not inbound:
		fail("TND_CONTROL_INVALID", "The inbound event identity is required.")
	existing = frappe.db.get_value(DOCTYPE, {"producer": producer, "inbound_event_id": inbound}, ["name", "status"], as_dict=True)
	if existing:
		return {"ok": True, "idempotent": True, "action": "duplicate", "inquiry": existing.name, "status": existing.status}
	candidate = cstr(candidate_identity).strip()
	text = " ".join(cstr(question).split())
	if not candidate:
		fail("TND_CONTROL_INVALID", "The authenticated candidate identity is required.")
	if not (5 <= len(text) <= 2000):
		fail("TND_CONTROL_INVALID", "The question must be 5–2,000 characters.")
	root, version = draft_commands.load(tender)
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	addendum_row = frappe.db.get_value("Tender Addendum", addendum, ["name", "tender", "status", "addendum_reference", "effective_at"], as_dict=True)
	if not addendum_row or addendum_row.tender != root.name or addendum_row.status != "Issued":
		fail("TND_STALE_VERSION", "Inquiries can be received only about an issued addendum.")
	received = get_datetime(received_at) if received_at else clock.now()
	deadline = inquiry_deadline(root, addendum_row)
	late = deadline is not None and received > deadline
	with envelope.atomic("receive-inquiry"):
		doc = envelope.insert(
			frappe.get_doc(
				{
					"doctype": DOCTYPE, "tender": root.name, "addendum": addendum_row.name, "producer": producer, "inbound_event_id": inbound, "candidate_identity": candidate, "question": text,
					"received_at": received, "status": "Late" if late else "Awaiting response", "record_version": 0, "fixture_namespace": root.fixture_namespace,
				}
			)
		)
		task = None
		if not late:
			task = lifecycle.new_task(root, version, task_type=TASK_RESPONSE, business_role=ROLE_PROCUREMENT_OFFICER, subject_type=DOCTYPE, subject_id=doc.name)
		envelope.bump(root)
		events.emit(tender=root.name, event_type="AddendumInquiryReceived", command="ReceiveAddendumInquiry", idempotency_key=inbound, actor=producer, previous_status="", resulting_status=doc.status, record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, payload={"addendum": addendum_row.addendum_reference, "received_at": cstr(received), "late": late, "inquiry_deadline": cstr(deadline), "producer": producer, "inbound_event_id": inbound}, fixture_namespace=root.fixture_namespace)
	return {"ok": True, "idempotent": False, "action": "received", "inquiry": doc.name, "status": doc.status, "task": task.name if task else "", "record_version": root.record_version}


def respond_to_addendum_inquiry(*, tender: str, inquiry: str, response: str, affects_requirements, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment, role = authz.require_any_site_role((ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION), actor)
	affects = affects_requirements in (True, 1, "1", "true", "True", "Yes")
	payload = {"tender": tender, "inquiry": inquiry, "response": response, "affects_requirements": affects}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	doc = envelope.locked(DOCTYPE, inquiry)
	if doc.tender != root.name:
		authz.not_found()
	if doc.status == "Late":
		fail("TND_INQUIRY_LATE")
	if doc.status == "Answered":
		fail("TND_STALE_VERSION", "This inquiry has already been answered.")
	text = " ".join(cstr(response).split())
	if not (5 <= len(text) <= 2000):
		fail("TND_CONTROL_INVALID", "Enter a response of 5–2,000 characters.", {"fields": {"response": "Enter a response of 5–2,000 characters."}})
	responded_at = clock.now()
	with envelope.atomic("respond-inquiry"):
		broadcast_digest = ""
		if affects:
			broadcast_payload = {"tender_reference": root.tender_reference, "addendum": cstr(frappe.db.get_value("Tender Addendum", doc.addendum, "addendum_reference")), "question": cstr(doc.question), "response": text, "responded_at": cstr(responded_at)}
			broadcast_digest = digest.sha256_hex(broadcast_payload)
			events.emit(tender=root.name, event_type=BROADCAST_EVENT, command="RespondToAddendumInquiry", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Awaiting response", resulting_status="Answered", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, status="Pending", consumer="bidder-service", payload={"broadcast": broadcast_payload, "broadcast_digest": broadcast_digest, "audience": "every registered candidate", "source_identity_included": False}, fixture_namespace=root.fixture_namespace)
		else:
			events.emit(tender=root.name, event_type=DIRECT_EVENT, command="RespondToAddendumInquiry", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Awaiting response", resulting_status="Answered", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, status="Pending", consumer="bidder-service", payload={"response": text, "responded_at": cstr(responded_at), "audience": "the asking candidate", "candidate_identity_reference": doc.name}, fixture_namespace=root.fixture_namespace)
		envelope.bump(doc, response=text, affects_requirements=1 if affects else 0, responded_by=actor, responded_at=responded_at, status="Answered", broadcast_status="Broadcast" if affects else "Not required", broadcast_digest=broadcast_digest)
		decision = lifecycle.record_decision(root, version, decision="Respond to addendum inquiry", actor=actor, business_role=role, assignment=assignment, idempotency_key=idempotency_key, subject_type=DOCTYPE, subject_id=doc.name)
		task = lifecycle.open_task(root, task_type=TASK_RESPONSE, subject_id=doc.name)
		if task:
			lifecycle.complete_task(task, decision.name)
		envelope.bump(root)
	result = {"ok": True, "idempotent": False, "action": "answered", "tender": root.name, "record_version": root.record_version, "inquiry": doc.name, "affects_requirements": affects, "broadcast_status": doc.broadcast_status, "broadcast_digest": broadcast_digest}
	envelope.record_command(idempotency_key=idempotency_key, command="RespondToAddendumInquiry", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result
