# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.7 / §5.5 / §7.3 — `ConfirmPublicationChannel` and
the one generic confirmation engine the addendum and cancellation-notice
paths reuse.

KenTender validates record completeness, field formats, actor authority,
package/channel identity, file integrity and scan result, duplicate and
conflicting confirmations and the applicable channel rules. It does **not**
independently prove that a website, notice board or newspaper was publicly
available: that factual confirmation is the named Head of Procurement
Function's accountable attestation supported by the recorded evidence
(§4.7, TPR08-AC-046..050). An identical replay is idempotent; a conflicting
second confirmation is rejected and preserved for audit (§5.8(10)); the
attestation, evidence and confirmation commit atomically (§11.5)."""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import file_integrity
from kentender_procurement.tenders.services import clock, configuration_gateway, digest, envelope, events, serializer
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail

DOCTYPE = "Tender Channel Confirmation"
SUBJECT_PUBLICATION = "Publication"
SUBJECT_ADDENDUM = "Addendum"
SUBJECT_CANCELLATION = "Cancellation notice"
ATTESTATION = "I confirm that the exact approved {package} was publicly available through the {channel} at the date and time stated above."
PACKAGE_WORDING = {SUBJECT_PUBLICATION: "Tender package", SUBJECT_ADDENDUM: "addendum", SUBJECT_CANCELLATION: "cancellation notice"}
_URL = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)


def attestation_text(*, subject_type: str, channel_label: str) -> str:
	return ATTESTATION.format(package=PACKAGE_WORDING[subject_type], channel=channel_label)


def create_rows(*, root, publication_name: str, subject_type: str, subject_id: str, subject_digest: str, channels: list[dict[str, Any]]) -> list[Any]:
	"""One `Awaiting confirmation` record per required channel, unique by
	subject + channel (§4.7 `channel_confirmation_id`)."""
	rows = []
	for channel in channels:
		if frappe.db.exists(DOCTYPE, {"subject_type": subject_type, "subject_id": subject_id, "channel": channel["channel"]}):
			continue
		rows.append(
			envelope.insert(
				frappe.get_doc(
					{
						"doctype": DOCTYPE, "tender": root.name, "publication": publication_name, "subject_type": subject_type, "subject_id": subject_id, "subject_digest": subject_digest,
						"channel": channel["channel"], "channel_label": channel["label"], "confirmation_mode": configuration_gateway.CONFIRMATION_MODE, "status": "Awaiting confirmation",
						"record_version": 0, "fixture_namespace": root.fixture_namespace,
					}
				)
			)
		)
	return rows


def rows_for(subject_type: str, subject_id: str) -> list[Any]:
	return [frappe.get_doc(DOCTYPE, n) for n in frappe.get_all(DOCTYPE, filters={"subject_type": subject_type, "subject_id": subject_id}, pluck="name", order_by="creation asc")]


def all_confirmed(subject_type: str, subject_id: str) -> bool:
	rows = frappe.get_all(DOCTYPE, filters={"subject_type": subject_type, "subject_id": subject_id}, fields=["status"])
	return bool(rows) and all(r.status == "Confirmed" for r in rows)


def latest_available_at(subject_type: str, subject_id: str):
	rows = frappe.get_all(DOCTYPE, filters={"subject_type": subject_type, "subject_id": subject_id, "status": "Confirmed"}, pluck="available_at")
	return max((get_datetime(r) for r in rows if r), default=None)


def _validate_inputs(row, *, available_at, evidence_reference, public_url, url_not_applicable_reason, evidence_file, evidence_notes, attestation_confirmed, package_digest) -> dict[str, Any]:
	fields: dict[str, str] = {}
	if not available_at:
		fields["available_at"] = "Enter the date and time the documents became available."
	else:
		try:
			get_datetime(available_at)
		except Exception:
			fields["available_at"] = "Enter a valid date and time."
	reference = " ".join(cstr(evidence_reference).split())
	if not (1 <= len(reference) <= 160):
		fields["evidence_reference"] = "Enter the publication reference (1–160 characters)."
	url = cstr(public_url).strip()
	reason = " ".join(cstr(url_not_applicable_reason).split())
	if row.channel in configuration_gateway.ONLINE_CHANNELS:
		if url and not _URL.match(url):
			fields["public_url"] = "Enter a valid public URL."
		if not url and not reason:
			fields["public_url"] = "Enter the public URL, or state why no stable public URL exists."
	elif url:
		fields["public_url"] = "This channel has no public URL."
	notes = " ".join(cstr(evidence_notes).split())
	if len(notes) > 500:
		fields["evidence_notes"] = "Notes are limited to 500 characters."
	if not cstr(evidence_file).strip():
		fields["evidence_file"] = "Attach the publication evidence file."
	if not attestation_confirmed:
		fields["attestation"] = "Confirm the attestation."
	if cstr(package_digest) != cstr(row.subject_digest):
		fail("TND_PUBLICATION_DIGEST_MISMATCH", detail={"channel": row.channel, "expected": row.subject_digest, "presented": cstr(package_digest)})
	if fields:
		fail("TND_PUBLICATION_CONFIRMATION_INCOMPLETE", detail={"fields": fields, "channel": row.channel})
	return {"available_at": get_datetime(available_at), "evidence_reference": reference, "public_url": url, "url_not_applicable_reason": reason, "evidence_notes": notes}


def confirm_channel(
	*,
	subject_type: str,
	subject_id: str,
	channel: str,
	available_at,
	evidence_reference: str,
	public_url: str = "",
	url_not_applicable_reason: str = "",
	evidence_file: str = "",
	evidence_notes: str = "",
	attestation_confirmed: bool = False,
	package_digest: str,
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
	on_all_confirmed=None,
	command: str = "ConfirmPublicationChannel",
) -> dict[str, Any]:
	"""The generic engine. `on_all_confirmed(root, rows)` runs inside the
	same transaction when this confirmation completes the set (the final
	channel of a publication publishes the Tender; of an addendum, issues it)."""
	actor = authz.actor(user)
	assignment = authz.require_hopf(actor)
	payload = {
		"subject_type": subject_type, "subject_id": subject_id, "channel": channel, "available_at": cstr(available_at), "evidence_reference": cstr(evidence_reference), "public_url": cstr(public_url),
		"evidence_file": cstr(evidence_file), "evidence_notes": cstr(evidence_notes), "package_digest": cstr(package_digest),
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	name = frappe.db.get_value(DOCTYPE, {"subject_type": subject_type, "subject_id": subject_id, "channel": channel}, "name")
	if not name:
		authz.not_found()
	row = envelope.locked(DOCTYPE, name)
	root = envelope.locked("Tender", row.tender)
	if root.overall_status == "Cancelled" and subject_type != SUBJECT_CANCELLATION:
		fail("TND_CANCELLED")
	envelope.check_record_version(root, expected_record_version)
	clean = _validate_inputs(row, available_at=available_at, evidence_reference=evidence_reference, public_url=public_url, url_not_applicable_reason=url_not_applicable_reason, evidence_file=evidence_file, evidence_notes=evidence_notes, attestation_confirmed=attestation_confirmed, package_digest=package_digest)
	checked = file_integrity.check_file(cstr(evidence_file).strip(), fail=lambda message: fail("TND_PUBLICATION_EVIDENCE_INVALID", message, {"channel": channel, "fields": {"evidence_file": message}}))
	if row.status == "Confirmed":
		same = (
			get_datetime(row.available_at) == clean["available_at"] and cstr(row.evidence_reference) == clean["evidence_reference"] and cstr(row.public_url) == clean["public_url"]
			and cstr(row.evidence_digest) == checked["digest"]
		)
		if same:
			result = _result(row, root, idempotent_action="already_confirmed")
			envelope.record_command(idempotency_key=idempotency_key, command=command, payload=payload, result=result, document_type=DOCTYPE, document_name=row.name, actor=actor, fixture_namespace=root.fixture_namespace)
			return result
		events.emit(
			tender=root.name, event_type="ConfirmationConflictRejected", command=command, idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Confirmed", resulting_status="Confirmed", record_version=root.record_version, subject_type=DOCTYPE, subject_id=row.name,
			payload={"channel": channel, "presented": {**clean, "available_at": cstr(clean["available_at"]), "evidence_digest": checked["digest"]}, "recorded": {"available_at": cstr(row.available_at), "evidence_reference": row.evidence_reference, "public_url": row.public_url, "evidence_digest": row.evidence_digest}},
			fixture_namespace=root.fixture_namespace,
		)
		fail("TND_PUBLICATION_ALREADY_CONFIRMED", detail={"channel": channel, "confirmation": row.name})
	attestation = attestation_text(subject_type=subject_type, channel_label=row.channel_label)
	with envelope.atomic("confirm-channel"):
		envelope.bump(
			row, status="Confirmed", available_at=clean["available_at"], evidence_reference=clean["evidence_reference"], public_url=clean["public_url"],
			url_not_applicable_reason=clean["url_not_applicable_reason"], evidence_file=cstr(evidence_file).strip(), evidence_digest=checked["digest"], evidence_check_result=checked["check_result"],
			evidence_notes=clean["evidence_notes"], attestation_text=attestation, attested_by=actor, attested_at=clock.now(),
		)
		events.emit(
			tender=root.name, event_type="ChannelConfirmed", command=command, idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Awaiting confirmation", resulting_status="Confirmed", record_version=root.record_version, subject_type=DOCTYPE, subject_id=row.name,
			payload={"subject_type": subject_type, "subject_id": subject_id, "channel": channel, "available_at": cstr(clean["available_at"]), "evidence_reference": clean["evidence_reference"], "public_url": clean["public_url"], "evidence_digest": checked["digest"], "evidence_check_result": checked["check_result"], "attestation": attestation, "package_digest": cstr(package_digest)},
			fixture_namespace=root.fixture_namespace,
		)
		completed = None
		if on_all_confirmed and all_confirmed(subject_type, subject_id):
			completed = on_all_confirmed(root, rows_for(subject_type, subject_id), actor=actor, assignment=assignment, idempotency_key=idempotency_key)
		envelope.bump(root)
	result = _result(row, root, idempotent_action="confirmed", completed=completed)
	envelope.record_command(idempotency_key=idempotency_key, command=command, payload=payload, result=result, document_type=DOCTYPE, document_name=row.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def _result(row, root, *, idempotent_action: str, completed: dict[str, Any] | None = None) -> dict[str, Any]:
	row.reload() if row.name else None
	return {
		"ok": True, "idempotent": False, "action": idempotent_action, "tender": root.name, "record_version": int(frappe.db.get_value("Tender", root.name, "record_version") or 0), "confirmation": row.name, "channel": row.channel,
		"status": row.status, "available_at": cstr(row.available_at), "available_at_label": serializer.fmt_datetime_short(row.available_at) if row.available_at else "", "attested_by": cstr(row.attested_by),
		"subject_type": row.subject_type, "subject_id": row.subject_id, "all_confirmed": all_confirmed(row.subject_type, row.subject_id), "completed": completed or {},
	}


def confirmation_digest(subject_type: str, subject_id: str) -> str:
	rows = frappe.get_all(DOCTYPE, filters={"subject_type": subject_type, "subject_id": subject_id}, fields=["channel", "status", "available_at", "evidence_reference", "public_url", "evidence_digest", "attested_by", "attested_at", "subject_digest"], order_by="channel asc")
	return digest.sha256_hex([dict(r) for r in rows])
