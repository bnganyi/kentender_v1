# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EvidenceExportAuthorizationService — SEC-0600.

Enforces who can export evidence and records export audits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.security.audit.denied_action import (
	DeniedActionAuditService,
)
from kentender_procurement.tender_management.security.audit.event_catalog import (
	AuditEventCode,
)
from kentender_procurement.tender_management.security.audit.event_service import (
	AuditEventService,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)


def _norm(value: Any) -> str:
	return str(value or "").strip()


def _role_set(context: dict[str, Any]) -> frozenset[str]:
	raw = context.get("security_role_codes") or ()
	if isinstance(raw, str):
		raw = (raw,)
	return frozenset(_norm(x) for x in raw if _norm(x))


@dataclass(frozen=True)
class EvidenceExportAuthorizationOutcome:
	allowed: bool
	denial_code: str | None = None
	message: str = ""
	risk_level: str = "High"


class EvidenceExportAuthorizationService:
	"""Pack §18 — evidence export authorization + audit recording."""

	@classmethod
	def check_can_export_evidence(
		cls,
		actor: str,
		tender_code: str,
		context: dict[str, Any] | None = None,
	) -> EvidenceExportAuthorizationOutcome:
		ctx = dict(context or {})
		act = _norm(actor)
		tc = _norm(tender_code)
		if not act or not tc or not frappe.db.exists("TM2 Tender", tc):
			return EvidenceExportAuthorizationOutcome(
				False,
				DenialCode.AUDIT_EXPORT_DENIED,
				"Evidence export requires a valid actor and tender.",
			)
		roles = _role_set(ctx)
		owner = _norm(frappe.db.get_value("TM2 Tender", tc, "owner"))
		if "ROLE_AUDITOR" in roles:
			return EvidenceExportAuthorizationOutcome(True, None, "Auditor can export evidence.")
		if "ROLE_PROCUREMENT_OFFICER" in roles:
			policy_allows = bool(ctx.get("policy_allow_procurement_officer_export", True))
			if policy_allows and owner and owner == act:
				return EvidenceExportAuthorizationOutcome(True, None, "Assigned Procurement Officer can export evidence.")
		if "ROLE_APPROVING_AUTHORITY" in roles:
			if bool(ctx.get("policy_allow_approving_authority_export", False)):
				return EvidenceExportAuthorizationOutcome(True, None, "Approving Authority export allowed by policy.")
		return EvidenceExportAuthorizationOutcome(
			False,
			DenialCode.AUDIT_EXPORT_DENIED,
			"Actor is not authorized to export evidence for this tender.",
		)

	@classmethod
	def assert_can_export_evidence(
		cls,
		actor: str,
		tender_code: str,
		context: dict[str, Any] | None = None,
	) -> None:
		out = cls.check_can_export_evidence(actor, tender_code, context)
		if out.allowed:
			return
		DeniedActionAuditService.record_denied_action(
			actor,
			"EXPORT_EVIDENCE_PACKAGE",
			"TM2 Tender",
			tender_code,
			{
				"denial_code": _norm(out.denial_code) or DenialCode.AUDIT_EXPORT_DENIED,
				"risk_level": out.risk_level,
				"message": out.message,
				"audit_on_attempt": True,
			},
			{"tender_code": tender_code, "event_type": AuditEventCode.AUDIT_EXPORT_DENIED, "source": "SEC-0600"},
		)
		frappe.throw(
			_(out.message or DenialCode.AUDIT_EXPORT_DENIED),
			title=_norm(out.denial_code) or DenialCode.AUDIT_EXPORT_DENIED,
			exc=frappe.ValidationError,
		)

	@classmethod
	def record_evidence_export(
		cls,
		actor: str,
		tender_code: str,
		fmt: str,
		evidence_package_hash: str,
		context: dict[str, Any] | None = None,
	) -> str:
		ctx = dict(context or {})
		tc = _norm(tender_code)
		act = _norm(actor)
		return AuditEventService.record_success(
			AuditEventCode.EVIDENCE_PACKAGE_EXPORTED,
			{
				"audit_event_code": AuditEventCode.EVIDENCE_PACKAGE_EXPORTED,
				"event_type": AuditEventCode.EVIDENCE_PACKAGE_EXPORTED,
				"actor_user_code": act or _norm(getattr(frappe.session, "user", None)) or "Administrator",
				"object_type": "TM2 Tender",
				"object_code": tc,
				"tender_code": tc,
				"action_code": "EXPORT_EVIDENCE_PACKAGE",
				"result": "Success",
				"risk_level": "High",
				"evidence_package_hash": _norm(evidence_package_hash),
				"details": {
					"format": _norm(fmt),
					"source": _norm(ctx.get("source")) or "SEC-0600",
				},
			},
		)

	# Pack aliases (camelCase)
	assertCanExportEvidence = assert_can_export_evidence
	recordEvidenceExport = record_evidence_export
