# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening endpoints (BOP-CHG-001 v0.10 §7, §11; plan D9). Thin: each
names its arguments explicitly and forwards to one service, which applies
every rule; nothing is taken from the client except these arguments and the
signed-in user. Proceedings has no endpoint of its own (PRC-CHG-001 v0.9 §9).

A refusal is returned as data with its §8 code and sentence, and every
refused, stale or protected attempt is written to the audit log after the
command's own writes have been undone (PRC-CHG-001 v0.9 §12; BOP-CHG-001
v0.10 §12). A protected record answers exactly like a missing one."""

from __future__ import annotations

import json
from typing import Any, Callable

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_opening.services.errors import BidOpeningError

NOT_FOUND = "Not found"


def _json(value, default):
	if value is None:
		return default
	if isinstance(value, str):
		return json.loads(value) if value.strip() else default
	return value


def _tender(tender_reference: str) -> str:
	name = frappe.db.get_value("Tender", {"tender_reference": cstr(tender_reference).strip()}, "name")
	if not name:
		raise frappe.DoesNotExistError(NOT_FOUND)
	return name


def _audit(command: str, tender_reference: str, outcome: str, detail: dict | None = None) -> None:
	from kentender_core.services.audit_event_service import log_audit_event

	try:
		log_audit_event(event_type=f"Bid opening {outcome}", entity="Bid Opening", document_type="Tender", document_name=cstr(tender_reference), action=command,
			performed_by=frappe.session.user, metadata={"outcome": outcome, **(detail or {})})
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="Bid opening audit write failed")


def _call(command: str, tender_reference: str, fn: Callable[..., dict[str, Any]], **kwargs) -> dict[str, Any]:
	try:
		result = fn(tender=_tender(tender_reference), user=frappe.session.user, **kwargs)
	except BidOpeningError as exc:
		_audit(command, tender_reference, "refused", {"code": exc.code})
		return {"ok": False, "code": exc.code, "message": str(exc), "detail": exc.detail}
	except frappe.DoesNotExistError:
		_audit(command, tender_reference, "not found")
		raise frappe.DoesNotExistError(NOT_FOUND)
	if isinstance(result, dict) and result.get("ok") is False:
		_audit(command, tender_reference, "refused", {"code": cstr(result.get("code") or result.get("reason"))})
	return result


def _download(result: dict[str, Any]) -> None:
	frappe.local.response.filename = result["filename"]
	frappe.local.response.filecontent = result["content"]
	frappe.local.response.type = "download"
	frappe.local.response.display_content_as = "inline"


# -- reads -------------------------------------------------------------------------


@frappe.whitelist(methods=["GET"])
def get_opening(tender_reference: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import reads

	return _call("GetOpening", tender_reference, reads.get_opening)


@frappe.whitelist(methods=["GET"])
def get_bid_pages(tender_reference: str, entry: str) -> None:
	from kentender_procurement.bid_opening.services import pages

	_download(_call("ViewBidPages", tender_reference, pages.bid_pages, entry=entry))


@frappe.whitelist(methods=["GET"])
def get_record_pages(tender_reference: str, minutes_version: str) -> None:
	from kentender_procurement.bid_opening.services import pages

	_download(_call("ReadOpeningRecord", tender_reference, pages.record_pages, minutes_version=minutes_version))


@frappe.whitelist(methods=["GET"])
def export_opening(tender_reference: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import export

	return _call("ExportOpening", tender_reference, export.export_opening)


# -- preparation ----------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def appoint_committee(tender_reference: str, members, expected_version: int, idempotency_key: str, reason: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import appointment

	return _call("AppointOpeningCommittee", tender_reference, appointment.appoint_opening_committee, members=_json(members, []), reason=reason,
		expected_version=int(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def publish_arrangements(tender_reference: str, attendance_method: str, expected_version: int, idempotency_key: str, access_instructions: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import arrangements

	return _call("PublishOpeningArrangements", tender_reference, arrangements.publish_opening_arrangements, attendance_method=attendance_method,
		access_instructions=access_instructions, expected_version=int(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def join_opening(tender_reference: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import presence

	return _call("JoinOpening", tender_reference, presence.join_opening, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def leave_opening(tender_reference: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import presence

	return _call("LeaveOpening", tender_reference, presence.leave_opening, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def heartbeat(tender_reference: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import presence

	return _call("Heartbeat", tender_reference, presence.heartbeat)


@frappe.whitelist(methods=["POST"])
def notify_member(tender_reference: str, member: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import reminders

	return _call("NotifyMember", tender_reference, reminders.notify_member, member=member, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def notify_support(tender_reference: str, incident: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import incidents

	return _call("NotifySupport", tender_reference, incidents.notify_support, incident=incident, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_incident_outcome(tender_reference: str, incident: str, resolved: int, note: str, idempotency_key: str) -> dict[str, Any]:
	"""Opening access support: resolved, or cannot be fixed."""
	from kentender_procurement.bid_opening.services import incidents

	fn = incidents.record_resolution if str(resolved) in ("1", "true", "True") else incidents.record_unresolved
	return _call("RecordIncidentOutcome", tender_reference, fn, incident=incident, resolution_note=note, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_not_held(tender_reference: str, reason: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import not_held

	return _call("RecordOpeningNotHeld", tender_reference, not_held.record_opening_not_held, reason=reason, expected_version=int(expected_version),
		idempotency_key=idempotency_key)


# -- the ceremony ------------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def begin_opening(tender_reference: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import ceremony

	return _call("BeginOpening", tender_reference, ceremony.begin_opening, expected_version=int(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def open_next_bid(tender_reference: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import ceremony

	return _call("OpenNextTender", tender_reference, ceremony.open_next_tender, expected_version=int(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def retry_opening(tender_reference: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import ceremony

	return _call("RetryOpening", tender_reference, ceremony.retry_opening, expected_version=int(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def resume_opening(tender_reference: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import ceremony

	return _call("ResumeOpening", tender_reference, ceremony.resume_opening, expected_version=int(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_readout(tender_reference: str, entry: str, speaker: str, designated_pages, expected_version: int, idempotency_key: str,
		reported_speech_at: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import readout

	return _call("RecordReadout", tender_reference, readout.record_readout, entry=entry, speaker=speaker, designated_pages=_json(designated_pages, []),
		expected_version=int(expected_version), idempotency_key=idempotency_key, reported_speech_at=reported_speech_at or None)


@frappe.whitelist(methods=["POST"])
def record_attendance(tender_reference: str, person_name: str, capacity: str, movement: str, idempotency_key: str, attendee: str = "",
		represented_tenderer: str = "", reported_at: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import interventions

	return _call("RecordAttendance", tender_reference, interventions.record_attendance, person_name=person_name, capacity=capacity, movement=movement,
		attendee=attendee, represented_tenderer=represented_tenderer, reported_at=reported_at or None, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_intervention(tender_reference: str, exception_class: str, speaker_name: str, what: str, response: str, idempotency_key: str, entry: str = "",
		reported_at: str = "", linked_account: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import interventions

	return _call("RecordIntervention", tender_reference, interventions.record_intervention, exception_class=exception_class, speaker_name=speaker_name,
		what=what, response=response, entry=entry, reported_at=reported_at or None, linked_account=linked_account, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_member_account(tender_reference: str, account: str, idempotency_key: str, entry: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import interventions

	return _call("RecordMemberAccount", tender_reference, interventions.record_member_account, account=account, entry=entry, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_comment_for_evaluation(tender_reference: str, entry: str, made_by: str, comment: str, response: str, idempotency_key: str,
		reported_at: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import interventions

	return _call("RecordCommentForEvaluation", tender_reference, interventions.record_comment_for_evaluation, entry=entry, made_by=made_by, comment=comment,
		response=response, reported_at=reported_at or None, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def end_opening(tender_reference: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import finish

	return _call("FinishCeremony", tender_reference, finish.finish_ceremony, expected_version=int(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def end_opening_with_no_bids(tender_reference: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import finish

	return _call("EndOpeningWithNoBids", tender_reference, finish.end_with_no_bids, expected_version=int(expected_version), idempotency_key=idempotency_key)


# -- the opening record and after -------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def finish_opening_record(tender_reference: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import record

	return _call("FreezeOpeningMinutes", tender_reference, record.freeze_opening_minutes, expected_version=int(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def correct_opening_record_draft(tender_reference: str, reason: str, correction_note: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
	"""Before completion: a new version of the opening record."""
	from kentender_procurement.bid_opening.services import record

	return _call("SupersedeFrozenMinutes", tender_reference, record.supersede_opening_minutes, reason=reason, correction_note=correction_note,
		expected_version=int(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def sign_opening_record(tender_reference: str, minutes_version: str, targets, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import signing

	return _call("AttestOpeningTarget", tender_reference, signing.sign_opening_record, minutes_version=minutes_version, targets=_json(targets, []),
		idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def correct_opening_record(tender_reference: str, kind: str, correct_information: str, reason: str, expected_version: int, idempotency_key: str) -> dict[str, Any]:
	"""After completion: a correction supplement of one of the four kinds."""
	from kentender_procurement.bid_opening.services import correction

	return _call("CorrectOpeningRecord", tender_reference, correction.correct_opening_record, kind=kind, correct_information=correct_information, reason=reason,
		expected_version=int(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def provide_register_copy(tender_reference: str, request: str, idempotency_key: str, decline_reason: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import register_copy

	return _call("ProvideOpeningRegister", tender_reference, register_copy.provide_register_copy, request=request, decline_reason=decline_reason,
		idempotency_key=idempotency_key)
