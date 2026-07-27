# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BWMF persistence application services (Phase 2A — no compiler / no UI)."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.audit import (
	append_audit_event,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.concurrency import (
	assert_expected_response_version,
	next_response_version,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.decimal_money import (
	decimal_to_storage_str,
	exact_decimal_roundtrip,
	serialize_manifest_money,
	sum_money,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.idempotency import (
	canonical_request_fingerprint,
	resolve_idempotency,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.isolation import (
	assert_manifest_in_org_scope,
	assert_org_party_match,
	assert_row_org_party,
	assert_same_workspace_manifest_binding,
	assert_workspace_tenant,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_ARTIFACT_RESOURCE_BINDING,
	DT_AUTHORITY_REFERENCE,
	DT_COMPILE_ARTIFACT,
	DT_COMPILE_REQUEST,
	DT_COMPILE_RUN,
	DT_CONFIRMATION,
	DT_EVIDENCE_ITEM,
	DT_EVIDENCE_LINK,
	DT_EVIDENCE_VERSION,
	DT_MANIFEST_APPROVAL,
	DT_MANIFEST_PUBLICATION,
	DT_MANIFEST_RESOURCE,
	DT_MANIFEST_VERSION,
	DT_MATERIALIZATION_REPORT,
	DT_RESPONSE_VERSION,
	DT_SUBMISSION,
	DT_SUBMISSION_RECEIPT,
	DT_VALIDATION_REPORT,
	DT_WORKSPACE,
	DT_WORKSPACE_BINDING,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.snapshot import (
	SNAPSHOT_SCHEMA_VERSION,
	build_submission_snapshot,
	snapshot_to_json,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.workspace_lifecycle import (
	PREPARATORY_WORKSPACE_STATUSES,
	WS_CLOSED,
	WS_NOT_STARTED,
	WS_READY_TO_SUBMIT,
	WS_SUBMITTED,
	WS_WITHDRAWN,
	WorkspaceReadinessSignals,
	collect_workspace_readiness_signals,
	derive_workspace_status,
)

OP_COMPILE_REQUEST = "compile_request"
OP_COMPILE_RUN = "compile_run"
OP_SEAL_SUBMISSION = "seal_submission"


def _hash_digest(label: str) -> str:
	import hashlib

	return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def create_compile_request(
	*,
	compile_request_id: str,
	idempotency_key: str,
	compile_mode: str = "preview",
	target_manifest_id: str,
	target_manifest_version: int = 1,
	published_tender_ref: str,
	published_tender_version: int = 1,
	requested_by: str = "system:phase2",
	organization: str = "",
	bindings: list[dict[str, Any]] | None = None,
) -> str:
	organization = organization or "ORG-UNSPECIFIED"
	bindings = bindings or []
	fingerprint_payload = {
		"compile_request_id": compile_request_id,
		"compile_mode": compile_mode,
		"target_manifest_id": target_manifest_id,
		"target_manifest_version": target_manifest_version,
		"published_tender_ref": published_tender_ref,
		"published_tender_version": published_tender_version,
		"bindings": bindings,
	}
	fp = canonical_request_fingerprint(fingerprint_payload)

	def _create() -> str:
		if frappe.db.exists(DT_COMPILE_REQUEST, {"compile_request_id": compile_request_id}):
			frappe.throw(_("Duplicate compile_request_id."), title="BWMF_DUPLICATE_STABLE_ID")
		doc = frappe.get_doc(
			{
				"doctype": DT_COMPILE_REQUEST,
				"compile_request_id": compile_request_id,
				"idempotency_key": idempotency_key,
				"compile_mode": compile_mode,
				"status": "Accepted",
				"target_manifest_id": target_manifest_id,
				"target_manifest_version": target_manifest_version,
				"published_tender_ref": published_tender_ref,
				"published_tender_version": published_tender_version,
				"requested_by": requested_by,
				"requested_at": now_datetime(),
				"expected_input_digests_json": json.dumps({}),
				"input_bindings": bindings,
				"organization": organization,
				"operation": OP_COMPILE_REQUEST,
				"request_fingerprint": fp,
			}
		)
		doc.insert(ignore_permissions=True)
		append_audit_event(
			event_type="compile_request.created",
			organization=organization,
			actor=requested_by,
			correlation_ref=compile_request_id,
			idempotency_ref=idempotency_key,
			metadata={"compile_request": doc.name},
		)
		return doc.name

	return resolve_idempotency(
		organization=organization,
		operation=OP_COMPILE_REQUEST,
		idempotency_key=idempotency_key,
		request_fingerprint=fp,
		result_doctype=DT_COMPILE_REQUEST,
		create_result=_create,
	)


def create_compile_run(
	*,
	run_id: str,
	idempotency_key: str,
	compile_request: str,
	organization: str = "",
) -> str:
	"""Create a compile run in Queued state. Transitions are controlled separately."""
	if not frappe.db.exists(DT_COMPILE_REQUEST, compile_request):
		frappe.throw(_("Missing compile request."), title="BWMF_REF_MISSING")
	req = frappe.db.get_value(
		DT_COMPILE_REQUEST,
		compile_request,
		["organization", "compile_request_id", "status"],
		as_dict=True,
	)
	organization = organization or req.organization or "ORG-UNSPECIFIED"
	fp = canonical_request_fingerprint({"run_id": run_id, "compile_request": compile_request})

	def _create() -> str:
		doc = frappe.get_doc(
			{
				"doctype": DT_COMPILE_RUN,
				"run_id": run_id,
				"idempotency_key": idempotency_key,
				"compile_request": compile_request,
				"compiler_version": "1.0.0",
				"state": "Queued",
				"stage_trace": [],
			}
		)
		doc.insert(ignore_permissions=True)
		append_audit_event(
			event_type="compile_run.queued",
			organization=organization,
			compile_run_ref=doc.name,
			correlation_ref=run_id,
			idempotency_ref=idempotency_key,
		)
		return doc.name

	return resolve_idempotency(
		organization=organization,
		operation=OP_COMPILE_RUN,
		idempotency_key=idempotency_key,
		request_fingerprint=fp,
		result_doctype=DT_COMPILE_RUN,
		create_result=_create,
	)


def transition_compile_run(*, run_name: str, new_state: str, organization: str = "ORG-UNSPECIFIED") -> None:
	doc = frappe.get_doc(DT_COMPILE_RUN, run_name)
	doc.state = new_state
	if new_state == "Running" and not doc.started_at:
		doc.started_at = now_datetime()
	if new_state in {"Succeeded", "Failed", "Cancelled"}:
		doc.ended_at = now_datetime()
	doc.save(ignore_permissions=True)
	append_audit_event(
		event_type=f"compile_run.{new_state.lower()}",
		organization=organization,
		compile_run_ref=run_name,
		metadata={"state": new_state},
	)


def append_compile_stage_trace(
	*,
	run_name: str,
	stage: str,
	state: str,
	detail: dict[str, Any] | None = None,
	organization: str = "ORG-UNSPECIFIED",
) -> None:
	doc = frappe.get_doc(DT_COMPILE_RUN, run_name)
	doc.append(
		"stage_trace",
		{
			"stage": stage,
			"state": state,
			"started_at": now_datetime(),
			"ended_at": now_datetime(),
			"detail_json": json.dumps(detail or {}),
		},
	)
	doc.save(ignore_permissions=True)
	append_audit_event(
		event_type="compile_run.stage_trace.appended",
		organization=organization,
		compile_run_ref=run_name,
		metadata={"stage": stage, "state": state},
	)


def complete_compile_run_success(
	*,
	run_name: str,
	organization: str = "ORG-UNSPECIFIED",
) -> None:
	"""Convenience for fixtures: Queued -> Running (+trace) -> Succeeded."""
	transition_compile_run(run_name=run_name, new_state="Running", organization=organization)
	append_compile_stage_trace(
		run_name=run_name,
		stage="C00",
		state="succeeded",
		organization=organization,
	)
	transition_compile_run(run_name=run_name, new_state="Succeeded", organization=organization)


_SUBMISSION_POLICY_REQUIRED: frozenset[str] = frozenset(
	{
		"deadline_at",
		"timezone",
		"server_time_authoritative",
		"late_submission_behavior",
		"withdrawal_mode",
		"replacement_mode",
		"submission_authority_policy_ref",
		"reauthentication_policy_ref",
		"seal_policy_ref",
		"receipt_policy_ref",
		"concurrent_submission_policy",
		"idempotency_policy",
	}
)


def assert_complete_submission_policy(policy: Any) -> dict[str, Any]:
	"""Fail closed when submission_policy is missing or incomplete. No runtime defaults."""
	if not isinstance(policy, dict) or not policy:
		frappe.throw(_("submission_policy is required and must be complete."), title="BWMF_SUBMISSION_POLICY")
	missing = sorted(_SUBMISSION_POLICY_REQUIRED - set(policy.keys()))
	if missing:
		frappe.throw(
			_("submission_policy missing required fields: {0}").format(", ".join(missing)),
			title="BWMF_SUBMISSION_POLICY",
		)
	return policy


def create_compile_artifact(
	*,
	artifact_id: str,
	compile_run: str,
	compile_mode: str,
	target_manifest_id: str,
	target_manifest_version: int,
	envelope: dict[str, Any],
	payload: dict[str, Any] | None = None,
	payload_digest: str | None = None,
	projection_digest: str = "",
	diagnostic_digest: str = "",
	resource_candidates: list[dict[str, Any]] | None = None,
	addendum_impact: dict[str, Any] | None = None,
	digest_label: str = "unmaterialized_preview_payload",
	artifact_kind: str | None = None,
	organization: str = "ORG-UNSPECIFIED",
) -> str:
	"""Persist an immutable run-bound compile artifact (preview/recompile safe).

	failed_result artifacts must omit payload and payload_digest (never synthetic).
	"""
	if frappe.db.exists(DT_COMPILE_ARTIFACT, {"artifact_id": artifact_id}):
		frappe.throw(_("Duplicate compile artifact_id."), title="BWMF_DUPLICATE_STABLE_ID")
	kind_map = {
		"preview": "preview",
		"publication": "publication_candidate",
		"addendum_preview": "addendum_preview",
		"addendum_publication": "addendum_publication",
	}
	kind = artifact_kind or kind_map.get(compile_mode, "preview")
	is_failed = kind == "failed_result"
	if is_failed:
		digest_label = "failed_result"
		payload_digest = None
		payload = None
		resource_candidates = []
	doc = frappe.get_doc(
		{
			"doctype": DT_COMPILE_ARTIFACT,
			"artifact_id": artifact_id,
			"compile_run": compile_run,
			"compile_mode": compile_mode,
			"target_manifest_id": target_manifest_id,
			"target_manifest_version": int(target_manifest_version),
			"artifact_kind": kind,
			"digest_label": digest_label,
			"payload_digest": "" if payload_digest is None else payload_digest,
			"projection_digest": projection_digest or "",
			"diagnostic_digest": diagnostic_digest or "",
			"immutable": 1,
			"envelope_json": json.dumps(envelope or {}),
			"payload_json": "" if payload is None else json.dumps(payload),
			"resource_candidates_json": json.dumps(resource_candidates or []),
			"addendum_impact_json": json.dumps(addendum_impact or {}),
			"organization": organization,
		}
	)
	doc.insert(ignore_permissions=True)
	append_audit_event(
		event_type="compile_artifact.created",
		organization=organization,
		compile_run_ref=compile_run,
		metadata={
			"artifact_id": artifact_id,
			"artifact_kind": kind,
			"digest_label": digest_label,
			"payload_digest": payload_digest,
			"target_manifest_id": target_manifest_id,
			"target_manifest_version": target_manifest_version,
		},
	)
	return doc.name


def create_manifest_resource(
	*,
	resource_id: str,
	resource_type: str,
	schema_ref: str,
	schema_version: str,
	item_count: int,
	ordering_contract: list[str],
	resource_digest: str,
	storage_mode: str,
	content_ref: str = "",
	physical_object_digest: str = "",
	source_refs: list[Any] | None = None,
	chunks: list[dict[str, Any]] | None = None,
	inline_items: list[dict[str, Any]] | None = None,
	document_content_digest: str = "",
	organization: str = "ORG-UNSPECIFIED",
) -> str:
	"""Create an immutable Manifest Resource (independent of Manifest Version).

	Uniqueness is composite (resource_id, resource_digest, schema_ref, schema_version).
	Identical content bytes may be shared across different resource identities.
	"""
	from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.keys import (
		resource_version_key,
	)

	version_key = resource_version_key(resource_id, resource_digest, schema_ref, schema_version)
	existing_name = frappe.db.get_value(
		DT_MANIFEST_RESOURCE, {"resource_version_key": version_key}, "name"
	)
	if existing_name:
		existing = frappe.get_doc(DT_MANIFEST_RESOURCE, existing_name)
		if (existing.content_ref or "") != (content_ref or ""):
			frappe.throw(
				_("Resource version reused with different content_ref."),
				title="BWMF_RESOURCE_CONFLICT",
			)
		return existing.name
	if storage_mode == "content_addressed" and not content_ref:
		frappe.throw(_("content_addressed requires content_ref."), title="BWMF_RESOURCE_STORAGE")
	if storage_mode == "inline" and content_ref:
		frappe.throw(_("inline storage cannot set content_ref."), title="BWMF_RESOURCE_STORAGE")
	if storage_mode == "content_addressed" and inline_items:
		frappe.throw(_("content_addressed cannot set inline_items."), title="BWMF_RESOURCE_STORAGE")
	doc = frappe.get_doc(
		{
			"doctype": DT_MANIFEST_RESOURCE,
			"resource_version_key": version_key,
			"resource_id": resource_id,
			"resource_type": resource_type,
			"schema_ref": schema_ref,
			"schema_version": schema_version,
			"item_count": int(item_count),
			"ordering_contract_json": json.dumps(ordering_contract or []),
			"resource_digest": resource_digest,
			"storage_mode": storage_mode,
			"content_ref": content_ref or "",
			"physical_object_digest": physical_object_digest or "",
			"chunks_json": json.dumps(chunks or []),
			"source_refs_json": json.dumps(source_refs or []),
			"document_content_digest": document_content_digest or resource_digest,
			"immutable": 1,
			"content_json": json.dumps(inline_items) if inline_items is not None else "",
			"organization": organization,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def create_artifact_resource_binding(
	*,
	binding_id: str,
	compile_artifact: str,
	resource_id: str,
	resource_digest: str,
	content_ref: str,
	resource_docname: str = "",
	organization: str = "ORG-UNSPECIFIED",
) -> str:
	"""Bind a finalized Compile Artifact to an exact Manifest Resource version.

	Unique on (compile_artifact, resource_id).
	"""
	from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.keys import (
		artifact_resource_key,
	)

	ark = artifact_resource_key(compile_artifact, resource_id)
	existing_name = frappe.db.get_value(
		DT_ARTIFACT_RESOURCE_BINDING, {"artifact_resource_key": ark}, "name"
	)
	if existing_name:
		return existing_name
	if frappe.db.exists(DT_ARTIFACT_RESOURCE_BINDING, {"binding_id": binding_id}):
		return frappe.db.get_value(DT_ARTIFACT_RESOURCE_BINDING, {"binding_id": binding_id}, "name")
	doc = frappe.get_doc(
		{
			"doctype": DT_ARTIFACT_RESOURCE_BINDING,
			"binding_id": binding_id,
			"artifact_resource_key": ark,
			"compile_artifact": compile_artifact,
			"resource_id": resource_id,
			"resource_digest": resource_digest,
			"resource_docname": resource_docname or "",
			"content_ref": content_ref,
			"immutable": 1,
			"organization": organization,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def create_materialization_report(
	*,
	report_id: str,
	source_artifact: str,
	state: str,
	report: dict[str, Any],
	descriptor_set_digest: str = "",
	finalized_artifact: str = "",
	organization: str = "ORG-UNSPECIFIED",
) -> str:
	if frappe.db.exists(DT_MATERIALIZATION_REPORT, {"report_id": report_id}):
		return frappe.db.get_value(DT_MATERIALIZATION_REPORT, {"report_id": report_id}, "name")
	doc = frappe.get_doc(
		{
			"doctype": DT_MATERIALIZATION_REPORT,
			"report_id": report_id,
			"source_artifact": source_artifact,
			"finalized_artifact": finalized_artifact or "",
			"state": state,
			"descriptor_set_digest": descriptor_set_digest or "",
			"report_json": json.dumps(report),
			"immutable": 1,
			"organization": organization,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def assert_compile_artifact_eligible_for_publication(artifact_name: str) -> None:
	"""Fail closed: failed_result / empty-digest artifacts cannot enter approval or publication."""
	doc = frappe.get_doc(DT_COMPILE_ARTIFACT, artifact_name)
	if doc.artifact_kind == "failed_result":
		frappe.throw(
			_("Failed compile artifacts cannot be submitted for approval or publication."),
			title="BWMF_FAILED_RESULT",
		)
	if not (doc.payload_digest or "").strip() or not (doc.payload_json or "").strip():
		frappe.throw(
			_("Compile artifact lacks a payload digest and cannot be published."),
			title="BWMF_FAILED_RESULT",
		)
	envelope = json.loads(doc.envelope_json or "{}")
	if envelope.get("failed") or envelope.get("artifact_kind") == "failed_result":
		frappe.throw(
			_("Compile artifact is not eligible for publication."),
			title="BWMF_FAILED_RESULT",
		)


def create_manifest_version(
	*,
	manifest_id: str,
	manifest_version: int,
	lifecycle_state: str = "Draft",
	payload: dict[str, Any] | None = None,
	published_tender_ref: str = "",
	published_tender_version: int = 1,
	organization: str = "ORG-UNSPECIFIED",
) -> str:
	"""Create a published-track Manifest Version.

	Uniqueness of (manifest_id, manifest_version) applies to this DocType only.
	Preview recompiles must use BWMF Compile Artifact, not this helper.
	"""
	if frappe.db.exists(
		DT_MANIFEST_VERSION, {"manifest_id": manifest_id, "manifest_version": manifest_version}
	):
		frappe.throw(_("Duplicate manifest_id/version."), title="BWMF_DUPLICATE_STABLE_ID")

	if not isinstance(payload, dict) or not payload:
		frappe.throw(
			_("create_manifest_version requires an explicit payload including submission_policy."),
			title="BWMF_SUBMISSION_POLICY",
		)
	assert_complete_submission_policy(payload.get("submission_policy"))
	payload = serialize_manifest_money(payload)
	payload_digest = _hash_digest(f"{manifest_id}:{manifest_version}:{json.dumps(payload, sort_keys=True)}")
	envelope = {
		"manifest_schema_version": "1.0.0",
		"control": {
			"artifact_mode": "preview",
			"generated_at": frappe.utils.now_datetime().isoformat(),
			"generated_by": "bwmf.persistence.create_manifest_version",
			"compiler_run_id": "persistence-helper",
		},
		"payload": payload,
		"integrity": {"payload_digest": payload_digest},
	}
	doc = frappe.get_doc(
		{
			"doctype": DT_MANIFEST_VERSION,
			"manifest_id": manifest_id,
			"manifest_version": manifest_version,
			"lifecycle_state": lifecycle_state,
			"manifest_schema_version": "1.0.0",
			"payload_digest": payload_digest,
			"envelope_json": json.dumps(envelope),
			"payload_json": json.dumps(payload),
			"published_tender_ref": published_tender_ref,
			"published_tender_version": published_tender_version,
		}
	)
	doc.insert(ignore_permissions=True)
	append_audit_event(
		event_type="manifest.created",
		organization=organization,
		manifest_doc=doc.name,
		metadata={"manifest_id": manifest_id, "manifest_version": manifest_version},
	)
	return doc.name


def publish_manifest_version(manifest_name: str, *, organization: str = "ORG-UNSPECIFIED") -> None:
	"""Draft -> Published. Does not rewrite payload, bindings, resources, or digest."""
	doc = frappe.get_doc(DT_MANIFEST_VERSION, manifest_name)
	if doc.lifecycle_state == "Published":
		return
	prior_digest = doc.payload_digest
	prior_payload = doc.payload_json
	doc.lifecycle_state = "Published"
	doc.save(ignore_permissions=True)
	# Guard against accidental rewrite during publish
	after = frappe.db.get_value(
		DT_MANIFEST_VERSION, manifest_name, ["payload_digest", "payload_json"], as_dict=True
	)
	if after.payload_digest != prior_digest or after.payload_json != prior_payload:
		frappe.throw(_("Publication must not rewrite manifest payload."), title="BWMF_MANIFEST_CONTENT_IMMUTABLE")
	append_audit_event(
		event_type="manifest.published",
		organization=organization,
		manifest_doc=manifest_name,
		metadata={"payload_digest": prior_digest},
	)


def supersede_manifest_version(manifest_name: str, *, organization: str = "ORG-UNSPECIFIED") -> None:
	"""Published -> Superseded. Historical payload and digest remain unchanged."""
	doc = frappe.get_doc(DT_MANIFEST_VERSION, manifest_name)
	prior_digest = doc.payload_digest
	prior_payload = doc.payload_json
	doc.lifecycle_state = "Superseded"
	doc.save(ignore_permissions=True)
	after = frappe.db.get_value(
		DT_MANIFEST_VERSION, manifest_name, ["payload_digest", "payload_json", "lifecycle_state"], as_dict=True
	)
	if after.payload_digest != prior_digest or after.payload_json != prior_payload:
		frappe.throw(_("Supersession must not alter historical payload."), title="BWMF_MANIFEST_CONTENT_IMMUTABLE")
	append_audit_event(
		event_type="manifest.superseded",
		organization=organization,
		manifest_doc=manifest_name,
		metadata={"payload_digest": prior_digest, "lifecycle_state": after.lifecycle_state},
	)


def cancel_manifest_version(manifest_name: str, *, organization: str = "ORG-UNSPECIFIED") -> None:
	"""Published -> Cancelled. Historical payload and digest remain unchanged."""
	doc = frappe.get_doc(DT_MANIFEST_VERSION, manifest_name)
	prior_digest = doc.payload_digest
	prior_payload = doc.payload_json
	doc.lifecycle_state = "Cancelled"
	doc.save(ignore_permissions=True)
	after = frappe.db.get_value(
		DT_MANIFEST_VERSION, manifest_name, ["payload_digest", "payload_json", "lifecycle_state"], as_dict=True
	)
	if after.payload_digest != prior_digest or after.payload_json != prior_payload:
		frappe.throw(_("Cancellation must not alter historical payload."), title="BWMF_MANIFEST_CONTENT_IMMUTABLE")
	append_audit_event(
		event_type="manifest.cancelled",
		organization=organization,
		manifest_doc=manifest_name,
		metadata={"payload_digest": prior_digest, "lifecycle_state": after.lifecycle_state},
	)


def manifest_allows_withdrawal(manifest_name: str) -> bool:
	"""True when payload.submission_policy.withdrawal_mode permits withdrawal."""
	raw = frappe.db.get_value(DT_MANIFEST_VERSION, manifest_name, "payload_json") or "{}"
	try:
		payload = json.loads(raw)
	except json.JSONDecodeError:
		return False
	mode = ((payload.get("submission_policy") or {}).get("withdrawal_mode")) or "not_permitted"
	return mode in {"permitted_before_deadline", "governed_special"}


def create_validation_report(*, report_id: str, compile_run: str, readiness: str = "pass") -> str:
	doc = frappe.get_doc(
		{
			"doctype": DT_VALIDATION_REPORT,
			"report_id": report_id,
			"compile_run": compile_run,
			"diagnostic_digest": _hash_digest(report_id),
			"readiness": readiness,
			"immutable": 1,
			"report_json": json.dumps({"ok": readiness == "pass"}),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def create_approval(
	*,
	approval_id: str,
	manifest_name: str,
	validation_report: str,
	approver: str = "system:approver",
) -> str:
	manifest = frappe.get_doc(DT_MANIFEST_VERSION, manifest_name)
	doc = frappe.get_doc(
		{
			"doctype": DT_MANIFEST_APPROVAL,
			"approval_id": approval_id,
			"manifest_version": manifest_name,
			"payload_digest": manifest.payload_digest,
			"validation_report": validation_report,
			"approver": approver,
			"decision": "approved",
			"decided_at": now_datetime(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def create_publication(
	*,
	publication_id: str,
	manifest_name: str,
	approval: str = "",
	approval_decision: str = "",
	published_tender_ref: str,
	published_tender_version: int = 1,
	organization: str = "ORG-UNSPECIFIED",
) -> str:
	if not approval and not approval_decision:
		frappe.throw(
			_("Publication requires approval or approval_decision."),
			title="BWMF_PUBLICATION_APPROVAL",
		)
	doc = frappe.get_doc(
		{
			"doctype": DT_MANIFEST_PUBLICATION,
			"publication_id": publication_id,
			"manifest_version": manifest_name,
			"approval": approval or None,
			"approval_decision": approval_decision or None,
			"published_tender_ref": published_tender_ref,
			"published_tender_version": published_tender_version,
			"published_at": now_datetime(),
			"transaction_ref": publication_id,
			"organization": organization,
		}
	)
	doc.insert(ignore_permissions=True)
	publish_manifest_version(manifest_name, organization=organization)
	return doc.name


def create_workspace(
	*,
	workspace_id: str,
	organization: str,
	bidder_party: str,
	published_tender_ref: str,
) -> str:
	if frappe.db.exists(DT_WORKSPACE, {"workspace_id": workspace_id}):
		frappe.throw(_("Duplicate workspace_id."), title="BWMF_DUPLICATE_STABLE_ID")
	doc = frappe.get_doc(
		{
			"doctype": DT_WORKSPACE,
			"workspace_id": workspace_id,
			"organization": organization,
			"bidder_party": bidder_party,
			"published_tender_ref": published_tender_ref,
			"status": WS_NOT_STARTED,
		}
	)
	doc.insert(ignore_permissions=True)
	append_audit_event(
		event_type="workspace.created",
		organization=organization,
		bidder_party=bidder_party,
		workspace=doc.name,
		metadata={"status": WS_NOT_STARTED},
	)
	return doc.name


def _save_workspace_with_mode(doc, *, mode: str) -> None:
	frappe.flags.bwmf_workspace_lifecycle_mode = mode
	try:
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.bwmf_workspace_lifecycle_mode = None


def refresh_derived_workspace_status(
	*,
	workspace: str,
	organization: str,
	bidder_party: str,
	signals: WorkspaceReadinessSignals | None = None,
) -> str:
	"""Update preparatory status from readiness signals. Never sets transactional statuses."""
	assert_workspace_tenant(workspace=workspace, organization=organization, bidder_party=bidder_party)
	doc = frappe.get_doc(DT_WORKSPACE, workspace)
	if doc.status in {WS_SUBMITTED, WS_WITHDRAWN, WS_CLOSED}:
		return doc.status
	signals = signals or collect_workspace_readiness_signals(
		workspace=workspace,
		organization=organization,
		bidder_party=bidder_party,
		response_doctype=DT_RESPONSE_VERSION,
		confirmation_doctype=DT_CONFIRMATION,
	)
	derived = derive_workspace_status(signals)
	if derived not in PREPARATORY_WORKSPACE_STATUSES:
		frappe.throw(_("Derived status must be preparatory."), title="BWMF_WORKSPACE_DERIVE_FORBIDDEN")
	if derived != doc.status:
		doc.status = derived
		_save_workspace_with_mode(doc, mode="derive")
		append_audit_event(
			event_type="workspace.status.derived",
			organization=organization,
			bidder_party=bidder_party,
			workspace=workspace,
			metadata={"status": derived},
		)
	return derived


def submit_workspace(
	*,
	workspace: str,
	organization: str,
	bidder_party: str,
	active_submission: str,
) -> None:
	"""ready_to_submit -> submitted. active_submission is server-controlled."""
	assert_workspace_tenant(workspace=workspace, organization=organization, bidder_party=bidder_party)
	assert_row_org_party(
		doctype=DT_SUBMISSION,
		name=active_submission,
		organization=organization,
		bidder_party=bidder_party,
	)
	doc = frappe.get_doc(DT_WORKSPACE, workspace)
	if doc.status != WS_READY_TO_SUBMIT:
		frappe.throw(
			_("Workspace must be ready_to_submit before submission (found {0}).").format(doc.status),
			title="BWMF_WORKSPACE_NOT_READY",
		)
	doc.status = WS_SUBMITTED
	doc.active_submission = active_submission
	_save_workspace_with_mode(doc, mode="transaction")
	append_audit_event(
		event_type="workspace.submitted",
		organization=organization,
		bidder_party=bidder_party,
		workspace=workspace,
		submission_ref=active_submission,
		metadata={"status": WS_SUBMITTED},
	)


def withdraw_workspace(
	*,
	workspace: str,
	organization: str,
	bidder_party: str,
) -> None:
	"""submitted -> withdrawn only when active manifest policy permits."""
	assert_workspace_tenant(workspace=workspace, organization=organization, bidder_party=bidder_party)
	doc = frappe.get_doc(DT_WORKSPACE, workspace)
	if doc.status != WS_SUBMITTED:
		frappe.throw(_("Only submitted workspaces may be withdrawn."), title="BWMF_WORKSPACE_ILLEGAL_TRANSITION")
	active_manifest = frappe.db.get_value(
		DT_WORKSPACE_BINDING, {"workspace": workspace, "is_active": 1}, "manifest_doc"
	)
	if not active_manifest or not manifest_allows_withdrawal(active_manifest):
		frappe.throw(
			_("Manifest policy does not permit withdrawal."),
			title="BWMF_WITHDRAWAL_POLICY_DENIED",
		)
	doc.status = WS_WITHDRAWN
	_save_workspace_with_mode(doc, mode="transaction")
	append_audit_event(
		event_type="workspace.withdrawn",
		organization=organization,
		bidder_party=bidder_party,
		workspace=workspace,
		manifest_doc=active_manifest,
		metadata={"status": WS_WITHDRAWN},
	)


def close_workspace(
	*,
	workspace: str,
	organization: str,
	bidder_party: str,
) -> None:
	"""submitted|withdrawn -> closed (terminal)."""
	assert_workspace_tenant(workspace=workspace, organization=organization, bidder_party=bidder_party)
	doc = frappe.get_doc(DT_WORKSPACE, workspace)
	if doc.status not in {WS_SUBMITTED, WS_WITHDRAWN}:
		frappe.throw(
			_("Only submitted or withdrawn workspaces may close."),
			title="BWMF_WORKSPACE_ILLEGAL_TRANSITION",
		)
	doc.status = WS_CLOSED
	_save_workspace_with_mode(doc, mode="transaction")
	append_audit_event(
		event_type="workspace.closed",
		organization=organization,
		bidder_party=bidder_party,
		workspace=workspace,
		metadata={"status": WS_CLOSED},
	)


def bind_workspace_manifest(
	*,
	workspace: str,
	manifest_name: str,
	organization: str,
	bidder_party: str,
) -> str:
	"""Race-safe rebinding: lock workspace row, deactivate prior active, insert new active key."""
	assert_workspace_tenant(workspace=workspace, organization=organization, bidder_party=bidder_party)
	manifest = assert_manifest_in_org_scope(manifest_name=manifest_name)

	# Row lock serializes concurrent binders for this workspace.
	locked = frappe.db.sql(
		"select name from `tabBWMF Workspace` where name=%s for update",
		(workspace,),
	)
	if not locked:
		frappe.throw(_("Unknown BWMF workspace."), title="BWMF_WORKSPACE_NOT_FOUND")

	for name in frappe.get_all(
		DT_WORKSPACE_BINDING,
		filters={"workspace": workspace, "is_active": 1},
		pluck="name",
	):
		b = frappe.get_doc(DT_WORKSPACE_BINDING, name)
		b.is_active = 0
		b.active_binding_key = None
		b.save(ignore_permissions=True)
		# Data fields may coerce None→""; unique nullable key requires SQL NULL.
		frappe.db.sql(
			"update `tabBWMF Workspace Manifest Binding` set active_binding_key=NULL where name=%s",
			(name,),
		)
	doc = frappe.get_doc(
		{
			"doctype": DT_WORKSPACE_BINDING,
			"workspace": workspace,
			"manifest_id": manifest.manifest_id,
			"manifest_version": manifest.manifest_version,
			"payload_digest": manifest.payload_digest,
			"manifest_doc": manifest_name,
			"is_active": 1,
			"bound_at": now_datetime(),
			"organization": organization,
			"bidder_party": bidder_party,
			"active_binding_key": f"active:{workspace}",
		}
	)
	try:
		doc.insert(ignore_permissions=True)
	except frappe.UniqueValidationError:
		frappe.throw(
			_("Concurrent active binding conflict for workspace."),
			title="BWMF_BINDING_RACE",
		)

	append_audit_event(
		event_type="workspace.binding.active",
		organization=organization,
		bidder_party=bidder_party,
		workspace=workspace,
		manifest_doc=manifest_name,
		metadata={"binding": doc.name},
	)
	return doc.name


def append_response_version(
	*,
	response_id: str,
	workspace: str,
	manifest_name: str,
	section_key: str,
	organization: str,
	bidder_party: str,
	values: dict[str, Any] | None = None,
	expected_version: int | None = None,
	task_ref: str | None = None,
	scope_ref: str | None = None,
) -> str:
	"""Append an immutable response version. Replacement = new version row only."""
	assert_workspace_tenant(workspace=workspace, organization=organization, bidder_party=bidder_party)
	assert_manifest_in_org_scope(manifest_name=manifest_name)
	assert_same_workspace_manifest_binding(workspace=workspace, manifest_name=manifest_name)

	if expected_version is not None:
		assert_expected_response_version(response_id, expected_version)
	version = next_response_version(response_id)
	values = serialize_manifest_money(values or {})
	digest = _hash_digest(f"{response_id}:{version}:{json.dumps(values, sort_keys=True)}")
	doc = frappe.get_doc(
		{
			"doctype": DT_RESPONSE_VERSION,
			"response_id": response_id,
			"version": version,
			"workspace": workspace,
			"manifest_doc": manifest_name,
			"section_key": section_key,
			"state": "Immutable",
			"response_digest": digest,
			"values_json": json.dumps(values),
			"organization": organization,
			"bidder_party": bidder_party,
			"task_ref": task_ref,
			"scope_ref": scope_ref,
		}
	)
	doc.insert(ignore_permissions=True)
	append_audit_event(
		event_type="response.version.appended",
		organization=organization,
		bidder_party=bidder_party,
		workspace=workspace,
		manifest_doc=manifest_name,
		response_ref=f"{response_id}@{version}",
	)
	return doc.name


def seal_response_version(name: str) -> None:
	"""Sealing binds existing immutable versions; it must not rewrite response rows.

	Kept as a compatibility no-op that emits an audit event only.
	"""
	doc = frappe.get_doc(DT_RESPONSE_VERSION, name)
	append_audit_event(
		event_type="response.version.bound_for_seal",
		organization=doc.organization,
		bidder_party=doc.bidder_party,
		workspace=doc.workspace,
		manifest_doc=doc.manifest_doc,
		response_ref=f"{doc.response_id}@{doc.version}",
		metadata={"response_doc": name, "response_digest": doc.response_digest},
	)


def create_evidence_item(
	*,
	evidence_id: str,
	workspace: str,
	organization: str,
	bidder_party: str,
	evidence_type: str = "file",
) -> str:
	assert_workspace_tenant(workspace=workspace, organization=organization, bidder_party=bidder_party)
	doc = frappe.get_doc(
		{
			"doctype": DT_EVIDENCE_ITEM,
			"evidence_id": evidence_id,
			"workspace": workspace,
			"owner_party": bidder_party,
			"evidence_type": evidence_type,
			"organization": organization,
			"bidder_party": bidder_party,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def create_evidence_version(
	*,
	evidence_item: str,
	version: int,
	organization: str,
	bidder_party: str,
	content_label: str,
	content_digest: str | None = None,
) -> str:
	"""Create immutable evidence version. content_digest is not globally unique."""
	if not frappe.db.exists(DT_EVIDENCE_ITEM, evidence_item):
		frappe.throw(_("Missing evidence item."), title="BWMF_REF_MISSING")
	assert_row_org_party(
		doctype=DT_EVIDENCE_ITEM,
		name=evidence_item,
		organization=organization,
		bidder_party=bidder_party,
	)
	if frappe.db.exists(DT_EVIDENCE_VERSION, {"evidence_item": evidence_item, "version": version}):
		frappe.throw(_("Duplicate evidence_id/version."), title="BWMF_DUPLICATE_STABLE_ID")
	digest = content_digest or _hash_digest(f"ev:{evidence_item}:{version}:{content_label}")
	doc = frappe.get_doc(
		{
			"doctype": DT_EVIDENCE_VERSION,
			"evidence_item": evidence_item,
			"version": version,
			"content_digest": digest,
			"document_content_digest": digest,
			"state": "Immutable",
			"mime_type": "application/pdf",
			"organization": organization,
			"bidder_party": bidder_party,
		}
	)
	doc.insert(ignore_permissions=True)
	append_audit_event(
		event_type="evidence.version.created",
		organization=organization,
		bidder_party=bidder_party,
		evidence_ref=f"{evidence_item}@{version}",
	)
	return doc.name


def link_evidence(
	*,
	evidence_version: str,
	workspace: str,
	task_ref: str,
	organization: str,
	bidder_party: str,
) -> str:
	assert_workspace_tenant(workspace=workspace, organization=organization, bidder_party=bidder_party)
	if not frappe.db.exists(DT_EVIDENCE_VERSION, evidence_version):
		frappe.throw(_("Missing evidence version."), title="BWMF_REF_MISSING")
	assert_row_org_party(
		doctype=DT_EVIDENCE_VERSION,
		name=evidence_version,
		organization=organization,
		bidder_party=bidder_party,
	)
	ev_item = frappe.db.get_value(DT_EVIDENCE_VERSION, evidence_version, "evidence_item")
	item_ws = frappe.db.get_value(DT_EVIDENCE_ITEM, ev_item, "workspace")
	if item_ws != workspace:
		frappe.throw(
			_("Evidence link crosses workspace boundaries."),
			title="BWMF_CROSS_WORKSPACE_LINK",
		)
	# Active manifest binding must exist for the workspace (manifest scope).
	active = frappe.db.get_value(
		DT_WORKSPACE_BINDING,
		{"workspace": workspace, "is_active": 1},
		"manifest_doc",
	)
	if not active:
		frappe.throw(_("Evidence link requires an active workspace manifest binding."), title="BWMF_REF_MISSING")

	doc = frappe.get_doc(
		{
			"doctype": DT_EVIDENCE_LINK,
			"evidence_version": evidence_version,
			"workspace": workspace,
			"task_ref": task_ref,
			"organization": organization,
			"bidder_party": bidder_party,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def create_confirmation(
	*,
	confirmation_id: str,
	workspace: str,
	response_id: str,
	response_version: int,
	organization: str,
	bidder_party: str,
	authority_ref: str | None = None,
	expected_response_digest: str | None = None,
) -> str:
	assert_workspace_tenant(workspace=workspace, organization=organization, bidder_party=bidder_party)
	resp = frappe.db.get_value(
		DT_RESPONSE_VERSION,
		{"response_id": response_id, "version": response_version},
		["name", "organization", "bidder_party", "workspace", "response_digest", "manifest_doc"],
		as_dict=True,
	)
	if not resp:
		frappe.throw(_("Missing response version for confirmation."), title="BWMF_REF_MISSING")
	assert_org_party_match(
		organization=organization,
		bidder_party=bidder_party,
		row_organization=resp.organization,
		row_bidder_party=resp.bidder_party,
	)
	if resp.workspace != workspace:
		frappe.throw(_("Confirmation response is cross-workspace."), title="BWMF_CROSS_WORKSPACE_LINK")
	assert_same_workspace_manifest_binding(workspace=workspace, manifest_name=resp.manifest_doc)
	if expected_response_digest is not None and expected_response_digest != resp.response_digest:
		frappe.throw(
			_("Confirmation response digest does not match the response version."),
			title="BWMF_RESPONSE_DIGEST_MISMATCH",
		)

	authority_name = None
	if authority_ref:
		if not frappe.db.exists(DT_AUTHORITY_REFERENCE, authority_ref):
			auth = frappe.get_doc(
				{
					"doctype": DT_AUTHORITY_REFERENCE,
					"authority_ref": authority_ref,
					"authority_version": "1",
					"label": authority_ref,
				}
			)
			auth.insert(ignore_permissions=True)
		authority_name = authority_ref
	doc = frappe.get_doc(
		{
			"doctype": DT_CONFIRMATION,
			"confirmation_id": confirmation_id,
			"workspace": workspace,
			"response_id": response_id,
			"response_version": response_version,
			"response_digest": resp.response_digest,
			"legal_text_ref": "LEGAL-IT-STD-1",
			"legal_text_digest": _hash_digest("legal"),
			"statement_digest": _hash_digest("statement"),
			"actor_ref": bidder_party,
			"capacity": "authorized_signatory",
			"authority": authority_name,
			"confirmed_at": now_datetime(),
			"state": "confirmed",
			"organization": organization,
			"bidder_party": bidder_party,
		}
	)
	doc.insert(ignore_permissions=True)
	append_audit_event(
		event_type="confirmation.created",
		organization=organization,
		bidder_party=bidder_party,
		workspace=workspace,
		confirmation_ref=confirmation_id,
		response_ref=f"{response_id}@{response_version}",
	)
	return doc.name


def create_or_get_sealed_submission(
	*,
	submission_id: str,
	idempotency_key: str,
	workspace: str,
	manifest_name: str,
	organization: str,
	bidder_party: str,
	snapshot: dict[str, Any] | None = None,
	total_amount: str | Decimal | None = None,
	responses: list[dict[str, Any]] | None = None,
	evidence: list[dict[str, Any]] | None = None,
	confirmations: list[dict[str, Any]] | None = None,
) -> str:
	"""Seal a submission. Snapshot ``totals`` is authoritative; ``total_amount`` is a projection."""
	ws = assert_workspace_tenant(workspace=workspace, organization=organization, bidder_party=bidder_party)
	manifest = assert_manifest_in_org_scope(manifest_name=manifest_name)
	assert_same_workspace_manifest_binding(workspace=workspace, manifest_name=manifest_name)

	if snapshot is not None:
		snap_total = decimal_to_storage_str(
			exact_decimal_roundtrip((snapshot.get("totals") or {}).get("grand_total") or "0")
		)
		if total_amount is not None:
			caller_total = decimal_to_storage_str(exact_decimal_roundtrip(total_amount))
			if caller_total != snap_total:
				frappe.throw(
					_("Submission total_amount does not match sealed snapshot totals."),
					title="BWMF_TOTAL_MISMATCH",
				)
		amount_str = snap_total
	else:
		amount_str = decimal_to_storage_str(exact_decimal_roundtrip(total_amount if total_amount is not None else "1000.00"))

	fingerprint_payload = {
		"submission_id": submission_id,
		"workspace": workspace,
		"manifest_doc": manifest_name,
		"payload_digest": manifest.payload_digest,
		"totals": {"grand_total": amount_str},
		"responses": responses or [],
		"evidence": evidence or [],
		"confirmations": confirmations or [],
	}
	fp = canonical_request_fingerprint(fingerprint_payload)

	def _create() -> str:
		if frappe.db.exists(DT_SUBMISSION, {"submission_id": submission_id}):
			frappe.throw(_("Duplicate submission_id."), title="BWMF_DUPLICATE_STABLE_ID")
		closed = snapshot or build_submission_snapshot(
			submission_id=submission_id,
			submission_version=1,
			organization=organization,
			bidder_party=bidder_party,
			workspace_id=ws.workspace_id,
			manifest={
				"manifest_id": manifest.manifest_id,
				"manifest_version": manifest.manifest_version,
				"payload_digest": manifest.payload_digest,
				"manifest_doc": manifest_name,
			},
			responses=responses
			or [
				{
					"response_id": r.response_id,
					"version": int(r.version),
					"response_digest": r.response_digest,
					"section_key": r.section_key,
				}
				for r in frappe.get_all(
					DT_RESPONSE_VERSION,
					filters={"workspace": workspace, "organization": organization, "bidder_party": bidder_party},
					fields=["response_id", "version", "response_digest", "section_key"],
					order_by="response_id, version",
				)
			],
			evidence=evidence
			or [
				{
					"evidence_version": e.name,
					"content_digest": e.content_digest,
					"version": int(e.version),
				}
				for e in frappe.get_all(
					DT_EVIDENCE_VERSION,
					filters={"organization": organization, "bidder_party": bidder_party},
					fields=["name", "content_digest", "version"],
				)
			],
			confirmations=confirmations,
			totals={"grand_total": amount_str},
		)
		# Authoritative totals live in the snapshot; top-level field is derived projection.
		projected = decimal_to_storage_str(
			exact_decimal_roundtrip((closed.get("totals") or {}).get("grand_total") or "0")
		)
		if projected != amount_str:
			frappe.throw(
				_("Submission total_amount does not match sealed snapshot totals."),
				title="BWMF_TOTAL_MISMATCH",
			)
		_assert_submission_snapshot_integrity(
			snapshot=closed,
			workspace=workspace,
			manifest_name=manifest_name,
			organization=organization,
			bidder_party=bidder_party,
			payload_digest=manifest.payload_digest,
		)
		snap_json = snapshot_to_json(closed)
		snap_digest = _hash_digest(snap_json)
		doc = frappe.get_doc(
			{
				"doctype": DT_SUBMISSION,
				"submission_id": submission_id,
				"submission_version": 1,
				"idempotency_key": idempotency_key,
				"workspace": workspace,
				"manifest_doc": manifest_name,
				"payload_digest": manifest.payload_digest,
				"snapshot_digest": snap_digest,
				"snapshot_json": snap_json,
				"snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
				"status": "Sealed",
				"sealed_at": now_datetime(),
				"organization": organization,
				"bidder_party": bidder_party,
				"total_amount": projected,
			}
		)
		doc.insert(ignore_permissions=True)
		append_audit_event(
			event_type="submission.sealed",
			organization=organization,
			bidder_party=bidder_party,
			workspace=workspace,
			manifest_doc=manifest_name,
			submission_ref=submission_id,
			idempotency_ref=idempotency_key,
			metadata={"snapshot_digest": snap_digest, "total_amount": projected},
		)
		return doc.name

	return resolve_idempotency(
		organization=organization,
		operation=OP_SEAL_SUBMISSION,
		idempotency_key=idempotency_key,
		request_fingerprint=fp,
		result_doctype=DT_SUBMISSION,
		create_result=_create,
	)


def issue_receipt(*, receipt_id: str, submission: str, organization: str, bidder_party: str) -> str:
	assert_row_org_party(
		doctype=DT_SUBMISSION,
		name=submission,
		organization=organization,
		bidder_party=bidder_party,
	)
	status = frappe.db.get_value(DT_SUBMISSION, submission, "status")
	if status != "Sealed":
		frappe.throw(_("Receipt requires a sealed submission."), title="BWMF_SUBMISSION_NOT_SEALED")
	doc = frappe.get_doc(
		{
			"doctype": DT_SUBMISSION_RECEIPT,
			"receipt_id": receipt_id,
			"submission": submission,
			"verification_value": _hash_digest(f"receipt:{receipt_id}"),
			"issued_at": now_datetime(),
			"safe_summary": "Submission sealed",
			"organization": organization,
			"bidder_party": bidder_party,
		}
	)
	doc.insert(ignore_permissions=True)
	append_audit_event(
		event_type="submission.receipt.issued",
		organization=organization,
		bidder_party=bidder_party,
		submission_ref=submission,
		metadata={"receipt_id": receipt_id},
	)
	return doc.name


def prove_money_totals(values: list[str | Decimal]) -> str:
	"""Public helper for tests: exact sum without float."""
	return decimal_to_storage_str(sum_money(values))


def _assert_submission_snapshot_integrity(
	*,
	snapshot: dict[str, Any],
	workspace: str,
	manifest_name: str,
	organization: str,
	bidder_party: str,
	payload_digest: str,
) -> None:
	manifest_block = snapshot.get("manifest") or {}
	if manifest_block.get("manifest_doc") and manifest_block.get("manifest_doc") != manifest_name:
		frappe.throw(_("Submission snapshot manifest_doc mismatch."), title="BWMF_SNAPSHOT_BINDING_MISMATCH")
	if manifest_block.get("payload_digest") != payload_digest:
		frappe.throw(_("Submission snapshot payload_digest mismatch."), title="BWMF_SNAPSHOT_BINDING_MISMATCH")
	for resp in snapshot.get("responses") or []:
		rid = resp.get("response_id")
		ver = resp.get("version")
		row = frappe.db.get_value(
			DT_RESPONSE_VERSION,
			{"response_id": rid, "version": ver},
			["workspace", "manifest_doc", "response_digest", "organization", "bidder_party"],
			as_dict=True,
		)
		if not row:
			frappe.throw(
				_("Submission snapshot references unresolved response {0}@{1}.").format(rid, ver),
				title="BWMF_SNAPSHOT_BINDING_MISMATCH",
			)
		if row.workspace != workspace or row.manifest_doc != manifest_name:
			frappe.throw(
				_("Submission snapshot response bound to wrong workspace/manifest."),
				title="BWMF_SNAPSHOT_BINDING_MISMATCH",
			)
		if row.response_digest != resp.get("response_digest"):
			frappe.throw(
				_("Submission snapshot response digest mismatch."),
				title="BWMF_SNAPSHOT_BINDING_MISMATCH",
			)
		assert_org_party_match(
			organization=organization,
			bidder_party=bidder_party,
			row_organization=row.organization,
			row_bidder_party=row.bidder_party,
		)
