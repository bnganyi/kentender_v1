# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NegativePermissionService — SEC-0330 / Cursor pack §11.

Explicit **NEG_*** prohibitions override broad grants. Used by
:class:`~kentender_procurement.tender_management.security.authorization.decision_engine.AuthorizationDecisionEngine`
when ``context["enforce_negative_permission_rules"]`` is true (after permission
passes). Pack Java name ``evaluateNegativeRules`` maps to :meth:`evaluate_negative_rules`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)

# --- Pack §11 rule codes (stable identifiers for audit / tests) ---------------

NEG_STD_ADMIN_NO_INSTANCE_CREATE = "NEG_STD_ADMIN_NO_INSTANCE_CREATE"
"""STD Admin must not create tender STD instances."""

NEG_STD_ADMIN_NO_PACKAGE_RELEASE = "NEG_STD_ADMIN_NO_PACKAGE_RELEASE"
"""STD Admin must not release procurement packages to tender (fixture NEG-SEC-001)."""

NEG_PROC_NO_TEMPLATE_CONFIG = "NEG_PROC_NO_TEMPLATE_CONFIG"
"""Procurement Officer must not perform STD template configuration / mapping edits."""

NEG_ASSISTANT_NO_MARK_READY = "NEG_ASSISTANT_NO_MARK_READY"
"""Procurement Assistant must not publish, submit for approval, or run publication readiness by default."""

NEG_APPROVER_NO_SILENT_EDIT = "NEG_APPROVER_NO_SILENT_EDIT"
"""Approving Authority must not silently edit tender / instance content during approval."""

NEG_OPENING_NO_EVALUATION = "NEG_OPENING_NO_EVALUATION"
"""Opening Committee must not perform evaluation-stage BOQ corrections."""

NEG_EVAL_NO_MANUAL_CRITERIA = "NEG_EVAL_NO_MANUAL_CRITERIA"
"""Evaluation Committee must not add manual evaluation criteria."""

NEG_CONTRACT_NO_DCM_OVERRIDE = "NEG_CONTRACT_NO_DCM_OVERRIDE"
"""Contract party must not silently override DCM binding."""

NEG_AUDITOR_NO_MUTATION = "NEG_AUDITOR_NO_MUTATION"
"""Auditor must not mutate operational records."""

NEG_SYSADMIN_NO_OPERATIONAL_APPROVAL = "NEG_SYSADMIN_NO_OPERATIONAL_APPROVAL"
"""System Administrator must not approve or publish tenders by default."""

NEG_PUBLISHED_NO_DIRECT_EDIT = "NEG_PUBLISHED_NO_DIRECT_EDIT"
"""Published artifacts cannot be directly edited (caller sets ``published_direct_edit_negation``)."""


@dataclass(frozen=True)
class NegativePermissionOutcome:
	"""Result of :meth:`NegativePermissionService.evaluate_negative_rules`."""

	allowed: bool
	denial_codes: tuple[str, ...] = ()
	message: str = ""
	rule_codes: tuple[str, ...] = ()


def _norm_user(uid: str | None) -> str:
	return (uid or "").strip()


def _norm_action(ac: str | None) -> str:
	return (ac or "").strip()


def _roles_from_context(context: dict[str, Any]) -> frozenset[str]:
	raw = context.get("security_role_codes") or ()
	if isinstance(raw, str):
		raw = (raw,)
	return frozenset(str(x).strip() for x in raw if str(x).strip())


def _outcome_ok() -> NegativePermissionOutcome:
	return NegativePermissionOutcome(True, (), "", ())


def _outcome_deny(
	*,
	denial_code: str,
	message: str,
	rule_code: str,
) -> NegativePermissionOutcome:
	dc = (denial_code or "").strip() or DenialCode.STD_AUTH_PERMISSION_DENIED
	msg = (message or "").strip() or dc
	return NegativePermissionOutcome(False, (dc,), msg, (rule_code,))


class NegativePermissionService:
	"""Pack §11 — negative rules keyed by ``ROLE_*`` + ``action_code`` (+ optional context flags)."""

	_ROLE_STD_ADMIN: ClassVar[str] = "ROLE_STD_ADMIN"
	_ROLE_PROCUREMENT_OFFICER: ClassVar[str] = "ROLE_PROCUREMENT_OFFICER"
	_ROLE_PROCUREMENT_ASSISTANT: ClassVar[str] = "ROLE_PROCUREMENT_ASSISTANT"
	_ROLE_APPROVING_AUTHORITY: ClassVar[str] = "ROLE_APPROVING_AUTHORITY"
	_ROLE_OPENING_COMMITTEE: ClassVar[str] = "ROLE_OPENING_COMMITTEE"
	_ROLE_EVALUATION_COMMITTEE: ClassVar[str] = "ROLE_EVALUATION_COMMITTEE"
	_ROLE_AUDITOR: ClassVar[str] = "ROLE_AUDITOR"
	_ROLE_SYSTEM_ADMIN: ClassVar[str] = "ROLE_SYSTEM_ADMIN"
	# Not (yet) in SEC-0110 matrix; used only for this negative gate + tests / SEC-0700 fixtures.
	_ROLE_CONTRACT_OFFICER: ClassVar[str] = "ROLE_CONTRACT_OFFICER"

	_PUBLISHED_EDIT_ACTIONS: ClassVar[frozenset[str]] = frozenset(
		{
			"EDIT_STD_INSTANCE_PARAMETERS",
			"UPLOAD_STD_SECTION_ATTACHMENT",
			"CONFIGURE_WORKS_BOQ",
			"GENERATE_STD_OUTPUTS",
			"EDIT_WORKS_BOQ_DURING_APPROVAL",
		}
	)

	_AUDITOR_MUTATION_ACTIONS: ClassVar[frozenset[str]] = frozenset(
		{
			"IMPORT_OFFICIAL_STD_PACKAGE",
			"VALIDATE_STD_TEMPLATE",
			"ACTIVATE_STD_TEMPLATE",
			"RELEASE_PACKAGE_TO_TENDER",
			"CREATE_STD_INSTANCE_FROM_TENDER",
			"EDIT_STD_INSTANCE_PARAMETERS",
			"UPLOAD_STD_SECTION_ATTACHMENT",
			"CONFIGURE_WORKS_BOQ",
			"GENERATE_STD_OUTPUTS",
			"RUN_PUBLICATION_READINESS",
			"SUBMIT_TENDER_FOR_APPROVAL",
			"APPROVE_TENDER_PUBLICATION",
			"RETURN_TENDER_FOR_CORRECTION",
			"PUBLISH_TENDER",
			"CREATE_ADDENDUM",
			"CONFIGURE_STD_TEMPLATE_MAPPINGS",
			"EDIT_WORKS_BOQ_DURING_APPROVAL",
			"PERFORM_BOQ_ARITHMETIC_CORRECTION",
			"ADD_MANUAL_EVALUATION_CRITERIA",
			"SILENT_DCM_CONTRACT_OVERRIDE",
		}
	)

	_APPROVER_INSTANCE_EDITS: ClassVar[frozenset[str]] = frozenset(
		{
			"EDIT_STD_INSTANCE_PARAMETERS",
			"UPLOAD_STD_SECTION_ATTACHMENT",
			"CONFIGURE_WORKS_BOQ",
		}
	)

	_TEMPLATE_CONFIG_ACTIONS: ClassVar[frozenset[str]] = frozenset(
		{
			"IMPORT_OFFICIAL_STD_PACKAGE",
			"ACTIVATE_STD_TEMPLATE",
			"VALIDATE_STD_TEMPLATE",
			"CONFIGURE_STD_TEMPLATE_MAPPINGS",
		}
	)

	_ASSISTANT_MARK_READY_ACTIONS: ClassVar[frozenset[str]] = frozenset(
		{
			"PUBLISH_TENDER",
			"SUBMIT_TENDER_FOR_APPROVAL",
			"RUN_PUBLICATION_READINESS",
		}
	)

	@classmethod
	def evaluate_negative_rules(
		cls,
		actor: str,
		action_code: str,
		object_type: str,
		object_code: str,
		context: dict[str, Any] | None = None,
	) -> NegativePermissionOutcome:
		"""Evaluate pack §11 negative rules for ``actor`` and ``action_code``.

		``object_type`` / ``object_code`` are reserved for future tender-scoped rules.
		Role hints are taken from ``context["security_role_codes"]`` (same as the
		authorization engine). Optional flags:

		- ``tender_in_approval`` (bool): Approver silent-edit rule for ordinary instance edits.
		- ``published_direct_edit_negation`` (bool): Published-artifact direct-edit denial.
		"""
		_ = (object_type, object_code)
		ctx = dict(context) if context else {}
		ac = _norm_action(action_code)
		if not ac:
			return _outcome_ok()
		if _norm_user(actor) == "Administrator":
			return _outcome_ok()

		roles = _roles_from_context(ctx)

		# --- Published artifact (explicit caller flag) -------------------------
		if bool(ctx.get("published_direct_edit_negation")) and ac in cls._PUBLISHED_EDIT_ACTIONS:
			return _outcome_deny(
				denial_code=DenialCode.POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED,
				message="Published artifacts cannot be directly edited; an addendum is required.",
				rule_code=NEG_PUBLISHED_NO_DIRECT_EDIT,
			)

		# --- STD Admin ---------------------------------------------------------
		if cls._ROLE_STD_ADMIN in roles:
			if ac == "CREATE_STD_INSTANCE_FROM_TENDER":
				return _outcome_deny(
					denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
					message="STD Administrator cannot create tender STD instances.",
					rule_code=NEG_STD_ADMIN_NO_INSTANCE_CREATE,
				)
			if ac == "RELEASE_PACKAGE_TO_TENDER":
				return _outcome_deny(
					denial_code=DenialCode.RELEASE_PERMISSION_DENIED,
					message="STD Administrator cannot release procurement packages to tender.",
					rule_code=NEG_STD_ADMIN_NO_PACKAGE_RELEASE,
				)

		# --- Procurement Officer (template configuration) -------------------
		if cls._ROLE_PROCUREMENT_OFFICER in roles and ac in cls._TEMPLATE_CONFIG_ACTIONS:
			return _outcome_deny(
				denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
				message="Procurement Officer cannot edit STD template mappings or configuration.",
				rule_code=NEG_PROC_NO_TEMPLATE_CONFIG,
			)

		# --- Procurement Assistant --------------------------------------------
		if cls._ROLE_PROCUREMENT_ASSISTANT in roles and ac in cls._ASSISTANT_MARK_READY_ACTIONS:
			if ac == "PUBLISH_TENDER":
				return _outcome_deny(
					denial_code=DenialCode.PUBLISH_PERMISSION_DENIED,
					message="Procurement Assistant cannot publish tenders by default.",
					rule_code=NEG_ASSISTANT_NO_MARK_READY,
				)
			return _outcome_deny(
				denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
				message="Procurement Assistant cannot submit or run publication readiness by default.",
				rule_code=NEG_ASSISTANT_NO_MARK_READY,
			)

		# --- Approving Authority ------------------------------------------------
		if cls._ROLE_APPROVING_AUTHORITY in roles:
			if ac == "EDIT_WORKS_BOQ_DURING_APPROVAL":
				return _outcome_deny(
					denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
					message="Approving Authority cannot edit tender content during approval.",
					rule_code=NEG_APPROVER_NO_SILENT_EDIT,
				)
			if bool(ctx.get("tender_in_approval")) and ac in cls._APPROVER_INSTANCE_EDITS:
				return _outcome_deny(
					denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
					message="Approving Authority cannot silently edit tender content during approval.",
					rule_code=NEG_APPROVER_NO_SILENT_EDIT,
				)

		# --- Opening Committee --------------------------------------------------
		if cls._ROLE_OPENING_COMMITTEE in roles and ac == "PERFORM_BOQ_ARITHMETIC_CORRECTION":
			return _outcome_deny(
				denial_code=DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION,
				message="Opening Committee cannot perform evaluation-stage BOQ arithmetic corrections.",
				rule_code=NEG_OPENING_NO_EVALUATION,
			)

		# --- Evaluation Committee ----------------------------------------------
		if cls._ROLE_EVALUATION_COMMITTEE in roles and ac == "ADD_MANUAL_EVALUATION_CRITERIA":
			return _outcome_deny(
				denial_code=DenialCode.MANUAL_EVALUATION_CRITERIA_DENIED,
				message="Evaluation Committee cannot add manual evaluation criteria.",
				rule_code=NEG_EVAL_NO_MANUAL_CRITERIA,
			)

		# --- Contract (non-matrix role code) -----------------------------------
		if cls._ROLE_CONTRACT_OFFICER in roles and ac == "SILENT_DCM_CONTRACT_OVERRIDE":
			return _outcome_deny(
				denial_code=DenialCode.STD_AUTH_DCM_CONTRACT_BINDING_VIOLATION,
				message="Contract role cannot silently override DCM binding.",
				rule_code=NEG_CONTRACT_NO_DCM_OVERRIDE,
			)

		# --- Auditor ------------------------------------------------------------
		if cls._ROLE_AUDITOR in roles and ac in cls._AUDITOR_MUTATION_ACTIONS:
			return _outcome_deny(
				denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
				message="Auditor cannot mutate operational records.",
				rule_code=NEG_AUDITOR_NO_MUTATION,
			)

		# --- System Administrator ---------------------------------------------
		if cls._ROLE_SYSTEM_ADMIN in roles and ac in {"APPROVE_TENDER_PUBLICATION", "PUBLISH_TENDER"}:
			return _outcome_deny(
				denial_code=DenialCode.STD_AUTH_PERMISSION_DENIED,
				message="System Administrator cannot approve or publish tenders by default.",
				rule_code=NEG_SYSADMIN_NO_OPERATIONAL_APPROVAL,
			)

		return _outcome_ok()

	@classmethod
	def evaluateNegativeRules(
		cls,
		actor: str,
		action_code: str,
		object_type: str,
		object_code: str,
		context: dict[str, Any] | None = None,
	) -> NegativePermissionOutcome:
		"""Alias for :meth:`evaluate_negative_rules` (pack §11 spelling)."""
		return cls.evaluate_negative_rules(actor, action_code, object_type, object_code, context)
