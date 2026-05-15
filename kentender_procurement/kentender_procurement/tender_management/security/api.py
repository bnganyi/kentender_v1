from __future__ import annotations

import json
from typing import Any, Callable

import frappe
from frappe import _

from kentender_procurement.tender_management.security.audit.event_service import (
	AuditEventService,
)
from kentender_procurement.tender_management.security.evidence.export_authorization import (
	EvidenceExportAuthorizationService,
)

SEC_API_INTERNAL_ERROR = "SEC_API_INTERNAL_ERROR"
SEC_API_PAYLOAD_INVALID = "SEC_API_PAYLOAD_INVALID"
SEC_API_OBJECT_TYPE_REQUIRED = "SEC_API_OBJECT_TYPE_REQUIRED"
SEC_API_OBJECT_CODE_REQUIRED = "SEC_API_OBJECT_CODE_REQUIRED"
SEC_API_TENDER_CODE_REQUIRED = "SEC_API_TENDER_CODE_REQUIRED"

_KNOWN_VALIDATION_CODES: frozenset[str] = frozenset(
	{
		SEC_API_PAYLOAD_INVALID,
		SEC_API_OBJECT_TYPE_REQUIRED,
		SEC_API_OBJECT_CODE_REQUIRED,
		SEC_API_TENDER_CODE_REQUIRED,
	}
)


def _api_fail(error_code: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
	return {
		"success": False,
		"error_code": str(error_code),
		"message": str(message),
		"details": dict(details or {}),
	}


def _api_ok(**payload: Any) -> dict[str, Any]:
	out: dict[str, Any] = {"success": True}
	out.update(payload)
	return out


def _stable_title_from_message_log() -> str | None:
	log = frappe.get_message_log()
	if not log:
		return None
	return str(log[-1].get("title") or "").strip() or None


def _wrap(handler_id: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
	frappe.clear_messages()
	try:
		return fn()
	except frappe.ValidationError as exc:
		code = _stable_title_from_message_log()
		if code not in _KNOWN_VALIDATION_CODES:
			code = SEC_API_PAYLOAD_INVALID
		return _api_fail(code, str(exc), details={})
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"SEC-0900 {handler_id}")
		return _api_fail(SEC_API_INTERNAL_ERROR, _("Unexpected server error."), details={})


def _as_payload_dict(raw: Any, *, field: str) -> dict[str, Any]:
	if raw is None:
		return {}
	if isinstance(raw, dict):
		return dict(raw)
	if isinstance(raw, str):
		s = raw.strip()
		if not s:
			return {}
		try:
			parsed = json.loads(s)
		except json.JSONDecodeError:
			frappe.throw(
				_(f"{field} must be valid JSON."),
				title=SEC_API_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)
		if not isinstance(parsed, dict):
			frappe.throw(
				_(f"{field} must be a JSON object."),
				title=SEC_API_PAYLOAD_INVALID,
				exc=frappe.ValidationError,
			)
		return dict(parsed)
	frappe.throw(
		_(f"{field} must be a dict or JSON object."),
		title=SEC_API_PAYLOAD_INVALID,
		exc=frappe.ValidationError,
	)


def _required_text(value: Any, *, code: str, field: str) -> str:
	txt = str(value or "").strip()
	if txt:
		return txt
	frappe.throw(
		_(f"{field} is required."),
		title=code,
		exc=frappe.ValidationError,
	)


def _session_actor() -> str:
	return str(frappe.session.user or "").strip()


@frappe.whitelist()
def sec_api_audit_events(
	object_type: str,
	object_code: str,
	filters: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""GET /api/audit/events?object_type=&object_code=."""

	def _run() -> dict[str, Any]:
		ot = _required_text(object_type, code=SEC_API_OBJECT_TYPE_REQUIRED, field="object_type")
		oc = _required_text(object_code, code=SEC_API_OBJECT_CODE_REQUIRED, field="object_code")
		query_filters = _as_payload_dict(filters, field="filters")
		rows = AuditEventService.get_audit_events_for_object(ot, oc, query_filters)
		return _api_ok(actor_user_code=_session_actor(), object_type=ot, object_code=oc, events=rows)

	return _wrap("audit_events_object", _run)


@frappe.whitelist()
def sec_api_audit_tender_events(
	tender_code: str,
	filters: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""GET /api/audit/tenders/{tender_code}/events."""

	def _run() -> dict[str, Any]:
		tc = _required_text(tender_code, code=SEC_API_TENDER_CODE_REQUIRED, field="tender_code")
		query_filters = _as_payload_dict(filters, field="filters")
		rows = AuditEventService.get_audit_events_for_tender(tc, query_filters)
		return _api_ok(actor_user_code=_session_actor(), tender_code=tc, events=rows)

	return _wrap("audit_events_tender", _run)


@frappe.whitelist()
def sec_api_evidence_export_availability(
	tender_code: str,
	context: dict[str, Any] | str | None = None,
	actor: str | None = None,
) -> dict[str, Any]:
	"""POST /api/tenders/{tender_code}/evidence/export-availability."""

	def _run() -> dict[str, Any]:
		tc = _required_text(tender_code, code=SEC_API_TENDER_CODE_REQUIRED, field="tender_code")
		ctx = _as_payload_dict(context, field="context")
		session_actor = _session_actor()
		_ = actor  # session actor is mandatory for SEC-0900 API checks.
		out = EvidenceExportAuthorizationService.check_can_export_evidence(session_actor, tc, ctx)
		return _api_ok(
			actor_user_code=session_actor,
			tender_code=tc,
			allowed=bool(out.allowed),
			denial_code=(out.denial_code or None),
			message=(out.message or ""),
			risk_level=(out.risk_level or ""),
		)

	return _wrap("evidence_export_availability", _run)
