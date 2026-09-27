# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`SubmitBid` (BDS-CHG-001 v0.8 §5.7, §5.9, §5.10, §7.3; plan D8).

Submission is two-phase with a durable attempt — a documented exception to
the one-transaction rule (AGENTS.md §4.4), required because the tender
box's answer can be lost:

1. Under a lock on the bid, the trusted instant the complete signed request
   arrived is checked against the effective deadline (strictly before), every
   pre-signing check runs again, the canonical package is rebuilt, the
   signature is verified against it, and a `Bid Submission Attempt` with its
   own correlation is recorded and **committed**.
2. The exact package is deposited in the tender box under that correlation.
3. One outcome is committed together: Accepted — the immutable Submitted
   Version, the tender-box envelope, the bidder receipt and the bid's
   Submitted state; Rejected — the attempt closes, the Draft is unchanged and
   nothing else exists; no answer — the attempt stays Uncertain with a
   support reference, and the reconciler later asks the box about the same
   correlation, never dispatching a second deposit.

Nothing supplier-facing says Submitted except an accepted custody result
(§5.11 item 6, BDS01-AC-068). The request key names the attempt: the same key
and payload returns the same outcome; the same key with a different payload
is refused; a second attempt while one is pending is refused. Outcomes the
supplier must see (rejected, pending) are returned as data, so the recorded
attempt is never rolled back with an exception."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import (
	bid_context,
	clock,
	gateways,
	labels,
	package,
	records,
	references,
	signature,
	tenders_gateway,
)
from kentender_procurement.bid_submission.services.errors import MESSAGES, fail, field_errors

ATTEMPT = "Bid Submission Attempt"
VERSION = "Bid Submission Version"
ENVELOPE = "Tender Box Envelope"
RECEIPT = "Bid Receipt"
#: A Dispatching attempt older than this whose deposit the box never saw is definitively not received.
STALE_DISPATCH = timedelta(minutes=2)


def _hash(value: Any) -> str:
	return hashlib.sha256(package.canonical(value)).hexdigest()


def _lock(workspace: str) -> None:
	frappe.db.sql("select name from `tabBid Workspace` where name=%s for update", workspace)


def _attempt_by_key(key_hash: str):
	name = frappe.db.get_value(ATTEMPT, {"idempotency_key_hash": key_hash}, "name")
	return frappe.get_doc(ATTEMPT, name) if name else None


def submit_bid(*, bid_reference: str, signature_ref: str = "", confirmed=False, expected_record_version=None, idempotency_key: str = "", organisation: str = "", user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	key = cstr(idempotency_key).strip()
	if not key:
		fail("BDS_FIELD_INVALID", "A request key is required.", {"fields": {"idempotency_key": "A request key is required."}})
	key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
	payload_hash = _hash({"bid_reference": cstr(bid_reference), "signature": cstr(signature_ref), "confirmed": signature._ticked(confirmed)})
	at = clock.now()  # the trusted instant the complete signed request reached the server
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)  # masks another organisation's bid
	_lock(ctx.workspace.name)
	replay = _attempt_by_key(key_hash)
	if replay:
		if replay.bid_workspace != ctx.workspace.name or replay.payload_hash != payload_hash:
			fail("BDS_IDEMPOTENCY_CONFLICT")
		return outcome(replay)
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)  # re-read under the lock
	try:
		signatory, root = signature.submittable(ctx, actor=actor, at=at, expected_record_version=expected_record_version, confirmed=confirmed)
	except signature._Unconfirmed:
		return field_errors({"confirmed": signature.CONFIRMATION_MISSING})
	built = package.build(ctx, signatory=signatory, confirmed=True)
	verified = gateways.trust().verify(signature=cstr(signature_ref), package_digest=built.package_digest, user=actor, organisation=ctx.workspace.lead_organisation, at=at)
	if not verified.get("valid"):
		fail("BDS_SIGNATURE_INVALID", detail={"reason": cstr(verified.get("reason"))})
	attempt = records.insert(frappe.get_doc({
		"doctype": ATTEMPT, "correlation_id": references.correlation_id(ctx.workspace.tender, ctx.workspace.tender_reference), "bid_workspace": ctx.workspace.name,
		"tender": ctx.workspace.tender, "attempt_kind": "Initial submission", "idempotency_key_hash": key_hash, "payload_hash": payload_hash,
		"draft_version": int(ctx.workspace.current_draft_version or 0), "package_digest": built.package_digest, "response_snapshot_digest": built.response_snapshot_digest,
		"evidence_set_digest": built.evidence_set_digest, "signed_by": actor, "signatory_assignment": signatory["assignment_id"], "signature_ref": cstr(signature_ref),
		"signature_evidence_json": json.dumps({**verified["evidence"], "signed_at": str(verified["signed_at"])}, sort_keys=True, default=str),
		"summary_json": json.dumps({**built.summary, "tender_title": _title(ctx), "signatory_name": signatory["full_name"]}, sort_keys=True),
		"received_at": at, "status": "Dispatching", "simulation": int(bool(verified["evidence"].get("simulation"))),
	}))
	records.emit(
		"BidSubmissionAttemptRecorded", tender=ctx.workspace.tender, arrangement=ctx.arrangement.name, workspace=ctx.workspace.name, organisation=ctx.workspace.lead_organisation, actor=actor, at=at,
		payload={"correlation_id": attempt.correlation_id, "draft_version": attempt.draft_version, "package_digest": built.package_digest},
	)
	frappe.db.commit()  # plan D8: the attempt is durable before the deposit leaves
	try:
		answer = gateways.custody().deposit(correlation_id=attempt.correlation_id, tender=ctx.workspace.tender, package=built.content, package_digest=built.package_digest, deadline=root.submission_deadline, at=at)
	except Exception:
		frappe.log_error(title="Bid Submission: tender-box deposit without an answer", message=f"correlation {attempt.correlation_id}")
		answer = {"result": "Uncertain"}
	return finalize(attempt.name, answer)


def _title(ctx) -> str:
	published = tenders_gateway.published_tender(ctx.workspace.tender_reference, at=clock.now()) or {}
	return cstr(published.get("title"))


def finalize(attempt_name: str, answer: dict[str, Any]) -> dict[str, Any]:
	"""Commit the one outcome of an attempt from the tender box's answer.
	Idempotent: a resolved attempt keeps its outcome."""
	attempt = frappe.get_doc(ATTEMPT, attempt_name)
	_lock(attempt.bid_workspace)
	attempt.reload()
	if attempt.status in ("Accepted", "Rejected"):
		return outcome(attempt)
	at = clock.now()
	result = cstr(answer.get("result"))
	with records.atomic("finalize-submission"):
		if result == "Accepted":
			deadline = frappe.db.get_value("Tender", attempt.tender, "submission_deadline")
			if get_datetime(answer["accepted_at"]) >= get_datetime(deadline):
				_reject(attempt, cstr(answer.get("envelope_ref")), "The tender box accepted the deposit only after the deadline.", at)
			else:
				_accept(attempt, answer, at)
		elif result == "Rejected":
			_reject(attempt, cstr(answer.get("rejection_reference")), cstr(answer.get("rejection_reason")), at)
		else:
			_uncertain(attempt, at)
	return outcome(attempt)


def _accept(attempt, answer: dict[str, Any], at) -> None:
	workspace = frappe.get_doc("Bid Workspace", attempt.bid_workspace)
	summary = json.loads(attempt.summary_json or "{}")
	evidence = json.loads(attempt.signature_evidence_json or "{}")
	number = frappe.db.count(VERSION, {"bid_workspace": workspace.name}) + 1
	version_id = references.submission_version_id(workspace.name, number)
	accepted_at = get_datetime(answer["accepted_at"])
	envelope = records.insert(frappe.get_doc({
		"doctype": ENVELOPE, "envelope_id": answer["envelope_ref"], "tender": workspace.tender, "submission_version": version_id, "package_digest": attempt.package_digest,
		"accepted_at": accepted_at, "custody_receipt": answer["custody_receipt"], "custody_service": cstr(answer.get("service")), "box_state": "Sealed", "simulation": attempt.simulation,
	}))
	arrangement = frappe.get_doc("Bidder Arrangement", workspace.bidder_arrangement)
	receipt = records.insert(frappe.get_doc({
		"doctype": RECEIPT, "receipt_reference": references.receipt_reference(workspace.tender, workspace.tender_reference), "tender": workspace.tender,
		"tender_reference": workspace.tender_reference, "tender_title": summary.get("tender_title") or workspace.tender_reference, "bid_workspace": workspace.name,
		"bidder_name": cstr(arrangement.joint_venture_name) or cstr(arrangement.lead_legal_name), "submission_version": version_id, "version_number": number,
		"submitted_by": attempt.signed_by, "submitted_by_name": summary.get("signatory_name") or attempt.signed_by, "received_at": attempt.received_at, "accepted_at": accepted_at,
		"deadline_at": frappe.db.get_value("Tender", workspace.tender, "submission_deadline"), "summary_json": json.dumps({k: summary.get(k, "") for k in ("bid_total", "offered_item", "quantity", "delivery_date")}, sort_keys=True),
		"simulation": attempt.simulation,
	}))
	records.insert(frappe.get_doc({
		"doctype": VERSION, "bid_submission_version_id": version_id, "version_number": number, "bid_workspace": workspace.name, "tender": workspace.tender,
		"bid_definition_id": workspace.bid_definition_id, "definition_version": workspace.definition_version, "definition_digest": workspace.definition_digest,
		"organisation_snapshot": workspace.organisation_snapshot, "organisation_snapshot_version": workspace.organisation_snapshot_version, "draft_version": attempt.draft_version,
		"response_snapshot_digest": attempt.response_snapshot_digest, "evidence_set_digest": attempt.evidence_set_digest, "package_digest": attempt.package_digest,
		"signed_by": attempt.signed_by, "signatory_assignment": attempt.signatory_assignment, "signed_at": get_datetime(evidence.get("signed_at")),
		"signature_certificate_ref": cstr(evidence.get("certificate_ref")), "signature_verification_evidence": attempt.signature_evidence_json, "received_at": attempt.received_at,
		"accepted_at": accepted_at, "status": "Submitted", "status_since": accepted_at, "tender_box_envelope": envelope.name, "receipt": receipt.name, "attempt": attempt.name,
		"simulation": attempt.simulation,
	}))
	records.save(_set(attempt, status="Accepted", resolved_at=at, submission_version=version_id))
	records.bump(workspace, status="Submitted", status_since=accepted_at, current_submission_version=version_id)
	records.emit(
		"BidSubmitted", tender=workspace.tender, arrangement=workspace.bidder_arrangement, workspace=workspace.name, organisation=workspace.lead_organisation, actor=attempt.signed_by, at=accepted_at,
		payload={"correlation_id": attempt.correlation_id, "submission_version": version_id, "version_number": number, "receipt": receipt.name, "envelope": envelope.name, "package_digest": attempt.package_digest, "received_at": str(attempt.received_at)},
	)


def _reject(attempt, reference: str, reason: str, at) -> None:
	records.save(_set(attempt, status="Rejected", rejection_reference=reference, rejection_reason=reason[:140], resolved_at=at))
	records.emit("BidSubmissionRejected", tender=attempt.tender, workspace=attempt.bid_workspace, actor=attempt.signed_by, at=at, payload={"correlation_id": attempt.correlation_id, "rejection_reference": reference})


def _uncertain(attempt, at) -> None:
	if attempt.status != "Uncertain":
		reference = references.support_reference(attempt.tender, frappe.db.get_value("Tender", attempt.tender, "tender_reference"))
		records.save(_set(attempt, status="Uncertain", support_reference=reference))
		records.emit("BidSubmissionUncertain", tender=attempt.tender, workspace=attempt.bid_workspace, actor=attempt.signed_by, at=at, payload={"correlation_id": attempt.correlation_id, "support_reference": reference})


def _set(doc, **values):
	for field, value in values.items():
		doc.set(field, value)
	return doc


def _deadline_open(attempt) -> bool:
	deadline = frappe.db.get_value("Tender", attempt.tender, "submission_deadline")
	return bool(deadline) and clock.now() < get_datetime(deadline)


def outcome(attempt) -> dict[str, Any]:
	"""What the supplier is told about an attempt (§8, §10.13)."""
	if attempt.status == "Accepted":
		receipt = frappe.db.get_value(VERSION, attempt.submission_version, "receipt")
		return {"ok": True, "status": "Submitted", "receipt_reference": receipt, "bid_reference": attempt.bid_workspace}
	if attempt.status == "Rejected":
		return {
			"ok": False, "code": "BDS_CUSTODY_REJECTED", "message": MESSAGES["BDS_CUSTODY_REJECTED"], "rejection_reference": cstr(attempt.rejection_reference),
			"retry_allowed": _deadline_open(attempt), "current_time": labels.datetime_label(clock.now()),
		}
	return {
		"ok": False, "code": "BDS_SUBMISSION_UNCERTAIN", "message": MESSAGES["BDS_SUBMISSION_UNCERTAIN"], "correlation_id": attempt.correlation_id,
		"support_reference": cstr(attempt.support_reference),
	}


def reconcile_uncertain_attempts(limit: int = 50) -> dict[str, int]:
	"""Scheduler: resolve pending attempts from the tender box's answer for the
	same correlation, never by a second deposit (§5.10, BDS01-AC-064)."""
	box = gateways.custody()
	done = {"accepted": 0, "rejected": 0, "pending": 0}
	if box is None:
		return done
	now = clock.now()
	rows = frappe.get_all(ATTEMPT, filters={"status": ("in", ("Uncertain", "Dispatching"))}, fields=["name", "correlation_id", "status", "received_at", "creation"], order_by="creation asc", limit_page_length=limit)
	for row in rows:
		answer = box.status(correlation_id=row.correlation_id)
		if answer.get("result") == "NotReceived":
			if get_datetime(row.creation) > now - STALE_DISPATCH and row.status == "Dispatching":
				continue  # the deposit may still be on its way
			answer = {"result": "Rejected", "rejection_reference": "", "rejection_reason": "The deposit never reached the tender box."}
		if answer.get("result") not in ("Accepted", "Rejected"):
			done["pending"] += 1
			if row.status == "Dispatching":
				finalize(row.name, {"result": "Uncertain"})
			continue
		finalize(row.name, answer)
		done["accepted" if answer["result"] == "Accepted" else "rejected"] += 1
		frappe.db.commit()
	return done


def get_submission_status(*, bid_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""§11.5 View status: the latest attempt as the supplier may see it. A read;
	it never dispatches anything."""
	actor = cstr(user or frappe.session.user)
	workspace, _assignment = bid_context.workspace_for(bid_reference, actor=actor, organisation=organisation, at=clock.now())
	name = frappe.db.get_value(ATTEMPT, {"bid_workspace": workspace.name}, "name", order_by="creation desc")
	if not name:
		return {"status": "Not submitted", "text": "This bid has not been submitted."}
	attempt = frappe.get_doc(ATTEMPT, name)
	result = outcome(attempt)
	if attempt.status == "Accepted":
		return {"status": "Submitted", "text": "Your bid was accepted into the electronic tender box.", "receipt_reference": result["receipt_reference"]}
	if attempt.status == "Rejected":
		return {"status": "Rejected", "text": result["message"], "rejection_reference": result["rejection_reference"], "retry_allowed": result["retry_allowed"]}
	return {"status": "Confirmation pending", "text": result["message"], "correlation_id": attempt.correlation_id, "support_reference": result["support_reference"]}



def _acknowledgement(ctx) -> str:
	"""Who acknowledged the effective addendum and when, or that none is due."""
	keys = [f.key for f in ctx.model.fields_of("documents") if f.kind == "confirmation"]
	if not keys:
		return "No addendum to acknowledge"
	row = frappe.db.get_value(
		"Bid Draft Change", {"bid_workspace": ctx.workspace.name, "response_key": ("in", keys), "new_value": "true"}, ["actor", "changed_at"], as_dict=True, order_by="changed_at desc",
	)
	if not row or not all(ctx.values.get(k) for k in keys):
		return "Not yet acknowledged"
	return f"{frappe.utils.get_fullname(row.actor)} · {labels.datetime_label(row.changed_at)}"


def get_submit_bid(*, bid_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""BDS-DES-12 read (§10.13, §11.5): the trusted current server time, the
	consequence, the submission summary, the signatory and certificate, the
	final confirmation text and — from the same checks `SubmitBid` runs —
	whether this person can submit now and, if not, the exact §8 reason. It
	creates nothing."""
	from kentender_procurement.bid_submission.services import price, projection, readiness, tender_security
	from kentender_procurement.bid_submission.services.errors import BidSubmissionError

	actor = cstr(user or frappe.session.user)
	at = clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	ws = ctx.workspace
	root = tenders_gateway.tender_root(ws.tender_reference)
	deadline = labels.datetime_label(root.submission_deadline) if root else ""
	blocked = None
	try:
		signature.submittable(ctx, actor=actor, at=at, expected_record_version=ws.record_version, confirmed=True)
	except BidSubmissionError as error:
		blocked = {"code": error.code, "message": str(error), "detail": error.detail}
	confirm = next((f for f in ctx.model.fields_of(readiness.REVIEW_TASK) if f.field_key == package.CONFIRMED_FIELD), None)
	calc = price.summary(ctx)
	security = tender_security.response(ctx)
	certificate_status = ""
	if ctx.assignment.get("responsibility") == "Authorised Signatory" and gateways.trust_healthy():
		certificate_status = "Ready" if gateways.trust().certificate(user=actor, organisation=ws.lead_organisation, at=at)["status"] == "Ready" else "Required"
	return {
		"current_time": labels.datetime_label(at),
		"consequence": f"After submission, this Version cannot be edited. You may prepare a replacement or withdraw it before {deadline}. The bid will not be opened or evaluated now.",
		"summary": {
			"tender": ws.tender_reference, "tender_title": _title(ctx), "bidder": ctx.tenderer_name, "bid": ws.name, "bid_total": calc["total"], "deadline": deadline,
			"addendum_acknowledged": _acknowledgement(ctx), "security_receipt": security.get("physical_receipt_status", "") if security.get("required") else "Not required",
		},
		"signatory": {
			"name": cstr(frappe.utils.get_fullname(actor)), "job_title": cstr(ctx.assignment.get("job_title")), "responsibility": cstr(ctx.assignment.get("responsibility")),
			"authority_evidence": "Available" if ctx.assignment.get("signatory_ready") else "Not available", "certificate": certificate_status,
		},
		"confirmation_label": projection.label(ctx, confirm) if confirm else "",
		"dialog_text": "KenTender will apply your digital signature and submit this exact Version to the electronic tender box. Wait for the submission receipt to confirm acceptance. If confirmation takes longer, you can return through View status; do not submit again while the same attempt is being checked.",
		"can_submit": blocked is None, "blocked": blocked,
		"record_version": int(ws.record_version or 0), "draft_version": int(ws.current_draft_version or 0),
	}
