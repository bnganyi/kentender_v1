# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Canonical role–permission matrix — SEC-0110 / pack §6 + std engine §6.

Grants follow Cursor pack §6 where specified; ``ROLE_LEGAL_REVIEWER`` follows
std engine §6.2. ``explicit_non_grants`` are pack ``Required non-grants`` blocks
or std §6.2 ``No`` rows, plus prose-derived checks where the pack requires them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from kentender_procurement.tender_management.security.permissions.catalog import (
	CANONICAL_PERMISSION_IDS,
)


@dataclass(frozen=True)
class RoleMatrixEntry:
	"""One canonical ``ROLE_*`` row: display metadata + grant / non-grant sets."""

	role_name: str
	description: str
	grants: frozenset[str]
	explicit_non_grants: frozenset[str]


# Cursor pack §6 — ROLE_STD_ADMIN … SYSTEM_ADMIN; Legal reviewer from std §6.2.
ROLE_MATRIX: dict[str, RoleMatrixEntry] = {
	"ROLE_STD_ADMIN": RoleMatrixEntry(
		role_name="STD Administrator",
		description="Maintains official STD library and advanced template configuration.",
		grants=frozenset(
			{
				"PERM_TEMPLATE_VIEW",
				"PERM_TEMPLATE_CREATE",
				"PERM_TEMPLATE_EDIT_STRUCTURE",
				"PERM_TEMPLATE_CONFIGURE_PARAMETERS",
				"PERM_TEMPLATE_CONFIGURE_FORMS",
				"PERM_TEMPLATE_CONFIGURE_COMPONENTS",
				"PERM_TEMPLATE_CONFIGURE_MAPPINGS",
				"PERM_TEMPLATE_CONFIGURE_READINESS",
				"PERM_TEMPLATE_RUN_VALIDATION",
				"PERM_TEMPLATE_SUBMIT_REVIEW",
			},
		),
		explicit_non_grants=frozenset(
			{
				"PERM_INSTANCE_CREATE",
				"PERM_PACKAGE_RELEASE_TO_TENDER",
				"PERM_TENDER_APPROVE",
				"PERM_TENDER_PUBLISH",
			},
		),
	),
	"ROLE_LEGAL_REVIEWER": RoleMatrixEntry(
		role_name="Legal / Policy Reviewer",
		description="Reviews and approves STD template versions; activation when governance assigns.",
		grants=frozenset(
			{
				"PERM_TEMPLATE_VIEW",
				"PERM_TEMPLATE_REVIEW",
				"PERM_TEMPLATE_APPROVE",
				"PERM_TEMPLATE_ACTIVATE",
			},
		),
		explicit_non_grants=frozenset(
			{
				"PERM_TEMPLATE_CONFIGURE_MAPPINGS",
				"PERM_INSTANCE_CREATE",
				"PERM_TENDER_PUBLISH",
			},
		),
	),
	"ROLE_PROCUREMENT_OFFICER": RoleMatrixEntry(
		role_name="Procurement Officer",
		description="Releases packages to Tender; creates and completes STD Instances; submit/publish.",
		grants=frozenset(
			{
				"PERM_PACKAGE_RELEASE_TO_TENDER",
				"PERM_PACKAGE_RELEASE_VIEW",
				"PERM_TENDER_CREATE",
				"PERM_TENDER_VIEW",
				"PERM_TENDER_EDIT",
				"PERM_TENDER_SUBMIT_APPROVAL",
				"PERM_TENDER_PUBLISH",
				"PERM_INSTANCE_VIEW",
				"PERM_INSTANCE_CREATE",
				"PERM_INSTANCE_EDIT_PARAMETERS",
				"PERM_INSTANCE_UPLOAD_ATTACHMENTS",
				"PERM_INSTANCE_CONFIGURE_BOQ",
				"PERM_INSTANCE_GENERATE_OUTPUTS",
				"PERM_INSTANCE_RUN_READINESS",
				"PERM_INSTANCE_MARK_READY",
				"PERM_PUBLICATION_READINESS_RUN",
				"PERM_TENDER_EVIDENCE_EXPORT",
			},
		),
		explicit_non_grants=frozenset(
			{
				"PERM_TEMPLATE_CONFIGURE_MAPPINGS",
				"PERM_TEMPLATE_EDIT_STRUCTURE",
				"PERM_TENDER_APPROVE",
			},
		),
	),
	"ROLE_PROCUREMENT_ASSISTANT": RoleMatrixEntry(
		role_name="Procurement Assistant",
		description="Delegated support for tender data entry and instance preparation.",
		grants=frozenset(
			{
				"PERM_TENDER_VIEW",
				"PERM_TENDER_EDIT",
				"PERM_INSTANCE_VIEW",
				"PERM_INSTANCE_EDIT_PARAMETERS",
				"PERM_INSTANCE_UPLOAD_ATTACHMENTS",
				"PERM_INSTANCE_CONFIGURE_BOQ",
				"PERM_INSTANCE_RUN_READINESS",
			},
		),
		explicit_non_grants=frozenset(
			{
				"PERM_PACKAGE_RELEASE_TO_TENDER",
				"PERM_INSTANCE_MARK_READY",
				"PERM_TENDER_SUBMIT_APPROVAL",
				"PERM_TENDER_APPROVE",
				"PERM_TENDER_PUBLISH",
			},
		),
	),
	"ROLE_APPROVING_AUTHORITY": RoleMatrixEntry(
		role_name="Approving Authority",
		description="Approves tender package for publication; publication readiness.",
		grants=frozenset(
			{
				"PERM_TENDER_VIEW",
				"PERM_INSTANCE_VIEW",
				"PERM_TENDER_APPROVE",
				"PERM_TENDER_REVIEW_RETURN",
				"PERM_PUBLICATION_READINESS_RUN",
			},
		),
		explicit_non_grants=frozenset(
			{
				"PERM_TENDER_EDIT",
				"PERM_INSTANCE_EDIT_PARAMETERS",
				"PERM_INSTANCE_CONFIGURE_BOQ",
				"PERM_TENDER_PUBLISH",
			},
		),
	),
	"ROLE_OPENING_COMMITTEE": RoleMatrixEntry(
		role_name="Opening Committee Member",
		description="Conducts bid opening using DOM.",
		grants=frozenset(
			{
				"PERM_TENDER_VIEW",
				"PERM_INSTANCE_VIEW",
				"PERM_OPENING_EXECUTE",
				"PERM_OPENING_RECORD",
			},
		),
		explicit_non_grants=frozenset(
			{
				"PERM_EVALUATION_EXECUTE",
				"PERM_EVALUATION_SUBMIT_REPORT",
				"PERM_INSTANCE_EDIT_PARAMETERS",
				"PERM_TENDER_EDIT",
			},
		),
	),
	"ROLE_EVALUATION_COMMITTEE": RoleMatrixEntry(
		role_name="Evaluation Committee Member",
		description="Conducts bid evaluation using DEM.",
		grants=frozenset(
			{
				"PERM_TENDER_VIEW",
				"PERM_INSTANCE_VIEW",
				"PERM_EVALUATION_EXECUTE",
				"PERM_EVALUATION_SUBMIT_REPORT",
			},
		),
		explicit_non_grants=frozenset(
			{
				"PERM_OPENING_EXECUTE",
				"PERM_OPENING_RECORD",
				"PERM_INSTANCE_EDIT_PARAMETERS",
				"PERM_TENDER_EDIT",
			},
		),
	),
	"ROLE_AUDITOR": RoleMatrixEntry(
		role_name="Auditor / Oversight User",
		description="Reviews audit trail and exports evidence packages.",
		grants=frozenset(
			{
				"PERM_TENDER_VIEW",
				"PERM_TEMPLATE_VIEW",
				"PERM_INSTANCE_VIEW",
				"PERM_INSTANCE_AUDIT_VIEW",
				"PERM_AUDIT_VIEW",
				"PERM_AUDIT_EXPORT",
				"PERM_TENDER_EVIDENCE_EXPORT",
			},
		),
		explicit_non_grants=frozenset(
			{
				"PERM_TENDER_EDIT",
				"PERM_TENDER_PUBLISH",
				"PERM_INSTANCE_EDIT_PARAMETERS",
			},
		),
	),
	"ROLE_SYSTEM_ADMIN": RoleMatrixEntry(
		role_name="System Administrator",
		description="Manages users, roles, platform configuration, and controlled administration.",
		grants=frozenset(
			{
				"PERM_ADMIN_MANAGE_USERS",
				"PERM_ADMIN_OVERRIDE",
				"PERM_AUDIT_VIEW",
			},
		),
		explicit_non_grants=frozenset(
			{
				"PERM_TENDER_APPROVE",
				"PERM_TENDER_PUBLISH",
				"PERM_PACKAGE_RELEASE_TO_TENDER",
			},
		),
	),
}


CANONICAL_ROLE_CODES: frozenset[str] = frozenset(ROLE_MATRIX)


def _validate_matrix(matrix: Mapping[str, RoleMatrixEntry]) -> None:
	for code, entry in matrix.items():
		if not code.startswith("ROLE_"):
			raise ValueError(f"Invalid role code: {code!r}")
		overlap = entry.grants & entry.explicit_non_grants
		if overlap:
			raise ValueError(f"Role {code}: grant overlaps explicit_non_grants: {overlap!r}")
		unknown_g = entry.grants - CANONICAL_PERMISSION_IDS
		if unknown_g:
			raise ValueError(f"Role {code}: unknown grant ids: {unknown_g!r}")
		unknown_n = entry.explicit_non_grants - CANONICAL_PERMISSION_IDS
		if unknown_n:
			raise ValueError(f"Role {code}: unknown non-grant ids: {unknown_n!r}")


_validate_matrix(ROLE_MATRIX)


def role_matrix_entry(role_code: str) -> RoleMatrixEntry | None:
	return ROLE_MATRIX.get((role_code or "").strip())
