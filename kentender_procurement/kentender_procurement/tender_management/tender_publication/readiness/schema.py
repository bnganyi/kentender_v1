# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0100 — Publication readiness finding schema (Cursor pack §5 / std engine §6.4).

Stable codes, severities, and default messages for ``PublicationReadinessService`` (PUB-0110).
"""

from __future__ import annotations

from typing import TypedDict

# Stable title for structural validation (tracker workstream-6 §4).
PUBLICATION_READINESS_FINDING_INVALID = "PUBLICATION_READINESS_FINDING_INVALID"

PUBLICATION_READINESS_BRIDGE_UNKNOWN = "PUBLICATION_READINESS_BRIDGE_UNKNOWN"

# ``PublicationReadinessService.assert_ready_for_*`` when status is not Ready.
PUBLICATION_READINESS_GATE_FAILED = "PUBLICATION_READINESS_GATE_FAILED"

PUBLICATION_READINESS_SEVERITIES: frozenset[str] = frozenset(
	{
		"Info",
		"Warning",
		"High",
		"Critical",
	},
)

PUBLICATION_CRITICAL_BLOCKER_CODES: frozenset[str] = frozenset(
	{
		"RELEASE_RECORD_MISSING",
		"STD_BINDING_MISSING",
		"STD_INSTANCE_MISSING",
		"STD_INSTANCE_NOT_READY",
		"TEMPLATE_LINEAGE_INVALID",
		"TDS_INCOMPLETE",
		"SCC_INCOMPLETE",
		"WORKS_REQUIREMENTS_INCOMPLETE",
		"DRAWINGS_INCOMPLETE",
		"BOQ_INCOMPLETE",
		"BUNDLE_NOT_CURRENT",
		"DSM_NOT_CURRENT",
		"DOM_NOT_CURRENT",
		"DEM_NOT_CURRENT",
		"DCM_NOT_CURRENT",
		"OUTPUT_TRACE_MISSING",
		"SNAPSHOT_CREATION_FAILED",
		"APPROVAL_REQUIRED",
		"EVIDENCE_PACKAGE_FAILED",
	},
)

PUBLICATION_WARNING_CODES: frozenset[str] = frozenset(
	{
		"AUDIT_NONCRITICAL_EVENT_MISSING",
		"SOURCE_HASH_MISSING",
		"OPTIONAL_ATTACHMENT_MISSING",
		"REVIEW_NOTE_UNRESOLVED",
	},
)

PUBLICATION_READINESS_KNOWN_CODES: frozenset[str] = (
	PUBLICATION_CRITICAL_BLOCKER_CODES | PUBLICATION_WARNING_CODES
)

PUBLICATION_READINESS_DEFAULT_AFFECTED_AREA: dict[str, str] = {
	"RELEASE_RECORD_MISSING": "Planning Release",
	"STD_BINDING_MISSING": "STD Binding",
	"STD_INSTANCE_MISSING": "STD Instance",
	"STD_INSTANCE_NOT_READY": "STD Instance",
	"TEMPLATE_LINEAGE_INVALID": "Template/Profile",
	"TDS_INCOMPLETE": "STD Completion",
	"SCC_INCOMPLETE": "STD Completion",
	"WORKS_REQUIREMENTS_INCOMPLETE": "STD Completion",
	"DRAWINGS_INCOMPLETE": "STD Completion",
	"BOQ_INCOMPLETE": "STD Completion",
	"BUNDLE_NOT_CURRENT": "Generated Outputs",
	"DSM_NOT_CURRENT": "Generated Outputs",
	"DOM_NOT_CURRENT": "Generated Outputs",
	"DEM_NOT_CURRENT": "Generated Outputs",
	"DCM_NOT_CURRENT": "Generated Outputs",
	"OUTPUT_TRACE_MISSING": "Output Traceability",
	"SNAPSHOT_CREATION_FAILED": "Snapshots",
	"APPROVAL_REQUIRED": "Approval",
	"EVIDENCE_PACKAGE_FAILED": "Evidence",
	"AUDIT_NONCRITICAL_EVENT_MISSING": "Audit Integrity",
	"SOURCE_HASH_MISSING": "Output Traceability",
	"OPTIONAL_ATTACHMENT_MISSING": "Attachments",
	"REVIEW_NOTE_UNRESOLVED": "Review Preconditions",
}

PUBLICATION_READINESS_DEFAULT_MESSAGES: dict[str, str] = {
	"RELEASE_RECORD_MISSING": "Planning-to-tender release record is missing or not released.",
	"STD_BINDING_MISSING": "Tender is not bound to a Tender STD Instance.",
	"STD_INSTANCE_MISSING": "Tender STD Instance row is missing.",
	"STD_INSTANCE_NOT_READY": "Tender STD Instance readiness is not Ready.",
	"TEMPLATE_LINEAGE_INVALID": "Template or applicability profile lineage is invalid.",
	"TDS_INCOMPLETE": "Required TDS parameter values are missing or invalid.",
	"SCC_INCOMPLETE": "Required SCC values are missing or invalid.",
	"WORKS_REQUIREMENTS_INCOMPLETE": "Required Works requirement content is incomplete.",
	"DRAWINGS_INCOMPLETE": "Required drawings are missing or invalid.",
	"BOQ_INCOMPLETE": "Required BOQ is missing or invalid.",
	"BUNDLE_NOT_CURRENT": "Bundle output is missing, stale, or not current.",
	"DSM_NOT_CURRENT": "DSM output is missing, stale, or not current.",
	"DOM_NOT_CURRENT": "DOM output is missing, stale, or not current.",
	"DEM_NOT_CURRENT": "DEM output is missing, stale, or not current.",
	"DCM_NOT_CURRENT": "DCM output is missing, stale, or not current.",
	"OUTPUT_TRACE_MISSING": "Required generated output traceability is missing.",
	"SNAPSHOT_CREATION_FAILED": "A required snapshot could not be created.",
	"APPROVAL_REQUIRED": "Approval for publication is not complete.",
	"EVIDENCE_PACKAGE_FAILED": "Evidence package cannot be assembled for this tender.",
	"AUDIT_NONCRITICAL_EVENT_MISSING": "A non-critical audit event expected by policy is missing.",
	"SOURCE_HASH_MISSING": "Source evidence hash is missing while a reference exists.",
	"OPTIONAL_ATTACHMENT_MISSING": "An optional attachment was not provided.",
	"REVIEW_NOTE_UNRESOLVED": "A non-blocking review note remains unresolved.",
}

PUBLICATION_READINESS_DEFAULT_RESOLUTIONS: dict[str, str] = {
	"RELEASE_RECORD_MISSING": "Create or complete the planning release record, then rerun readiness.",
	"STD_BINDING_MISSING": "Bind a valid STD template instance to the tender, then rerun readiness.",
	"STD_INSTANCE_MISSING": "Create the Tender STD Instance via binding, then rerun readiness.",
	"STD_INSTANCE_NOT_READY": "Complete STD instance inputs and generated outputs, then rerun readiness.",
	"TEMPLATE_LINEAGE_INVALID": "Correct template and applicability profile selection, then rerun readiness.",
	"TDS_INCOMPLETE": "Complete required TDS parameters, then rerun readiness.",
	"SCC_INCOMPLETE": "Complete required SCC fields, then rerun readiness.",
	"WORKS_REQUIREMENTS_INCOMPLETE": "Complete Works requirements, then rerun readiness.",
	"DRAWINGS_INCOMPLETE": "Complete the drawings register, then rerun readiness.",
	"BOQ_INCOMPLETE": "Complete or validate the BOQ, then rerun readiness.",
	"BUNDLE_NOT_CURRENT": "Regenerate Bundle and rerun readiness.",
	"DSM_NOT_CURRENT": "Regenerate DSM and rerun readiness.",
	"DOM_NOT_CURRENT": "Regenerate DOM and rerun readiness.",
	"DEM_NOT_CURRENT": "Regenerate DEM and rerun readiness.",
	"DCM_NOT_CURRENT": "Regenerate DCM and rerun readiness.",
	"OUTPUT_TRACE_MISSING": "Regenerate affected outputs so source traces are present, then rerun readiness.",
	"SNAPSHOT_CREATION_FAILED": "Resolve snapshot preconditions and retry snapshot creation.",
	"APPROVAL_REQUIRED": "Complete the approval workflow before publication.",
	"EVIDENCE_PACKAGE_FAILED": "Fix evidence assembly inputs (outputs, snapshots, audit trail), then rerun readiness.",
	"AUDIT_NONCRITICAL_EVENT_MISSING": "Record the missing audit event or adjust policy if not applicable.",
	"SOURCE_HASH_MISSING": "Regenerate outputs or refresh hashes so evidence links are complete.",
	"OPTIONAL_ATTACHMENT_MISSING": "Attach optional files or document waiver per procedure.",
	"REVIEW_NOTE_UNRESOLVED": "Resolve or formally close the review note.",
}


class PublicationReadinessFinding(TypedDict, total=False):
	"""Pack §5 shape for one readiness row (validated by ``validator``)."""

	code: str
	severity: str
	message: str
	affected_area: str
	affected_object_type: str | None
	affected_object_code: str | None
	resolution_action: str
	blocks_approval: bool
	blocks_publication: bool


def is_critical_code(code: str) -> bool:
	return (code or "").strip() in PUBLICATION_CRITICAL_BLOCKER_CODES


def is_warning_code(code: str) -> bool:
	return (code or "").strip() in PUBLICATION_WARNING_CODES


def default_blocks_for_code(code: str) -> tuple[bool, bool]:
	"""Return (blocks_approval, blocks_publication) for pack default policy."""
	if is_critical_code(code):
		return True, True
	if is_warning_code(code):
		return False, False
	return False, False
