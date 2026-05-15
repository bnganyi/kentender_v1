# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §7.6 — ``audit_access_denied`` for action-availability guard failures.

Bridges :func:`~kentender_procurement.tender_management.security.action_availability.service.get_action_availability`
§7.3 payloads into :class:`~kentender_procurement.tender_management.security.audit.denied_action.DeniedActionAuditService`
so denied legal attempts always leave an ``Audit Event`` trail.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from kentender_procurement.tender_management.security.audit.denied_action import (
	DeniedActionAuditService,
)
from kentender_procurement.tender_management.security.audit.event_catalog import (
	AuditEventCode,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)


def _norm(value: Any) -> str:
	return str(value or "").strip()


def audit_access_denied(
	actor: str,
	object_code: str,
	availability: Mapping[str, Any],
	payload: dict[str, Any] | None = None,
) -> str | None:
	"""Record an append-only audit row for a denied action-availability check (doc 9 §7.6).

	:param actor: Authenticated user id (email or ``Administrator``).
	:param object_code: Primary object business code (fallback if missing from ``availability``).
	:param availability: §7.3-shaped dict from ``get_action_availability`` / ``ActionAvailabilityService``.
	:param payload: Optional extra context (merged into denied-action audit context).

	When ``availability["allowed"]`` is true, this is a no-op and returns ``None``.
	Otherwise ``audit_on_attempt`` is forced so low-risk denials still persist for TM2 guards.
	"""
	av = dict(availability or {})
	if av.get("allowed") is True:
		return None

	pl = dict(payload or {})
	action_code = _norm(av.get("action_code")) or "UNKNOWN"
	obj_type = _norm(av.get("object_type")) or _norm(pl.get("object_type")) or "Authorization Target"
	obj_code = _norm(object_code) or _norm(av.get("object_code")) or "UNKNOWN"
	msg = _norm(av.get("user_message")) or _norm(av.get("message")) or "Action not allowed."
	denial_code = _norm(av.get("denial_code")) or DenialCode.AUTH_ACTION_AVAILABILITY_DENIED.value

	denial_decision: dict[str, Any] = {
		"denial_code": denial_code,
		"risk_level": _norm(av.get("risk_level")) or "Medium",
		"message": msg,
		"required_permission": _norm(av.get("required_permission")),
		# Doc §7.6: denied guard path must leave evidence even when engine risk is Low/Medium.
		"audit_on_attempt": True,
	}

	ctx = dict(pl)
	ctx.setdefault("source", "audit_access_denied")
	if not _norm(ctx.get("event_type")):
		ctx["event_type"] = AuditEventCode.ACTION_AVAILABILITY_DENIED.value

	tc = _norm(ctx.get("tender_code"))
	if not tc and obj_type == "TM2 Tender":
		ctx["tender_code"] = obj_code

	return DeniedActionAuditService.record_denied_action(
		_norm(actor) or "Administrator",
		action_code,
		obj_type,
		obj_code,
		denial_decision,
		ctx,
	)


def auditAccessDenied(
	actor: str,
	object_code: str,
	availability: Mapping[str, Any],
	payload: dict[str, Any] | None = None,
) -> str | None:
	"""CamelCase alias for :func:`audit_access_denied`."""
	return audit_access_denied(actor, object_code, availability, payload=payload)
