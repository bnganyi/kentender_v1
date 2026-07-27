# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Server-side resource verifier — fail closed with stable diagnostic codes."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.ordering import (
	sort_by_keys,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_MANIFEST_RESOURCE,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.cas import (
	assert_valid_content_ref,
	content_ref_for_bytes,
	get_verified,
	physical_digest_for_bytes,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.chunking import (
	validate_chunks,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.canonical import (
	descriptor_set_digest,
	logical_resource_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.item_schemas import (
	FORBIDDEN_ITEM_KEYS,
	NSSF_RESOURCE_SPECS,
)


class ResourceVerifyError(Exception):
	def __init__(self, code: str, message: str):
		self.code = code
		self.message = message
		super().__init__(f"{code}: {message}")


def _resolve_resource_doc(resource_ref: str):
	"""Accept document name or resource_id (latest single match)."""
	if frappe.db.exists(DT_MANIFEST_RESOURCE, resource_ref):
		return frappe.get_doc(DT_MANIFEST_RESOURCE, resource_ref)
	names = frappe.get_all(
		DT_MANIFEST_RESOURCE, filters={"resource_id": resource_ref}, pluck="name"
	)
	if not names:
		raise ResourceVerifyError("BWMF_RESOURCE_MISSING", f"missing resource {resource_ref}")
	if len(names) > 1:
		raise ResourceVerifyError(
			"BWMF_RESOURCE_MISSING",
			f"ambiguous resource_id {resource_ref}; pass document name",
		)
	return frappe.get_doc(DT_MANIFEST_RESOURCE, names[0])


def verify_resource_row(
	resource_ref: str,
	*,
	expected_schema_ref: str | None = None,
	expected_schema_version: str | None = None,
	expected_fields: tuple[str, ...] | None = None,
	expected_content_ref: str | None = None,
	expected_physical_digest: str | None = None,
	enforce_order: bool = True,
) -> dict[str, Any]:
	doc = _resolve_resource_doc(resource_ref)
	spec = NSSF_RESOURCE_SPECS.get(doc.resource_id)
	schema_ref = doc.schema_ref or ""
	schema_version = doc.schema_version or ""
	if not schema_ref or not schema_version:
		raise ResourceVerifyError("BWMF_RESOURCE_SCHEMA", "unknown schema or version")
	if expected_schema_ref is not None and schema_ref != expected_schema_ref:
		raise ResourceVerifyError("BWMF_RESOURCE_SCHEMA", "unknown schema")
	if expected_schema_version is not None and schema_version != expected_schema_version:
		raise ResourceVerifyError("BWMF_RESOURCE_SCHEMA", "wrong schema version")
	if spec:
		if schema_ref != spec["schema_ref"]:
			raise ResourceVerifyError("BWMF_RESOURCE_SCHEMA", "unknown schema")
		if schema_version != spec["schema_version"]:
			raise ResourceVerifyError("BWMF_RESOURCE_SCHEMA", "wrong schema version")

	ordering = json.loads(doc.ordering_contract_json or "[]")
	if not ordering or not all(isinstance(k, str) and k for k in ordering):
		raise ResourceVerifyError("BWMF_RESOURCE_ORDER", "unreconstructable ordering contract")
	source_refs = json.loads(doc.source_refs_json or "[]")
	if not source_refs:
		raise ResourceVerifyError("BWMF_RESOURCE_LINEAGE", "missing source lineage")

	allowed_fields = expected_fields
	if allowed_fields is None and spec:
		allowed_fields = tuple(spec["fields"])

	items: list[dict[str, Any]] = []
	raw_bytes: bytes | None = None
	if doc.storage_mode == "content_addressed":
		if not doc.content_ref:
			raise ResourceVerifyError("BWMF_CAS_REF", "missing content_ref")
		try:
			assert_valid_content_ref(doc.content_ref)
			raw_bytes = get_verified(doc.content_ref)
		except ResourceVerifyError:
			raise
		except Exception as exc:
			title = getattr(exc, "title", None) or "BWMF_CAS_REF"
			if title in {"BWMF_CAS_MISSING", "BWMF_CAS_CORRUPT", "BWMF_CAS_REF"}:
				raise ResourceVerifyError(title, str(exc)) from exc
			raise ResourceVerifyError("BWMF_CAS_REF", "incorrect deterministic content_ref") from exc
		items = json.loads(raw_bytes.decode("utf-8"))
		actual_phys = physical_digest_for_bytes(raw_bytes)
		if doc.physical_object_digest and doc.physical_object_digest != actual_phys:
			raise ResourceVerifyError("BWMF_CAS_CORRUPT", "physical object digest mismatch")
		if expected_physical_digest and expected_physical_digest != actual_phys:
			raise ResourceVerifyError("BWMF_CAS_CORRUPT", "physical object digest mismatch")
		actual_ref = content_ref_for_bytes(raw_bytes)
		if doc.content_ref != actual_ref:
			raise ResourceVerifyError("BWMF_CAS_REF", "incorrect deterministic content_ref")
		if expected_content_ref and expected_content_ref != doc.content_ref:
			raise ResourceVerifyError("BWMF_CAS_REF", "incorrect deterministic content_ref")
	elif doc.storage_mode == "inline":
		items = json.loads(doc.content_json or "[]")
	elif doc.storage_mode == "content_addressed_chunked":
		chunks = json.loads(doc.chunks_json or "[]")
		try:
			validate_chunks(chunks, expected_item_count=int(doc.item_count), verify_bytes=True)
		except ValueError as exc:
			raise ResourceVerifyError("BWMF_CHUNK_INVALID", str(exc)) from exc
		except Exception as exc:
			code = getattr(exc, "http_status_code", None)
			title = getattr(exc, "title", None) or "BWMF_CHUNK_INVALID"
			if title in {"BWMF_CAS_MISSING", "BWMF_CAS_CORRUPT", "BWMF_CAS_REF"}:
				raise ResourceVerifyError(title, str(exc)) from exc
			raise ResourceVerifyError("BWMF_CHUNK_INVALID", str(exc)) from exc
		for ch in chunks:
			part = json.loads(get_verified(ch["content_ref"]).decode("utf-8"))
			items.extend(part)
	else:
		raise ResourceVerifyError("BWMF_RESOURCE_SCHEMA", f"unknown storage_mode {doc.storage_mode}")

	if len(items) != int(doc.item_count):
		raise ResourceVerifyError(
			"BWMF_RESOURCE_COUNT",
			f"expected {doc.item_count} got {len(items)}",
		)

	id_key = ordering[-1] if ordering else None
	ids: list[Any] = []
	for row in items:
		if not isinstance(row, dict):
			raise ResourceVerifyError("BWMF_RESOURCE_SCHEMA", "item not object")
		for k in row:
			if k in FORBIDDEN_ITEM_KEYS:
				raise ResourceVerifyError("BWMF_RESOURCE_SCHEMA", f"forbidden item property {k}")
			if allowed_fields is not None and k not in allowed_fields:
				raise ResourceVerifyError("BWMF_RESOURCE_SCHEMA", f"unknown item property {k}")
		if allowed_fields is not None:
			for req in allowed_fields:
				if req not in row:
					raise ResourceVerifyError(
						"BWMF_RESOURCE_SCHEMA",
						f"missing required item property {req}",
					)
		if id_key:
			ident = row.get(id_key)
			if ident in ids:
				raise ResourceVerifyError("BWMF_RESOURCE_DUP_ID", f"duplicate {id_key}={ident}")
			ids.append(ident)

	if enforce_order:
		try:
			reordered = sort_by_keys(list(items), tuple(ordering))
		except Exception as exc:
			raise ResourceVerifyError("BWMF_RESOURCE_ORDER", "unreconstructable ordering contract") from exc
		if reordered != items:
			raise ResourceVerifyError("BWMF_RESOURCE_ORDER", "reordered logical items")

	actual_digest = logical_resource_digest(items)
	if actual_digest != doc.resource_digest:
		raise ResourceVerifyError("BWMF_RESOURCE_DIGEST", "logical digest mismatch")

	return {
		"resource_id": doc.resource_id,
		"resource_docname": doc.name,
		"item_count": len(items),
		"resource_digest": actual_digest,
		"content_ref": doc.content_ref or "",
		"physical_object_digest": doc.physical_object_digest or "",
		"items": items,
	}


def verify_descriptor_set(
	resource_refs: list[str],
	expected_set_digest: str,
) -> str:
	digests = []
	for ref in resource_refs:
		info = verify_resource_row(ref)
		digests.append(info["resource_digest"])
	actual = descriptor_set_digest(digests)
	if actual != expected_set_digest:
		raise ResourceVerifyError("BWMF_DESCRIPTOR_SET", "descriptor-set digest mismatch")
	return actual


def verify_sections_reference_resources(sections: list[dict[str, Any]], resource_ids: set[str]) -> None:
	for sec in sections:
		for ref in sec.get("resource_refs") or []:
			if ref not in resource_ids:
				raise ResourceVerifyError(
					"BWMF_SECTION_RESOURCE",
					f"section {sec.get('section_key')} references absent resource {ref}",
				)


def assert_candidates_cover_preview(
	preview_candidates: list[dict[str, Any]],
	resource_ids: list[str],
) -> None:
	preview_ids = {
		c.get("resource_id") or c.get("candidate_id") for c in preview_candidates
	}
	for rid in resource_ids:
		if rid not in preview_ids:
			raise ResourceVerifyError(
				"BWMF_CANDIDATE_ABSENT",
				f"resource candidate absent from the preview artifact: {rid}",
			)
