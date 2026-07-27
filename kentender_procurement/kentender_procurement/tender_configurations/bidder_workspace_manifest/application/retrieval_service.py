# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Exact verified retrieval of published BWMF Manifest Versions (Phase 5)."""

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
	DT_MANIFEST_PUBLICATION,
	DT_MANIFEST_RESOURCE_BINDING,
	DT_MANIFEST_VERSION,
	DT_TENDER_PUBLICATION_STATE,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.cas import (
	get_verified,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.canonical import (
	descriptor_set_digest,
)


def retrieve_published_manifest(
	*,
	published_tender_ref: str | None = None,
	published_tender_version: int | None = None,
	manifest_id: str | None = None,
	manifest_version: int | None = None,
	publication_id: str | None = None,
	active_only: bool = False,
) -> dict[str, Any]:
	"""Return immutable published envelope + exact verified resource bindings.

	Does not connect to bidder checklist / workspace runtime (Phase 6).
	"""
	mv_name = None
	pub = None

	if publication_id:
		pub = frappe.get_doc(DT_MANIFEST_PUBLICATION, {"publication_id": publication_id})
		mv_name = pub.manifest_version
	elif active_only and published_tender_ref:
		lineage = frappe.db.get_value(
			DT_TENDER_PUBLICATION_STATE,
			{"published_tender_ref": published_tender_ref, "public_active": 1},
			["active_manifest_version", "active_publication"],
			as_dict=True,
		)
		if not lineage or not lineage.active_manifest_version:
			frappe.throw(_("No active publication for tender."), title="BWMF_RETRIEVE_MISSING")
		mv_name = lineage.active_manifest_version
		if lineage.active_publication:
			pub = frappe.get_doc(DT_MANIFEST_PUBLICATION, lineage.active_publication)
	elif manifest_id is not None and manifest_version is not None:
		mv_name = frappe.db.get_value(
			DT_MANIFEST_VERSION,
			{"manifest_id": manifest_id, "manifest_version": int(manifest_version)},
			"name",
		)
	elif published_tender_ref is not None and published_tender_version is not None:
		mv_name = frappe.db.get_value(
			DT_MANIFEST_VERSION,
			{
				"published_tender_ref": published_tender_ref,
				"published_tender_version": int(published_tender_version),
			},
			"name",
		)

	if not mv_name:
		frappe.throw(_("Published manifest not found."), title="BWMF_RETRIEVE_MISSING")

	mv = frappe.get_doc(DT_MANIFEST_VERSION, mv_name)
	if mv.lifecycle_state not in {"Published", "Superseded", "Cancelled"}:
		frappe.throw(_("Manifest is not a published-track version."), title="BWMF_RETRIEVE_STATE")

	payload = json.loads(mv.payload_json)
	if jcs_sha256_digest(payload) != mv.payload_digest:
		frappe.throw(_("Published payload digest corruption."), title="BWMF_RETRIEVE_CORRUPT")

	bindings = frappe.get_all(
		DT_MANIFEST_RESOURCE_BINDING,
		filters={"manifest_version": mv.name},
		fields=[
			"name",
			"binding_id",
			"resource_id",
			"resource_docname",
			"resource_version_key",
			"resource_digest",
			"content_ref",
			"schema_ref",
			"schema_version",
			"item_count",
			"descriptor_order",
			"binding_digest",
		],
		order_by="descriptor_order asc",
	)
	if not bindings:
		frappe.throw(_("Published manifest has no resource bindings."), title="BWMF_RETRIEVE_CORRUPT")

	resolved: list[dict[str, Any]] = []
	digests: list[str] = []
	docnames: list[str] = []
	for b in bindings:
		try:
			verify_resource_row(b.resource_docname)
			get_verified(b.content_ref)
		except (ResourceVerifyError, frappe.ValidationError, Exception):
			frappe.throw(
				_("Missing or corrupt published resource {0}.").format(b.resource_id),
				title="BWMF_RETRIEVE_CORRUPT",
			)
		digests.append(b.resource_digest)
		docnames.append(b.resource_docname)
		resolved.append(dict(b))

	try:
		verify_descriptor_set(docnames, descriptor_set_digest(digests))
	except ResourceVerifyError:
		frappe.throw(_("Published descriptor-set digest mismatch."), title="BWMF_RETRIEVE_CORRUPT")
	payload_set = ((payload.get("resource_registry") or {}).get("descriptor_set_digest")) or ""
	if payload_set and payload_set != descriptor_set_digest(digests):
		frappe.throw(_("Published descriptor-set digest mismatch."), title="BWMF_RETRIEVE_CORRUPT")

	if not pub:
		pub_name = frappe.db.get_value(DT_MANIFEST_PUBLICATION, {"manifest_version": mv.name}, "name")
		if pub_name:
			pub = frappe.get_doc(DT_MANIFEST_PUBLICATION, pub_name)

	envelope = json.loads(mv.envelope_json)
	return {
		"manifest_id": mv.manifest_id,
		"manifest_version": int(mv.manifest_version),
		"lifecycle_state": mv.lifecycle_state,
		"payload_digest": mv.payload_digest,
		"envelope": envelope,
		"payload": payload,
		"publication_id": pub.publication_id if pub else "",
		"published_tender_ref": mv.published_tender_ref,
		"published_tender_version": int(mv.published_tender_version or mv.manifest_version),
		"approval_decision": (pub.approval_decision if pub else "") or "",
		"resources": resolved,
		"bidder_workspace_cutover": False,
	}
