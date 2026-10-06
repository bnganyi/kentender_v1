# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Evaluation endpoints (EVL-CHG-001 v0.4 §7.2, §10; plan D3, D20; tracker
EVL4-1001). Thin: each names its arguments explicitly and forwards to one
service, which applies every rule; nothing is taken from the client except
these arguments and the signed-in user, and nothing is forwarded as
`**kwargs` into a keyword-only service (Frappe adds its own transport fields
to the request). A refusal is returned as data with its §8 code, sentence
and every applicable reason; a form value to correct is returned with its
field messages. Every refused, stale or protected attempt is audited after
the command's own writes were undone. A protected record answers exactly
like a missing one."""

from __future__ import annotations

import json
from typing import Any, Callable

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_evaluation.services.errors import EvaluationError, InputError

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
		log_audit_event(event_type=f"Bid evaluation {outcome}", entity="Bid Evaluation", document_type="Tender", document_name=cstr(tender_reference), action=command,
			performed_by=frappe.session.user, metadata={"outcome": outcome, **(detail or {})})
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="Bid evaluation audit write failed")


def _call(command: str, tender_reference: str, fn: Callable[..., dict[str, Any]], *, by_reference: bool = False, **kwargs) -> dict[str, Any]:
	try:
		if by_reference:
			result = fn(tender_reference=cstr(tender_reference).strip(), user=frappe.session.user, **kwargs)
		else:
			result = fn(tender=_tender(tender_reference), user=frappe.session.user, **kwargs)
	except InputError as exc:
		return {"ok": False, "code": exc.code, "message": str(exc), "fields": exc.fields}
	except EvaluationError as exc:
		_audit(command, tender_reference, "refused", {"code": exc.code})
		return {"ok": False, "code": exc.code, "message": str(exc), "detail": exc.detail, "reasons": exc.reasons}
	except frappe.DoesNotExistError:
		_audit(command, tender_reference, "not found")
		raise frappe.DoesNotExistError(NOT_FOUND)
	if isinstance(result, dict) and result.get("ok") is False:
		_audit(command, tender_reference, "refused", {"code": cstr(result.get("code") or result.get("reason"))})
	return result


# -- reads -------------------------------------------------------------------------
@frappe.whitelist(methods=["GET"])
def get_evaluation(tender_reference: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import reads

	return _call("ResolveEvaluation", tender_reference, reads.resolve, by_reference=True)


@frappe.whitelist(methods=["GET"])
def get_bid(tender_reference: str, bid: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import reads

	return _call("ReadEvaluationBid", tender_reference, reads.bid, by_reference=True, bid=bid)


@frappe.whitelist(methods=["GET"])
def get_delivered_bid(tender_reference: str, bid: str, version: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import reads

	return _call("ReadDeliveredEvaluationBid", tender_reference, reads.delivered_bid, by_reference=True, bid=bid, version=version)


@frappe.whitelist(methods=["GET"])
def get_evidence(tender_reference: str, bid: str, digest: str, version: str = "") -> None:
	from kentender_procurement.bid_evaluation.services import reads

	result = _call("ReadEvaluationEvidence", tender_reference, reads.evidence, by_reference=True, bid=bid, digest=digest, version=version)
	if result.get("ok") is False:
		raise frappe.DoesNotExistError(NOT_FOUND)
	frappe.local.response.filename = result["filename"]
	frappe.local.response.filecontent = result["content"]
	frappe.local.response.type = "download"
	frappe.local.response.display_content_as = "inline"


@frappe.whitelist(methods=["GET"])
def get_report(tender_reference: str, version: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import reads

	return _call("ReadEvaluationReport", tender_reference, reads.report_view, by_reference=True, version=version)


@frappe.whitelist(methods=["GET"])
def get_committee_record(tender_reference: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import reads

	return _call("ReadCommitteeRecord", tender_reference, reads.committee_record, by_reference=True)


@frappe.whitelist(methods=["GET"])
def get_candidates(tender_reference: str, purpose: str = "committee") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import reads

	result = _call("ReadAppointmentCandidates", tender_reference, reads.candidates, by_reference=True, purpose=cstr(purpose))
	return result if isinstance(result, dict) else {"candidates": result}


@frappe.whitelist(methods=["GET"])
def list_work(query: str = "", state: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import reads

	return reads.list_work(user=frappe.session.user, query=cstr(query), state=cstr(state))


@frappe.whitelist(methods=["GET"])
def get_own_clarification(tender_reference: str, clarification: str, organisation: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import reads

	return _call("ReadOwnClarification", tender_reference, reads.own_clarification, by_reference=True, clarification=clarification, organisation=organisation)


@frappe.whitelist(methods=["POST"])
def heartbeat(tender_reference: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import discussion

	return _call("Heartbeat", tender_reference, discussion.heartbeat)


# -- preparation and committee ----------------------------------------------------------
@frappe.whitelist(methods=["POST"])
def appoint_committee(tender_reference: str, members, appointment_reference: str, expected_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import appointment

	return _call("AppointEvaluationCommittee", tender_reference, appointment.appoint_committee, members=_json(members, []),
		appointment_reference=appointment_reference, expected_version=cint(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def replace_member(tender_reference: str, outgoing: str, incoming, appointment_reference: str, reason: str, expected_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import appointment

	return _call("ReplaceEvaluationMember", tender_reference, appointment.replace_member, outgoing=outgoing, incoming=_json(incoming, {}),
		appointment_reference=appointment_reference, reason=reason, expected_version=cint(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def assign_secretary(tender_reference: str, secretary: str, appointment_reference: str, expected_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import secretary as service

	return _call("AssignEvaluationSecretary", tender_reference, service.assign_secretary, secretary=secretary, appointment_reference=appointment_reference,
		expected_version=cint(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def declare_interest(tender_reference: str, choice: str, confidentiality_accepted, idempotency_key: str, conflict_description: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import declaration

	return _call("DeclareEvaluationInterest", tender_reference, declaration.declare_interest, choice=choice,
		confidentiality_accepted=bool(cint(confidentiality_accepted)), conflict_description=conflict_description, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_unavailability(tender_reference: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import declaration

	return _call("RecordMemberUnavailability", tender_reference, declaration.record_unavailability, reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def retry_intake(tender_reference: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import intake

	return _call("RetryEvaluationOperation", tender_reference, intake.retry)


# -- findings and discussion -----------------------------------------------------------
@frappe.whitelist(methods=["POST"])
def record_finding(tender_reference: str, bid: str, requirement_key: str, result: str, reason: str, idempotency_key: str, evidence_reference: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import findings

	return _call("RecordEvidenceFinding", tender_reference, findings.record_evidence_finding, bid=bid, requirement_key=requirement_key, result=result, reason=reason,
		evidence_reference=evidence_reference, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def raise_concern(tender_reference: str, bid: str, requirement_key: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import findings

	return _call("RaiseFindingConcern", tender_reference, findings.raise_concern, bid=bid, requirement_key=requirement_key, reason=reason,
		idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def start_discussion(tender_reference: str, subject: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import discussion

	return _call("StartDiscussion", tender_reference, discussion.start_discussion, subject=subject, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def join_discussion(tender_reference: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import discussion

	return _call("JoinDiscussion", tender_reference, discussion.join_discussion, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def leave_discussion(tender_reference: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import discussion

	return _call("LeaveDiscussion", tender_reference, discussion.leave_discussion, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def end_discussion(tender_reference: str, idempotency_key: str, note: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import discussion

	return _call("EndDiscussion", tender_reference, discussion.end_discussion, note=note, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_note(tender_reference: str, subject: str, note: str, idempotency_key: str, reason: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import discussion

	return _call("RecordDiscussionNote", tender_reference, discussion.record_note, subject=subject, note=note, reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_conclusion(tender_reference: str, bid: str, requirement_key: str, result: str, reason: str, idempotency_key: str, qualified=0) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import conclusion

	return _call("RecordCommitteeConclusion", tender_reference, conclusion.record_conclusion, bid=bid, requirement_key=requirement_key, result=result,
		reason=reason, qualified=bool(cint(qualified)), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_case_conclusion(tender_reference: str, kind: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import conclusion

	return _call("RecordCommitteeConclusion", tender_reference, conclusion.record_case_conclusion, kind=kind, reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_disagreement(tender_reference: str, statement: str, idempotency_key: str, conclusion: str = "", report_version: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import conclusion as service

	return _call("RecordDisagreement", tender_reference, service.record_disagreement, statement=statement, conclusion=conclusion, report_version=report_version,
		idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def report_issue(tender_reference: str, bid: str, requirement_key: str, description: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import issues

	return _call("ReportEvaluationIssue", tender_reference, issues.report_issue, bid=bid, requirement_key=requirement_key, description=description,
		idempotency_key=idempotency_key)


# -- clarification ----------------------------------------------------------------------
@frappe.whitelist(methods=["POST"])
def authorise_clarification(tender_reference: str, bid: str, requirement_key: str, question: str, reply_scope: str, reply_deadline: str, idempotency_key: str,
		replaces: str = "", replacement_reason: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import clarification

	return _call("AuthoriseClarification", tender_reference, clarification.authorise, bid=bid, requirement_key=requirement_key, question=question,
		reply_scope=reply_scope, reply_deadline=reply_deadline, replaces=replaces, replacement_reason=replacement_reason, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def send_clarification(tender_reference: str, clarification: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import clarification as service

	return _call("SendClarification", tender_reference, service.send, clarification=clarification, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def retry_clarification_notice(tender_reference: str, clarification: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import clarification as service

	return _call("RetryClarificationNotice", tender_reference, service.retry_notice, clarification=clarification, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def withdraw_clarification(tender_reference: str, clarification: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import clarification as service

	return _call("WithdrawClarification", tender_reference, service.withdraw, clarification=clarification, reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_reply_disposition(tender_reference: str, clarification: str, disposition: str, result: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import clarification as service

	return _call("RecordReplyDisposition", tender_reference, service.record_disposition, clarification=clarification, disposition=disposition, result=result,
		reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def save_clarification_draft(tender_reference: str, clarification: str, body: str, idempotency_key: str, attachments=None, organisation: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import clarification as service

	return _call("SaveClarificationDraft", tender_reference, service.save_draft, clarification=clarification, body=body, attachments=_json(attachments, []),
		organisation=organisation, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def submit_clarification_reply(tender_reference: str, clarification: str, body: str, idempotency_key: str, attachments=None, organisation: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import clarification as service

	return _call("SubmitClarificationReply", tender_reference, service.submit_reply, clarification=clarification, body=body, attachments=_json(attachments, []),
		organisation=organisation, idempotency_key=idempotency_key)


# -- due diligence -----------------------------------------------------------------------
@frappe.whitelist(methods=["POST"])
def record_verification_plan(tender_reference: str, scope: str, basis: str, participants, lead: str, idempotency_key: str, change_reason: str = "") -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import diligence

	return _call("RecordVerificationPlan", tender_reference, diligence.record_plan, scope=scope, basis=basis, participants_=_json(participants, []), lead=lead,
		change_reason=change_reason, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_verification_findings(tender_reference: str, findings: str, idempotency_key: str, evidence=None) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import diligence

	return _call("RecordDueDiligence", tender_reference, diligence.record_observation, findings_=findings, evidence=_json(evidence, []),
		idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def send_verification_for_signing(tender_reference: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import diligence

	return _call("SendDueDiligenceForSigning", tender_reference, diligence.send_for_signing, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def sign_verification_report(tender_reference: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import diligence

	return _call("SignDueDiligenceReport", tender_reference, diligence.sign, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_verification_outcome(tender_reference: str, bid: str, requirement_key: str, result: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import diligence

	return _call("RecordVerificationOutcome", tender_reference, diligence.record_outcome, bid=bid, requirement_key=requirement_key, result=result, reason=reason,
		idempotency_key=idempotency_key)


# -- report, signing and correction -------------------------------------------------------------
@frappe.whitelist(methods=["POST"])
def save_report_narrative(tender_reference: str, narrative: str, expected_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import report

	return _call("SaveReportNarrative", tender_reference, report.save_narrative, narrative=narrative, expected_version=cint(expected_version),
		idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def send_report_for_signing(tender_reference: str, expected_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import signing

	return _call("SendReportForSigning", tender_reference, signing.send_for_signing, expected_version=cint(expected_version), idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def sign_report(tender_reference: str, report_version: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import signing

	return _call("SignEvaluationReport", tender_reference, signing.sign, report_version=report_version, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def raise_report_concern(tender_reference: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import signing

	return _call("RaiseReportConcern", tender_reference, signing.raise_report_concern, reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def revise_report(tender_reference: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import signing

	return _call("ReviseEvaluationReport", tender_reference, signing.revise, reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def retry_delivery(tender_reference: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import signing

	return _call("RetryEvaluationOperation", tender_reference, signing.retry_delivery, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def return_report(tender_reference: str, comment: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import correction

	return _call("ReturnEvaluationReport", tender_reference, correction.return_report, comment=comment, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def report_status_issue(tender_reference: str, description: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import correction

	return _call("ReportDecisionStatusIssue", tender_reference, correction.report_status_issue, description=description, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_correction_notice(tender_reference: str, reason: str, correction: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import correction as service

	return _call("RecordCorrectionNotice", tender_reference, service.record_correction_notice, reason=reason, correction=correction, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def assess_opening_update(tender_reference: str, source_event: str, impact: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import correction

	return _call("AssessOpeningSupplement", tender_reference, correction.assess_supplement, source_event=source_event, impact=impact, reason=reason,
		idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_head_review(tender_reference: str, item: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import correction

	return _call("RecordHeadReview", tender_reference, correction.head_review, item=item, idempotency_key=idempotency_key)
