# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0800 — ``PublicationAuthorizationService``.

Maps pack §16 permission IDs to Frappe **Role** checks (aligned with SEC-0110 intent in
workstream-7). Denials append a ``TENDER_PUBLICATION_AUTHORIZATION_DENIED`` audit row when a
real user is involved (not ``Administrator`` bypass).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_core.services.audit_event_service import log_audit_event

from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_TENDER_PUBLICATION_AUTHORIZATION_DENIED,
	PACK_AUTHORIZATION_DENIED,
)

# Pack §16 — permission identifiers (documentation / audit metadata).
PERM_INSTANCE_RUN_READINESS = "PERM_INSTANCE_RUN_READINESS"
PERM_PUBLICATION_READINESS_RUN = "PERM_PUBLICATION_READINESS_RUN"
PERM_TENDER_SUBMIT_APPROVAL = "PERM_TENDER_SUBMIT_APPROVAL"
PERM_TENDER_APPROVE = "PERM_TENDER_APPROVE"
PERM_TENDER_REVIEW_RETURN = "PERM_TENDER_REVIEW_RETURN"
PERM_TENDER_PUBLISH = "PERM_TENDER_PUBLISH"
PERM_AUDIT_EXPORT = "PERM_AUDIT_EXPORT"
PERM_TENDER_EVIDENCE_EXPORT = "PERM_TENDER_EVIDENCE_EXPORT"

# Stable ``frappe.throw`` titles (match existing callers / tests).
TITLE_PUBLISH_PERMISSION_DENIED = DenialCode.PUBLISH_PERMISSION_DENIED
TITLE_APPROVAL_DECISION_PERMISSION_DENIED = "APPROVAL_DECISION_PERMISSION_DENIED"
TITLE_PUBLICATION_READINESS_PERMISSION_DENIED = "PUBLICATION_READINESS_PERMISSION_DENIED"
TITLE_SUBMIT_FOR_APPROVAL_PERMISSION_DENIED = "PUBLICATION_SUBMIT_FOR_APPROVAL_DENIED"
TITLE_EVIDENCE_EXPORT_PERMISSION_DENIED = "PUBLICATION_EVIDENCE_EXPORT_DENIED"

# SEC-0110–style role grants (Frappe role names on this bench).
_ROLES_RUN_PUBLICATION_READINESS: frozenset[str] = frozenset(
	{
		"Procurement Officer",
		"System Manager",
		"Purchase Manager",
	}
)
_ROLES_SUBMIT_FOR_APPROVAL: frozenset[str] = frozenset(
	{
		"Procurement Officer",
		"System Manager",
	}
)
_ROLES_APPROVE_OR_RETURN: frozenset[str] = frozenset(
	{
		"System Manager",
		"Purchase Manager",
	}
)
_ROLES_PUBLISH_TENDER: frozenset[str] = frozenset(
	{
		"Procurement Officer",
		"Procurement Manager",
		"Purchase Manager",
		"System Manager",
	}
)
_ROLES_EXPORT_EVIDENCE: frozenset[str] = frozenset(
	{
		"Auditor",
		"Procurement Officer",
		"System Manager",
		"Purchase Manager",
	}
)


def _strip(value: str | None) -> str:
	return (value or "").strip()


def _effective_actor(actor: str | None) -> str:
	return _strip(actor) or _strip(frappe.session.user) or "Administrator"


def _user_roles(user: str) -> set[str]:
	if not user or user == "Guest":
		return set()
	try:
		return set(frappe.get_roles(user))
	except Exception:
		return set()


def _emit_authorization_denied(
	*,
	actor: str,
	action: str,
	required_permission: str,
	metadata: dict[str, Any] | None = None,
) -> None:
	if actor in ("Administrator", "Guest"):
		return
	meta: dict[str, Any] = {
		"action": action,
		"required_permission": required_permission,
		"user_roles": sorted(_user_roles(actor)),
	}
	if metadata:
		meta.update(metadata)
	meta["event_code"] = PACK_AUTHORIZATION_DENIED
	log_audit_event(
		event_type=AUDIT_TENDER_PUBLICATION_AUTHORIZATION_DENIED,
		entity="TENDER_PUBLICATION",
		document_type="User",
		document_name=actor,
		action="publication_authorization_denied",
		performed_by=actor,
		timestamp=now_datetime(),
		metadata=meta,
	)


def _assert_any_role(
	*,
	actor: str,
	allowed: frozenset[str],
	action: str,
	required_permission: str,
	title: str,
	message: str,
	audit_meta: dict[str, Any] | None = None,
) -> None:
	if actor == "Administrator":
		return
	roles = _user_roles(actor)
	if roles & allowed:
		return
	_emit_authorization_denied(
		actor=actor,
		action=action,
		required_permission=required_permission,
		metadata=audit_meta,
	)
	frappe.throw(_(message), title=title, exc=frappe.ValidationError)


class PublicationAuthorizationService:
	"""Role checks for publication workflow (pack §16 / PUB-0800)."""

	@staticmethod
	def assertCanRunPublicationReadiness(actor: str | None = None) -> None:
		"""``PERM_INSTANCE_RUN_READINESS`` or ``PERM_PUBLICATION_READINESS_RUN`` (pack §16).

		Procurement Assistant is **not** granted tender-scope publication readiness in SEC-0110;
		they may still run STD instance readiness via other services.
		"""
		act = _effective_actor(actor)
		_assert_any_role(
			actor=act,
			allowed=_ROLES_RUN_PUBLICATION_READINESS,
			action="run_publication_readiness",
			required_permission=f"{PERM_INSTANCE_RUN_READINESS}|{PERM_PUBLICATION_READINESS_RUN}",
			title=TITLE_PUBLICATION_READINESS_PERMISSION_DENIED,
			message=_("Not permitted to run publication readiness for this tender."),
		)

	@staticmethod
	def assertCanSubmitForApproval(actor: str | None = None) -> None:
		"""``PERM_TENDER_SUBMIT_APPROVAL`` — configuration snapshot / submit-for-approval path."""
		act = _effective_actor(actor)
		_assert_any_role(
			actor=act,
			allowed=_ROLES_SUBMIT_FOR_APPROVAL,
			action="submit_for_approval",
			required_permission=PERM_TENDER_SUBMIT_APPROVAL,
			title=TITLE_SUBMIT_FOR_APPROVAL_PERMISSION_DENIED,
			message=_("Not permitted to submit this tender for publication approval."),
		)

	@staticmethod
	def assertCanApproveForPublication(actor: str | None = None) -> None:
		"""``PERM_TENDER_APPROVE`` or ``PERM_TENDER_REVIEW_RETURN`` for return/reject/clarify."""
		act = _effective_actor(actor)
		_assert_any_role(
			actor=act,
			allowed=_ROLES_APPROVE_OR_RETURN,
			action="approve_or_return",
			required_permission=f"{PERM_TENDER_APPROVE}|{PERM_TENDER_REVIEW_RETURN}",
			title=TITLE_APPROVAL_DECISION_PERMISSION_DENIED,
			message=_("Not permitted to record publication approval decisions."),
		)

	@staticmethod
	def assertCanPublishTender(actor: str | None = None) -> None:
		"""``PERM_TENDER_PUBLISH``."""
		act = _effective_actor(actor)
		_assert_any_role(
			actor=act,
			allowed=_ROLES_PUBLISH_TENDER,
			action="publish_tender",
			required_permission=PERM_TENDER_PUBLISH,
			title=TITLE_PUBLISH_PERMISSION_DENIED,
			message=_("Publishing is not allowed for this user."),
		)

	@staticmethod
	def assertCanExportPublicationEvidence(actor: str | None = None) -> None:
		"""``PERM_AUDIT_EXPORT`` or ``PERM_TENDER_EVIDENCE_EXPORT``."""
		act = _effective_actor(actor)
		_assert_any_role(
			actor=act,
			allowed=_ROLES_EXPORT_EVIDENCE,
			action="export_publication_evidence",
			required_permission=f"{PERM_AUDIT_EXPORT}|{PERM_TENDER_EVIDENCE_EXPORT}",
			title=TITLE_EVIDENCE_EXPORT_PERMISSION_DENIED,
			message=_("Not authorized to export publication evidence."),
		)

	@staticmethod
	def actorMayRunPublicationReadiness(actor: str | None = None) -> bool:
		act = _effective_actor(actor)
		if act == "Administrator":
			return True
		return bool(_user_roles(act) & _ROLES_RUN_PUBLICATION_READINESS)

	@staticmethod
	def actorMaySubmitForApproval(actor: str | None = None) -> bool:
		act = _effective_actor(actor)
		if act == "Administrator":
			return True
		return bool(_user_roles(act) & _ROLES_SUBMIT_FOR_APPROVAL)

	@staticmethod
	def actorMayApproveOrReturn(actor: str | None = None) -> bool:
		act = _effective_actor(actor)
		if act == "Administrator":
			return True
		return bool(_user_roles(act) & _ROLES_APPROVE_OR_RETURN)

	@staticmethod
	def actorMayPublishTender(actor: str | None = None) -> bool:
		act = _effective_actor(actor)
		if act == "Administrator":
			return True
		return bool(_user_roles(act) & _ROLES_PUBLISH_TENDER)

	@staticmethod
	def actorMayExportPublicationEvidence(actor: str | None = None) -> bool:
		act = _effective_actor(actor)
		if act == "Administrator":
			return True
		return bool(_user_roles(act) & _ROLES_EXPORT_EVIDENCE)
