# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DeniedActionAuditService — SEC-0530."""

from __future__ import annotations

from typing import Any

from kentender_procurement.tender_management.security.audit.event_catalog import (
	AuditEventCode,
)
from kentender_procurement.tender_management.security.audit.event_service import (
	AuditEventService,
)


def _norm(value: Any) -> str:
	return str(value or "").strip()


def _is_high_critical(risk_level: str) -> bool:
	return _norm(risk_level) in {"High", "Critical"}


def _default_event_type(action_code: str, object_type: str, denial_code: str) -> str:
	ac = _norm(action_code)
	ot = _norm(object_type).lower()
	dc = _norm(denial_code)
	if dc == "POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED":
		return AuditEventCode.POST_PUBLICATION_EDIT_DENIED
	if ac == "RELEASE_PACKAGE_TO_TENDER":
		return AuditEventCode.RELEASE_PERMISSION_DENIED
	if ac in {
		"IMPORT_OFFICIAL_STD_PACKAGE",
		"VALIDATE_STD_TEMPLATE",
		"ACTIVATE_STD_TEMPLATE",
		"CONFIGURE_STD_TEMPLATE_MAPPINGS",
	} or "template" in ot:
		return AuditEventCode.STD_TEMPLATE_EDIT_DENIED
	if ac in {"ADD_MANUAL_EVALUATION_CRITERIA", "SILENT_DCM_CONTRACT_OVERRIDE"}:
		return AuditEventCode.MANUAL_RULE_INJECTION_DENIED
	if ac in {"PUBLISH_TENDER", "APPROVE_TENDER_PUBLICATION"}:
		return AuditEventCode.PUBLICATION_DENIED
	return AuditEventCode.PUBLICATION_DENIED


class DeniedActionAuditService:
	"""Pack §17 denied-action recorder (uniform metadata + high/critical guarantee)."""

	@classmethod
	def record_denied_action(
		cls,
		actor: str,
		action_code: str,
		object_type: str,
		object_code: str,
		denial_decision: dict[str, Any],
		context: dict[str, Any] | None = None,
	) -> str | None:
		ctx = dict(context or {})
		dd = dict(denial_decision or {})
		risk_level = _norm(dd.get("risk_level")) or _norm(ctx.get("risk_level")) or "Medium"
		audit_on_attempt = bool(dd.get("audit_on_attempt") if "audit_on_attempt" in dd else ctx.get("audit_on_attempt"))
		if not _is_high_critical(risk_level) and not audit_on_attempt:
			return None

		denial_code = _norm(dd.get("denial_code")) or "STD_AUTH_PERMISSION_DENIED"
		event_type = _norm(ctx.get("event_type")) or _default_event_type(action_code, object_type, denial_code)
		tender_code = _norm(ctx.get("tender_code")) or _norm(dd.get("tender_code"))
		meta: dict[str, Any] = {
			"audit_event_code": event_type,
			"event_type": event_type,
			"actor_user_code": _norm(actor) or "Administrator",
			"object_type": _norm(object_type) or "Authorization Target",
			"object_code": _norm(object_code) or "UNKNOWN",
			"action_code": _norm(action_code),
			"result": "Denied",
			"denial_code": denial_code,
			"risk_level": risk_level,
			"message": _norm(dd.get("message")) or _norm(ctx.get("message")) or "Action denied.",
			"tender_code": tender_code or None,
			"request_id": _norm(ctx.get("request_id")) or None,
			"ip_address": _norm(ctx.get("ip_address")) or None,
			"details": {
				"required_permission": _norm(dd.get("required_permission")),
				"source": _norm(ctx.get("source")) or "DeniedActionAuditService",
			},
		}
		return AuditEventService.record_denied(event_type, denial_code, meta)

	@classmethod
	def recordDeniedAction(
		cls,
		actor: str,
		action_code: str,
		object_type: str,
		object_code: str,
		denial_decision: dict[str, Any],
		context: dict[str, Any] | None = None,
	) -> str | None:
		return cls.record_denied_action(actor, action_code, object_type, object_code, denial_decision, context)
