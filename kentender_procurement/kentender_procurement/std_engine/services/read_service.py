# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Core read-model queries for STD Engine."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.std_engine.services.envelope import (
	build_error_envelope,
	build_package_context,
	build_read_envelope,
)
from kentender_procurement.std_engine.services.library_kpi_service import (
	build_library_kpi_summary,
)


def get_std_families() -> dict[str, Any]:
	families = frappe.get_all(
		"STD Family",
		fields=["name", "family_code", "family_name", "authority_code", "procurement_category"],
		order_by="family_name asc",
	)
	items: list[dict[str, Any]] = []
	package_context = None
	for family in families:
		versions = frappe.get_all(
			"STD Version",
			filters={"family_code": family.family_code},
			fields=[
				"package_id",
				"version_code",
				"lifecycle_state",
				"activation_allowed",
				"ui_mode",
				"validation_status",
				"package_quality",
				"is_immutable",
			],
			order_by="modified desc",
		)
		latest = versions[0] if versions else None
		if latest and package_context is None:
			package_context = build_package_context(latest)
		items.append(
			{
				"familyCode": family.family_code,
				"familyName": family.family_name,
				"authorityCode": family.authority_code,
				"procurementCategory": family.procurement_category,
				"versionCount": len(versions),
				"latestPackageId": latest.package_id if latest else None,
			}
		)
	library_summary = build_library_kpi_summary()
	return build_read_envelope(
		data={
			"families": items,
			"libraryKpis": library_summary["kpis"],
			"libraryHealth": library_summary["health"],
		},
		package_context=package_context,
	)


def get_std_family(family_code: str) -> dict[str, Any]:
	code = (family_code or "").strip()
	if not code or not frappe.db.exists("STD Family", code):
		return build_error_envelope("STD_FAMILY_NOT_FOUND", f"STD family not found: {code}")

	family = frappe.get_doc("STD Family", code)
	versions = frappe.get_all(
		"STD Version",
		filters={"family_code": code},
		fields=[
			"package_id",
			"version_code",
			"version_label",
			"lifecycle_state",
			"activation_allowed",
			"ui_mode",
			"validation_status",
			"package_quality",
			"is_immutable",
		],
		order_by="modified desc",
	)
	package_context = build_package_context(versions[0]) if versions else None
	return build_read_envelope(
		data={
			"familyCode": family.family_code,
			"familyName": family.family_name,
			"authorityCode": family.authority_code,
			"procurementCategory": family.procurement_category,
			"versions": [
				{
					"packageId": row.package_id,
					"versionCode": row.version_code,
					"versionLabel": row.version_label,
					"lifecycleState": row.lifecycle_state,
					"activationAllowed": bool(int(row.activation_allowed or 0)),
					"uiMode": row.ui_mode,
					"validationStatus": row.validation_status,
					"packageQuality": row.package_quality,
					"immutable": bool(int(row.is_immutable or 0)),
				}
				for row in versions
			],
		},
		package_context=package_context,
		package_id=versions[0].package_id if versions else None,
	)


def get_std_version(package_id: str) -> dict[str, Any]:
	version = _load_version(package_id)
	if not version:
		return build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {package_id}")

	package_context = build_package_context(version)
	return build_read_envelope(
		data={
			"packageId": version.package_id,
			"familyCode": version.family_code,
			"versionCode": version.version_code,
			"versionLabel": version.version_label,
			"lifecycleState": version.lifecycle_state,
			"activationAllowed": bool(int(version.activation_allowed or 0)),
			"uiMode": version.ui_mode,
			"packageQuality": version.package_quality,
			"validationStatus": version.validation_status,
			"packageSha256": version.package_sha256,
			"manifestHash": version.manifest_hash,
			"sourceAuthority": version.source_authority,
			"immutable": bool(int(version.is_immutable or 0)),
		},
		package_context=package_context,
		package_id=version.package_id,
	)


def get_std_version_source_traceability(package_id: str) -> dict[str, Any]:
	version = _load_version(package_id)
	if not version:
		return build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {package_id}")

	source_documents = frappe.get_all(
		"STD Source Document",
		filters={"package_id": package_id},
		fields=[
			"name",
			"source_document_key",
			"filename",
			"source_hash",
			"file_path",
			"source_role",
			"page_count",
		],
		order_by="source_role asc, filename asc",
	)
	anchors = frappe.get_all(
		"STD Source Anchor",
		filters={"package_id": package_id},
		fields=[
			"name",
			"anchor_key",
			"source_document",
			"section_ref",
			"clause_ref",
			"page_from",
			"page_to",
		],
		order_by="page_from asc, anchor_key asc",
	)
	package_context = build_package_context(version)
	return build_read_envelope(
		data={
			"sourceDocuments": [
				{
					"id": row.source_document_key,
					"code": row.source_document_key.split(".")[-1],
					"name": row.filename,
					"role": row.source_role,
					"hash": row.source_hash,
					"filePath": row.file_path,
					"pageCount": row.page_count,
				}
				for row in source_documents
			],
			"anchors": [
				{
					"id": row.anchor_key,
					"code": row.clause_ref or row.section_ref or row.anchor_key,
					"name": row.anchor_key,
					"sourceDocumentId": row.source_document,
					"sectionRef": row.section_ref,
					"clauseRef": row.clause_ref,
					"pageFrom": row.page_from,
					"pageTo": row.page_to,
				}
				for row in anchors
			],
		},
		package_context=package_context,
		package_id=package_id,
	)


def get_std_version_sections(package_id: str) -> dict[str, Any]:
	version = _load_version(package_id)
	if not version:
		return build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {package_id}")

	sections = frappe.get_all(
		"STD Section",
		filters={"package_id": package_id},
		fields=[
			"name",
			"section_key",
			"object_key",
			"title",
			"section_number",
			"parent_section",
			"source_anchor",
		],
		order_by="section_number asc, title asc",
	)
	clauses = frappe.get_all(
		"STD Clause",
		filters={"package_id": package_id},
		fields=["name", "clause_key", "object_key", "title", "section", "source_anchor"],
		order_by="title asc",
	)
	clause_counts: dict[str, int] = {}
	for clause in clauses:
		section_id = clause.section or ""
		clause_counts[section_id] = clause_counts.get(section_id, 0) + 1

	package_context = build_package_context(version)
	return build_read_envelope(
		data={
			"sections": [
				{
					"id": row.section_key,
					"code": row.section_number or row.object_key,
					"name": row.title,
					"parentSectionId": row.parent_section,
					"sourceAnchorId": row.source_anchor,
					"clauseCount": clause_counts.get(row.name, 0),
				}
				for row in sections
			],
			"clauses": [
				{
					"id": row.clause_key,
					"code": row.object_key,
					"name": row.title,
					"sectionId": row.section,
					"sourceAnchorId": row.source_anchor,
				}
				for row in clauses
			],
		},
		package_context=package_context,
		package_id=package_id,
	)


def get_std_clause(clause_key: str) -> dict[str, Any]:
	key = (clause_key or "").strip()
	if not key or not frappe.db.exists("STD Clause", key):
		return build_error_envelope("STD_CLAUSE_NOT_FOUND", f"STD clause not found: {key}")

	clause = frappe.get_doc("STD Clause", key)
	version = _load_version(clause.package_id)
	if not version:
		return build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {clause.package_id}")

	metadata = _parse_metadata(clause.metadata_json)
	package_context = build_package_context(version)
	return build_read_envelope(
		data={
			"id": clause.clause_key,
			"code": clause.object_key,
			"name": clause.title,
			"sectionId": clause.section,
			"description": clause.description,
			"validationStatus": clause.validation_status,
			"sourceAnchorId": clause.source_anchor,
			"clauseText": clause.clause_text,
			"metadata": metadata,
		},
		package_context=package_context,
		package_id=clause.package_id,
	)


def _load_version(package_id: str) -> frappe._dict | None:
	code = (package_id or "").strip()
	if not code or not frappe.db.exists("STD Version", code):
		return None
	return frappe.get_doc("STD Version", code).as_dict()


def _parse_metadata(raw: str | None) -> dict[str, Any]:
	if not raw:
		return {}
	try:
		parsed = json.loads(raw)
	except json.JSONDecodeError:
		return {}
	return parsed if isinstance(parsed, dict) else {}
