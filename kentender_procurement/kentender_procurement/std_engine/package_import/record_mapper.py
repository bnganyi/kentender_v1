# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Map STD seed package JSON records to Frappe DocType payloads."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kentender_procurement.std_engine.constants import (
	COMMIT_TARGET_STATE_M1,
	FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION,
	PACKAGE_QUALITY_RECONCILED_DRAFT,
	UI_MODE_READ_ONLY_INSPECTION,
)
from kentender_procurement.std_engine.package_import.import_planner import _should_skip_source_document
from kentender_procurement.std_engine.package_import.package_reader import PackageInspectionResult


@dataclass(frozen=True)
class PackageContext:
	package_id: str
	family_code: str
	version_code: str


def package_context_from_inspection(inspection: PackageInspectionResult) -> PackageContext:
	return PackageContext(
		package_id=inspection.package_id,
		family_code=inspection.family_code,
		version_code=inspection.version_code,
	)


def metadata_json(record: dict[str, Any]) -> str:
	return json.dumps(record, sort_keys=True, default=str)


def map_family_record(record: dict[str, Any]) -> dict[str, Any]:
	return {
		"doctype": "STD Family",
		"family_code": record["family_code"],
		"family_name": record.get("family_name") or record["family_code"],
		"authority_code": record.get("authority_code") or "PPRA",
		"procurement_category": record.get("procurement_category") or "IT",
		"metadata_json": metadata_json(record),
	}


def map_version_record(
	record: dict[str, Any],
	ctx: PackageContext,
	*,
	package_sha256: str,
	manifest_hash: str,
	inspection: PackageInspectionResult,
) -> dict[str, Any]:
	manifest = inspection.manifest
	return {
		"doctype": "STD Version",
		"package_id": ctx.package_id,
		"family_code": ctx.family_code,
		"version_code": ctx.version_code,
		"version_label": record.get("version_label"),
		"lifecycle_state": COMMIT_TARGET_STATE_M1,
		"activation_allowed": int(bool(manifest.get("activation_allowed"))),
		"ui_mode": UI_MODE_READ_ONLY_INSPECTION,
		"is_immutable": 0,
		"package_sha256": package_sha256,
		"manifest_hash": manifest_hash,
		"package_quality": manifest.get("package_quality")
		or manifest.get("quality_status")
		or PACKAGE_QUALITY_RECONCILED_DRAFT,
		"validation_status": "OPEN",
		"source_authority": record.get("source_authority"),
		"metadata_json": metadata_json(record),
	}


def map_source_document_record(
	record: dict[str, Any],
	ctx: PackageContext,
	*,
	pdf_path: Path,
	source_hash: str,
) -> dict[str, Any]:
	return {
		"doctype": "STD Source Document",
		"package_id": ctx.package_id,
		"family_code": ctx.family_code,
		"version_code": ctx.version_code,
		"source_document_key": record["source_document_key"],
		"filename": pdf_path.name,
		"source_hash": source_hash,
		"file_path": str(pdf_path.resolve()),
		"source_role": record.get("role"),
		"metadata_json": metadata_json(record),
	}


def map_source_anchor_record(record: dict[str, Any], ctx: PackageContext) -> dict[str, Any]:
	return {
		"doctype": "STD Source Anchor",
		"package_id": ctx.package_id,
		"family_code": ctx.family_code,
		"version_code": ctx.version_code,
		"anchor_key": record["source_anchor_key"],
		"source_document": record["source_document_key"],
		"section_ref": record.get("section_code"),
		"clause_ref": record.get("anchor_code"),
		"page_from": record.get("official_print_page_start"),
		"page_to": record.get("official_print_page_end"),
		"metadata_json": metadata_json(record),
	}


def map_section_record(record: dict[str, Any], ctx: PackageContext) -> dict[str, Any]:
	doc = {
		"doctype": "STD Section",
		"package_id": ctx.package_id,
		"family_code": ctx.family_code,
		"version_code": ctx.version_code,
		"section_key": record["section_key"],
		"object_key": record.get("section_code") or record["section_key"],
		"title": record.get("display_title"),
		"validation_status": record.get("activation_status") or record.get("extraction_status"),
		"section_number": record.get("section_code"),
		"metadata_json": metadata_json(record),
	}
	if record.get("source_anchor_key"):
		doc["source_anchor"] = record["source_anchor_key"]
	if record.get("parent_section_key"):
		doc["parent_section"] = record["parent_section_key"]
	return doc


def map_clause_record(record: dict[str, Any], ctx: PackageContext) -> dict[str, Any]:
	full_text = record.get("full_clause_text") or record.get("clause_text") or ""
	doc = {
		"doctype": "STD Clause",
		"package_id": ctx.package_id,
		"family_code": ctx.family_code,
		"version_code": ctx.version_code,
		"clause_key": record["clause_key"],
		"section": record["section_key"],
		"object_key": record.get("clause_code") or record["clause_key"],
		"title": record.get("display_title") or record.get("clause_title"),
		"clause_text": full_text,
		"content_hash": record.get("normalized_text_hash") or record.get("content_hash"),
		"validation_status": record.get("text_status") or record.get("extraction_status") or record.get("extraction_pass"),
		"metadata_json": metadata_json(record),
	}
	if record.get("source_anchor_key"):
		doc["source_anchor"] = record["source_anchor_key"]
	return doc


def map_identity_record(
	record: dict[str, Any],
	ctx: PackageContext,
	*,
	doctype: str,
	key_field: str,
	record_key: str,
	title_field: str | None = None,
	status_field: str | None = None,
	anchor_field: str = "source_anchor_key",
) -> dict[str, Any]:
	doc = {
		"doctype": doctype,
		"package_id": ctx.package_id,
		"family_code": ctx.family_code,
		"version_code": ctx.version_code,
		key_field: record[record_key],
		"object_key": record.get(record_key.replace("_key", "_code")) or record[record_key],
		"title": record.get(title_field) if title_field else None,
		"validation_status": record.get(status_field) if status_field else record.get("status"),
		"metadata_json": metadata_json(record),
	}
	if record.get(anchor_field):
		doc["source_anchor"] = record[anchor_field]
	return doc


def map_parameter_record(record: dict[str, Any], ctx: PackageContext) -> dict[str, Any]:
	return map_identity_record(
		record,
		ctx,
		doctype="STD Parameter",
		key_field="parameter_key",
		record_key="parameter_key",
		title_field="display_label",
		status_field="extraction_status",
	)


def map_rule_record(record: dict[str, Any], ctx: PackageContext) -> dict[str, Any]:
	return map_identity_record(
		record,
		ctx,
		doctype="STD Rule",
		key_field="rule_key",
		record_key="rule_key",
		title_field="message",
		status_field="extraction_status",
	)


def map_form_record(
	record: dict[str, Any],
	ctx: PackageContext,
	*,
	form_fields: list[dict[str, Any]],
) -> dict[str, Any]:
	doc = map_identity_record(
		record,
		ctx,
		doctype="STD Form Schema",
		key_field="form_key",
		record_key="form_key",
		title_field="display_title",
		status_field="extraction_status",
	)
	doc["form_fields"] = [
		{
			"doctype": "STD Form Field",
			"field_key": field["field_key"],
			"field_label": field.get("field_label") or field.get("display_label") or field["field_key"],
			"field_type": field.get("field_type") or "text",
			"is_required": int(bool(field.get("required"))),
			"display_order": field.get("ordinal") or field.get("display_order"),
			"field_schema_json": metadata_json(field),
		}
		for field in form_fields
	]
	return doc


def map_requirement_record(record: dict[str, Any], ctx: PackageContext) -> dict[str, Any]:
	return map_identity_record(
		record,
		ctx,
		doctype="STD Requirement Schema",
		key_field="requirement_schema_key",
		record_key="schema_key",
		status_field="status",
		anchor_field="",
	)


def map_price_schedule_record(record: dict[str, Any], ctx: PackageContext) -> dict[str, Any]:
	return map_identity_record(
		record,
		ctx,
		doctype="STD Price Schedule Schema",
		key_field="price_schedule_schema_key",
		record_key="price_schedule_key",
		title_field="display_title",
		status_field="status",
	)


def map_evaluation_record(record: dict[str, Any], ctx: PackageContext) -> dict[str, Any]:
	return map_identity_record(
		record,
		ctx,
		doctype="STD Evaluation Schema",
		key_field="evaluation_schema_key",
		record_key="evaluation_schema_key",
		status_field="status",
	)


def map_render_block_record(record: dict[str, Any], ctx: PackageContext) -> dict[str, Any]:
	return map_identity_record(
		record,
		ctx,
		doctype="STD Render Block",
		key_field="render_block_key",
		record_key="render_block_key",
		title_field="display_title",
		status_field="template_status",
	)


def map_usage_binding_record(record: dict[str, Any], ctx: PackageContext) -> dict[str, Any]:
	test_key = record["test_key"]
	return {
		"doctype": "STD Usage Binding",
		"package_id": ctx.package_id,
		"family_code": ctx.family_code,
		"version_code": ctx.version_code,
		"binding_key": test_key,
		"fixture_source": FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION,
		"tender_ref": record.get("tender_ref"),
		"binding_status": record.get("status") or "FIXTURE",
		"metadata_json": metadata_json(
			{
				"testKey": test_key,
				"displayTitle": record.get("display_title"),
				"category": record.get("category"),
				"expectedResult": record.get("expected_result"),
				"fixtureSource": FIXTURE_SOURCE_SMOKE_TEST_EXPECTATION,
			}
		),
	}


def importable_source_documents(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
	if not payload:
		return []
	records = payload.get("records") or []
	return [record for record in records if not _should_skip_source_document(record)]
