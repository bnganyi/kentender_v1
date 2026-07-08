# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — project legacy ``package_json`` (manifest/fields/forms/rules) into ``std_config`` reads."""

from __future__ import annotations

from typing import Any

from frappe import _

from kentender_procurement.tender_management.services.std_config_section_schema import (
	normalize_applicability,
	section_default,
)
from kentender_procurement.tender_management.services.std_library_package_projection import (
	resolve_procurement_methods,
	resolve_template_title,
)

VALIDATION_RULE_TYPES = frozenset(
	{
		"VALIDATE_DATE_ORDER",
		"VALIDATE_NUMERIC_LIMIT",
		"VALIDATE_ALLOWED_COMBINATION",
		"WARNING_ONLY",
		"INFO_ONLY",
	}
)

LEGACY_FIELD_GROUP_TO_UI: dict[str, str] = {
	"TENDER_IDENTITY": "tender_identity",
	"DATES_MEETINGS": "timetable",
	"SECURITIES": "bid_security",
	"METHOD_PARTICIPATION": "tender_identity",
	"ALTERNATIVES_LOTS": "lots",
	"QUALIFICATION": "contract_conditions",
	"WORKS_REQUIREMENTS": "delivery_completion",
	"CONTRACT_SCC": "contract_conditions",
	"SYSTEM_AUDIT": "contacts",
}

FIELD_TYPE_TO_UI: dict[str, str] = {
	"TEXT": "Text",
	"LONG_TEXT": "Text",
	"SELECT": "Text",
	"MULTI_SELECT": "Text",
	"BOOLEAN": "Text",
	"INTEGER": "Number",
	"DECIMAL": "Number",
	"MONEY": "Money",
	"PERCENT": "Number",
	"DATE": "Date",
	"DATETIME": "Date/Time",
	"EMAIL": "Text",
	"URL": "Text",
	"ORGANIZATION_REF": "Text",
	"USER_REF": "Text",
	"DURATION_DAYS": "Number",
	"DURATION_MONTHS": "Number",
	"JSON_OBJECT": "Text",
}


def _safe_get(d: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
	cur: Any = d
	for key in keys:
		if not isinstance(cur, dict) or key not in cur:
			return default
		cur = cur[key]
	return cur


def legacy_package_available(package: dict[str, Any] | None) -> bool:
	if not isinstance(package, dict):
		return False
	return isinstance(package.get("manifest"), dict) and bool(_safe_get(package, "fields", "fields"))


def section_is_populated(section: str, data: Any) -> bool:
	if not isinstance(data, dict):
		return False
	if section == "metadata":
		return bool(str(data.get("title") or data.get("short_title") or "").strip())
	if section == "applicability":
		return bool(
			str(data.get("procurement_category") or data.get("procurement_method") or "").strip()
			or len(data.get("rules") or []) > 0
		)
	if section == "tender_fields":
		return len(data.get("fields") or []) > 0
	if section == "supplier_requirements":
		return len(data.get("requirements") or []) > 0
	if section == "forms_and_attachments":
		return len(data.get("forms") or []) > 0 or len(data.get("supplier_forms") or []) > 0
	if section == "evaluation_setup":
		return len(data.get("stages") or data.get("criteria") or []) > 0
	if section == "contract_terms":
		return len(data.get("terms") or []) > 0
	if section == "rules":
		return len(data.get("rules") or []) > 0
	if section == "validations":
		return len(data.get("validations") or []) > 0
	if section == "output_mappings":
		return len(data.get("mappings") or []) > 0
	return bool(data)


def _map_field_type(raw: str) -> str:
	key = str(raw or "").strip().upper()
	return FIELD_TYPE_TO_UI.get(key, "Text")


def _map_field_group(group_code: str) -> str:
	code = str(group_code or "").strip().upper()
	return LEGACY_FIELD_GROUP_TO_UI.get(code, "contract_conditions")


def _project_metadata(package: dict[str, Any], doc: Any = None) -> dict[str, Any]:
	manifest = package.get("manifest") or {}
	classification = manifest.get("classification") or {}
	source = manifest.get("source_document") or {}
	versioning = manifest.get("versioning") or {}
	authority = manifest.get("authority") or {}
	methods = resolve_procurement_methods(doc, package)
	lifecycle = str(getattr(doc, "lifecycle_status", None) or "").strip()
	status = lifecycle or str(_safe_get(manifest, "status", "package_status") or "Imported")
	base = section_default("metadata")
	base.update(
		{
			"title": resolve_template_title(doc, package),
			"short_title": str(manifest.get("template_short_name") or manifest.get("template_name") or "").strip(),
			"description": str(manifest.get("description") or "").strip(),
			"authority": str(authority.get("abbreviation") or authority.get("name") or "PPRA").strip(),
			"document_family": str(classification.get("template_family") or "")
			.replace("_", " ")
			.title()
			.strip()
			or "Works",
			"procurement_category": str(classification.get("procurement_category") or "WORKS")
			.replace("_", " ")
			.title()
			.strip(),
			"procurement_method": methods[0] if methods else "",
			"version_label": str(
				versioning.get("source_version_label") or source.get("revision_label") or ""
			).strip(),
			"effective_date": str(versioning.get("package_version_date") or "").strip(),
			"owner": str(authority.get("name") or "PPRA").strip(),
			"status": status,
			"change_summary": str(source.get("source_treatment") or manifest.get("description") or "").strip(),
		}
	)
	return base


def _project_applicability(package: dict[str, Any], doc: Any = None) -> dict[str, Any]:
	manifest = package.get("manifest") or {}
	classification = manifest.get("classification") or {}
	app = manifest.get("applicability") or {}
	methods = resolve_procurement_methods(doc, package)
	supports_boq = bool(app.get("supports_boq"))
	return normalize_applicability(
		{
			"procurement_category": str(classification.get("procurement_category") or "WORKS")
			.replace("_", " ")
			.title(),
			"procurement_method": methods[0] if methods else "Open Competitive Tendering",
			"contract_type": "Works Contract",
			"works_subtype": "Building Works",
			"entity_scope": "All Entities",
			"currency": "KES",
			"threshold_basis": _("Open tender threshold for Works"),
			"lot_support": bool(app.get("allowed_contract_structures")),
			"test_case": {
				"test_category": "Works",
				"test_method": methods[0] if methods else "",
				"test_subtype": "Building Works",
				"test_entity": "All Entities",
				"test_value": "",
				"test_funding": "",
			},
		}
	)


def _project_tender_fields(package: dict[str, Any]) -> dict[str, Any]:
	rows = list(_safe_get(package, "fields", "fields") or [])
	fields: list[dict[str, Any]] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		code = str(row.get("field_code") or row.get("code") or "").strip()
		label = str(row.get("label") or row.get("field_label") or code).strip()
		group = _map_field_group(str(row.get("group_code") or row.get("group") or ""))
		required = bool(row.get("required_by_default") or row.get("poc_required"))
		fields.append(
			{
				"code": code,
				"label": label,
				"field_type": _map_field_type(str(row.get("field_type") or row.get("type") or "")),
				"required": required,
				"default_value": row.get("default_value"),
				"section": group,
				"group": group,
				"requirement_level": "Always Required" if required else "Optional",
				"fill_mode": "Manual",
				"output_surfaces": ", ".join(row.get("section_targets") or []) or "Tender Pack",
				"system_field": str(code).startswith("SYSTEM."),
			}
		)
	return {"fields": fields}


def _project_supplier_requirements(package: dict[str, Any]) -> dict[str, Any]:
	rows = list(_safe_get(package, "forms", "forms") or [])
	requirements: list[dict[str, Any]] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		code = str(row.get("form_code") or row.get("code") or "").strip()
		name = str(row.get("title") or row.get("label") or code).strip()
		required = bool(row.get("default_required"))
		requirements.append(
			{
				"code": code,
				"name": name,
				"requirement_type": str(row.get("category") or "Form").replace("_", " ").title(),
				"applies_to": str(row.get("respondent_type") or "All Suppliers").replace("_", " "),
				"mandatory": "Yes" if required else "No",
				"blocks_submission": "Yes" if required else "No",
				"used_in_evaluation": "No",
			}
		)
	return {"requirements": requirements}


def _project_forms_and_attachments(package: dict[str, Any]) -> dict[str, Any]:
	rows = list(_safe_get(package, "forms", "forms") or [])
	forms: list[dict[str, Any]] = []
	supplier_forms: list[dict[str, Any]] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		label = str(row.get("title") or row.get("label") or "").strip()
		code = str(row.get("form_code") or row.get("code") or "").strip()
		required = bool(row.get("default_required"))
		forms.append(
			{
				"label": label,
				"purpose": str(row.get("source_reference") or row.get("category") or "").strip(),
				"attachment_type": str(row.get("category") or "SYSTEM FORM").replace("_", " "),
				"source_output": "Imported Package",
				"linked_requirement": label,
				"visible_to_supplier": "After Publication",
				"in_package": "Yes" if required else "Optional",
				"status": "Approved",
			}
		)
		schema_fields = list(row.get("minimum_schema_fields") or [])
		supplier_forms.append(
			{
				"label": label,
				"code": code,
				"description": str(row.get("poc_treatment") or row.get("source_reference") or "").strip(),
				"field_count": len(schema_fields),
				"icon": "description",
			}
		)
	return {"forms": forms, "attachments": [], "supplier_forms": supplier_forms}


def _project_rules(package: dict[str, Any], *, validations: bool = False) -> dict[str, Any]:
	rows = list(_safe_get(package, "rules", "rules") or [])
	out: list[dict[str, Any]] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		rule_type = str(row.get("rule_type") or row.get("type") or "").strip().upper()
		is_validation = rule_type in VALIDATION_RULE_TYPES
		if validations != is_validation:
			continue
		code = str(row.get("rule_code") or row.get("code") or "").strip()
		label = str(row.get("label") or row.get("name") or code).strip()
		payload = {
			"code": code,
			"name": label,
			"when": str(row.get("description") or row.get("message") or "").strip(),
			"then": str(row.get("message") or rule_type).strip(),
			"enabled": bool(row.get("enabled", True)),
			"severity": str(row.get("severity") or "").strip(),
		}
		if validations:
			payload["message"] = str(row.get("message") or label).strip()
			payload["type"] = rule_type.replace("_", " ").title()
		out.append(payload)
	key = "validations" if validations else "rules"
	return {key: out}


def _project_evaluation_setup(package: dict[str, Any]) -> dict[str, Any]:
	sections = list(_safe_get(package, "sections", "sections") or [])
	stages: list[dict[str, Any]] = []
	seq = 0
	for row in sections:
		if not isinstance(row, dict):
			continue
		code = str(row.get("section_code") or "").strip()
		title = str(row.get("title") or code).strip()
		blob = f"{code} {title}".upper()
		if "EVALUATION" not in blob and "QUALIFICATION" not in blob:
			continue
		seq += 1
		stages.append(
			{
				"code": code.lower(),
				"name": title,
				"description": str(row.get("poc_treatment") or row.get("output_behavior") or "").strip(),
				"evaluation_type": "Pass / Fail",
				"stage_type": "Evaluation",
				"sequence": seq,
			}
		)
	if not stages:
		stages = [
			{
				"code": "preliminary",
				"name": "Preliminary Evaluation",
				"description": "Administrative and eligibility checks from imported package rules.",
				"evaluation_type": "Pass / Fail",
				"stage_type": "Preliminary",
				"sequence": 1,
			}
		]
	return {
		"governing_basis": "Weighted Aggregate",
		"method": "Weighted Aggregate",
		"stages": stages,
		"criteria": stages,
		"last_updated": str(_safe_get(package, "manifest", "versioning", "package_version_date") or ""),
	}


def _project_contract_terms(package: dict[str, Any]) -> dict[str, Any]:
	rows = [
		row
		for row in (_safe_get(package, "fields", "fields") or [])
		if isinstance(row, dict) and str(row.get("group_code") or "").upper() == "CONTRACT_SCC"
	]
	terms: list[dict[str, Any]] = []
	for row in rows:
		code = str(row.get("field_code") or "").strip()
		label = str(row.get("label") or code).strip()
		required = bool(row.get("required_by_default") or row.get("poc_required"))
		terms.append(
			{
				"title": label,
				"clause_reference": code,
				"term_type": "Contract Parameter",
				"required": "Yes" if required else "Optional",
				"default_value": str(row.get("default_value") or ""),
				"override_allowed": True,
				"approval_required": False,
				"carries_to_contract": "Yes",
				"visible_to_supplier": "Summary Only",
			}
		)
	return {
		"governing_contract_form": "FIDIC Red Book (Building and Engineering Works)",
		"terms": terms,
		"readiness": [],
	}


def _project_output_mappings(package: dict[str, Any]) -> dict[str, Any]:
	rows = list(_safe_get(package, "render_map", "render_sections") or [])
	mappings: list[dict[str, Any]] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		mappings.append(
			{
				"source": str(row.get("source") or row.get("source_section") or row.get("label") or ""),
				"target_code": str(row.get("target_code") or row.get("target") or ""),
				"target_label": str(row.get("target_label") or row.get("target_name") or ""),
				"generated_element": str(row.get("generated_element") or row.get("output_key") or ""),
				"mandatory": str(row.get("mandatory") or "No"),
				"status": str(row.get("status") or "Valid"),
			}
		)
	return {"mappings": mappings}


_PROJECTORS: dict[str, Any] = {
	"metadata": _project_metadata,
	"applicability": _project_applicability,
	"tender_fields": _project_tender_fields,
	"supplier_requirements": _project_supplier_requirements,
	"forms_and_attachments": _project_forms_and_attachments,
	"evaluation_setup": _project_evaluation_setup,
	"contract_terms": _project_contract_terms,
	"rules": lambda pkg: _project_rules(pkg, validations=False),
	"validations": lambda pkg: _project_rules(pkg, validations=True),
	"output_mappings": _project_output_mappings,
	"ui_schema": lambda _pkg: section_default("ui_schema"),
}


def project_legacy_std_config_section(
	package: dict[str, Any],
	section: str,
	doc: Any = None,
) -> dict[str, Any] | None:
	if not legacy_package_available(package):
		return None
	projector = _PROJECTORS.get(section)
	if not projector:
		return None
	result = projector(package) if section in {"metadata", "applicability"} else projector(package)
	return result if section_is_populated(section, result) else None


def project_legacy_std_config(package: dict[str, Any], doc: Any = None) -> dict[str, Any]:
	out: dict[str, Any] = {}
	if not legacy_package_available(package):
		return out
	for section in _PROJECTORS:
		projected = project_legacy_std_config_section(package, section, doc)
		if projected:
			out[section] = projected
	return out


def effective_std_config_section(
	package: dict[str, Any],
	section: str,
	doc: Any = None,
) -> dict[str, Any]:
	std_config = package.get("std_config")
	stored = std_config.get(section) if isinstance(std_config, dict) else None
	if isinstance(stored, dict) and section_is_populated(section, stored):
		return stored
	projected = project_legacy_std_config_section(package, section, doc)
	if projected:
		return projected
	if isinstance(stored, dict):
		return stored
	return section_default(section)


def effective_std_config(package: dict[str, Any], doc: Any = None) -> dict[str, Any]:
	std_config = package.get("std_config")
	base = dict(std_config) if isinstance(std_config, dict) else {}
	projected = project_legacy_std_config(package, doc)
	for section, payload in projected.items():
		if not section_is_populated(section, base.get(section)):
			base[section] = payload
	return base
