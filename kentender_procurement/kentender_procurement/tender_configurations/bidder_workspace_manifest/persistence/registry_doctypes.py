# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Canonical BWMF DocType names (Phase 2 / 2A)."""

from __future__ import annotations

DT_COMPILE_REQUEST = "BWMF Compile Request"
DT_COMPILE_INPUT_BINDING = "BWMF Compile Input Binding"
DT_COMPILE_RUN = "BWMF Compile Run"
DT_COMPILE_STAGE_TRACE = "BWMF Compile Stage Trace"
DT_COMPILE_ARTIFACT = "BWMF Compile Artifact"
DT_MANIFEST_VERSION = "BWMF Manifest Version"
DT_MANIFEST_RESOURCE = "BWMF Manifest Resource"
DT_CONTENT_OBJECT = "BWMF Content Object"
DT_ARTIFACT_RESOURCE_BINDING = "BWMF Artifact Resource Binding"
DT_MATERIALIZATION_REPORT = "BWMF Materialization Report"
DT_COMPILER_DIAGNOSTIC = "BWMF Compiler Diagnostic"
DT_VALIDATION_REPORT = "BWMF Validation Report"
DT_MANIFEST_APPROVAL = "BWMF Manifest Approval"
DT_MANIFEST_PUBLICATION = "BWMF Manifest Publication"
DT_REVIEW_PACKAGE = "BWMF Review Package"
DT_APPROVAL_DECISION = "BWMF Approval Decision"
DT_PUBLICATION_REQUEST = "BWMF Publication Request"
DT_MANIFEST_RESOURCE_BINDING = "BWMF Manifest Resource Binding"
DT_LIFECYCLE_EVENT = "BWMF Lifecycle Event"
DT_TENDER_PUBLICATION_STATE = "BWMF Tender Publication State"
DT_ADDENDUM_IMPACT_PLAN = "BWMF Addendum Impact Plan"
DT_WORKSPACE = "BWMF Workspace"
DT_WORKSPACE_BINDING = "BWMF Workspace Manifest Binding"
DT_RESPONSE_VERSION = "BWMF Response Version"
DT_EVIDENCE_ITEM = "BWMF Evidence Item"
DT_EVIDENCE_VERSION = "BWMF Evidence Version"
DT_EVIDENCE_LINK = "BWMF Evidence Link"
DT_CONFIRMATION = "BWMF Confirmation"
DT_AUTHORITY_REFERENCE = "BWMF Authority Reference"
DT_DEPENDENCY_SNAPSHOT = "BWMF Dependency Snapshot"
DT_INVALIDATION_EVENT = "BWMF Invalidation Event"
DT_VALIDATION_SNAPSHOT = "BWMF Validation Snapshot"
DT_VALIDATION_FINDING = "BWMF Validation Finding"
DT_SUBMISSION = "BWMF Submission"
DT_SUBMISSION_RECEIPT = "BWMF Submission Receipt"
DT_AUDIT_EVENT = "BWMF Audit Event"
DT_IDEMPOTENCY_RECORD = "BWMF Idempotency Record"

# Required canonical persistence concepts for coverage ledger machine-check
REQUIRED_PERSISTENCE_CONCEPTS: frozenset[str] = frozenset(
	{
		"compile_request",
		"compile_input_binding",
		"compile_run",
		"compile_stage_trace",
		"compile_artifact",
		"manifest_version",
		"manifest_resource",
		"content_object",
		"artifact_resource_binding",
		"materialization_report",
		"compiler_diagnostic",
		"validation_report",
		"manifest_approval",
		"manifest_publication",
		"review_package",
		"approval_decision",
		"publication_request",
		"manifest_resource_binding",
		"lifecycle_event",
		"tender_publication_state",
		"addendum_impact_plan",
		"workspace",
		"workspace_manifest_binding",
		"response_version",
		"evidence_item",
		"evidence_version",
		"evidence_link",
		"confirmation",
		"authority_reference",
		"dependency_snapshot",
		"invalidation_event",
		"validation_snapshot",
		"validation_finding",
		"submission",
		"submission_receipt",
		"audit_event",
		"idempotency_record",
	}
)

CLEAR_ORDER: tuple[str, ...] = (
	DT_AUDIT_EVENT,
	DT_LIFECYCLE_EVENT,
	DT_IDEMPOTENCY_RECORD,
	DT_SUBMISSION_RECEIPT,
	DT_SUBMISSION,
	DT_VALIDATION_SNAPSHOT,
	DT_INVALIDATION_EVENT,
	DT_DEPENDENCY_SNAPSHOT,
	DT_CONFIRMATION,
	DT_EVIDENCE_LINK,
	DT_EVIDENCE_VERSION,
	DT_EVIDENCE_ITEM,
	DT_RESPONSE_VERSION,
	DT_WORKSPACE_BINDING,
	DT_WORKSPACE,
	DT_ADDENDUM_IMPACT_PLAN,
	DT_PUBLICATION_REQUEST,
	DT_MANIFEST_PUBLICATION,
	DT_MANIFEST_RESOURCE_BINDING,
	DT_TENDER_PUBLICATION_STATE,
	DT_APPROVAL_DECISION,
	DT_REVIEW_PACKAGE,
	DT_MANIFEST_APPROVAL,
	DT_COMPILER_DIAGNOSTIC,
	DT_VALIDATION_REPORT,
	DT_MATERIALIZATION_REPORT,
	DT_ARTIFACT_RESOURCE_BINDING,
	DT_MANIFEST_RESOURCE,
	DT_CONTENT_OBJECT,
	DT_COMPILE_ARTIFACT,
	DT_COMPILE_RUN,
	DT_MANIFEST_VERSION,
	DT_COMPILE_REQUEST,
	DT_AUTHORITY_REFERENCE,
)
