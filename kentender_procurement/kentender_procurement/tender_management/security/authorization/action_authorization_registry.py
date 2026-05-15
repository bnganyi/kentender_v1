# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Action code → required ``PERM_*`` and risk — SEC-0300 / std engine §9.5 + doc 9 §7.4.

Each ``action_code`` maps to one canonical permission and a default ``risk_level`` for
``audit_on_attempt`` / ``requires_confirmation`` hints. Callers may override risk via
``context["risk_level"]``.

Doc 9 §7.4 (Tender Management v2 pack) TM2-style codes share ``PERM_*`` gates aligned
with doc 5 matrix semantics where a dedicated permission does not yet exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

RiskLabel = str  # Low | Medium | High | Critical


@dataclass(frozen=True)
class ActionAuthorizationSpec:
	"""Registry row: business action → permission gate + default risk."""

	required_permission: str
	default_risk_level: RiskLabel


_STD_ENGINE_ACTION_AUTHORIZATION_REGISTRY: dict[str, ActionAuthorizationSpec] = {
	"IMPORT_OFFICIAL_STD_PACKAGE": ActionAuthorizationSpec("PERM_TEMPLATE_CREATE", "High"),
	"VALIDATE_STD_TEMPLATE": ActionAuthorizationSpec("PERM_TEMPLATE_RUN_VALIDATION", "Medium"),
	"ACTIVATE_STD_TEMPLATE": ActionAuthorizationSpec("PERM_TEMPLATE_ACTIVATE", "Critical"),
	"RELEASE_PACKAGE_TO_TENDER": ActionAuthorizationSpec("PERM_PACKAGE_RELEASE_TO_TENDER", "Critical"),
	"CREATE_STD_INSTANCE_FROM_TENDER": ActionAuthorizationSpec("PERM_INSTANCE_CREATE", "High"),
	"EDIT_STD_INSTANCE_PARAMETERS": ActionAuthorizationSpec("PERM_INSTANCE_EDIT_PARAMETERS", "High"),
	"UPLOAD_STD_SECTION_ATTACHMENT": ActionAuthorizationSpec("PERM_INSTANCE_UPLOAD_ATTACHMENTS", "High"),
	"CONFIGURE_WORKS_BOQ": ActionAuthorizationSpec("PERM_INSTANCE_CONFIGURE_BOQ", "High"),
	"GENERATE_STD_OUTPUTS": ActionAuthorizationSpec("PERM_INSTANCE_GENERATE_OUTPUTS", "High"),
	"RUN_PUBLICATION_READINESS": ActionAuthorizationSpec("PERM_PUBLICATION_READINESS_RUN", "Medium"),
	"SUBMIT_TENDER_FOR_APPROVAL": ActionAuthorizationSpec("PERM_TENDER_SUBMIT_APPROVAL", "High"),
	"APPROVE_TENDER_PUBLICATION": ActionAuthorizationSpec("PERM_TENDER_APPROVE", "Critical"),
	"RETURN_TENDER_FOR_CORRECTION": ActionAuthorizationSpec("PERM_TENDER_REVIEW_RETURN", "High"),
	"PUBLISH_TENDER": ActionAuthorizationSpec("PERM_TENDER_PUBLISH", "Critical"),
	"CREATE_ADDENDUM": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"CONSUME_DSM": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"CONSUME_DOM": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"CONSUME_DEM": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"CONSUME_DCM": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"EXPORT_EVIDENCE_PACKAGE": ActionAuthorizationSpec("PERM_TENDER_EVIDENCE_EXPORT", "High"),
	# SEC-0330 / SEC-0700 fixture & smoke actions (same permission gates as underlying operations).
	"CONFIGURE_STD_TEMPLATE_MAPPINGS": ActionAuthorizationSpec("PERM_TEMPLATE_CONFIGURE_MAPPINGS", "High"),
	"EDIT_WORKS_BOQ_DURING_APPROVAL": ActionAuthorizationSpec("PERM_INSTANCE_CONFIGURE_BOQ", "High"),
	"PERFORM_BOQ_ARITHMETIC_CORRECTION": ActionAuthorizationSpec("PERM_INSTANCE_CONFIGURE_BOQ", "Medium"),
	"ADD_MANUAL_EVALUATION_CRITERIA": ActionAuthorizationSpec("PERM_EVALUATION_EXECUTE", "High"),
	"SILENT_DCM_CONTRACT_OVERRIDE": ActionAuthorizationSpec("PERM_CONTRACT_EXECUTE", "Critical"),
}

# Doc 9 §7.4 — Tender Management v2 minimum action catalogue (canonical ``TND2_*`` / ``STD2_*`` / … codes).
_TM2_DOC9_SECTION_74_REGISTRY: dict[str, ActionAuthorizationSpec] = {
	"TND2_CREATE_FROM_PACKAGE": ActionAuthorizationSpec("PERM_TENDER_CREATE", "High"),
	"TND2_VIEW": ActionAuthorizationSpec("PERM_TENDER_VIEW", "Low"),
	"TND2_EDIT_DRAFT": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"TND2_BIND_STD": ActionAuthorizationSpec("PERM_INSTANCE_CREATE", "High"),
	"TND2_RUN_READINESS": ActionAuthorizationSpec("PERM_PUBLICATION_READINESS_RUN", "Medium"),
	"TND2_SUBMIT_PUBLICATION_REVIEW": ActionAuthorizationSpec("PERM_TENDER_SUBMIT_APPROVAL", "High"),
	"TND2_RETURN_CORRECTION": ActionAuthorizationSpec("PERM_TENDER_REVIEW_RETURN", "High"),
	"TND2_APPROVE_PUBLICATION": ActionAuthorizationSpec("PERM_TENDER_APPROVE", "Critical"),
	"TND2_PUBLISH": ActionAuthorizationSpec("PERM_TENDER_PUBLISH", "Critical"),
	"TND2_CANCEL": ActionAuthorizationSpec("PERM_AWARD_APPROVE", "Critical"),
	"TND2_MARK_RETENDER_REQUIRED": ActionAuthorizationSpec("PERM_TENDER_APPROVE", "Critical"),
	"TND2_SUPERSEDE": ActionAuthorizationSpec("PERM_AWARD_APPROVE", "Critical"),
	"STD2_VIEW_BINDING": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"STD2_VIEW_READINESS": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"STD2_VIEW_BUNDLE": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"STD2_VIEW_DSM": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"STD2_VIEW_DOM": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"STD2_VIEW_DEM": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"STD2_VIEW_DCM": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"STD2_VIEW_PUBLICATION_SNAPSHOT": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"STD2_REQUEST_REGENERATION": ActionAuthorizationSpec("PERM_INSTANCE_GENERATE_OUTPUTS", "High"),
	"ACC2_CONFIGURE_ACCESS_RULE": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"INV2_CREATE": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"INV2_SEND": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"INV2_REVOKE": ActionAuthorizationSpec("PERM_TENDER_APPROVE", "Critical"),
	"CLR2_SUBMIT": ActionAuthorizationSpec("PERM_SUPPLIER_PORTAL_TRANSACT", "Low"),
	"CLR2_START_REVIEW": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"CLR2_DRAFT_RESPONSE": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"CLR2_APPROVE_RESPONSE": ActionAuthorizationSpec("PERM_TENDER_APPROVE", "Critical"),
	"CLR2_PUBLISH_RESPONSE": ActionAuthorizationSpec("PERM_TENDER_PUBLISH", "Critical"),
	"CLR2_REJECT": ActionAuthorizationSpec("PERM_TENDER_APPROVE", "Critical"),
	"CLR2_CONVERT_TO_ADDENDUM": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"ADD2_CREATE": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"ADD2_EDIT_DRAFT": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"ADD2_REQUEST_IMPACT_ANALYSIS": ActionAuthorizationSpec("PERM_INSTANCE_GENERATE_OUTPUTS", "High"),
	"ADD2_SUBMIT_LEGAL_REVIEW": ActionAuthorizationSpec("PERM_TENDER_EDIT", "High"),
	"ADD2_CLEAR_LEGAL_REVIEW": ActionAuthorizationSpec("PERM_TENDER_APPROVE", "Critical"),
	"ADD2_SUBMIT_APPROVAL": ActionAuthorizationSpec("PERM_TENDER_SUBMIT_APPROVAL", "High"),
	"ADD2_APPROVE": ActionAuthorizationSpec("PERM_TENDER_APPROVE", "Critical"),
	"ADD2_ISSUE": ActionAuthorizationSpec("PERM_TENDER_PUBLISH", "Critical"),
	"ADD2_CANCEL": ActionAuthorizationSpec("PERM_TENDER_APPROVE", "Critical"),
	"ADD2_ACKNOWLEDGE": ActionAuthorizationSpec("PERM_SUPPLIER_PORTAL_TRANSACT", "Low"),
	"BID2_START_DRAFT": ActionAuthorizationSpec("PERM_SUPPLIER_PORTAL_TRANSACT", "Low"),
	"BID2_SAVE_DRAFT": ActionAuthorizationSpec("PERM_SUPPLIER_PORTAL_TRANSACT", "Low"),
	"BID2_SUBMIT": ActionAuthorizationSpec("PERM_SUPPLIER_PORTAL_TRANSACT", "Critical"),
	"BID2_REPLACE": ActionAuthorizationSpec("PERM_SUPPLIER_PORTAL_TRANSACT", "High"),
	"BID2_WITHDRAW": ActionAuthorizationSpec("PERM_SUPPLIER_PORTAL_TRANSACT", "High"),
	"BID2_VIEW_METADATA_INTERNAL": ActionAuthorizationSpec("PERM_INSTANCE_VIEW", "Low"),
	"BID2_VIEW_SEALED_CONTENT": ActionAuthorizationSpec("PERM_OPENING_EXECUTE", "Critical"),
	"BID2_RECORD_LATE_ATTEMPT": ActionAuthorizationSpec("PERM_TENDER_VIEW", "Medium"),
	"CLS2_CLOSE_TENDER": ActionAuthorizationSpec("PERM_AWARD_APPROVE", "Critical"),
	"OR2_PREPARE_OPENING_READINESS": ActionAuthorizationSpec("PERM_OPENING_RECORD", "Critical"),
	"OR2_SEND_TO_OPENING": ActionAuthorizationSpec("PERM_OPENING_EXECUTE", "Critical"),
	"EV2_PREPARE_EVALUATION_HANDOFF": ActionAuthorizationSpec("PERM_EVALUATION_EXECUTE", "Critical"),
	"EV2_SEND_TO_EVALUATION": ActionAuthorizationSpec("PERM_EVALUATION_SUBMIT_REPORT", "Critical"),
	"CON2_CREATE_CONTRACT_HANDOFF": ActionAuthorizationSpec("PERM_CONTRACT_GENERATE", "Critical"),
	"AUD2_VIEW_AUDIT_TRAIL": ActionAuthorizationSpec("PERM_AUDIT_VIEW", "Medium"),
	"AUD2_EXPORT_EVIDENCE": ActionAuthorizationSpec("PERM_AUDIT_EXPORT", "High"),
	"OVR2_ADMIN_OVERRIDE": ActionAuthorizationSpec("PERM_ADMIN_OVERRIDE", "Critical"),
}

ACTION_AUTHORIZATION_REGISTRY: Final[dict[str, ActionAuthorizationSpec]] = {
	**_STD_ENGINE_ACTION_AUTHORIZATION_REGISTRY,
	**_TM2_DOC9_SECTION_74_REGISTRY,
}


def spec_for_action(action_code: str) -> ActionAuthorizationSpec | None:
	key = (action_code or "").strip()
	if not key:
		return None
	return ACTION_AUTHORIZATION_REGISTRY.get(key)


def registered_action_codes() -> frozenset[str]:
	return frozenset(ACTION_AUTHORIZATION_REGISTRY)


def tm2_doc9_section_74_action_codes() -> frozenset[str]:
	"""Doc 9 §7.4 — authoritative frozen set of TM2 pack action codes."""
	return frozenset(_TM2_DOC9_SECTION_74_REGISTRY)
