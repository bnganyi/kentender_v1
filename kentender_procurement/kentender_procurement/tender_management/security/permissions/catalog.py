# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Canonical ``PERM_*`` catalogue — SEC-0100 / workstream-7 pack §5 + std engine §5.

Risks match [std engine §5](docs/prompts/std-production-readiness/workstream-7/1.%20std_engine_security_permissions_and_audit_hardening.md).
``audit_required`` is true for Medium and above (operational audit trail).
"""

from __future__ import annotations

from typing import Any

# (permission_id, permission_name, domain, description, risk_level)
_RAW: tuple[tuple[str, str, str, str, str], ...] = (
	(
		"PERM_TEMPLATE_VIEW",
		"Template view",
		"STD Template Governance",
		"View STD templates/library records.",
		"Low",
	),
	(
		"PERM_TEMPLATE_CREATE",
		"Template create",
		"STD Template Governance",
		"Import/create STD template versions.",
		"High",
	),
	(
		"PERM_TEMPLATE_EDIT_STRUCTURE",
		"Template edit structure",
		"STD Template Governance",
		"Edit draft template structure/advanced configuration.",
		"High",
	),
	(
		"PERM_TEMPLATE_CONFIGURE_PARAMETERS",
		"Template configure parameters",
		"STD Template Governance",
		"Configure parameter definitions.",
		"High",
	),
	(
		"PERM_TEMPLATE_CONFIGURE_FORMS",
		"Template configure forms",
		"STD Template Governance",
		"Configure form definitions.",
		"High",
	),
	(
		"PERM_TEMPLATE_CONFIGURE_COMPONENTS",
		"Template configure components",
		"STD Template Governance",
		"Configure Works components/BOQ rules.",
		"High",
	),
	(
		"PERM_TEMPLATE_CONFIGURE_MAPPINGS",
		"Template configure mappings",
		"STD Template Governance",
		"Configure mappings to Bundle/DSM/DOM/DEM/DCM.",
		"Critical",
	),
	(
		"PERM_TEMPLATE_CONFIGURE_READINESS",
		"Template configure readiness",
		"STD Template Governance",
		"Configure template/instance readiness rules.",
		"Critical",
	),
	(
		"PERM_TEMPLATE_RUN_VALIDATION",
		"Template run validation",
		"STD Template Governance",
		"Run template validation.",
		"Medium",
	),
	(
		"PERM_TEMPLATE_SUBMIT_REVIEW",
		"Template submit review",
		"STD Template Governance",
		"Submit template for legal/policy review.",
		"High",
	),
	(
		"PERM_TEMPLATE_REVIEW",
		"Template review",
		"STD Template Governance",
		"Review template version.",
		"High",
	),
	(
		"PERM_TEMPLATE_APPROVE",
		"Template approve",
		"STD Template Governance",
		"Approve template version.",
		"Critical",
	),
	(
		"PERM_TEMPLATE_ACTIVATE",
		"Template activate",
		"STD Template Governance",
		"Activate template version for tender use.",
		"Critical",
	),
	(
		"PERM_PACKAGE_RELEASE_TO_TENDER",
		"Package release to tender",
		"Planning-to-Tender Release",
		"Release approved procurement package into Tender creation.",
		"Critical",
	),
	(
		"PERM_PACKAGE_RELEASE_VIEW",
		"Package release view",
		"Planning-to-Tender Release",
		"View release eligibility and release history.",
		"Medium",
	),
	(
		"PERM_INSTANCE_VIEW",
		"STD instance view",
		"STD Instance",
		"View tender STD Instance according to role visibility.",
		"Low",
	),
	(
		"PERM_INSTANCE_CREATE",
		"STD instance create",
		"STD Instance",
		"Create STD Instance through Tender context only.",
		"High",
	),
	(
		"PERM_INSTANCE_EDIT_PARAMETERS",
		"STD instance edit parameters",
		"STD Instance",
		"Edit tender-specific TDS/SCC parameter values before lock.",
		"High",
	),
	(
		"PERM_INSTANCE_UPLOAD_ATTACHMENTS",
		"STD instance upload attachments",
		"STD Instance",
		"Upload section-bound attachments before lock.",
		"High",
	),
	(
		"PERM_INSTANCE_CONFIGURE_BOQ",
		"STD instance configure BOQ",
		"STD Instance",
		"Configure tender-specific BOQ before lock.",
		"High",
	),
	(
		"PERM_INSTANCE_RUN_READINESS",
		"STD instance run readiness",
		"STD Instance",
		"Run instance/publication readiness.",
		"Medium",
	),
	(
		"PERM_INSTANCE_GENERATE_OUTPUTS",
		"STD instance generate outputs",
		"STD Instance",
		"Generate Bundle/DSM/DOM/DEM/DCM before lock/publication.",
		"High",
	),
	(
		"PERM_INSTANCE_MARK_READY",
		"STD instance mark ready",
		"STD Instance",
		"Mark STD Instance ready for publication workflow.",
		"High",
	),
	(
		"PERM_INSTANCE_AUDIT_VIEW",
		"STD instance audit view",
		"STD Instance",
		"View STD Instance audit.",
		"Medium",
	),
	(
		"PERM_TENDER_CREATE",
		"Tender create",
		"Tender Publication",
		"Create Tender from release context.",
		"High",
	),
	(
		"PERM_TENDER_VIEW",
		"Tender view",
		"Tender Publication",
		"View Tender according to scope.",
		"Low",
	),
	(
		"PERM_SUPPLIER_PORTAL_TRANSACT",
		"Supplier portal transactions",
		"Tender Management v2",
		"Supplier-side clarification, bid, and addendum acknowledgement actions.",
		"Low",
	),
	(
		"PERM_TENDER_EDIT",
		"Tender edit",
		"Tender Publication",
		"Edit Tender before lock.",
		"High",
	),
	(
		"PERM_TENDER_SUBMIT_APPROVAL",
		"Tender submit for approval",
		"Tender Publication",
		"Submit tender package for approval.",
		"High",
	),
	(
		"PERM_TENDER_APPROVE",
		"Tender approve publication",
		"Tender Publication",
		"Approve tender for publication.",
		"Critical",
	),
	(
		"PERM_TENDER_REVIEW_RETURN",
		"Tender return for correction",
		"Tender Publication",
		"Return tender to preparation during approval review.",
		"High",
	),
	(
		"PERM_TENDER_PUBLISH",
		"Tender publish",
		"Tender Publication",
		"Publish approved tender.",
		"Critical",
	),
	(
		"PERM_PUBLICATION_READINESS_RUN",
		"Publication readiness run",
		"Tender Publication",
		"Run publication readiness gate.",
		"Medium",
	),
	(
		"PERM_TENDER_EVIDENCE_EXPORT",
		"Tender evidence export",
		"Tender Publication",
		"Export tender evidence package.",
		"High",
	),
	(
		"PERM_OPENING_EXECUTE",
		"Opening execute",
		"Downstream",
		"Conduct bid opening using DOM.",
		"Critical",
	),
	(
		"PERM_OPENING_RECORD",
		"Opening record",
		"Downstream",
		"Record DOM-defined opening register.",
		"Critical",
	),
	(
		"PERM_EVALUATION_EXECUTE",
		"Evaluation execute",
		"Downstream",
		"Evaluate bids using DEM.",
		"Critical",
	),
	(
		"PERM_EVALUATION_SUBMIT_REPORT",
		"Evaluation submit report",
		"Downstream",
		"Submit evaluation report.",
		"Critical",
	),
	(
		"PERM_AWARD_APPROVE",
		"Award approve",
		"Downstream",
		"Approve award decision.",
		"Critical",
	),
	(
		"PERM_CONTRACT_GENERATE",
		"Contract generate",
		"Downstream",
		"Generate contract from DCM and award result.",
		"Critical",
	),
	(
		"PERM_CONTRACT_APPROVE",
		"Contract approve",
		"Downstream",
		"Approve contract.",
		"Critical",
	),
	(
		"PERM_CONTRACT_EXECUTE",
		"Contract execute",
		"Downstream",
		"Execute contract.",
		"Critical",
	),
	(
		"PERM_AUDIT_VIEW",
		"Audit view",
		"Audit",
		"View audit logs.",
		"Medium",
	),
	(
		"PERM_AUDIT_EXPORT",
		"Audit export",
		"Audit",
		"Export audit/evidence package.",
		"High",
	),
	(
		"PERM_ADMIN_MANAGE_USERS",
		"Admin manage users",
		"Administration",
		"Manage users and role assignments.",
		"Critical",
	),
	(
		"PERM_ADMIN_OVERRIDE",
		"Admin override",
		"Administration",
		"Controlled administrative override.",
		"Critical",
	),
)


def _audit_required_for_risk(risk_level: str) -> int:
	return 1 if risk_level in ("Medium", "High", "Critical") else 0


def canonical_permission_definitions() -> list[dict[str, Any]]:
	"""Return pack §5 rows as dicts (``permission_id`` … ``active``)."""
	out: list[dict[str, Any]] = []
	for pid, pname, domain, desc, risk in _RAW:
		out.append(
			{
				"permission_id": pid,
				"permission_name": pname,
				"domain": domain,
				"description": desc,
				"risk_level": risk,
				"audit_required": _audit_required_for_risk(risk),
				"active": 1,
			},
		)
	return out


CANONICAL_PERMISSION_IDS: frozenset[str] = frozenset(r[0] for r in _RAW)
