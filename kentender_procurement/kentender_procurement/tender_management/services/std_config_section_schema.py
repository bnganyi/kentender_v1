# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — canonical ``package_json.std_config`` section shapes for configurator UI.

Each section defines defaults, UI-facing field keys, and normalize/expand helpers so
tab renderers read a merged view while persistence stays consistent.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

FUNDING_SOURCE_KEYS: tuple[str, ...] = (
	"gok_exchequer",
	"internal_revenue",
	"donor_funded",
	"mixed_funding",
)

ENTITY_SCOPE_OPTIONS: tuple[str, ...] = (
	"All Entities",
	"Specific MDA",
	"Counties Only",
	"State Corporations",
)


def metadata_default() -> dict[str, Any]:
	return {
		"title": "",
		"short_title": "",
		"description": "",
		"authority": "",
		"document_family": "",
		"procurement_category": "",
		"procurement_method": "",
		"version_label": "",
		"effective_date": "",
		"owner": "",
		"status": "",
		"change_summary": "",
		"funding_sources": {key: False for key in FUNDING_SOURCE_KEYS},
	}


def applicability_default() -> dict[str, Any]:
	return {
		"procurement_category": "",
		"procurement_method": "",
		"contract_type": "",
		"works_subtype": "",
		"entity_scope": "All Entities",
		"entity_codes": [],
		"funding_source": "",
		"funding_sources": {key: False for key in FUNDING_SOURCE_KEYS},
		"currency": "KES",
		"threshold_basis": "",
		"min_value": "",
		"max_value": "",
		"lot_support": False,
		"test_case": {},
		"rules": [],
	}


def tender_fields_default() -> dict[str, Any]:
	return {"fields": []}


def supplier_requirements_default() -> dict[str, Any]:
	return {"requirements": []}


def forms_and_attachments_default() -> dict[str, Any]:
	return {"forms": [], "attachments": [], "supplier_forms": []}


def evaluation_setup_default() -> dict[str, Any]:
	return {
		"governing_basis": "Weighted Aggregate",
		"method": "Weighted Aggregate",
		"stages": [],
		"criteria": [],
		"last_updated": "",
	}


def contract_terms_default() -> dict[str, Any]:
	return {
		"governing_contract_form": "FIDIC Red Book",
		"terms": [],
		"readiness": [],
	}


def rules_default() -> dict[str, Any]:
	return {"rules": []}


def validations_default() -> dict[str, Any]:
	return {"validations": []}


SECTION_DEFAULTS: dict[str, dict[str, Any]] = {
	"metadata": metadata_default(),
	"applicability": applicability_default(),
	"tender_fields": tender_fields_default(),
	"supplier_requirements": supplier_requirements_default(),
	"forms_and_attachments": forms_and_attachments_default(),
	"evaluation_setup": evaluation_setup_default(),
	"contract_terms": contract_terms_default(),
	"rules": rules_default(),
	"validations": validations_default(),
	"ui_schema": {"tabs": []},
	"output_mappings": {"mappings": []},
}


def section_default(section: str) -> dict[str, Any]:
	base = SECTION_DEFAULTS.get(section)
	if base is None:
		return {}
	return deepcopy(base)


def _merge_dict(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
	out = deepcopy(base)
	for key, val in incoming.items():
		if isinstance(val, dict) and isinstance(out.get(key), dict):
			out[key] = _merge_dict(out[key], val)
		else:
			out[key] = val
	return out


def _primary_rule(data: dict[str, Any]) -> dict[str, Any]:
	rules = data.get("rules") or []
	if rules and isinstance(rules[0], dict):
		return rules[0]
	return {}


def expand_applicability(data: dict[str, Any]) -> dict[str, Any]:
	"""Merge flat editor fields with primary rule for UI reads."""
	base = applicability_default()
	merged = _merge_dict(base, data if isinstance(data, dict) else {})
	rule = _primary_rule(merged)
	for key in (
		"procurement_category",
		"procurement_method",
		"contract_type",
		"works_subtype",
		"entity_scope",
		"funding_source",
		"min_value",
		"max_value",
		"lot_support",
	):
		if not merged.get(key) and rule.get(key) is not None:
			merged[key] = rule.get(key)
	if not merged.get("entity_codes") and rule.get("entity_codes"):
		merged["entity_codes"] = list(rule.get("entity_codes") or [])
	if isinstance(rule.get("funding_sources"), dict):
		merged["funding_sources"] = _merge_dict(merged.get("funding_sources") or {}, rule["funding_sources"])
	return merged


def normalize_applicability(data: dict[str, Any]) -> dict[str, Any]:
	"""Persist flat editor fields into primary rule + section root."""
	merged = expand_applicability(data if isinstance(data, dict) else {})
	rules = list(merged.get("rules") or [])
	primary = dict(_primary_rule(merged))
	for key in (
		"procurement_category",
		"procurement_method",
		"contract_type",
		"works_subtype",
		"entity_scope",
		"funding_source",
		"min_value",
		"max_value",
		"lot_support",
	):
		if merged.get(key) not in (None, ""):
			primary[key] = merged.get(key)
	if merged.get("entity_codes"):
		primary["entity_codes"] = list(merged.get("entity_codes") or [])
	if isinstance(merged.get("funding_sources"), dict):
		primary["funding_sources"] = merged["funding_sources"]
	if not primary.get("code"):
		primary["code"] = "RULE-PRIMARY"
	if not primary.get("name"):
		primary["name"] = "Primary applicability rule"
	primary["active"] = True
	if rules:
		rules[0] = primary
	else:
		rules = [primary]
	out = {k: merged.get(k) for k in applicability_default().keys()}
	out["rules"] = rules
	return out


def expand_metadata(data: dict[str, Any]) -> dict[str, Any]:
	base = metadata_default()
	return _merge_dict(base, data if isinstance(data, dict) else {})


def normalize_metadata(data: dict[str, Any]) -> dict[str, Any]:
	merged = expand_metadata(data if isinstance(data, dict) else {})
	funding = merged.get("funding_sources")
	if not isinstance(funding, dict):
		merged["funding_sources"] = {key: False for key in FUNDING_SOURCE_KEYS}
	return merged


def expand_evaluation_setup(data: dict[str, Any]) -> dict[str, Any]:
	base = evaluation_setup_default()
	merged = _merge_dict(base, data if isinstance(data, dict) else {})
	if not merged.get("governing_basis") and merged.get("method"):
		merged["governing_basis"] = merged["method"]
	if not merged.get("stages") and merged.get("criteria"):
		merged["stages"] = list(merged["criteria"])
	return merged


def normalize_evaluation_setup(data: dict[str, Any]) -> dict[str, Any]:
	merged = expand_evaluation_setup(data if isinstance(data, dict) else {})
	merged["method"] = merged.get("governing_basis") or merged.get("method") or ""
	merged["criteria"] = list(merged.get("stages") or merged.get("criteria") or [])
	return merged


def expand_section(section: str, data: Any) -> dict[str, Any]:
	if not isinstance(data, dict):
		return section_default(section)
	if section == "metadata":
		return expand_metadata(data)
	if section == "applicability":
		return expand_applicability(data)
	if section == "evaluation_setup":
		return expand_evaluation_setup(data)
	base = section_default(section)
	return _merge_dict(base, data)


def normalize_section(section: str, data: Any) -> dict[str, Any]:
	if not isinstance(data, dict):
		return section_default(section)
	if section == "metadata":
		return normalize_metadata(data)
	if section == "applicability":
		return normalize_applicability(data)
	if section == "evaluation_setup":
		return normalize_evaluation_setup(data)
	base = section_default(section)
	return _merge_dict(base, data)


def evaluate_applicability(data: dict[str, Any], test_case: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Return applicability test result for simulator UI."""
	expanded = expand_applicability(data)
	case = test_case or expanded.get("test_case") or {}
	checks = {
		"category": not expanded.get("procurement_category")
		or str(case.get("test_category") or case.get("procurement_category") or "")
		in ("", str(expanded.get("procurement_category") or "")),
		"method": not expanded.get("procurement_method")
		or str(case.get("test_method") or case.get("procurement_method") or "")
		in ("", str(expanded.get("procurement_method") or "")),
	}
	applies = all(checks.values())
	return {
		"applies": applies,
		"checks": checks,
		"summary": expanded,
		"test_case": case,
	}


def ui_fixture_std_config() -> dict[str, Any]:
	"""Fully populated std_config for UI/Playwright (matches mockup sample data)."""
	return {
		"metadata": {
			"title": "Standard Tender Document for Building Works",
			"short_title": "Building Works STD",
			"description": "PPRA standard tender document for building and associated civil engineering works.",
			"authority": "PPRA",
			"document_family": "Works",
			"procurement_category": "Works",
			"procurement_method": "Open Tender",
			"version_label": "2.1",
			"effective_date": "2024-06-01",
			"owner": "Procurement Governance Unit",
			"status": "Draft",
			"change_summary": "Structural updates to Section III (Evaluation) to include environmental sustainability scoring.",
			"funding_sources": {
				"gok_exchequer": True,
				"internal_revenue": True,
				"donor_funded": False,
				"mixed_funding": False,
			},
		},
		"applicability": normalize_applicability(
			{
				"procurement_category": "Works",
				"procurement_method": "Open Tender",
				"contract_type": "Works Contract",
				"works_subtype": "Building Works",
				"entity_scope": "All Entities",
				"entity_codes": ["Ministry of Health", "Ministry of Education"],
				"funding_source": "GoK / Exchequer",
				"funding_sources": {
					"gok_exchequer": True,
					"internal_revenue": True,
					"donor_funded": False,
					"mixed_funding": False,
				},
				"currency": "KES",
				"threshold_basis": "Open Tender threshold for Works",
				"min_value": "6000000",
				"max_value": "",
				"lot_support": True,
				"test_case": {
					"test_category": "Works",
					"test_method": "Open Tender",
					"test_subtype": "Building Works",
					"test_entity": "Ministry of Health",
					"test_value": "98000000",
					"test_funding": "GoK",
				},
			}
		),
		"tender_fields": {
			"fields": [
				{
					"code": "tender_title",
					"label": "Tender Title",
					"field_type": "Text",
					"required": True,
					"default_value": "",
					"section": "tender_identity",
					"group": "tender_identity",
					"requirement_level": "Always Required",
					"fill_mode": "Manual",
					"output_surfaces": "Supplier Portal, Tender Notice, Bid Submission",
					"system_field": False,
				},
				{
					"code": "tender_reference",
					"label": "Tender Reference",
					"field_type": "Text",
					"required": True,
					"default_value": "AUTO_GEN",
					"section": "tender_identity",
					"group": "tender_identity",
					"requirement_level": "System Generated",
					"fill_mode": "Auto-generated",
					"output_surfaces": "Supplier Portal, Tender Notice, Bid Submission",
					"system_field": True,
				},
				{
					"code": "submission_deadline",
					"label": "Submission Deadline",
					"field_type": "Date/Time",
					"required": True,
					"default_value": "",
					"section": "timetable",
					"group": "timetable",
					"requirement_level": "Always Required",
					"fill_mode": "Manual",
					"output_surfaces": "Supplier Portal, Tender Notice, Bid Submission",
					"system_field": True,
				},
			]
		},
		"supplier_requirements": {
			"requirements": [
				{
					"code": "FORM_OF_TENDER",
					"name": "Form of Tender",
					"requirement_type": "Form",
					"applies_to": "All Suppliers",
					"mandatory": "Yes",
					"blocks_submission": "Yes",
					"used_in_evaluation": "No",
				},
				{
					"code": "BID_SECURITY",
					"name": "Bid Security",
					"requirement_type": "Document",
					"applies_to": "All Suppliers",
					"mandatory": "Yes",
					"blocks_submission": "Yes",
					"used_in_evaluation": "No",
				},
			]
		},
		"forms_and_attachments": {
			"forms": [
				{
					"label": "Standard Tender Document",
					"purpose": "Main tender document",
					"attachment_type": "PDF",
					"source_output": "System Generated",
					"linked_requirement": "",
					"visible_to_supplier": "Internal Only",
					"in_package": "Yes",
					"status": "Approved",
				},
				{
					"label": "Form of Tender",
					"purpose": "Supplier bid submission",
					"attachment_type": "SYSTEM FORM",
					"source_output": "System Generated",
					"linked_requirement": "Form of Tender requirement",
					"visible_to_supplier": "After Publication",
					"in_package": "Yes",
					"status": "Approved",
				},
			],
			"attachments": [],
			"supplier_forms": [
				{"label": "Company Profile", "code": "company_profile"},
				{"label": "Compliance Declaration", "code": "compliance_declaration"},
			],
		},
		"evaluation_setup": normalize_evaluation_setup(
			{
				"governing_basis": "Weighted Aggregate",
				"last_updated": "2023-10-24T14:30:00",
				"stages": [
					{
						"code": "preliminary",
						"name": "Preliminary Evaluation",
						"evaluation_type": "Pass / Fail",
						"weight": "",
						"minimum_score": "",
					},
					{
						"code": "technical",
						"name": "Technical Evaluation",
						"evaluation_type": "Scored",
						"weight": "70",
						"minimum_score": "75",
					},
					{
						"code": "financial",
						"name": "Financial Evaluation",
						"evaluation_type": "Lowest evaluated responsive bid",
						"weight": "30",
						"minimum_score": "",
					},
					{
						"code": "post_qual",
						"name": "Post-Qualification",
						"evaluation_type": "Pass / Fail",
						"weight": "",
						"minimum_score": "",
					},
				],
			}
		),
		"contract_terms": {
			"governing_contract_form": "FIDIC Red Book",
			"terms": [
				{
					"title": "Performance Security",
					"clause_reference": "FIDIC Red Book Clause 4.2",
					"term_type": "Financial",
					"required": "Yes",
					"default_value": "10% of Contract Price",
					"override_allowed": True,
					"approval_required": True,
					"carries_to_contract": True,
					"visible_to_supplier": True,
				},
				{
					"title": "Advance Payment",
					"clause_reference": "FIDIC Red Book Clause 14.2",
					"term_type": "Financial",
					"required": "Conditional",
					"default_value": "Up to 20%",
					"override_allowed": True,
					"approval_required": True,
					"carries_to_contract": False,
					"visible_to_supplier": True,
				},
			],
			"readiness": [
				{"key": "mandatory_terms", "label": "Mandatory terms defined", "status": "ok"},
				{"key": "defaults", "label": "Default values validated", "status": "ok"},
				{"key": "overrides", "label": "Approval-required overrides documented", "status": "warn"},
			],
		},
		"rules": {
			"rules": [
				{
					"when": "Bid security is required",
					"then": "Supplier must upload bid security document",
				}
			]
		},
		"validations": {
			"validations": [
				{"code": "PUBLICATION_PERIOD", "message": "Publication period must meet minimum days for Open Tender"}
			]
		},
		"ui_schema": {"tabs": []},
		"output_mappings": {"mappings": []},
	}
