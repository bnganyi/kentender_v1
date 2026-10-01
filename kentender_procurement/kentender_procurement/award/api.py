# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award endpoints (AWD-CHG-001 v0.4 §7, §9–§11; plan D3; `reconciliation/
command_map.md`). Thin: each names its arguments explicitly and forwards to
one service, which applies every rule; nothing is forwarded as `**kwargs`
into a keyword-only service (Frappe adds its own transport fields to the
request). A refusal is returned as data with its §8 code, sentence and every
applicable reason; a form value to correct is returned with its field
messages. Every refused or protected attempt is audited after the command's
own writes were undone. A protected record answers exactly like a missing one."""

from __future__ import annotations

from typing import Any, Callable

import frappe
from frappe.utils import cstr

from kentender_procurement.award.services.errors import AwardError, InputError

NOT_FOUND = "Not found"


def _audit(command: str, reference: str, outcome: str, detail: dict | None = None) -> None:
	from kentender_core.services.audit_event_service import log_audit_event

	try:
		log_audit_event(event_type=f"Award {outcome}", entity="Award", document_type="Award Case", document_name=cstr(reference), action=command,
			performed_by=frappe.session.user, metadata={"outcome": outcome, **(detail or {})})
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="Award audit write failed")


def _call(command: str, reference: str, fn: Callable[..., dict[str, Any]], **kwargs) -> dict[str, Any]:
	try:
		result = fn(user=frappe.session.user, **kwargs)
	except InputError as exc:
		return {"ok": False, "code": exc.code, "message": str(exc), "fields": exc.fields}
	except AwardError as exc:
		_audit(command, reference, "refused", {"code": exc.code})
		return {"ok": False, "code": exc.code, "message": str(exc), "detail": exc.detail, "reasons": exc.reasons}
	except frappe.DoesNotExistError:
		_audit(command, reference, "not found")
		raise frappe.DoesNotExistError(NOT_FOUND)
	if isinstance(result, dict) and result.get("ok") is False:
		_audit(command, reference, "refused", {"code": cstr(result.get("code"))})
	return result


# -- reads ------------------------------------------------------------------------
@frappe.whitelist(methods=["GET"])
def get_workspace() -> dict[str, Any]:
	from kentender_procurement.award.services import reads

	return _call("GetAwardWorkspace", "", reads.workspace)


@frappe.whitelist(methods=["GET"])
def get_award(award: str) -> dict[str, Any]:
	from kentender_procurement.award.services import reads

	return _call("GetAwardRecord", award, reads.record, award=cstr(award).strip())


@frappe.whitelist(methods=["GET"])
def get_notice_letter(award: str, notice: str) -> dict[str, Any]:
	"""The exact retained letter, read-only, for internal readers."""
	from kentender_procurement.award.services import guards, records, state

	def read(*, user: str) -> dict[str, Any]:
		guards.require_reader(user)
		if not frappe.db.exists(state.NOTICE, {"name": cstr(notice), "award_case": cstr(award)}):
			raise frappe.DoesNotExistError(NOT_FOUND)
		n = frappe.get_doc(state.NOTICE, notice)
		return {"ok": True, "notice": n.name, "letter_html": n.letter_html, "digest": n.content_digest, "label": records.loads(n.content_json).get("notice")}

	return _call("GetAwardRecord", award, read)


@frappe.whitelist(methods=["GET"])
def get_supplier_notice(notice: str) -> dict[str, Any]:
	from kentender_procurement.award.services import supplier

	return _call("GetSupplierAwardNotice", notice, supplier.notice_view, notice=cstr(notice).strip())


@frappe.whitelist(methods=["GET"])
def list_supplier_notices() -> dict[str, Any]:
	from kentender_procurement.award.services import supplier

	return {"ok": True, "notices": supplier.my_notices(user=frappe.session.user)}


# -- Head of Procurement ------------------------------------------------------------
@frappe.whitelist(methods=["POST"])
def save_opinion(award: str, conclusion: str = "", reason: str = "", addressed_issues: str = "", expected_version=None, idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import opinion

	return _call("SaveProfessionalOpinion", award, opinion.save, award=award, conclusion=conclusion, reason=reason, addressed_issues=addressed_issues,
		expected_version=expected_version, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def sign_opinion(award: str, expected_version=None, idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import opinion

	return _call("SignProfessionalOpinion", award, opinion.sign, award=award, expected_version=expected_version, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def return_report(award: str, reason: str = "", expected_version=None, idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import opinion

	return _call("ReturnEvaluationReport", award, opinion.return_report, award=award, reason=reason, expected_version=expected_version,
		idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_restriction(award: str, basis: str = "", source: str = "", received_at: str = "", effective_from: str = "", scope: str = "", evidence: str = "",
		reason: str = "", idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import restrictions

	return _call("RecordExternalAwardRestriction", award, restrictions.record_external, award=award, basis=basis, source=source, received_at=received_at,
		effective_from=effective_from, scope=scope, evidence=evidence, reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_disposition(award: str, issue: str, outcome: str = "", reason: str = "", evidence: str = "", next_action: str = "", idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import restrictions

	return _call("RecordAwardIssueDisposition", award, restrictions.disposition, award=award, issue=issue, outcome=outcome, reason=reason, evidence=evidence,
		next_action=next_action, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def save_explanation(award: str, request: str, reply: str = "", idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import explanation

	return _call("SaveAwardExplanation", award, explanation.save, award=award, request=request, reply=reply, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def send_explanation(award: str, request: str, reply: str = "", idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import explanation

	return _call("SendAwardExplanation", award, explanation.send, award=award, request=request, reply=reply, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def correct_contact(award: str, notice: str, idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import recovery

	return _call("RetryNoticeDelivery", award, recovery.correct_contact, award=award, notice=notice, idempotency_key=idempotency_key)


# -- Accounting Officer -------------------------------------------------------------
@frappe.whitelist(methods=["POST"])
def record_decision(award: str, outcome: str, reason: str = "", next_action: str = "", expected_version=None, idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import decision

	return _call("RecordAwardDecision", award, decision.record, award=award, outcome=outcome, reason=reason, next_action=next_action,
		expected_version=expected_version, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def record_correction_decision(award: str, outcome: str, reason: str = "", next_action: str = "", expected_version=None, idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import corrections

	return _call("RecordAwardCorrectionDecision", award, corrections.record, award=award, outcome=outcome, reason=reason, next_action=next_action,
		expected_version=expected_version, idempotency_key=idempotency_key)


# -- technical operator -------------------------------------------------------------
@frappe.whitelist(methods=["POST"])
def retry_operation(award: str, idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import recovery

	return _call("RetryOperation", award, recovery.retry_operation, award=award, idempotency_key=idempotency_key)


# -- supplier (portal) ------------------------------------------------------------
@frappe.whitelist(methods=["POST"])
def respond(notice: str, response: str, reason: str = "", notice_version=None, idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import supplier

	return _call("RespondToAward", notice, supplier.respond, notice=notice, response=response, reason=reason, notice_version=notice_version,
		idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def request_explanation(notice: str, request: str = "", idempotency_key: str = "") -> dict[str, Any]:
	from kentender_procurement.award.services import supplier

	return _call("RequestAwardExplanation", notice, supplier.request_explanation, notice=notice, request=request, idempotency_key=idempotency_key)
