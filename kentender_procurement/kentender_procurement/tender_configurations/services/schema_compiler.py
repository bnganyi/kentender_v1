# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Compile electronic bidder submission schema from Tender Configuration + pack 10 template.

Runtime schema is derived from CFG blobs (190 matrix, 22 price lines, prelim/techqual)
merged with pack 10 section templates and validation_rules. Never treat NSSF as master STD.

Non-authoritative for the bidder checklist: lean A2 reads
``IT Tender Publication Record.electronic_template_snapshot`` only.
``SECTION_KEYS`` below are retained for wizard/preview compile paths, not checklist authority.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.services.e1_nssf_fixture_mapper import (
	load_schema_10,
	map_all_cfg_blobs,
	map_bidder_submission_schema,
)

# Pack-10 keys — NOT the lean bidder checklist authority (see electronic_std_templates.CANONICAL_SECTION_KEYS).
SECTION_KEYS = (
	"tender_document_acknowledgement",
	"form_of_tender",
	"confidential_business_questionnaire",
	"preliminary_documents",
	"technical_qualification",
	"technical_compliance_matrix",
	"implementation_plan",
	"price_schedule",
	"contract_terms_acknowledgement",
	"final_declaration_and_submit",
)

RESPONSE_FIELDS_PER_REQUIREMENT = (
	{"field_key": "compliant_yes_no", "label": "Compliant (Yes/No)", "type": "text", "required": True},
	{
		"field_key": "compliance_statement",
		"label": "Compliance statement",
		"type": "narrative",
		"required": True,
	},
	{"field_key": "reference_pages", "label": "Reference pages", "type": "text", "required": False},
	{"field_key": "evidence_uploads", "label": "Evidence uploads", "type": "file", "required": False},
	{
		"field_key": "deviation_note_if_any",
		"label": "Deviation note (if any)",
		"type": "narrative",
		"required": False,
	},
)


def _parse_json_field(raw: Any) -> Any:
	if raw is None or raw == "":
		return None
	if isinstance(raw, (dict, list)):
		return raw
	try:
		return json.loads(raw)
	except (TypeError, ValueError):
		return None


def _canonical_hash(payload: dict[str, Any]) -> str:
	blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
	return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _matrix_row_from_requirement(row: dict[str, Any]) -> dict[str, Any]:
	rid = cstr(row.get("requirement_id") or "").strip()
	title = cstr(row.get("title") or "").strip()
	desc = cstr(row.get("description") or "").strip()
	fmt = cstr(row.get("bidder_response_format") or "").strip()
	# Map CFG format back to fixture-ish response type labels for schema consumers
	if fmt == "Compliance statement" and "Evidence required" in cstr(
		row.get("evidence_requirement") or ""
	):
		brt = "compliance_statement_plus_evidence_upload"
	elif "reference" in cstr(row.get("bidder_response_instruction") or "").lower():
		brt = "yes_no_plus_reference_pages_and_compliance_statement"
	elif fmt == "Yes/No confirmation":
		brt = "yes_no_plus_compliance_statement"
	else:
		brt = "yes_no_plus_reference_pages_and_compliance_statement"
	return {
		"id": rid,
		"requirement_id": rid,
		"requirement_title": title,
		"requirement_statement": desc.split("\n\n")[0] if desc else title,
		"mandatory": True,
		"bidder_response_type": brt,
		"category_label": cstr(row.get("category_label") or "").strip(),
	}


def _price_line_from_item(row: dict[str, Any]) -> dict[str, Any]:
	item_id = cstr(row.get("item_id") or "").strip()
	name = cstr(row.get("item_name") or "").strip()
	basis = cstr(row.get("pricing_basis") or "").strip()
	model = (
		"unit_cost_and_total_cost"
		if basis == "Unit price"
		else "total_cost_only"
	)
	return {
		"line_id": item_id,
		"module_or_item": name,
		"bidder_field_model": model,
		"unit_cost_required": model == "unit_cost_and_total_cost",
		"total_cost_required": True,
		"currency": cstr(row.get("currency") or "KES").strip() or "KES",
		"quantity": cstr(row.get("quantity") or "1").strip(),
		"unit": cstr(row.get("unit") or "Lot").strip(),
	}


def _eval_requirements(criteria: list[dict[str, Any]], *, stage: str, basis: str) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for row in criteria:
		if cstr(row.get("stage") or "") != stage:
			continue
		if cstr(row.get("evaluation_basis") or "") != basis:
			continue
		cid = cstr(row.get("criterion_id") or "").strip()
		out.append(
			{
				"id": cid,
				"criterion": cstr(row.get("criterion_name") or "").strip(),
				"requirement": cstr(row.get("pass_fail_rule") or "Mandatory").strip(),
				"supporting_documentation": cstr(row.get("evidence_instruction") or "").strip(),
				"mandatory": True,
				"bidder_schema": (
					"upload_or_e_declaration"
					if stage == "Preliminary"
					else "structured_response_plus_upload"
				),
			}
		)
	return out


def compile_schema_from_mapped(mapped: dict[str, Any], *, configuration_id: str = "", std_version: str = "") -> dict[str, Any]:
	"""Compile schema from mapper output (no DB)."""
	template = map_bidder_submission_schema()
	sections_by_key = {
		cstr(s.get("key") or ""): dict(s) for s in (template.get("sections") or []) if isinstance(s, dict)
	}

	reqs = mapped.get("it_requirements") or []
	matrix = sections_by_key.get("technical_compliance_matrix") or {
		"key": "technical_compliance_matrix",
		"label": "Technical Compliance Matrix",
	}
	matrix["requirements"] = [_matrix_row_from_requirement(r) for r in reqs if isinstance(r, dict)]
	matrix["response_fields_per_requirement"] = list(RESPONSE_FIELDS_PER_REQUIREMENT)
	sections_by_key["technical_compliance_matrix"] = matrix

	price_items = (mapped.get("price_schedule") or {}).get("items") or []
	price_sec = sections_by_key.get("price_schedule") or {"key": "price_schedule", "label": "Price Schedule"}
	price_sec["price_lines"] = [_price_line_from_item(r) for r in price_items if isinstance(r, dict)]
	price_sec.setdefault(
		"summary_fields",
		[
			{"field_key": "subtotal_excluding_vat", "label": "Subtotal excluding VAT", "type": "money", "required": True},
			{"field_key": "vat_16_percent", "label": "VAT (16%)", "type": "money", "required": True},
			{
				"field_key": "grand_total_inclusive_vat",
				"label": "Grand Total (inclusive of VAT)",
				"type": "money",
				"required": True,
			},
		],
	)
	sections_by_key["price_schedule"] = price_sec

	criteria = (mapped.get("evaluation_setup") or {}).get("criteria") or []
	prelim = sections_by_key.get("preliminary_documents") or {
		"key": "preliminary_documents",
		"label": "Mandatory Preliminary Documents",
	}
	prelim["requirements"] = _eval_requirements(criteria, stage="Preliminary", basis="Pass/Fail")
	sections_by_key["preliminary_documents"] = prelim

	techq = sections_by_key.get("technical_qualification") or {
		"key": "technical_qualification",
		"label": "Technical Qualification",
	}
	techq["requirements"] = _eval_requirements(criteria, stage="Technical", basis="Pass/Fail")
	sections_by_key["technical_qualification"] = techq

	ordered = [sections_by_key[k] for k in SECTION_KEYS if k in sections_by_key]
	# Keep any unexpected template sections after known order
	for k, sec in sections_by_key.items():
		if k not in SECTION_KEYS:
			ordered.append(sec)

	schema: dict[str, Any] = {
		"schema_name": template.get("schema_name") or "NSSF ERP Electronic Bidder Submission Schema v1.0",
		"source_fixture": template.get("source_fixture"),
		"submission_policy": template.get("submission_policy"),
		"sections": ordered,
		"validation_rules": list(template.get("validation_rules") or []),
		"_kentender_artifact": dict(template.get("_kentender_artifact") or {}),
		"configuration_id": configuration_id,
		"std_version": std_version,
		"compiled_from": "tender_configuration_cfg",
	}
	# Hash without self-referential hash field
	schema["schema_hash"] = _canonical_hash(
		{k: v for k, v in schema.items() if k != "schema_hash"}
	)
	return schema


def compile_schema_from_fixture(*, configuration_id: str = "", std_version: str = "") -> dict[str, Any]:
	return compile_schema_from_mapped(
		map_all_cfg_blobs(),
		configuration_id=configuration_id,
		std_version=std_version,
	)


def compile_schema_for_configuration(configuration_id: str) -> dict[str, Any]:
	"""Compile from persisted Tender Configuration CFG fields."""
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	reqs = _parse_json_field(getattr(doc, "it_requirements", None))
	if not isinstance(reqs, list):
		reqs = []
	price = _parse_json_field(getattr(doc, "price_schedule", None)) or {}
	evaluation = _parse_json_field(getattr(doc, "evaluation_setup", None)) or {}
	mapped = {
		"it_requirements": reqs,
		"price_schedule": price if isinstance(price, dict) else {"items": []},
		"evaluation_setup": evaluation if isinstance(evaluation, dict) else {"criteria": []},
	}
	return compile_schema_from_mapped(
		mapped,
		configuration_id=doc.name,
		std_version=cstr(doc.std_version or ""),
	)


def persist_compiled_schema(configuration_id: str) -> dict[str, Any]:
	schema = compile_schema_for_configuration(configuration_id)
	frappe.db.set_value(
		"Tender Configuration",
		configuration_id,
		"bidder_submission_schema",
		json.dumps(schema),
		update_modified=False,
	)
	return schema
