# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Server-derived review/publication eligibility for finalized Compile Artifacts."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_configurations.bidder_workspace_manifest.application.resource_verifier import (
	ResourceVerifyError,
	verify_descriptor_set,
	verify_resource_row,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	jcs_sha256_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_ARTIFACT_RESOURCE_BINDING,
	DT_COMPILE_ARTIFACT,
	DT_COMPILE_RUN,
	DT_MANIFEST_RESOURCE,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.canonical import (
	descriptor_set_digest,
)

CALIBRATION_DIGEST_LABELS = frozenset(
	{
		"materialized_calibration_payload",
		"unmaterialized_preview_payload",
	}
)


def _throw(code: str, message: str) -> None:
	frappe.throw(_(message), title=code)


def assert_eligible_for_review(artifact_name: str) -> dict[str, Any]:
	"""Derive eligibility server-side. Never trust a client `eligible` Boolean."""
	if not frappe.db.exists(DT_COMPILE_ARTIFACT, artifact_name):
		_throw("BWMF_ELIGIBILITY", "Compile artifact not found.")
	art = frappe.get_doc(DT_COMPILE_ARTIFACT, artifact_name)

	if art.artifact_kind != "finalized_materialized":
		_throw(
			"BWMF_ELIGIBILITY",
			f"Artifact kind {art.artifact_kind!r} is not eligible for approval.",
		)
	if art.artifact_kind in {"preview", "failed_result"} or art.digest_label == "failed_result":
		_throw("BWMF_ELIGIBILITY", "Preview or failed-result artifacts cannot be submitted.")

	# Explicit NSSF / calibration rejection
	if art.digest_label in CALIBRATION_DIGEST_LABELS or "calibration" in (art.digest_label or "").lower():
		_throw("BWMF_CALIBRATION_NOT_PUBLISHABLE", "NSSF calibration artifacts cannot be approved or published.")
	if art.compile_mode not in {"publication", "addendum_publication"}:
		_throw(
			"BWMF_ELIGIBILITY",
			f"Compile mode {art.compile_mode!r} is not a publication mode.",
		)

	run_state = frappe.db.get_value(DT_COMPILE_RUN, art.compile_run, "state")
	if run_state != "Succeeded":
		_throw("BWMF_ELIGIBILITY", "Compile run must have succeeded.")

	if not (art.payload_json or "").strip() or not (art.payload_digest or "").strip():
		_throw("BWMF_ELIGIBILITY", "Artifact lacks payload/digest.")

	try:
		payload = json.loads(art.payload_json)
	except json.JSONDecodeError:
		_throw("BWMF_ELIGIBILITY", "Artifact payload is not valid JSON.")

	recomputed = jcs_sha256_digest(payload)
	if recomputed != art.payload_digest:
		_throw("BWMF_ELIGIBILITY", "Payload does not reproduce its RFC 8785 JCS digest.")

	pr = payload.get("publication_readiness") or {}
	if not pr.get("passed"):
		_throw("BWMF_ELIGIBILITY", "publication_readiness.passed must be true.")
	if int(pr.get("error_count") or 0) != 0:
		_throw("BWMF_ELIGIBILITY", "publication_readiness.error_count must be zero.")
	rr = pr.get("resource_readiness") or {}
	if not rr.get("passed"):
		_throw("BWMF_ELIGIBILITY", "resource_readiness.passed must be true.")
	if pr.get("calibration_only") or payload.get("calibration_only"):
		_throw("BWMF_CALIBRATION_NOT_PUBLISHABLE", "Calibration-only artifacts are not publishable.")

	# Source / policy / target
	if not (art.target_manifest_id or "").strip():
		_throw("BWMF_ELIGIBILITY", "Target tender/manifest identity is required.")
	sp = payload.get("submission_policy")
	if not isinstance(sp, dict) or not sp:
		_throw("BWMF_ELIGIBILITY", "Submission policy must be complete.")

	bindings = frappe.get_all(
		DT_ARTIFACT_RESOURCE_BINDING,
		filters={"compile_artifact": art.name},
		fields=[
			"name",
			"resource_id",
			"resource_digest",
			"content_ref",
			"resource_docname",
		],
	)
	if not bindings:
		_throw("BWMF_ELIGIBILITY", "Incomplete resource bindings on finalized artifact.")
	by_id = {b.resource_id: b for b in bindings}

	# Canonical order = payload resource_registry.resources (not alphabetical resource_id).
	registry_resources = ((payload.get("resource_registry") or {}).get("resources")) or []
	ordered_ids = [r.get("resource_id") for r in registry_resources if r.get("resource_id")]
	if not ordered_ids:
		ordered_ids = sorted(by_id.keys())
	if set(ordered_ids) != set(by_id.keys()):
		_throw("BWMF_ELIGIBILITY", "Artifact bindings do not match payload resource registry.")

	resource_docnames: list[str] = []
	digests: list[str] = []
	resources: list[dict[str, Any]] = []
	try:
		for idx, rid in enumerate(ordered_ids):
			b = by_id[rid]
			docname = b.resource_docname or frappe.db.get_value(
				DT_MANIFEST_RESOURCE,
				{"resource_id": b.resource_id, "resource_digest": b.resource_digest},
				"name",
			)
			if not docname:
				_throw("BWMF_ELIGIBILITY", f"Missing Manifest Resource for {b.resource_id}.")
			verify_resource_row(docname)
			rd = frappe.get_doc(DT_MANIFEST_RESOURCE, docname)
			if rd.resource_digest != b.resource_digest or (rd.content_ref or "") != (b.content_ref or ""):
				_throw("BWMF_ELIGIBILITY", f"Artifact binding mismatch for {b.resource_id}.")
			resource_docnames.append(docname)
			digests.append(rd.resource_digest)
			resources.append(
				{
					"resource_id": rd.resource_id,
					"resource_docname": rd.name,
					"resource_version_key": rd.resource_version_key,
					"resource_type": rd.resource_type,
					"schema_ref": rd.schema_ref,
					"schema_version": rd.schema_version,
					"resource_digest": rd.resource_digest,
					"content_ref": rd.content_ref,
					"item_count": int(rd.item_count or 0),
					"descriptor_order": idx,
				}
			)

		set_digest = descriptor_set_digest(digests)
		verify_descriptor_set(resource_docnames, set_digest)
	except ResourceVerifyError as exc:
		_throw(exc.code, exc.message)

	payload_set = (
		((payload.get("resource_registry") or {}).get("descriptor_set_digest"))
		or (payload.get("resource_descriptor_set") or {}).get("digest")
		or payload.get("descriptor_set_digest")
	)
	if payload_set and payload_set != set_digest:
		_throw("BWMF_ELIGIBILITY", "Descriptor-set digest mismatch versus bindings.")

	# Finalization provenance
	if not art.diagnostic_digest:
		_throw("BWMF_ELIGIBILITY", "Finalization provenance incomplete (diagnostic_digest).")

	envelope = json.loads(art.envelope_json or "{}")
	integrity = envelope.get("integrity") or {}
	if integrity.get("final_runtime_manifest") is True:
		_throw("BWMF_ELIGIBILITY", "Artifact incorrectly marked as final_runtime_manifest before publication.")

	warnings = _extract_warnings(payload, envelope)

	return {
		"artifact": art,
		"payload": payload,
		"envelope": envelope,
		"publication_readiness": pr,
		"resources": resources,
		"descriptor_set_digest": set_digest,
		"warnings": warnings,
		"eligible": True,  # derived only; never accept from client
	}


def _extract_warnings(payload: dict[str, Any], envelope: dict[str, Any]) -> list[dict[str, Any]]:
	raw = (
		payload.get("warnings")
		or (payload.get("diagnostics") or {}).get("warnings")
		or envelope.get("warnings")
		or []
	)
	out: list[dict[str, Any]] = []
	for w in raw:
		if not isinstance(w, dict):
			continue
		code = str(w.get("code") or w.get("warning_code") or "WARN")
		fp = str(w.get("fingerprint") or jcs_sha256_digest({"code": code, "message": w.get("message") or ""}))
		out.append(
			{
				"code": code,
				"fingerprint": fp,
				"message": str(w.get("message") or ""),
				"path": str(w.get("path") or ""),
			}
		)
	# Also surface publication_readiness warning codes if present
	pr = payload.get("publication_readiness") or {}
	for code in pr.get("warning_codes") or []:
		fp = jcs_sha256_digest({"code": str(code), "source": "publication_readiness"})
		out.append({"code": str(code), "fingerprint": fp, "message": "", "path": "publication_readiness"})
	# Deduplicate by fingerprint
	seen: set[str] = set()
	deduped: list[dict[str, Any]] = []
	for w in out:
		if w["fingerprint"] in seen:
			continue
		seen.add(w["fingerprint"])
		deduped.append(w)
	return deduped
