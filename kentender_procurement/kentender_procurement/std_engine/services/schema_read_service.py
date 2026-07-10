# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Schema read-model queries for STD Engine (parameters, rules, forms, etc.)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.std_engine.services.envelope import (
	build_error_envelope,
	build_package_context,
	build_read_envelope,
)
from kentender_procurement.std_engine.services.read_service import _load_version, _parse_metadata


def _parameter_business_code(parameter_key: str, object_key: str) -> str:
	for value in (object_key, parameter_key):
		if not value:
			continue
		marker = ".parameter."
		if marker in value:
			return value.split(marker, 1)[1]
	return object_key or parameter_key


def _rule_business_code(rule_key: str, object_key: str) -> str:
	for value in (object_key, rule_key):
		if not value:
			continue
		marker = ".rule."
		if marker in value:
			return value.split(marker, 1)[1]
	return object_key or rule_key


def _render_block_business_code(render_block_key: str, object_key: str) -> str:
	for value in (object_key, render_block_key):
		if not value:
			continue
		for marker in (".render_block.", ".render."):
			if marker in value:
				return value.split(marker, 1)[1]
	return object_key or render_block_key


def _resolve_rule_summaries(rule_keys: list[str]) -> list[dict[str, Any]]:
	summaries: list[dict[str, Any]] = []
	for rule_key in rule_keys:
		lookup = (rule_key or "").strip()
		if not lookup:
			continue
		if not frappe.db.exists("STD Rule", lookup):
			summaries.append(
				{
					"id": lookup,
					"code": _rule_business_code(lookup, ""),
					"name": lookup,
				}
			)
			continue
		row = frappe.db.get_value(
			"STD Rule",
			lookup,
			["rule_key", "object_key", "title", "metadata_json"],
			as_dict=True,
		)
		metadata = _parse_metadata(row.metadata_json)
		summaries.append(
			{
				"id": row.rule_key,
				"code": _rule_business_code(row.rule_key, row.object_key),
				"name": row.title,
				"severity": metadata.get("severity"),
				"ruleType": metadata.get("rule_type"),
				"lifecycleStage": metadata.get("lifecycle_stage"),
			}
		)
	return summaries


def _resolve_render_binding_summaries(binding_keys: list[str]) -> list[dict[str, Any]]:
	summaries: list[dict[str, Any]] = []
	for binding_key in binding_keys:
		lookup = (binding_key or "").strip()
		if not lookup:
			continue
		normalized = lookup.replace(".render.", ".render_block.", 1)
		if frappe.db.exists("STD Render Block", normalized):
			row = frappe.db.get_value(
				"STD Render Block",
				normalized,
				["render_block_key", "object_key", "title", "validation_status"],
				as_dict=True,
			)
			summaries.append(
				{
					"id": row.render_block_key,
					"code": _render_block_business_code(row.render_block_key, row.object_key),
					"name": row.title,
					"validationStatus": row.validation_status,
				}
			)
			continue
		if frappe.db.exists("STD Render Block", lookup):
			row = frappe.db.get_value(
				"STD Render Block",
				lookup,
				["render_block_key", "object_key", "title", "validation_status"],
				as_dict=True,
			)
			summaries.append(
				{
					"id": row.render_block_key,
					"code": _render_block_business_code(row.render_block_key, row.object_key),
					"name": row.title,
					"validationStatus": row.validation_status,
				}
			)
			continue
		summaries.append(
			{
				"id": lookup,
				"code": _render_block_business_code(lookup, ""),
				"name": lookup,
			}
		)
	return summaries


def _parameter_list_item(row: frappe._dict) -> dict[str, Any]:
	metadata = _parse_metadata(row.metadata_json)
	section_key = metadata.get("applies_to_section_key")
	section_title = (
		frappe.db.get_value("STD Section", section_key, "title") if section_key else None
	)
	group_key = metadata.get("group_key") or ""
	group_label = group_key.split(".parameter_group.", 1)[-1] if group_key else None
	validation_rule_keys = metadata.get("validation_rule_keys") or []
	render_binding_keys = metadata.get("render_binding_keys") or []
	applies_to = metadata.get("applies_to") or section_title or "—"
	if section_title and applies_to == "—":
		applies_to = section_title
	return {
		**_identity_summary(row, id_field="parameter_key"),
		"code": _parameter_business_code(row.parameter_key, row.object_key),
		"fieldType": metadata.get("field_type"),
		"sectionTitle": section_title,
		"appliesTo": applies_to,
		"required": bool(metadata.get("required")),
		"defaultValue": metadata.get("default_value"),
		"optionSetKey": metadata.get("option_set_key"),
		"validationRuleCount": len(validation_rule_keys),
		"renderBindingCount": len(render_binding_keys),
		"groupLabel": group_label,
	}


def _rule_is_catalog_active(metadata: dict[str, Any]) -> bool:
	if metadata.get("enabled") is False or metadata.get("active") is False:
		return False
	status = str(metadata.get("catalog_status") or metadata.get("rule_status") or "").strip().upper()
	if status in {"INACTIVE", "DISABLED", "RETIRED", "ARCHIVED"}:
		return False
	return True


def _build_rule_list_summary(items: list[dict[str, Any]]) -> dict[str, int]:
	summary = {
		"total": len(items),
		"blockerRules": 0,
		"warningRules": 0,
		"infoRules": 0,
		"activeRules": 0,
	}
	for item in items:
		severity = str(item.get("severity") or "").upper()
		if severity == "BLOCKER":
			summary["blockerRules"] += 1
		elif severity == "WARNING":
			summary["warningRules"] += 1
		elif severity == "INFO":
			summary["infoRules"] += 1
		if item.get("isActive"):
			summary["activeRules"] += 1
	return summary


def _rule_list_item(row: frappe._dict) -> dict[str, Any]:
	metadata = _parse_metadata(row.metadata_json)
	affected_keys = metadata.get("affected_parameter_keys") or []
	affected_object = affected_keys[0] if affected_keys else metadata.get("affected_object_key") or "—"
	if affected_keys:
		affected_object = _parameter_business_code(affected_keys[0], "") or affected_keys[0]
	return {
		**_identity_summary(row, id_field="rule_key"),
		"code": _rule_business_code(row.rule_key, row.object_key),
		"ruleType": metadata.get("rule_type"),
		"severity": metadata.get("severity"),
		"scope": metadata.get("scope") or metadata.get("applies_to_section_key") or "—",
		"lifecycleStage": metadata.get("lifecycle_stage"),
		"affectedObject": affected_object,
		"affectedParameterKeys": affected_keys,
		"sourceBasis": metadata.get("source_anchor_key") or row.source_anchor or "—",
		"testCoverage": metadata.get("test_coverage") or "—",
		"isActive": _rule_is_catalog_active(metadata),
	}


def _rule_matches_parameter(metadata: dict[str, Any], parameter_key: str) -> bool:
	if not parameter_key:
		return True
	affected_keys = metadata.get("affected_parameter_keys") or []
	return parameter_key in affected_keys


def get_std_version_parameters(package_id: str) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	rows = frappe.get_all(
		"STD Parameter",
		filters={"package_id": package_id},
		fields=["parameter_key", "object_key", "title", "validation_status", "source_anchor", "metadata_json"],
		order_by="title asc",
	)
	return build_read_envelope(
		data={
			"parameters": [_parameter_list_item(row) for row in rows],
			"count": len(rows),
		},
		package_context=build_package_context(version),
		package_id=package_id,
	)


def get_std_version_rules(package_id: str, parameter_key: str | None = None) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	rows = frappe.get_all(
		"STD Rule",
		filters={"package_id": package_id},
		fields=["rule_key", "object_key", "title", "validation_status", "source_anchor", "metadata_json"],
		order_by="title asc",
	)
	filter_key = (parameter_key or "").strip()
	items: list[dict[str, Any]] = []
	for row in rows:
		metadata = _parse_metadata(row.metadata_json)
		if filter_key and not _rule_matches_parameter(metadata, filter_key):
			continue
		items.append(_rule_list_item(row))
	summary = _build_rule_list_summary(items)
	return build_read_envelope(
		data={
			"rules": items,
			"count": summary["total"],
			"summary": summary,
			"filterParameterKey": filter_key or None,
		},
		package_context=build_package_context(version),
		package_id=package_id,
	)


def get_std_rule(rule_key: str) -> dict[str, Any]:
	lookup = (rule_key or "").strip()
	if not lookup or not frappe.db.exists("STD Rule", lookup):
		return build_error_envelope("STD_RULE_NOT_FOUND", f"STD Rule not found: {lookup}")

	doc = frappe.get_doc("STD Rule", lookup)
	version = _load_version(doc.package_id)
	if not version:
		return build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {doc.package_id}")

	metadata = _parse_metadata(doc.metadata_json)
	affected_keys = metadata.get("affected_parameter_keys") or []
	return build_read_envelope(
		data={
			"id": doc.rule_key,
			"code": _rule_business_code(doc.rule_key, doc.object_key),
			"name": doc.title,
			"description": doc.description or metadata.get("message"),
			"validationStatus": doc.validation_status,
			"sourceAnchorId": doc.source_anchor,
			"ruleType": metadata.get("rule_type"),
			"severity": metadata.get("severity"),
			"lifecycleStage": metadata.get("lifecycle_stage"),
			"expression": metadata.get("expression"),
			"expressionLanguage": metadata.get("expression_language"),
			"message": metadata.get("message"),
			"blockingOnPublish": bool(metadata.get("blocking_on_publish")),
			"affectedParameterKeys": affected_keys,
			"sourceAnchorKey": metadata.get("source_anchor_key") or doc.source_anchor,
			"extractionStatus": metadata.get("extraction_status"),
			"metadata": metadata,
		},
		package_context=build_package_context(version),
		package_id=doc.package_id,
	)


def get_std_parameter(parameter_key: str) -> dict[str, Any]:
	lookup = (parameter_key or "").strip()
	if not lookup or not frappe.db.exists("STD Parameter", lookup):
		return build_error_envelope("STD_PARAMETER_NOT_FOUND", f"STD Parameter not found: {lookup}")

	doc = frappe.get_doc("STD Parameter", lookup)
	version = _load_version(doc.package_id)
	if not version:
		return build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {doc.package_id}")

	metadata = _parse_metadata(doc.metadata_json)
	section_key = metadata.get("applies_to_section_key")
	section_title = (
		frappe.db.get_value("STD Section", section_key, "title") if section_key else None
	)
	group_key = metadata.get("group_key") or ""
	group_label = group_key.split(".parameter_group.", 1)[-1] if group_key else None
	validation_rule_keys = metadata.get("validation_rule_keys") or []
	render_binding_keys = metadata.get("render_binding_keys") or []
	validation_rules = _resolve_rule_summaries(validation_rule_keys)
	render_binding_items = _resolve_render_binding_summaries(render_binding_keys)
	return build_read_envelope(
		data={
			"id": doc.parameter_key,
			"code": _parameter_business_code(doc.parameter_key, doc.object_key),
			"name": doc.title or metadata.get("display_label"),
			"description": doc.description,
			"validationStatus": doc.validation_status,
			"sourceAnchorId": doc.source_anchor,
			"fieldType": metadata.get("field_type"),
			"required": bool(metadata.get("required")),
			"defaultValue": metadata.get("default_value"),
			"optionSetKey": metadata.get("option_set_key"),
			"groupKey": group_key,
			"groupLabel": group_label,
			"sectionKey": section_key,
			"sectionTitle": section_title,
			"renderBindings": render_binding_keys,
			"renderBindingItems": render_binding_items,
			"validationRuleKeys": validation_rule_keys,
			"validationRules": validation_rules,
			"sourceAnchorKey": metadata.get("source_anchor_key") or doc.source_anchor,
			"extractionStatus": metadata.get("extraction_status"),
			"metadata": metadata,
		},
		package_context=build_package_context(version),
		package_id=doc.package_id,
	)


def get_std_version_forms(package_id: str) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	rows = frappe.get_all(
		"STD Form Schema",
		filters={"package_id": package_id},
		fields=["form_key", "object_key", "title", "validation_status", "source_anchor"],
		order_by="title asc",
	)
	return _version_list_envelope(version, package_id, list_key="forms", rows=rows, id_field="form_key")


def get_std_form(form_key: str) -> dict[str, Any]:
	key = (form_key or "").strip()
	if not key or not frappe.db.exists("STD Form Schema", key):
		return build_error_envelope("STD_FORM_NOT_FOUND", f"STD form not found: {key}")

	form = frappe.get_doc("STD Form Schema", key)
	version = _load_version(form.package_id)
	if not version:
		return build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {form.package_id}")

	metadata = _parse_metadata(form.metadata_json)
	seen_field_keys: set[str] = set()
	form_fields: list[dict[str, Any]] = []
	for field in sorted(form.form_fields, key=lambda row: int(row.display_order or 0)):
		if field.field_key in seen_field_keys:
			continue
		seen_field_keys.add(field.field_key)
		schema = _parse_metadata(field.field_schema_json)
		form_fields.append(
			{
				"id": field.field_key,
				"code": schema.get("field_code") or field.field_key.split(".")[-1],
				"name": field.field_label,
				"fieldType": field.field_type,
				"isRequired": bool(int(field.is_required or 0)),
				"displayOrder": field.display_order,
				"schema": schema,
			}
		)

	return build_read_envelope(
		data={
			"id": form.form_key,
			"code": metadata.get("form_code") or form.object_key,
			"name": form.title or metadata.get("display_title"),
			"description": form.description,
			"validationStatus": form.validation_status,
			"sourceAnchorId": form.source_anchor,
			"respondentType": metadata.get("respondent_type"),
			"stage": metadata.get("stage"),
			"sectionKey": metadata.get("section_key"),
			"sourceAnchorKey": metadata.get("source_anchor_key") or form.source_anchor,
			"metadata": metadata,
			"formFields": form_fields,
		},
		package_context=build_package_context(version),
		package_id=form.package_id,
	)


def get_std_version_requirements(package_id: str) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	rows = frappe.get_all(
		"STD Requirement Schema",
		filters={"package_id": package_id},
		fields=[
			"requirement_schema_key",
			"object_key",
			"title",
			"validation_status",
			"source_anchor",
		],
		order_by="title asc",
	)
	return _version_list_envelope(
		version,
		package_id,
		list_key="requirements",
		rows=rows,
		id_field="requirement_schema_key",
	)


def get_std_version_price_schedules(package_id: str) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	rows = frappe.get_all(
		"STD Price Schedule Schema",
		filters={"package_id": package_id},
		fields=[
			"price_schedule_schema_key",
			"object_key",
			"title",
			"validation_status",
			"source_anchor",
		],
		order_by="title asc",
	)
	return _version_list_envelope(
		version,
		package_id,
		list_key="priceSchedules",
		rows=rows,
		id_field="price_schedule_schema_key",
	)


def get_std_version_evaluation_schema(package_id: str) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	rows = frappe.get_all(
		"STD Evaluation Schema",
		filters={"package_id": package_id},
		fields=[
			"evaluation_schema_key",
			"object_key",
			"title",
			"validation_status",
			"source_anchor",
		],
		order_by="title asc",
	)
	return build_read_envelope(
		data={
			"schemas": [_identity_summary(row, id_field="evaluation_schema_key") for row in rows],
			"count": len(rows),
		},
		package_context=build_package_context(version),
		package_id=package_id,
	)


def get_std_version_render_blocks(package_id: str) -> dict[str, Any]:
	version, error = _require_version(package_id)
	if error:
		return error

	rows = frappe.get_all(
		"STD Render Block",
		filters={"package_id": package_id},
		fields=["render_block_key", "object_key", "title", "validation_status", "source_anchor"],
		order_by="title asc",
	)
	return build_read_envelope(
		data={
			"renderBlocks": [
				{
					**_identity_summary(row, id_field="render_block_key"),
					"code": _render_block_business_code(row.render_block_key, row.object_key),
				}
				for row in rows
			],
			"count": len(rows),
		},
		package_context=build_package_context(version),
		package_id=package_id,
	)


def _require_version(package_id: str) -> tuple[Any, dict[str, Any] | None]:
	code = (package_id or "").strip()
	version = _load_version(code)
	if not version:
		return None, build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {code}")
	return version, None


def _version_list_envelope(
	version: Any,
	package_id: str,
	*,
	list_key: str,
	rows: list[frappe._dict],
	id_field: str,
) -> dict[str, Any]:
	return build_read_envelope(
		data={
			list_key: [_identity_summary(row, id_field=id_field) for row in rows],
			"count": len(rows),
		},
		package_context=build_package_context(version),
		package_id=package_id,
	)


def _identity_summary(row: frappe._dict, *, id_field: str) -> dict[str, Any]:
	return {
		"id": row.get(id_field),
		"code": row.get("object_key") or row.get(id_field),
		"name": row.get("title"),
		"validationStatus": row.get("validation_status"),
		"sourceAnchorId": row.get("source_anchor"),
	}


def _get_identity_detail(
	*,
	doctype: str,
	key: str,
	not_found_code: str,
	id_field: str,
) -> dict[str, Any]:
	lookup = (key or "").strip()
	if not lookup or not frappe.db.exists(doctype, lookup):
		return build_error_envelope(not_found_code, f"{doctype} not found: {lookup}")

	doc = frappe.get_doc(doctype, lookup)
	version = _load_version(doc.package_id)
	if not version:
		return build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {doc.package_id}")

	return build_read_envelope(
		data={
			"id": getattr(doc, id_field),
			"code": doc.object_key,
			"name": doc.title,
			"description": doc.description,
			"validationStatus": doc.validation_status,
			"sourceAnchorId": doc.source_anchor,
			"metadata": _parse_metadata(doc.metadata_json),
		},
		package_context=build_package_context(version),
		package_id=doc.package_id,
	)
