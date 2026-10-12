# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Tender's tender-security statements after publication (Project Owner, 10 October 2026).

Two cases, kept apart:

1. **Missing system data, requirement already explicit in the published Tender.** A Tender published before it stated its
   submission method and original delivery has the requirement in its issued documents but not in structured form.
   `CorrectSecurityStatement` records it as an auditable *correction* (who, when, where the published Tender states it, why),
   one per Tender, and never alters the published definition or any published requirement. Bid Submission reads the correction
   as the Tender's statement. Only the Head of Procurement Function corrects; a Tender that already states both, or already has
   a correction, cannot be corrected (a change is an addendum).
2. **A requirement that genuinely changes.** That is a formal addendum before closing (`addenda`, affected references
   `tender_security_method` and `tender_security_original`), communicated to bidders under the existing channel confirmation and
   subject to the deadline-extension rules. A closed Tender keeps the requirements it issued.

Reading writes nothing."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import bid_definition, controls, envelope, events
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.security_statement_review import stated_in

DOCTYPE = "Tender Security Statement"
ORIGINALS = controls.SECURITY_ORIGINALS


def consistent(method: str, original: str) -> bool:
	"""A paper instrument needs its original delivered."""
	return not (method == controls.SECURITY_PAPER and original != "Required")


def overlay(tender_name: str) -> dict[str, str]:
	"""The correction's two facts for this Tender, or {}."""
	row = frappe.db.get_value(DOCTYPE, {"tender": tender_name}, ["submission_method", "original_delivery"], as_dict=True)
	return {"submission_method": cstr(row.submission_method), "original_delivery": cstr(row.original_delivery)} if row else {}


def correct_security_statement(*, tender: str, submission_method: str, original_delivery: str, source_reference: str, basis: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""`CorrectSecurityStatement` (Head of Procurement Function): record what the published Tender already states."""
	actor = authz.actor(user)
	assignment = authz.require_hopf(actor)
	payload = {"tender": tender, "submission_method": submission_method, "original_delivery": original_delivery, "source_reference": source_reference, "basis": basis}
	replay = envelope.replay_or_none(idempotency_key, payload, command="CorrectSecurityStatement", actor=actor)
	if replay:
		return replay
	fields: dict[str, str] = {}
	if submission_method not in controls.SECURITY_METHODS:
		fields["submission_method"] = "Choose one of: " + ", ".join(controls.SECURITY_METHODS) + "."
	if original_delivery not in ORIGINALS:
		fields["original_delivery"] = "Choose one of: " + ", ".join(ORIGINALS) + "."
	elif not fields and not consistent(submission_method, original_delivery):
		fields["original_delivery"] = "A paper tender security needs its original delivered."
	source = " ".join(cstr(source_reference).split())
	text = " ".join(cstr(basis).split())
	if not (3 <= len(source) <= 200):
		fields["source_reference"] = "Say where the published Tender states it (3–200 characters), for example the clause of its Tender Data Sheet."
	if not (20 <= len(text) <= 1000):
		fields["basis"] = "Explain, in 20–1,000 characters, how the published Tender already makes this requirement explicit."
	if fields:
		envelope.release_claim(idempotency_key)
		return {"ok": False, "code": "TND_CONTROL_INVALID", "message": "Check the highlighted value.", "errors": fields}
	root = frappe.get_doc("Tender", tender) if frappe.db.exists("Tender", tender) else None
	if root is None or not root.published_at:
		envelope.release_claim(idempotency_key)
		raise frappe.DoesNotExistError("Tender not found")
	envelope.check_record_version(root, expected_record_version)
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	current = bid_definition.current(root.name)
	if frappe.db.exists(DOCTYPE, {"tender": root.name}) or not current or stated_in(current["definition"]) is not False:
		fail("TND_STALE_VERSION", "This Tender already states how its tender security is submitted. A change to it is made by addendum.")
	with envelope.atomic("correct-security-statement"):
		row = envelope.insert(frappe.get_doc({
			"doctype": DOCTYPE, "tender": root.name, "tender_reference": root.tender_reference, "submission_method": submission_method, "original_delivery": original_delivery,
			"source_reference": source, "basis": text, "corrected_by": actor, "corrected_at": frappe.utils.now_datetime(), "fixture_namespace": root.fixture_namespace,
		}))
		envelope.bump(root)
		events.emit(tender=root.name, event_type="TenderSecurityStatementCorrected", command="CorrectSecurityStatement", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status=root.overall_status, resulting_status=root.overall_status, record_version=root.record_version, subject_type=DOCTYPE, subject_id=row.name,
			payload={"submission_method": submission_method, "original_delivery": original_delivery, "source_reference": source}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "tender": root.name, "record_version": root.record_version, "statement": row.name}
	envelope.record_command(idempotency_key=idempotency_key, command="CorrectSecurityStatement", payload=payload, result=result, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result
