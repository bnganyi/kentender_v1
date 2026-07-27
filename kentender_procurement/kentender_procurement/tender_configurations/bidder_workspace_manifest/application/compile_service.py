# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Application service: compile run lifecycle + immutable Compile Artifact persistence.

Never mutates published tender documents, workspace status, or prior compile artifacts.
Never publishes. Never persists unmaterialized candidates as BWMF Manifest Resource.
Never fabricates payload digests for failed compiles.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.pipeline import run as pure_run
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.types import (
	CompileRequestDTO,
	CompileResult,
	SourceSet,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import services as bwmf
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.audit import (
	append_audit_event,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_COMPILER_DIAGNOSTIC,
	DT_COMPILE_RUN,
)


PREVIEW_DIGEST_LABEL = "unmaterialized_preview_payload"


def _severity_for_doctype(severity: str) -> str:
	if severity == "information":
		return "info"
	if severity in {"error", "warning", "info"}:
		return severity
	return "info"


def execute_compile(
	*,
	compile_request_id: str,
	idempotency_key: str,
	run_id: str,
	run_idempotency_key: str,
	request: CompileRequestDTO,
	sources: SourceSet,
	organization: str = "ORG-UNSPECIFIED",
	bindings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
	"""Create/accept compile request, run Queued→Running→terminal, persist Compile Artifact."""
	req_name = bwmf.create_compile_request(
		compile_request_id=compile_request_id,
		idempotency_key=idempotency_key,
		compile_mode=request.compile_mode,
		target_manifest_id=request.target_manifest_id,
		target_manifest_version=request.target_manifest_version,
		published_tender_ref=request.published_tender_ref,
		published_tender_version=request.published_tender_version,
		requested_by=request.generated_by,
		organization=organization,
		bindings=bindings or [],
	)
	run_name = bwmf.create_compile_run(
		run_id=run_id,
		idempotency_key=run_idempotency_key,
		compile_request=req_name,
		organization=organization,
	)
	bwmf.transition_compile_run(run_name=run_name, new_state="Running", organization=organization)

	request.compiler_run_id = run_id
	result: CompileResult = pure_run(request, sources)

	for tr in result.traces:
		bwmf.append_compile_stage_trace(
			run_name=run_name,
			stage=tr["stage"],
			state=tr["state"],
			detail={"detail": tr.get("detail") or ""},
			organization=organization,
		)

	artifact_name = ""
	digest_label = result.digest_label or PREVIEW_DIGEST_LABEL
	if result.ok:
		artifact_name = bwmf.create_compile_artifact(
			artifact_id=f"ART-{run_id}",
			compile_run=run_name,
			compile_mode=request.compile_mode,
			target_manifest_id=request.target_manifest_id,
			target_manifest_version=request.target_manifest_version,
			envelope=result.envelope,
			payload=result.payload,
			payload_digest=result.payload_digest,
			projection_digest=result.projection_digest or "",
			diagnostic_digest=result.diagnostic_digest or "",
			resource_candidates=result.logical_resources,
			addendum_impact=result.addendum_impact,
			digest_label=digest_label,
			organization=organization,
		)
	else:
		# Failed-result artifact: diagnostics only — never synthetic payload_digest.
		digest_label = "failed_result"
		artifact_name = bwmf.create_compile_artifact(
			artifact_id=f"ART-{run_id}",
			compile_run=run_name,
			compile_mode=request.compile_mode,
			target_manifest_id=request.target_manifest_id,
			target_manifest_version=request.target_manifest_version,
			envelope=result.envelope
			or {
				"failed": True,
				"fail_code": result.fail_code,
				"artifact_kind": "failed_result",
				"integrity": {
					"final_runtime_manifest": False,
					"payload_digest": None,
					"diagnostic_digest": result.diagnostic_digest or "",
				},
				"eligible_for_approval": False,
				"eligible_for_publication": False,
			},
			payload=None,
			payload_digest=None,
			projection_digest="",
			diagnostic_digest=result.diagnostic_digest or "",
			resource_candidates=[],
			addendum_impact=result.addendum_impact,
			digest_label=digest_label,
			artifact_kind="failed_result",
			organization=organization,
		)
	# Phase 3 never creates Manifest Versions (Phase 5 atomic publication only).
	frappe.db.set_value(DT_COMPILE_RUN, run_name, "output_manifest", "")

	report_name = bwmf.create_validation_report(
		report_id=f"VAL-{run_id}",
		compile_run=run_name,
		readiness="fail",
	)
	_persist_diagnostics(run_name, report_name, result.diagnostics)

	terminal = "Succeeded" if result.ok else "Failed"
	bwmf.transition_compile_run(run_name=run_name, new_state=terminal, organization=organization)
	append_audit_event(
		event_type="compile.completed",
		organization=organization,
		compile_run_ref=run_name,
		metadata={
			"ok": result.ok,
			"compile_artifact": artifact_name,
			"artifact_kind": "failed_result" if not result.ok else request.compile_mode,
			"payload_digest": result.payload_digest or None,
			"digest_label": digest_label,
			"projection_digest": result.projection_digest or None,
			"diagnostic_digest": result.diagnostic_digest,
			"publication_ready": False,
			"canonical_resources_created": 0,
			"manifest_version_created": False,
		},
	)
	return {
		"ok": result.ok,
		"compile_request": req_name,
		"compile_run": run_name,
		"compile_artifact": artifact_name,
		"manifest_version": "",  # Phase 3/4: never; Phase 5 publication only
		"validation_report": report_name,
		"payload_digest": result.payload_digest or None,
		"digest_label": digest_label,
		"projection_digest": result.projection_digest or None,
		"diagnostic_digest": result.diagnostic_digest,
		"publication_ready": False,
		"fail_code": result.fail_code,
		"canonical_resources_created": 0,
		"artifact_kind": "failed_result" if not result.ok else None,
		"result": result,
	}


def assert_preview_artifact_immutable(artifact_name: str) -> None:
	"""Phase 4 must not mutate preview artifacts — exercised by tests attempting save."""
	doc = frappe.get_doc("BWMF Compile Artifact", artifact_name)
	doc.payload_json = '{"tampered": true}'
	doc.save(ignore_permissions=True)


def assert_failed_result_not_submittable(artifact_name: str) -> None:
	"""Failed-result artifacts cannot enter approval/publication."""
	bwmf.assert_compile_artifact_eligible_for_publication(artifact_name)


def _persist_diagnostics(run_name: str, report_name: str, diagnostics: list[dict[str, Any]]) -> None:
	import hashlib

	for d in diagnostics:
		diag_id = d.get("diagnostic_id") or frappe.generate_hash(length=10)
		if frappe.db.exists(DT_COMPILER_DIAGNOSTIC, diag_id):
			diag_id = f"{diag_id}-{frappe.generate_hash(length=6)}"
		fingerprint = hashlib.sha256(
			f"{d.get('code')}|{d.get('severity')}|{d.get('message')}".encode()
		).hexdigest()[:16]
		frappe.get_doc(
			{
				"doctype": DT_COMPILER_DIAGNOSTIC,
				"diagnostic_id": diag_id,
				"compile_run": run_name,
				"validation_report": report_name,
				"code": d.get("code") or "UNKNOWN",
				"severity": _severity_for_doctype(d.get("severity") or "info"),
				"stage": "",
				"message": d.get("message") or "",
				"fingerprint": fingerprint,
			}
		).insert(ignore_permissions=True)
