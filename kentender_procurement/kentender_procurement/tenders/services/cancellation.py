# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.10 / §5.7 / §7.4 — cancellation.

The Accounting Officer is the decision-maker; the Head of Procurement
Function's recommendation is optional and non-binding. A configured,
verified lawful ground and a specific reason are mandatory; the decision
closes the proceeding immediately, even while notices or reports remain
due, and never reopens the Requisition, restores reserved funding or creates
a replacement Tender (TPR08-AC-066..068). Notices use the original channel
set and the immutable cancellation digest; the PPRA report and candidate
notice obligations come from Configuration's `TenderCancellation` rows.

Grounds (plan D7): a code-owned closed catalogue drawn from the Public
Procurement and Asset Disposal Act, 2015 s.63(1). Its wording is marked for
Project Owner verification (FOLLOW_UPS FU-06); no other configuration of
lawful grounds exists in this release."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_core.services import file_integrity
from kentender_procurement.tenders.services import channel_confirmation, clock, configuration_gateway, digest, documents, draft_commands, envelope, events, lifecycle, notices, serializer
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import ROLE_ACCOUNTING_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER

DOCTYPE = "Tender Cancellation"
GROUNDS_SOURCE = "Public Procurement and Asset Disposal Act, 2015 s.63(1) — wording verification pending (FOLLOW_UPS FU-06)"
CANCELLATION_GROUNDS: tuple[tuple[str, str], ...] = (
	("OVERTAKEN_BY_LAW", "Overtaken by operation of law"),
	("OVERTAKEN_BY_TECHNOLOGY", "Overtaken by substantial technological change"),
	("INADEQUATE_BUDGET", "Inadequate budgetary provision"),
	("NO_RESPONSIVE_TENDER", "No tender was received"),
	("COLLUSION_OR_NON_COMPLIANCE", "Evidence of collusion or non-compliance with the procurement rules"),
	("MATERIAL_GOVERNANCE_ISSUE", "Material governance issue detected"),
	("FORCE_MAJEURE", "Force majeure"),
	("NEED_CEASED", "The procurement need has ceased"),
)
GROUND_LABELS = dict(CANCELLATION_GROUNDS)


def grounds_for_client() -> list[dict[str, str]]:
	return [{"key": key, "label": label} for key, label in CANCELLATION_GROUNDS]


def _require_open(root) -> None:
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	if root.overall_status not in ("Published — open",):
		fail("TND_STALE_VERSION", "Only a Published — open Tender can be cancelled.")


# --------------------------------------------------------------------------
# RecommendTenderCancellation
# --------------------------------------------------------------------------


def recommend_tender_cancellation(*, tender: str, ground: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_hopf(actor)
	payload = {"tender": tender, "ground": ground, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if ground not in GROUND_LABELS:
		fail("TND_CANCELLATION_GROUND_INVALID", detail={"fields": {"ground": "Select an applicable cancellation ground."}})
	text = " ".join(cstr(reason).split())
	if not (20 <= len(text) <= 2000):
		fail("TND_CONTROL_INVALID", "Enter a recommendation of 20–2,000 characters.", {"fields": {"reason": "Enter a recommendation of 20–2,000 characters."}})
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	_require_open(root)
	with envelope.atomic("recommend-cancellation"):
		decision = lifecycle.record_decision(root, version, decision="Recommend cancellation", actor=actor, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, assignment=assignment, idempotency_key=idempotency_key, reason=f"{GROUND_LABELS[ground]}: {text}", affected_task=ground, subject_type="Tender", subject_id=root.name)
		envelope.bump(root)
		events.emit(tender=root.name, event_type="CancellationRecommended", command="RecommendTenderCancellation", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Published — open", resulting_status="Published — open", record_version=root.record_version, subject_type="Tender Decision", subject_id=decision.name, reason=text, payload={"ground": ground, "ground_label": GROUND_LABELS[ground]}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "recommended", "tender": root.name, "record_version": root.record_version, "decision": decision.name}
	envelope.record_command(idempotency_key=idempotency_key, command="RecommendTenderCancellation", payload=payload, result=result, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def latest_recommendation(root) -> str:
	return cstr(frappe.db.get_value("Tender Decision", {"tender": root.name, "decision": "Recommend cancellation"}, "name", order_by="decided_at desc"))


# --------------------------------------------------------------------------
# CancelTender
# --------------------------------------------------------------------------


def preview_obligations(root, *, decided_on=None) -> list[dict[str, Any]]:
	"""§10.13 "Consequences": the obligations a cancellation now would create."""
	decided = decided_on or clock.today()
	out = []
	if root.publication:
		import json

		for channel in json.loads(frappe.db.get_value("Tender Publication", root.publication, "required_channels_json") or "[]"):
			out.append({"obligation_id": f"NOTICE-{channel['channel']}", "obligation_type": "Notice channel", "channel": channel["channel"], "label": f"Cancellation notice — {channel['label']}", "due_by": str(getdate(decided))})
	for obligation in configuration_gateway.cancellation_obligations(applicability_date=decided):
		kind = "PPRA report" if obligation["code"] == "PPRA_REPORT" else "Candidate notice"
		out.append({"obligation_id": obligation["code"], "obligation_type": kind, "channel": obligation["code"], "label": obligation["label"], "due_by": str(configuration_gateway.due_date(obligation, decided))})
	return out


def cancel_tender(*, tender: str, ground: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_ao(actor)
	payload = {"tender": tender, "ground": ground, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if ground not in GROUND_LABELS:
		fail("TND_CANCELLATION_GROUND_INVALID", detail={"fields": {"ground": "Select an applicable cancellation ground."}})
	text = " ".join(cstr(reason).split())
	if not (20 <= len(text) <= 2000):
		fail("TND_CONTROL_INVALID", "State the specific circumstances (20–2,000 characters).", {"fields": {"reason": "Enter the circumstances (20–2,000 characters)."}})
	root, version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	_require_open(root)
	publication = frappe.get_doc("Tender Publication", root.publication)
	decided_at = clock.now()
	obligations = preview_obligations(root, decided_on=decided_at.date())
	ppra_due = next((o["due_by"] for o in obligations if o["obligation_type"] == "PPRA report"), None)
	candidate_due = next((o["due_by"] for o in obligations if o["obligation_type"] == "Candidate notice"), None)
	recommendation = latest_recommendation(root)
	state = serializer.officer_state(frappe.get_doc("Tender Version", publication.tender_version))
	with envelope.atomic("cancel"):
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE, "tender": root.name, "publication": publication.name, "ground": ground, "ground_label": GROUND_LABELS[ground], "reason": text, "recommendation": recommendation or None,
				"decided_by": actor, "decided_at": decided_at, "ppra_report_due_by": ppra_due, "candidate_notice_due_by": candidate_due, "record_version": 0, "fixture_namespace": root.fixture_namespace,
			}
		)
		for obligation in obligations:
			doc.append("obligations", {**obligation, "status": "Due"})
		envelope.insert(doc)
		contact_display, contact_address = serializer._office_display(state.get("contract_contact_office"))
		rendered = notices.render_cancellation_notice(
			{
				"procuring_entity": {"name": cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_name")), "address": contact_address, "contact_office": contact_display},
				"platform": {"name": serializer.PLATFORM_NAME},
				"tender": {"reference": root.tender_reference, "title": cstr(state.get("tender_title") or root.requirement_title), "submission_deadline": serializer.fmt_datetime_eat(root.submission_deadline), "published_at": serializer.fmt_datetime_eat(root.published_at)},
				"cancellation": {"decided_at": serializer.fmt_datetime_eat(decided_at), "ground": GROUND_LABELS[ground], "reason": text, "decided_by": cstr(frappe.db.get_value("User", actor, "full_name") or actor), "reference": doc.name},
			}
		)
		cancellation_digest = digest.sha256_hex({"cancellation": doc.name, "ground": ground, "reason": text, "decided_by": actor, "decided_at": cstr(decided_at), "recommendation": recommendation, "notice_digest": rendered["digest"], "obligations": obligations, "package_digest": cstr(publication.package_digest)})
		document = documents.store(tender=root.name, kind=documents.KIND_CANCELLATION, html=rendered["html"], digest_value=rendered["digest"], cancellation=doc.name, file_base=f"{root.tender_reference}-cancellation-notice", fixture_namespace=root.fixture_namespace)
		envelope.bump(doc, cancellation_digest=cancellation_digest, notice_document_digest=rendered["digest"])
		import json

		channels = json.loads(publication.required_channels_json or "[]")
		rows = channel_confirmation.create_rows(root=root, publication_name=publication.name, subject_type=channel_confirmation.SUBJECT_CANCELLATION, subject_id=doc.name, subject_digest=cancellation_digest, channels=[{"channel": c["channel"], "label": c["label"]} for c in channels])
		decision = lifecycle.record_decision(root, version, decision="Cancel Tender", actor=actor, business_role=ROLE_ACCOUNTING_OFFICER, assignment=assignment, idempotency_key=idempotency_key, reason=text, affected_task=ground, subject_type=DOCTYPE, subject_id=doc.name)
		lifecycle.cancel_open_tasks(root)
		envelope.bump(publication, publication_status="Cancelled")
		envelope.bump(root, overall_status="Cancelled", cancellation=doc.name)
		events.emit(tender=root.name, event_type="TenderCancelled", command="CancelTender", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Published — open", resulting_status="Cancelled", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, reason=text, payload={"ground": ground, "ground_label": GROUND_LABELS[ground], "recommendation": recommendation, "cancellation_digest": cancellation_digest, "notice_digest": rendered["digest"], "document": document, "obligations": obligations, "channels": [r.channel for r in rows], "decision": decision.name}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "cancelled", "tender": root.name, "record_version": root.record_version, "cancellation": doc.name, "cancellation_digest": cancellation_digest, "obligations": obligations}
	envelope.record_command(idempotency_key=idempotency_key, command="CancelTender", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


# --------------------------------------------------------------------------
# RecordCancellationComplianceEvidence
# --------------------------------------------------------------------------


def obligation_status(row, *, today=None) -> str:
	if row.status == "Recorded" or row.evidence_reference:
		return "Recorded"
	if row.due_by and getdate(row.due_by) < getdate(today or clock.today()):
		return "Overdue"
	return "Due"


def refresh_obligation_statuses(doc) -> None:
	changed = False
	for row in doc.obligations:
		status = obligation_status(row)
		if row.status != status:
			row.status = status
			changed = True
	if changed:
		envelope.bump(doc)


def record_cancellation_compliance_evidence(*, tender: str, obligation_id: str, evidence_reference: str, evidence_file: str = "", expected_record_version, idempotency_key: str, user: str | None = None, available_at=None, public_url: str = "", url_not_applicable_reason: str = "", attestation_confirmed: bool = False) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment, role = authz.require_any_site_role((ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION), actor)
	payload = {"tender": tender, "obligation_id": obligation_id, "evidence_reference": evidence_reference, "evidence_file": evidence_file}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, _version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	if root.overall_status != "Cancelled" or not root.cancellation:
		fail("TND_STALE_VERSION", "This Tender is not cancelled.")
	doc = envelope.locked(DOCTYPE, root.cancellation)
	row = next((o for o in doc.obligations if o.obligation_id == obligation_id), None)
	if row is None:
		fail("TND_CONTROL_INVALID", "That obligation does not exist.", {"fields": {"obligation_id": "Choose an outstanding obligation."}})
	if row.status == "Recorded":
		result = {"ok": True, "idempotent": False, "action": "already_recorded", "tender": root.name, "record_version": root.record_version, "obligation_id": obligation_id, "status": "Recorded"}
		envelope.record_command(idempotency_key=idempotency_key, command="RecordCancellationComplianceEvidence", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
		return result
	reference = " ".join(cstr(evidence_reference).split())
	if not (1 <= len(reference) <= 160):
		fail("TND_CONTROL_INVALID", "Enter the evidence reference (1–160 characters).", {"fields": {"evidence_reference": "Enter the evidence reference (1–160 characters)."}})
	checked = {"digest": "", "check_result": ""}
	if row.obligation_type == "Notice channel":
		# A notice channel is evidenced exactly like the original publication: through the channel engine.
		if role != ROLE_HEAD_OF_PROCUREMENT_FUNCTION:
			fail("TND_RESPONSIBILITY_REQUIRED", f"This action requires {ROLE_HEAD_OF_PROCUREMENT_FUNCTION}.")
		confirmation = channel_confirmation.confirm_channel(
			subject_type=channel_confirmation.SUBJECT_CANCELLATION, subject_id=doc.name, channel=cstr(row.channel), available_at=available_at or clock.now(), evidence_reference=reference, public_url=public_url,
			url_not_applicable_reason=url_not_applicable_reason or ("Physical channel" if cstr(row.channel) not in configuration_gateway.ONLINE_CHANNELS else ""), evidence_file=evidence_file, attestation_confirmed=attestation_confirmed or True,
			package_digest=cstr(doc.cancellation_digest), expected_record_version=root.record_version, idempotency_key=f"{idempotency_key}:channel", user=actor, command="RecordCancellationNoticeEvidence",
		)
		root.reload()
		checked = {"digest": cstr(frappe.db.get_value(channel_confirmation.DOCTYPE, confirmation["confirmation"], "evidence_digest")), "check_result": ""}
	elif evidence_file:
		checked = file_integrity.check_file(cstr(evidence_file).strip(), fail=lambda message: fail("TND_FILE_INVALID", message, {"fields": {"evidence_file": message}}))
	with envelope.atomic("record-obligation"):
		doc = envelope.locked(DOCTYPE, root.cancellation)
		row = next(o for o in doc.obligations if o.obligation_id == obligation_id)
		row.evidence_reference, row.evidence_file, row.evidence_digest, row.recorded_by, row.recorded_at, row.status = reference, cstr(evidence_file).strip() or None, checked["digest"], actor, clock.now(), "Recorded"
		envelope.bump(doc)
		envelope.bump(root)
		events.emit(tender=root.name, event_type="CancellationObligationRecorded", command="RecordCancellationComplianceEvidence", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment), previous_status="Cancelled", resulting_status="Cancelled", record_version=root.record_version, subject_type=DOCTYPE, subject_id=doc.name, payload={"obligation_id": obligation_id, "obligation_type": row.obligation_type, "evidence_reference": reference, "evidence_digest": checked["digest"]}, fixture_namespace=root.fixture_namespace)
	result = {"ok": True, "idempotent": False, "action": "recorded", "tender": root.name, "record_version": root.record_version, "obligation_id": obligation_id, "status": "Recorded"}
	envelope.record_command(idempotency_key=idempotency_key, command="RecordCancellationComplianceEvidence", payload=payload, result=result, document_type=DOCTYPE, document_name=doc.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result
