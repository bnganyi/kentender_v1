# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §5.1 (last row) / §7.4 `CloseTenderSubmissionPeriod`
(plan D9). Internal — never a user action: an hourly scheduler job closes
every Published — open Tender whose effective submission deadline has
passed, one Tender per transaction; seeds and tests inject the clock. The
close writes one immutable `Tender Submission Handoff` (the package,
publication history, effective deadline and addendum trail) and emits the
`TenderSubmissionPeriodEnded` outbox event for the Bid Submission owner,
which does not exist in this release (FOLLOW_UPS FU-13)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.tenders.services import channel_confirmation, clock, digest, documents, draft_commands, envelope, events, lifecycle
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail

HANDOFF_DOCTYPE = "Tender Submission Handoff"
HANDOFF_VERSION = "1.0"
EVENT_TYPE = "TenderSubmissionPeriodEnded"
CONSUMER = "bid-submission"


def build_handoff_payload(root) -> dict[str, Any]:
	publication = frappe.get_doc("Tender Publication", root.publication)
	version = frappe.get_doc("Tender Version", publication.tender_version)
	addenda = frappe.get_all("Tender Addendum", filters={"tender": root.name, "status": "Issued"}, fields=["name", "addendum_reference", "addendum_number", "addendum_digest", "affected_reference_key", "previous_value", "revised_value", "revised_submission_deadline", "effective_at"], order_by="addendum_number asc")
	return {
		"handoff_version": HANDOFF_VERSION,
		"tender": {"name": root.name, "tender_reference": root.tender_reference, "plan_item_id": cstr(root.plan_item_id), "requisition_reference": cstr(root.requisition_reference), "fiscal_year": cstr(root.fiscal_year)},
		"tender_version": {"name": version.name, "version_number": int(version.version_number), "package_digest": cstr(version.package_digest), "invitation_digest": cstr(version.invitation_digest), "issued_tender_digest": cstr(version.issued_tender_digest), "response_schema_digest": cstr(version.response_schema_digest), "evaluation_contract_digest": cstr(version.evaluation_contract_digest), "contract_projection_digest": cstr(version.contract_projection_digest), "requisition_snapshot_digest": cstr(version.requisition_snapshot_digest), "template_release_id": cstr(version.template_release_id), "bundle_digest": cstr(version.bundle_digest)},
		"publication": {"name": publication.name, "published_at": cstr(publication.published_at), "publication_digest": cstr(publication.publication_digest), "rule_snapshot_id": cstr(publication.rule_snapshot_id), "required_channels": json.loads(publication.required_channels_json or "[]"), "confirmations_digest": channel_confirmation.confirmation_digest(channel_confirmation.SUBJECT_PUBLICATION, publication.name)},
		"effective_submission_deadline": cstr(root.submission_deadline),
		"opening_datetime": cstr(root.submission_deadline),
		"addenda": [{**dict(a), "revised_submission_deadline": cstr(a.revised_submission_deadline), "effective_at": cstr(a.effective_at), "confirmations_digest": channel_confirmation.confirmation_digest(channel_confirmation.SUBJECT_ADDENDUM, a.name)} for a in addenda],
		"documents": [{"kind": d.kind, "digest": d.digest, "addendum": cstr(d.addendum)} for d in documents.list_for_tender(root.name) if d.kind != documents.KIND_CANCELLATION and (not d.tender_version or d.tender_version == version.name)],
		"closed_at": cstr(clock.now()),
	}


def close_tender_submission_period(*, tender: str, idempotency_key: str, user: str | None = None, force: bool = False) -> dict[str, Any]:
	"""Internal/owner-authenticated: Administrator, System Manager or the
	scheduler. `force` lets a seed close at an injected instant."""
	from kentender_core.services.authorization import is_technical

	actor = cstr(user or frappe.session.user)
	if actor not in ("Administrator",) and not is_technical(actor):
		fail("TND_RESPONSIBILITY_REQUIRED", "Submission periods close by the system, never by a business user.")
	payload = {"tender": tender}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root = envelope.locked("Tender", draft_commands.resolve_tender_name(tender))
	if root.overall_status == "Submission period ended":
		return {"ok": True, "idempotent": True, "action": "already_closed", "tender": root.name, "handoff": cstr(root.submission_handoff)}
	if root.overall_status != "Published — open":
		fail("TND_STALE_VERSION", "Only a Published — open Tender closes its submission period.")
	deadline = get_datetime(root.submission_deadline)
	if not force and clock.now() < deadline:
		fail("TND_STALE_VERSION", "The submission deadline has not been reached.")
	with envelope.atomic("close"):
		payload_body = build_handoff_payload(root)
		handoff_digest = digest.sha256_hex(payload_body)
		handoff = envelope.insert(
			frappe.get_doc(
				{
					"doctype": HANDOFF_DOCTYPE, "tender": root.name, "tender_version": payload_body["tender_version"]["name"], "publication": root.publication, "handoff_version": HANDOFF_VERSION,
					"payload_json": digest.canonical_json(payload_body), "handoff_digest": handoff_digest, "effective_submission_deadline": deadline, "closed_at": clock.now(), "fixture_namespace": root.fixture_namespace,
				}
			)
		)
		lifecycle.cancel_open_tasks(root)
		envelope.bump(root, overall_status="Submission period ended", submission_handoff=handoff.name)
		events.emit(tender=root.name, event_type=EVENT_TYPE, command="CloseTenderSubmissionPeriod", idempotency_key=idempotency_key, actor=actor, previous_status="Published — open", resulting_status="Submission period ended", record_version=root.record_version, subject_type=HANDOFF_DOCTYPE, subject_id=handoff.name, status="Pending", consumer=CONSUMER, payload={"handoff_digest": handoff_digest, "effective_submission_deadline": cstr(deadline)}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "closed", "tender": root.name, "record_version": root.record_version, "handoff": handoff.name, "handoff_digest": handoff_digest}
	envelope.record_command(idempotency_key=idempotency_key, command="CloseTenderSubmissionPeriod", payload=payload, result=result, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def close_due_submission_periods() -> dict[str, Any]:
	"""`scheduler_events.hourly` — idempotent, one Tender per transaction."""
	closed, failed = [], []
	for name in frappe.get_all("Tender", filters={"overall_status": "Published — open", "submission_deadline": ("<=", clock.now())}, pluck="name"):
		try:
			close_tender_submission_period(tender=name, idempotency_key=f"close:{name}:{cstr(frappe.db.get_value('Tender', name, 'submission_deadline'))}", user="Administrator")
			frappe.db.commit()
			closed.append(name)
		except Exception:
			frappe.db.rollback()
			frappe.logger("kentender.tenders").error(f"submission close failed for {name}", exc_info=True)
			failed.append(name)
	return {"closed": closed, "failed": failed}


def get_submission_handoff(*, tender: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	root = frappe.get_doc("Tender", draft_commands.resolve_tender_name(tender))
	mode = authz.reader_mode(actor, contributing_org_units=authz.contributing_units_of(root))
	if mode == "department" or not root.submission_handoff:
		authz.not_found()
	doc = frappe.get_doc(HANDOFF_DOCTYPE, root.submission_handoff)
	return {"outcome": "OK", "handoff": doc.name, "handoff_version": doc.handoff_version, "handoff_digest": doc.handoff_digest, "closed_at": cstr(doc.closed_at), "payload": json.loads(doc.payload_json)}
