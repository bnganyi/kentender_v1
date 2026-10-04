# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CompleteOpening, an internal transition (BOP-CHG-001 v0.10 §5 Opening
complete, §7 CompleteOpening; binding row → PRC `FinalizeProceeding`, then
BOP completion and a conditional once-only handoff; BOP-A10, BOP-A19).

After the last verified proof, the system finalizes the Proceeding and then
completes the opening, once, with the system as actor. Only an opening that
opened bids issues one immutable Evaluation handoff: the exact opened
packages and their published mapping, the register and the opening record
with their digests, and the exceptions (comments for Evaluation flagged).
An empty opening ends "Opening complete — no bids to evaluate" with no
handoff. A failed finalization leaves the opening awaiting signatures. This
appoints no evaluator, creates no assessment and grants no access."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_opening.services import appointment, ceremony, clock, custody, finish, people, prc, records, register_copy

HANDOFF = "Evaluation Handoff"


def _handoff_payload(doc) -> dict[str, Any]:
	manifest = custody.closed_manifest(doc.tender)
	sealed = {e["envelope_id"]: e for e in (manifest or {}).get("payload", {}).get("envelopes", [])}
	register = frappe.get_doc(finish.REGISTER, doc.register)
	minutes = frappe.db.get_value("Proceeding Minutes Version", {"proceeding": doc.proceeding, "state": "Finalized"}, ["minutes_version_id", "content_digest"], as_dict=True)
	exceptions = frappe.get_all(ceremony.EXCEPTION, filters={"opening_case": doc.name, "exception_class": ("in", ("Repeat request", "Procedural comment",
		"Comment for Evaluation"))}, fields=["exception_id", "exception_class", "entry", "observed_fact", "outcome"], order_by="recorded_at asc")
	return {
		"handoff_version": "1.0", "tender": doc.tender, "tender_reference": doc.tender_reference, "opening": doc.opening_id,
		"packages": [{"entry": e.entry_id, "number": e.entry_number, "envelope_id": e.envelope_id, "receipt_reference": e.receipt_reference,
			"submission_version": e.submission_version, "package_digest": e.package_digest, "render_digest": e.render_digest,
			"bid_definition_id": cstr(sealed.get(e.envelope_id, {}).get("bid_definition_id")), "definition_version": cint(sealed.get(e.envelope_id, {}).get("definition_version")),
			"definition_digest": cstr(sealed.get(e.envelope_id, {}).get("definition_digest"))} for e in ceremony.entries(doc.name)],
		"register": {"register_id": register.register_id, "digest": register.register_digest},
		"opening_record": {"minutes_version": minutes.minutes_version_id, "digest": minutes.content_digest} if minutes else None,
		"exceptions": [{**dict(x), "for_evaluation": x.exception_class == "Comment for Evaluation"} for x in exceptions],
	}


def complete_if_ready(doc, key: str) -> bool:
	from kentender_procurement.proceedings.services import finalize
	from kentender_procurement.proceedings.services.errors import ProceedingsError

	proceeding = frappe.get_doc("Proceeding", doc.proceeding)
	if finalize.missing_proofs(proceeding):
		return False
	try:
		finalized = finalize.finalize_proceeding(**prc.ref(doc.name), idempotency_key=prc.key(key, "finalize"), actor=prc.SYSTEM_ACTOR)
	except ProceedingsError:
		frappe.log_error(title=f"Opening record could not be finalized for {doc.name}")
		return False
	at = clock.now()
	doc.update({"state": "Opening complete", "completed_at": at, "last_committed_event": finalized["event_id"]})
	if doc.outcome == "Bids opened" and not frappe.db.exists(HANDOFF, {"tender": doc.tender}):
		payload = _handoff_payload(doc)
		body = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)
		handoff = records.insert(frappe.get_doc({
			"doctype": HANDOFF, "handoff_id": f"EV-IN-{doc.tender_reference.removeprefix('TND-')}-01", "tender": doc.tender, "opening_case": doc.name,
			"payload_json": body, "handoff_digest": records.digest(payload), "issued_at": at, "consumer": "evaluation", "delivery_status": "Pending",
		}))
		doc.evaluation_handoff = handoff.name
	register_copy.release_pending(doc)
	_notify_completed(doc)
	return True


def _notify_completed(doc) -> None:
	from kentender_core.services.notification_service import emit_notification_log

	subject = f"Opening complete for {doc.tender_reference}"
	for user in {*(m["member_user"] for m in appointment.roster(doc.name)), *people.accounting_officers()}:
		emit_notification_log(for_user=user, subject=subject, message=subject, document_type=records.CASE, document_name=doc.name, event_type="Opening complete",
			entity_scope="Bid Opening", route=f"/app/tenders/{doc.tender_reference}/opening", correlation_key=f"bop-complete:{doc.name}")
