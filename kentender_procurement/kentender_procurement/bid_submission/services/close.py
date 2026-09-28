# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`CloseBidSubmission` and the Bid Opening hand-off (BDS-CHG-001 v0.8 §5.9,
§7.3; owner decision OD-H; plan D9).

Tenders closes a Tender's submission period by the system at its effective
deadline and emits `TenderSubmissionPeriodEnded` for the consumer
"bid-submission". The scheduler hands each such event to
`close_bid_submission`, once per Tender:

- pending submission attempts are first resolved from the tender box's answer
  (any the box still cannot answer are listed, never guessed);
- the tender box is closed and returns its own inventory of accepted
  envelopes;
- a Draft never submitted becomes Closed without submission and never enters
  the inventory; an unsent replacement Draft closes and its submitted Version
  stays current; withdrawn and submitted bids keep their state; every
  arrangement closes;
- one immutable Bid Opening hand-off records the closed box, the deadline
  evidence, every sealed envelope with its receipt, custody acknowledgement
  and replacement/withdrawal lineage, and the physical tender-security intake
  inventory and private matches — identities, instants and digests only,
  never bid content — addressed to the consumer "bid-opening".

No user, administrator or technical role can reopen, extend or backdate the
box: there is no command for it, and every submission, replacement and
withdrawal command checks the trusted instant against the deadline itself.
The same close run twice changes nothing. `TenderOpenForSubmission` (consumer
"bidder-service") is acknowledged here too: the portal reads open Tenders
live from Tenders, so nothing is stored for it."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import clock, gateways, package, records, submission, tenders_gateway

CLOSE = "Bid Submission Close"
HANDOFF = "Bid Opening Handoff"
HANDOFF_VERSION = "1.0"
PERIOD_ENDED, OPEN_FOR_SUBMISSION = "TenderSubmissionPeriodEnded", "TenderOpenForSubmission"
CONSUMER, OPEN_CONSUMER = "bid-submission", "bidder-service"
UNSUBMITTED = ("Draft", "Needs attention", "Ready to submit")


def _suffix(tender_reference: str) -> str:
	return cstr(tender_reference).removeprefix("TND-")


def close_bid_submission(*, tender: str, source_event: str = "", tenders_handoff: str = "") -> dict[str, Any]:
	existing = frappe.db.get_value(CLOSE, {"tender": tender}, ["name", "bid_opening_handoff"], as_dict=True)
	if existing:
		return {"ok": True, "idempotent": True, "close": existing.name, "handoff": existing.bid_opening_handoff}
	root = frappe.get_doc("Tender", tender)
	deadline = get_datetime(root.submission_deadline)
	at = clock.now()
	if at < deadline:
		frappe.throw("The submission deadline has not been reached.")
	unresolved = _resolve_pending(tender)
	box = gateways.custody()
	if box is None or not gateways.custody_healthy():
		frappe.throw("The tender box is unavailable; the close runs again on the next scheduler pass.")
	custody = box.close_box(tender=tender, at=at)
	with records.atomic("close-bid-submission"):
		drafts_closed = _close_workspaces(tender, at)
		for name in frappe.get_all("Bidder Arrangement", filters={"tender": tender, "status": "Active"}, pluck="name"):
			records.bump(frappe.get_doc("Bidder Arrangement", name), status="Closed", status_since=at)
		close = records.insert(frappe.get_doc({
			"doctype": CLOSE, "close_id": f"BSC-{_suffix(root.tender_reference)}", "tender": tender, "tender_reference": root.tender_reference, "effective_deadline": deadline,
			"closed_at": at, "source_event": source_event or "manual", "tenders_handoff": tenders_handoff, "custody_close_receipt": custody["close_receipt"],
			"envelopes_sealed": frappe.db.count("Tender Box Envelope", {"tender": tender}), "drafts_closed": drafts_closed,
		}))
		body = handoff_payload(root, close, custody, unresolved)
		handoff = records.insert(frappe.get_doc({
			"doctype": HANDOFF, "handoff_id": f"BOH-{_suffix(root.tender_reference)}", "tender": tender, "tender_reference": root.tender_reference, "handoff_version": HANDOFF_VERSION,
			"payload_json": package.canonical(body).decode("utf-8"), "handoff_digest": package.sha256(package.canonical(body)), "issued_at": at, "consumer": "bid-opening", "delivery_status": "Pending",
		}))
		records.save(submission._set(close, bid_opening_handoff=handoff.name))
		for name in frappe.get_all("Tender Box Envelope", filters={"tender": tender}, pluck="name"):
			records.save(submission._set(frappe.get_doc("Tender Box Envelope", name), box_state="Handed to Bid Opening"))
		records.emit(
			"BidSubmissionClosed", tender=tender, actor="Administrator", at=at,
			payload={"close": close.name, "handoff": handoff.name, "handoff_digest": handoff.handoff_digest, "envelopes": close.envelopes_sealed, "drafts_closed": drafts_closed, "unresolved_attempts": unresolved},
		)
	return {"ok": True, "idempotent": False, "close": close.name, "handoff": handoff.name, "drafts_closed": drafts_closed}


def _resolve_pending(tender: str) -> list[str]:
	box = gateways.custody()
	for row in frappe.get_all("Bid Submission Attempt", filters={"tender": tender, "status": ("in", ("Dispatching", "Uncertain"))}, fields=["name", "correlation_id"]):
		answer = box.status(correlation_id=row.correlation_id) if box else {"result": "Uncertain"}
		if answer.get("result") == "NotReceived":
			answer = {"result": "Rejected", "rejection_reference": "", "rejection_reason": "The deposit never reached the tender box."}
		if answer.get("result") in ("Accepted", "Rejected"):
			submission.finalize(row.name, answer)
		elif frappe.db.get_value("Bid Submission Attempt", row.name, "status") == "Dispatching":
			submission.finalize(row.name, {"result": "Uncertain"})
	return frappe.get_all("Bid Submission Attempt", filters={"tender": tender, "status": "Uncertain"}, pluck="correlation_id", order_by="creation asc")


def _close_workspaces(tender: str, at) -> int:
	closed = 0
	for name in frappe.get_all("Bid Workspace", filters={"tender": tender}, pluck="name", order_by="name asc"):
		ws = frappe.get_doc("Bid Workspace", name)
		if ws.status not in UNSUBMITTED:
			continue
		if ws.current_submission_version:
			records.bump(ws, status="Submitted", status_since=at)  # the unsent replacement closes; its Version stays current
			records.emit("ReplacementDraftClosed", tender=tender, workspace=ws.name, actor="Administrator", at=at, payload={"current_submission_version": ws.current_submission_version, "draft_version": ws.current_draft_version})
		else:
			records.bump(ws, status="Closed without submission", status_since=at)
			closed += 1
	return closed


def handoff_payload(root, close, custody: dict[str, Any], unresolved: list[str]) -> dict[str, Any]:
	"""Identities, instants, digests and lineage only; no response, price,
	filename or evidence content (§5.9 item 8, §12.3)."""
	tender = root.name
	versions = frappe.get_all(
		"Bid Submission Version", filters={"tender": tender},
		fields=[
			"name", "version_number", "bid_workspace", "tender_box_envelope", "receipt", "received_at", "accepted_at", "package_digest", "status", "predecessor_submission_version",
			"bid_definition_id", "definition_version", "definition_digest",
		],
		order_by="bid_workspace asc, version_number asc", limit_page_length=0,
	)
	envelopes = {e.name: e for e in frappe.get_all("Tender Box Envelope", filters={"tender": tender}, fields=["name", "custody_receipt", "accepted_at"], limit_page_length=0)}
	arrangements = dict(frappe.get_all("Bid Workspace", filters={"tender": tender}, fields=["name", "bidder_arrangement"], as_list=True))
	intakes = frappe.get_all(
		"Tender Security Intake", filters={"tender": tender},
		fields=["intake_reference", "instrument_type", "issuer", "instrument_reference", "amount", "currency", "received_at", "deadline_class", "recorded_by", "recorded_at"],
		order_by="recorded_at asc", limit_page_length=0,
	)
	matches = frappe.get_all("Tender Security Intake Match", filters={"tender": tender}, fields=["*"], limit_page_length=0)
	return {
		"handoff_version": HANDOFF_VERSION,
		"tender": {"tender": tender, "tender_reference": root.tender_reference, "tenders_submission_handoff": close.tenders_handoff},
		"closed_box": {
			"close_id": close.name, "effective_deadline": str(close.effective_deadline), "closed_at": str(close.closed_at), "custody_close_receipt": custody["close_receipt"],
			"custody_inventory": sorted(custody.get("envelopes") or []), "custody_service": cstr(custody.get("service")), "simulation": bool(custody.get("simulation")),
		},
		"envelopes": [
			{
				"envelope_id": v.tender_box_envelope, "submission_version": v.name, "version_number": int(v.version_number), "bid_reference": v.bid_workspace,
				"bidder_arrangement": cstr(arrangements.get(v.bid_workspace)), "receipt_reference": v.receipt, "received_at": str(v.received_at), "accepted_at": str(v.accepted_at),
				"package_digest": v.package_digest, "custody_receipt": envelopes[v.tender_box_envelope].custody_receipt if v.tender_box_envelope in envelopes else "",
				"status": v.status, "predecessor_submission_version": cstr(v.predecessor_submission_version),
				# BDS06-AC-014: the exact published definition the envelope answers
				"bid_definition_id": v.bid_definition_id, "definition_version": int(v.definition_version or 0), "definition_digest": v.definition_digest,
			}
			for v in versions
		],
		"changes": [
			dict(c) | {"acknowledged_at": str(c.acknowledged_at)}
			for c in frappe.get_all(
				"Bid Submission Change", filters={"tender": tender},
				fields=["submission_change_id", "change_type", "bid_workspace", "affected_submission_version", "new_submission_version", "acknowledgement_ref", "acknowledged_at"],
				order_by="acknowledged_at asc", limit_page_length=0,
			)
		],
		"unresolved_attempts": unresolved,
		"physical_tender_security": {
			"intakes": [{**dict(i), "amount": str(i.amount), "received_at": str(i.received_at), "recorded_at": str(i.recorded_at)} for i in intakes],
			"matches": [_match(m) for m in matches],
		},
	}


def _match(row) -> dict[str, Any]:
	fields = {k: cstr(v) for k, v in dict(row).items() if k in ("intake", "tender_security_intake", "bid_workspace", "status", "matched_at")}
	return dict(sorted(fields.items()))


def consume_tender_events(tender: str | None = None) -> dict[str, int]:
	"""Scheduler: close each Tender whose submission period Tenders has ended,
	one Tender per transaction; acknowledge open-for-submission events.
	`tender` limits a seed or test run to its own Tender."""
	done = {"closed": 0, "failed": 0, "acknowledged": 0}

	def mine(events):
		return [e for e in events if not tender or e.tender == tender]

	for event in mine(tenders_gateway.pending_events(event_type=PERIOD_ENDED, consumer=CONSUMER)):
		try:
			with records.running("CloseBidSubmission", event.name):
				close_bid_submission(tender=event.tender, source_event=event.name, tenders_handoff=cstr(event.subject_id))
			tenders_gateway.mark_event_consumed(event, consumer=CONSUMER)
			frappe.db.commit()
			done["closed"] += 1
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title="Bid Submission: close failed", message=f"Tender {event.tender}")
			done["failed"] += 1
	for event in mine(tenders_gateway.pending_events(event_type=OPEN_FOR_SUBMISSION, consumer=OPEN_CONSUMER)):
		tenders_gateway.mark_event_consumed(event, consumer=OPEN_CONSUMER)
		frappe.db.commit()
		done["acknowledged"] += 1
	return done

