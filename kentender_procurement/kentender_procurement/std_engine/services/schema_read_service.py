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


_PRICE_SCHEDULE_CODE_MAP = {
	"GRAND_SUMMARY_COST_TABLE": "GS-001",
	"SUPPLY_INSTALL_COST_SUMMARY": "SIC-SUM",
	"RECURRENT_COST_SUMMARY": "REC-SUM",
	"SUPPLY_INSTALL_COST_SUB_TABLE": "SIC-DET-01",
	"RECURRENT_COST_SUB_TABLE": "REC-DET-01",
	"COUNTRY_OF_ORIGIN_CODE_TABLE": "COO-001",
}

_IT_PRICE_SCHEDULE_SEMANTIC = {
	"IT-PRICE-01": "GRAND_SUMMARY_COST_TABLE",
	"IT-PRICE-02": "SUPPLY_INSTALL_COST_SUMMARY",
	"IT-PRICE-03": "RECURRENT_COST_SUMMARY",
	"IT-PRICE-04": "SUPPLY_INSTALL_COST_SUB_TABLE",
	"IT-PRICE-05": "RECURRENT_COST_SUB_TABLE",
	"IT-PRICE-06": "COUNTRY_OF_ORIGIN_CODE_TABLE",
}


_PRICE_SCHEDULE_PROFILES: dict[str, dict[str, str]] = {
	"GRAND_SUMMARY_COST_TABLE": {
		"subtitle": "All costs consolidated",
		"pricingBasis": "Aggregated Total",
		"currencyPolicy": "Multi-Currency",
		"taxPolicy": "Included / Detail",
		"recurrentCost": "Aggregated",
		"formulaRule": "Summation of Sub-Schedules",
		"evalLinkage": "EVAL_FINAL",
		"contractCarry": "Contract Base",
	},
	"SUPPLY_INSTALL_COST_SUMMARY": {
		"subtitle": "Summary from Sub-Tables",
		"pricingBasis": "Lump Sum",
		"currencyPolicy": "Contractual",
		"taxPolicy": "VAT Separated",
		"recurrentCost": "N/A",
		"formulaRule": "Sum(SIC-DET-*)",
		"evalLinkage": "→ GS-001",
		"contractCarry": "Payment Milestone",
	},
	"RECURRENT_COST_SUMMARY": {
		"subtitle": "5-Year operational costs",
		"pricingBasis": "Unit Rate",
		"currencyPolicy": "Contractual",
		"taxPolicy": "Duty Free",
		"recurrentCost": "Operational (5Y)",
		"formulaRule": "NPV(REC-DET-*)",
		"evalLinkage": "→ GS-001",
		"contractCarry": "SLA Link",
	},
	"SUPPLY_INSTALL_COST_SUB_TABLE": {
		"subtitle": "Itemized component breakdown",
		"pricingBasis": "Line Item",
		"currencyPolicy": "Item-Level",
		"taxPolicy": "Inclusive",
		"recurrentCost": "N/A",
		"formulaRule": "Unit Price * Qty",
		"evalLinkage": "→ SIC-SUM",
		"contractCarry": "Asset Registry",
	},
	"RECURRENT_COST_SUB_TABLE": {
		"subtitle": "SLA and maintenance detail",
		"pricingBasis": "Time & Material",
		"currencyPolicy": "Item-Level",
		"taxPolicy": "VAT Exempt",
		"recurrentCost": "Operational (5Y)",
		"formulaRule": "Rate * Duration",
		"evalLinkage": "→ REC-SUM",
		"contractCarry": "SLA Pricing",
	},
	"COUNTRY_OF_ORIGIN_CODE_TABLE": {
		"subtitle": "Compliance & origin tracking",
		"pricingBasis": "Non-Financial",
		"currencyPolicy": "N/A",
		"taxPolicy": "N/A",
		"recurrentCost": "N/A",
		"formulaRule": "Validation Check",
		"evalLinkage": "Validator",
		"contractCarry": "Provenance",
	},
}


def _resolve_price_schedule_semantic_key(schedule_code: str) -> str:
	code = (schedule_code or "").strip().upper()
	if code in _IT_PRICE_SCHEDULE_SEMANTIC:
		return _IT_PRICE_SCHEDULE_SEMANTIC[code]
	return code


def _price_schedule_business_code(schedule_code: str, object_key: str) -> str:
	semantic_key = _resolve_price_schedule_semantic_key(schedule_code)
	if semantic_key in _PRICE_SCHEDULE_CODE_MAP:
		return _PRICE_SCHEDULE_CODE_MAP[semantic_key]
	code = (schedule_code or "").strip().upper()
	if code in _PRICE_SCHEDULE_CODE_MAP:
		return _PRICE_SCHEDULE_CODE_MAP[code]
	for value in (object_key or "").split("."):
		if value.startswith("price."):
			suffix = value.split("price.", 1)[1]
			return suffix.replace("_", "-").upper()[:12]
	return object_key or schedule_code


def _format_price_source_anchor(anchor_key: str | None) -> str:
	anchor = (anchor_key or "").strip()
	if not anchor:
		return "—"
	if ".anchor." in anchor:
		return "#" + anchor.split(".anchor.", 1)[1].replace("_", "-").upper()
	return anchor


def _price_schedule_validation_label(validation_status: str | None) -> str:
	status = (validation_status or "").strip().upper()
	if "BLOCKER" in status or status in {"INVALID", "FAILED"}:
		return "BLOCKER"
	if "WARNING" in status:
		return "WARNING"
	return "VALID"


def _price_schedule_list_item(row: frappe._dict, *, lifecycle_state: str) -> dict[str, Any]:
	metadata = _parse_metadata(row.metadata_json)
	schedule_code = str(metadata.get("schedule_code") or "").strip().upper()
	semantic_key = _resolve_price_schedule_semantic_key(schedule_code)
	profile = _PRICE_SCHEDULE_PROFILES.get(semantic_key, {})
	required = metadata.get("required")
	if required is None:
		required = profile.get("required", False)
	return {
		"id": row.get("price_schedule_schema_key"),
		"code": _price_schedule_business_code(schedule_code, row.get("object_key") or ""),
		"name": row.get("title") or metadata.get("display_title") or row.get("object_key"),
		"description": row.get("description") or profile.get("subtitle") or "",
		"required": bool(required),
		"pricingBasis": profile.get("pricingBasis", "—"),
		"currencyPolicy": profile.get("currencyPolicy", "—"),
		"taxPolicy": profile.get("taxPolicy", "—"),
		"recurrentCost": profile.get("recurrentCost", "—"),
		"formulaRule": profile.get("formulaRule", "—"),
		"evalLinkage": profile.get("evalLinkage", "—"),
		"contractCarry": profile.get("contractCarry", "—"),
		"validationStatus": _price_schedule_validation_label(row.get("validation_status")),
		"lifecycleState": lifecycle_state or "ACTIVE",
		"sourceAnchorId": _format_price_source_anchor(
			row.get("source_anchor") or metadata.get("source_anchor_key")
		),
	}


def _build_price_schedule_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
	total_summaries = sum(
		1
		for item in items
		if "summary" in str(item.get("code") or "").lower()
		or "SUM" in str(item.get("code") or "")
	)
	return {
		"priceSchedules": len(items),
		"totalSummaries": total_summaries,
		"evaluationLinksLocked": "100%" if items else "0%",
		"contractBindings": len(items),
	}


def _form_list_item(row: frappe._dict) -> dict[str, Any]:
	metadata = _parse_metadata(row.metadata_json)
	activation_rules = metadata.get("activation_rule_keys") or []
	return {
		"id": row.get("form_key"),
		"code": metadata.get("form_code") or row.get("object_key"),
		"name": row.get("title") or metadata.get("display_title") or row.get("object_key"),
		"description": row.get("description") or "",
		"respondentType": metadata.get("respondent_type") or "—",
		"stage": metadata.get("stage") or "—",
		"required": metadata.get("required", True),
		"fieldCount": frappe.db.count("STD Form Field", {"parent": row.get("form_key")}),
		"evidenceCount": metadata.get("evidence_count", 0),
		"activationRules": activation_rules[0] if activation_rules else "—",
		"sourceAnchorId": _format_price_source_anchor(
			row.get("source_anchor") or metadata.get("source_anchor_key")
		),
		"validationStatus": row.get("validation_status"),
	}


def _requirement_list_item(row: frappe._dict) -> dict[str, Any]:
	metadata = _parse_metadata(row.metadata_json)
	requirement_class = (
		metadata.get("requirement_class")
		or metadata.get("requirementClass")
		or metadata.get("category")
		or "REQUIREMENT"
	)
	return {
		"id": row.get("requirement_schema_key"),
		"code": row.get("object_key") or row.get("requirement_schema_key"),
		"name": row.get("title") or metadata.get("display_title") or row.get("object_key"),
		"category": metadata.get("category") or row.get("title") or row.get("object_key"),
		"requirementClass": requirement_class,
		"requirementType": metadata.get("requirement_type")
		or metadata.get("requirementType")
		or metadata.get("type")
		or "—",
		"required": metadata.get("required", True),
		"responseRequired": metadata.get("response_required")
		or metadata.get("responseRequired")
		or "—",
		"complianceResponseType": metadata.get("compliance_response_type")
		or metadata.get("complianceResponseType")
		or "—",
		"evalLinkage": metadata.get("eval_linkage")
		or metadata.get("evalLinkage")
		or metadata.get("evaluation_linkage")
		or "—",
		"contractCarryForward": bool(
			metadata.get("contract_carry_forward", metadata.get("contractCarryForward", True))
		),
		"sourceAnchorId": _format_price_source_anchor(
			row.get("source_anchor") or metadata.get("source_anchor_key")
		),
		"validationStatus": _price_schedule_validation_label(row.get("validation_status")),
	}


def _render_block_list_item(row: frappe._dict, *, lifecycle_state: str) -> dict[str, Any]:
	metadata = _parse_metadata(row.metadata_json)
	validation = _price_schedule_validation_label(row.get("validation_status"))
	return {
		"id": row.get("render_block_key"),
		"code": _render_block_business_code(row.get("render_block_key"), row.get("object_key")),
		"name": row.get("title") or metadata.get("display_title") or row.get("object_key"),
		"documentArea": metadata.get("document_area") or metadata.get("section_title") or "—",
		"clauseBinding": metadata.get("clause_binding") or metadata.get("section_key") or "—",
		"sourceDataObject": metadata.get("source_data_object") or metadata.get("parameter_key") or "—",
		"requiredLabel": "Required" if metadata.get("required", True) else "Conditional",
		"format": metadata.get("format") or metadata.get("output_format") or "—",
		"lastRenderTest": metadata.get("last_render_test") or "SUCCESS",
		"validationStatus": validation,
		"lifecycleState": lifecycle_state or "ACTIVE",
		"sourceAnchorId": _format_price_source_anchor(
			row.get("source_anchor") or metadata.get("source_anchor_key")
		),
	}


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


def _derive_validation_rule_keys_for_parameter(parameter_key: str, package_id: str) -> list[str]:
	lookup = (parameter_key or "").strip()
	if not lookup or not package_id:
		return []
	rows = frappe.get_all(
		"STD Rule",
		filters={"package_id": package_id},
		fields=["rule_key", "metadata_json"],
		order_by="rule_key asc",
	)
	keys: list[str] = []
	for row in rows:
		metadata = _parse_metadata(row.metadata_json)
		if _rule_matches_parameter(metadata, lookup):
			keys.append(row.rule_key)
	return keys


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
	if not validation_rule_keys:
		validation_rule_keys = _derive_validation_rule_keys_for_parameter(lookup, doc.package_id)
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
			"verificationStatus": metadata.get("verification_status") or doc.validation_status,
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
			"sourceText": metadata.get("source_text"),
			"sourceTextHash": metadata.get("source_text_hash"),
			"normalizedTextHash": doc.content_hash or metadata.get("normalized_text_hash"),
			"sourcePageStart": metadata.get("source_page_start"),
			"sourcePageEnd": metadata.get("source_page_end"),
			"paragraphHint": metadata.get("paragraph_hint"),
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
		fields=[
			"form_key",
			"object_key",
			"title",
			"description",
			"validation_status",
			"source_anchor",
			"metadata_json",
		],
		order_by="title asc",
	)
	items = [_form_list_item(row) for row in rows]
	return build_read_envelope(
		data={"forms": items, "count": len(items)},
		package_context=build_package_context(version),
		package_id=package_id,
	)


def _form_field_display_name(field, schema: dict[str, Any]) -> str:
	label = (field.field_label or "").strip()
	if label and label != field.field_key:
		return label
	return (
		schema.get("field_label")
		or schema.get("display_label")
		or field.field_key.rsplit(".", 1)[-1]
	)


def _form_field_display_order(field, schema: dict[str, Any]) -> int:
	if field.display_order:
		return int(field.display_order)
	raw = schema.get("ordinal") or schema.get("display_order")
	return int(raw or 0)


def _form_field_row_rank(field, schema: dict[str, Any]) -> tuple[int, int]:
	short_key = field.field_key.rsplit(".", 1)[-1]
	name = _form_field_display_name(field, schema)
	has_human_label = int(name not in {field.field_key, short_key})
	return (has_human_label, _form_field_display_order(field, schema))


def get_std_form(form_key: str) -> dict[str, Any]:
	key = (form_key or "").strip()
	if not key or not frappe.db.exists("STD Form Schema", key):
		return build_error_envelope("STD_FORM_NOT_FOUND", f"STD form not found: {key}")

	form = frappe.get_doc("STD Form Schema", key)
	version = _load_version(form.package_id)
	if not version:
		return build_error_envelope("STD_VERSION_NOT_FOUND", f"STD version not found: {form.package_id}")

	metadata = _parse_metadata(form.metadata_json)
	best_by_key: dict[str, tuple[tuple[int, int], Any, dict[str, Any]]] = {}
	for field in form.form_fields:
		schema = _parse_metadata(field.field_schema_json)
		rank = _form_field_row_rank(field, schema)
		prev = best_by_key.get(field.field_key)
		if not prev or rank > prev[0]:
			best_by_key[field.field_key] = (rank, field, schema)

	form_fields: list[dict[str, Any]] = []
	for _, field, schema in sorted(best_by_key.values(), key=lambda item: _form_field_display_order(item[1], item[2])):
		form_fields.append(
			{
				"id": field.field_key,
				"code": schema.get("field_code") or field.field_key.split(".")[-1],
				"name": _form_field_display_name(field, schema),
				"fieldType": field.field_type,
				"isRequired": bool(int(field.is_required or 0)),
				"displayOrder": _form_field_display_order(field, schema),
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
			"metadata_json",
		],
		order_by="title asc",
	)
	items = [_requirement_list_item(row) for row in rows]
	return build_read_envelope(
		data={"requirements": items, "count": len(items)},
		package_context=build_package_context(version),
		package_id=package_id,
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
			"description",
			"validation_status",
			"source_anchor",
			"metadata_json",
		],
		order_by="title asc",
	)
	lifecycle_state = str(getattr(version, "lifecycle_state", None) or "ACTIVE")
	items = [_price_schedule_list_item(row, lifecycle_state=lifecycle_state) for row in rows]
	summary = _build_price_schedule_summary(items)
	return build_read_envelope(
		data={
			"priceSchedules": items,
			"count": len(items),
			"summary": summary,
		},
		package_context=build_package_context(version),
		package_id=package_id,
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
		fields=[
			"render_block_key",
			"object_key",
			"title",
			"validation_status",
			"source_anchor",
			"metadata_json",
		],
		order_by="title asc",
	)
	lifecycle_state = str(getattr(version, "lifecycle_state", None) or "ACTIVE")
	items = [_render_block_list_item(row, lifecycle_state=lifecycle_state) for row in rows]
	return build_read_envelope(
		data={
			"renderBlocks": items,
			"count": len(items),
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
