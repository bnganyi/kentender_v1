# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase 4 materialization: CAS resources + new finalized Compile Artifact."""

from __future__ import annotations

import copy
import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.resource_verifier import (
	ResourceVerifyError,
	assert_candidates_cover_preview,
	verify_descriptor_set,
	verify_resource_row,
	verify_sections_reference_resources,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.fixtures_loader import (
	load_nssf_calibration_source_set,
	load_synthetic_std_source_set,
	nssf_compile_request,
	synthetic_compile_request,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.pipeline import (
	run as pure_run,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.types import (
	CompileRequestDTO,
	SourceSet,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence import services as bwmf
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.audit import (
	append_audit_event,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.idempotency import (
	canonical_request_fingerprint,
	resolve_idempotency,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_ARTIFACT_RESOURCE_BINDING,
	DT_COMPILE_ARTIFACT,
	DT_MANIFEST_PUBLICATION,
	DT_MANIFEST_VERSION,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.cas import (
	STORAGE_PROFILE,
	put_canonical_json,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.chunking import (
	CHUNKING_ALGORITHM_VERSION,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.canonical import (
	canonicalize_items,
	descriptor_set_digest,
	logical_resource_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.item_schemas import (
	FORBIDDEN_ITEM_KEYS,
	NSSF_RESOURCE_SPECS,
)

OP_MATERIALIZE = "materialize_resources"
SCHEMA_SET_VERSION = "bwmf-item-schemas-1.0.0"

# Test-only inject: raise while processing the Nth resource (1-based).
_FAIL_DURING_RESOURCE_N: int | None = None


def set_fail_during_resource_n(n: int | None) -> None:
	"""Inject a failure during the Nth NSSF resource (1-based). None disables."""
	global _FAIL_DURING_RESOURCE_N
	_FAIL_DURING_RESOURCE_N = n


def _load_artifact(artifact_name: str):
	if not frappe.db.exists(DT_COMPILE_ARTIFACT, artifact_name):
		frappe.throw(_("Compile artifact not found."), title="BWMF_ARTIFACT_MISSING")
	return frappe.get_doc(DT_COMPILE_ARTIFACT, artifact_name)


def _reject_failed_result(art) -> None:
	if art.artifact_kind == "failed_result" or art.digest_label == "failed_result":
		frappe.throw(
			_("Failed-result artifacts cannot be materialized."),
			title="BWMF_MATERIALIZE_INPUT",
		)
	if not (art.payload_digest or "").strip() or not (art.payload_json or "").strip():
		frappe.throw(
			_("Compile artifact lacks a payload and cannot be materialized."),
			title="BWMF_MATERIALIZE_INPUT",
		)


def _candidate_items(candidate: dict[str, Any]) -> list[dict[str, Any]]:
	items = candidate.get("logical_items")
	if items is None:
		frappe.throw(
			_("Candidate {0} missing logical_items.").format(candidate.get("resource_id")),
			title="BWMF_CANDIDATE",
		)
	return list(items)


def _validate_candidate(candidate: dict[str, Any], *, spec: dict[str, Any] | None) -> dict[str, Any]:
	rid = candidate.get("resource_id") or candidate.get("candidate_id")
	items = _candidate_items(candidate)
	for row in items:
		for k in row:
			if k in FORBIDDEN_ITEM_KEYS:
				frappe.throw(_("Forbidden field in candidate items."), title="BWMF_CANDIDATE")
		for v in row.values():
			if isinstance(v, float):
				frappe.throw(_("Float values are not permitted."), title="BWMF_CANDIDATE")
	fields = tuple(spec["fields"]) if spec else tuple(sorted({k for r in items for k in r.keys()}))
	if spec:
		identity = spec["identity_key"]
		ordering = list(spec["ordering_contract"])
	else:
		for key in (
			"requirement_key",
			"group_key",
			"criterion_key",
			"line_key",
			"row_key",
			"condition_key",
			"decision_id",
			"item_key",
			"id",
		):
			if key in fields:
				identity = key
				break
		else:
			identity = fields[0] if fields else "id"
		ordering = ["order_weight", identity] if "order_weight" in fields else [identity]
	canonical = canonicalize_items(
		items,
		fields=fields,
		ordering_contract=ordering,
		identity_key=identity,
	)
	if len(canonical) != int(candidate.get("item_count") or len(items)):
		frappe.throw(_("Candidate item count mismatch."), title="BWMF_RESOURCE_COUNT")
	digest = logical_resource_digest(canonical)
	declared = candidate.get("logical_digest") or ""
	if declared and declared != digest:
		frappe.throw(
			_("Candidate logical digest mismatch for {0}.").format(rid),
			title="BWMF_RESOURCE_DIGEST",
		)
	return {
		"resource_id": rid,
		"resource_type": (spec or {}).get("resource_type") or candidate.get("resource_type"),
		"schema_ref": (spec or {}).get("schema_ref") or candidate.get("schema_ref"),
		"schema_version": (spec or {}).get("schema_version") or candidate.get("schema_version") or "1.0.0",
		"item_count": len(canonical),
		"ordering_contract": ordering,
		"resource_digest": digest,
		"items": canonical,
		"source_refs": [
			candidate.get("source_lineage") or candidate.get("lineage") or {"resource_id": rid}
		],
	}


def execute_materialization(
	*,
	source_artifact_name: str,
	idempotency_key: str,
	organization: str = "ORG-P4",
	sources: SourceSet | None = None,
	request: CompileRequestDTO | None = None,
	calibration_only: bool | None = None,
	chunk_resource_id: str | None = None,
	chunk_size: int = 0,
) -> dict[str, Any]:
	"""Materialize candidates from a preview artifact into CAS + finalized artifact."""
	art = _load_artifact(source_artifact_name)
	_reject_failed_result(art)
	preview_digest = art.payload_digest
	candidates = json.loads(art.resource_candidates_json or "[]")
	if not candidates:
		frappe.throw(_("No resource candidates on artifact."), title="BWMF_CANDIDATE")

	fingerprint = canonical_request_fingerprint(
		{
			"source_artifact_id": art.artifact_id,
			"source_payload_digest": preview_digest,
			"schema_set_version": SCHEMA_SET_VERSION,
			"storage_profile": STORAGE_PROFILE,
			"chunking_algorithm_version": CHUNKING_ALGORITHM_VERSION,
			"candidate_digests": [c.get("logical_digest") for c in candidates],
		}
	)

	def _create() -> str:
		return _materialize_body(
			art=art,
			candidates=candidates,
			organization=organization,
			sources=sources,
			request=request,
			calibration_only=calibration_only,
			chunk_resource_id=chunk_resource_id,
			chunk_size=chunk_size,
		)

	report_name = resolve_idempotency(
		organization=organization,
		operation=OP_MATERIALIZE,
		idempotency_key=idempotency_key,
		request_fingerprint=fingerprint,
		result_doctype="BWMF Materialization Report",
		create_result=_create,
	)
	report = frappe.get_doc("BWMF Materialization Report", report_name)
	body = json.loads(report.report_json)
	body["materialization_report"] = report_name
	body["ok"] = report.state == "Succeeded"
	return body


def _materialize_body(
	*,
	art,
	candidates: list[dict[str, Any]],
	organization: str,
	sources: SourceSet | None,
	request: CompileRequestDTO | None,
	calibration_only: bool | None,
	chunk_resource_id: str | None,
	chunk_size: int,
) -> str:
	append_audit_event(
		event_type="materialization.requested",
		organization=organization,
		compile_run_ref=art.compile_run,
		metadata={"source_artifact": art.name, "artifact_id": art.artifact_id},
	)
	dispositions: list[dict[str, Any]] = []
	verified_map: dict[str, Any] = {}
	resource_ids: list[str] = []
	resource_docnames: list[str] = []
	try:
		# 1) Validate ALL candidates before creating the finalized package.
		validated_list: list[dict[str, Any]] = []
		for cand in candidates:
			rid = cand.get("resource_id") or cand.get("candidate_id")
			spec = NSSF_RESOURCE_SPECS.get(rid)
			validated_list.append(_validate_candidate(cand, spec=spec))
		assert_candidates_cover_preview(candidates, [v["resource_id"] for v in validated_list])

		# 2) Persist CAS + Manifest Resources (idempotent; may remain if package fails).
		for idx, validated in enumerate(validated_list, start=1):
			if _FAIL_DURING_RESOURCE_N is not None and idx == _FAIL_DURING_RESOURCE_N:
				raise frappe.ValidationError(
					_("Injected materialization failure during resource {0}.").format(idx)
				)
			rid = validated["resource_id"]
			spec = NSSF_RESOURCE_SPECS.get(rid)
			stored = put_canonical_json(validated["items"], organization=organization)
			chunks = None
			storage_mode = "content_addressed"
			content_ref = stored["content_ref"]
			if chunk_resource_id and rid == chunk_resource_id and chunk_size > 0:
				from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.chunking import (
					chunk_items,
				)

				chunks = chunk_items(
					validated["items"],
					identity_key=(spec or {}).get("identity_key") or "id",
					chunk_size=chunk_size,
					organization=organization,
				)
				storage_mode = "content_addressed_chunked"
				content_ref = ""
			docname = bwmf.create_manifest_resource(
				resource_id=validated["resource_id"],
				resource_type=validated["resource_type"],
				schema_ref=validated["schema_ref"],
				schema_version=validated["schema_version"],
				item_count=validated["item_count"],
				ordering_contract=validated["ordering_contract"],
				resource_digest=validated["resource_digest"],
				storage_mode=storage_mode,
				content_ref=content_ref,
				physical_object_digest=stored["physical_object_digest"],
				source_refs=validated["source_refs"],
				chunks=chunks,
				organization=organization,
			)
			# Binding content_ref for registry always points at full-array CAS when available.
			bind_ref = stored["content_ref"]
			verified_map[rid] = {
				"storage_mode": storage_mode,
				"content_ref": bind_ref,
				"physical_object_digest": stored["physical_object_digest"],
				"resource_digest": validated["resource_digest"],
				"source_refs": validated["source_refs"],
				"chunks": chunks,
				"resource_docname": docname,
				"schema_ref": validated["schema_ref"],
				"schema_version": validated["schema_version"],
				"resource_type": validated["resource_type"],
				"ordering_contract": validated["ordering_contract"],
				"item_count": validated["item_count"],
			}
			resource_ids.append(rid)
			resource_docnames.append(docname)
			dispositions.append(
				{
					"resource_id": rid,
					"resource_docname": docname,
					"disposition": "materialized",
					"expected_count": validated["item_count"],
					"actual_count": validated["item_count"],
					"expected_digest": validated["resource_digest"],
					"actual_digest": validated["resource_digest"],
					"content_ref": bind_ref,
					"physical_object_digest": stored["physical_object_digest"],
				}
			)

		# 3) Re-verify every resource before finalized-artifact creation.
		for docname in resource_docnames:
			verify_resource_row(docname)
		set_digest = descriptor_set_digest([verified_map[r]["resource_digest"] for r in resource_ids])
		verify_descriptor_set(resource_docnames, set_digest)

		# 4) Pure finalize recompile (does not mutate preview).
		src = sources or _default_sources_for_artifact(art)
		raw = copy.deepcopy(src.raw)
		raw["verified_materialized_resources"] = {
			rid: {
				"storage_mode": verified_map[rid]["storage_mode"],
				"content_ref": verified_map[rid]["content_ref"],
				"physical_object_digest": verified_map[rid]["physical_object_digest"],
				"resource_digest": verified_map[rid]["resource_digest"],
				"source_refs": verified_map[rid]["source_refs"],
				"chunks": verified_map[rid]["chunks"],
			}
			for rid in resource_ids
		}
		is_cal = (
			calibration_only
			if calibration_only is not None
			else (raw.get("profile") == "nssf_calibration")
		)
		raw["calibration_only"] = bool(is_cal)
		src2 = SourceSet(raw=raw, insertion_order=list(src.insertion_order))
		req = request or _default_request_for_artifact(art, publication=not is_cal)
		result = pure_run(req, src2)
		if not result.ok:
			raise frappe.ValidationError(result.fail_code or "finalize failed")

		verify_sections_reference_resources(
			result.payload.get("sections") or [],
			set(resource_ids),
		)

		# 5) Atomic package: finalized artifact + bindings + success report.
		final_id = f"ART-FINAL-{art.artifact_id}"
		report_body = {
			"source_artifact": art.name,
			"source_artifact_id": art.artifact_id,
			"source_payload_digest": art.payload_digest,
			"finalized_artifact_id": final_id,
			"finalized_payload_digest": result.payload_digest,
			"digest_label": result.digest_label,
			"descriptor_set_digest": set_digest,
			"dispositions": dispositions,
			"publication_readiness": (result.payload or {}).get("publication_readiness") or {},
			"calibration_only": bool(is_cal),
			"manifest_versions_created": 0,
			"publications_created": 0,
			"canonical_resources": len(resource_ids),
		}

		frappe.db.savepoint("bwmf_finalize_package")
		try:
			final_name = bwmf.create_compile_artifact(
				artifact_id=final_id,
				compile_run=art.compile_run,
				compile_mode=req.compile_mode,
				target_manifest_id=art.target_manifest_id,
				target_manifest_version=int(art.target_manifest_version),
				envelope=result.envelope,
				payload=result.payload,
				payload_digest=result.payload_digest,
				projection_digest=result.projection_digest or "",
				diagnostic_digest=result.diagnostic_digest or "",
				resource_candidates=result.logical_resources,
				addendum_impact=result.addendum_impact,
				digest_label=result.digest_label,
				artifact_kind="finalized_materialized",
				organization=organization,
			)
			bindings: list[str] = []
			for rid in resource_ids:
				bname = bwmf.create_artifact_resource_binding(
					binding_id=f"BIND-{final_id}-{rid}",
					compile_artifact=final_name,
					resource_id=rid,
					resource_digest=verified_map[rid]["resource_digest"],
					content_ref=verified_map[rid]["content_ref"],
					resource_docname=verified_map[rid]["resource_docname"],
					organization=organization,
				)
				bindings.append(bname)
				# attach binding ref onto disposition for audit
				for d in dispositions:
					if d["resource_id"] == rid:
						d["binding_id"] = f"BIND-{final_id}-{rid}"
						d["binding_docname"] = bname
			report_body["finalized_artifact"] = final_name
			report_body["bindings"] = bindings
			report_name = bwmf.create_materialization_report(
				report_id=f"MAT-{art.artifact_id}",
				source_artifact=art.name,
				state="Succeeded",
				report=report_body,
				descriptor_set_digest=set_digest,
				finalized_artifact=final_name,
				organization=organization,
			)
			frappe.db.release_savepoint("bwmf_finalize_package")
		except Exception:
			frappe.db.rollback(save_point="bwmf_finalize_package")
			raise

		append_audit_event(
			event_type="materialization.succeeded",
			organization=organization,
			compile_run_ref=art.compile_run,
			metadata={
				"report": report_name,
				"finalized_artifact": final_name,
				"payload_digest": result.payload_digest,
				"descriptor_set_digest": set_digest,
			},
		)
		_ = (DT_MANIFEST_PUBLICATION, DT_ARTIFACT_RESOURCE_BINDING, DT_MANIFEST_VERSION)
		return report_name
	except Exception as exc:
		append_audit_event(
			event_type="materialization.failed",
			organization=organization,
			compile_run_ref=art.compile_run,
			metadata={"error": str(exc), "code": getattr(exc, "title", None) or type(exc).__name__},
		)
		fail_body = {
			"source_artifact": art.name,
			"source_artifact_id": art.artifact_id,
			"source_payload_digest": art.payload_digest,
			"dispositions": dispositions,
			"error": str(exc),
			"finalized_artifact": "",
			"canonical_resources": len(resource_ids),
			"publication_readiness": {"passed": False, "resource_readiness": {"passed": False}},
		}
		return bwmf.create_materialization_report(
			report_id=f"MAT-FAIL-{art.artifact_id}-{frappe.generate_hash(length=6)}",
			source_artifact=art.name,
			state="Failed",
			report=fail_body,
			organization=organization,
		)


def _default_sources_for_artifact(art) -> SourceSet:
	if "NSSF" in (art.target_manifest_id or "") or "P3" in (art.target_manifest_id or "") or "P4" in (
		art.target_manifest_id or ""
	):
		return load_nssf_calibration_source_set()
	return load_synthetic_std_source_set()


def _default_request_for_artifact(art, *, publication: bool) -> CompileRequestDTO:
	mode = "publication" if publication else "preview"
	if "SYN" in (art.target_manifest_id or "") or art.compile_mode == "publication":
		req = synthetic_compile_request(compile_mode=mode)
	else:
		req = nssf_compile_request(compile_mode="preview")
		req.compile_mode = "preview"
	req.target_manifest_id = art.target_manifest_id
	req.target_manifest_version = int(art.target_manifest_version)
	return req
