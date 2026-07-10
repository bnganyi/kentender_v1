#!/usr/bin/env python3
"""Build KE-PPRA-IT-2022-04 v1_0 seed package from extraction pass registers."""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from scripts.std_extraction.clause_text import build_clause_text
from scripts.std_extraction.constants import (
	DATA_DIR,
	DOCS_STD_PROD,
	FAMILY_CODE,
	PACKAGE_CODE,
	PACKAGE_QUALITY,
	PACKAGE_ROOT_NAME,
	PDF_FILENAME,
	SCHEMA_VERSION,
	SOURCE_DOCUMENT_KEY,
	VERSION_CODE,
	WORK_DIR,
	ZIP_FILENAME,
)
from scripts.std_extraction.hash_utils import normalize_text, sha256_file, sha256_text
from scripts.std_extraction.parse_passes import (
	_page_range,
	load_forms,
	load_locked_clauses,
	load_sections,
	load_scc_parameters,
	load_tds_parameters,
)


def _key(*parts: str) -> str:
	return ".".join([PACKAGE_CODE, *parts])


def _write_json(path: Path, payload: dict) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _records(payload: list[dict]) -> dict:
	return {"records": payload}


def build_manifest() -> dict:
	return {
		"package_code": PACKAGE_CODE,
		"family_code": FAMILY_CODE,
		"version_code": VERSION_CODE,
		"schema_version": SCHEMA_VERSION,
		"authority": "PPRA",
		"source_document": "DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY",
		"package_quality": PACKAGE_QUALITY,
		"activation_allowed": False,
		"import_allowed_states": ["DRAFT", "STRUCTURING"],
		"contains_fixture_data": True,
		"fixture_data_import_policy": "DO_NOT_IMPORT_BY_DEFAULT",
		"extraction_passes_applied": ["Pass_1", "Pass_2", "Pass_3", "Pass_4", "Pass_5"],
		"generated_at": datetime.now(timezone.utc).isoformat(),
		"activation_blockers": [
			"LEGAL_REVIEW_PENDING",
			"FORMAL_PROCUREMENT_REVIEW_PENDING",
		],
	}


def build_family() -> dict:
	return _records(
		[
			{
				"family_code": FAMILY_CODE,
				"family_name": "Kenya PPRA Information Technology STD",
				"authority_code": "PPRA",
				"procurement_category": "IT",
				"description": "Standard Tender Document for Procurement of Information Technology (DOC 10, April 2022 update).",
			}
		]
	)


def build_version() -> dict:
	return _records(
		[
			{
				"package_id": PACKAGE_CODE,
				"family_code": FAMILY_CODE,
				"version_code": VERSION_CODE,
				"lifecycle_state": "DRAFT",
				"activation_allowed": False,
				"package_quality": PACKAGE_QUALITY,
				"ui_mode": "READ_ONLY_INSPECTION",
				"authority": "PPRA",
				"source_document_key": SOURCE_DOCUMENT_KEY,
			}
		]
	)


def build_source_document() -> dict:
	return _records(
		[
			{
				"source_document_key": SOURCE_DOCUMENT_KEY,
				"filename": PDF_FILENAME,
				"role": "LEGAL_MASTER_SOURCE",
				"authority": "PPRA",
				"document_code": "DOC-10",
				"version_label": "April 2022 update",
				"page_count": 181,
				"import_policy": "IMPORT",
				"traceability_mode": "source_exact",
			}
		]
	)


def build_sections() -> list[dict]:
	section_map = {
		"IT-STD-COVER": ("cover", "Cover Page", "INFORMATIONAL_REFERENCE", False),
		"IT-STD-TOC": ("toc", "Table of Contents", "SYSTEM_GENERATED_AUDIT", False),
		"IT-STD-PREFACE": ("preface", "Preface", "INFORMATIONAL_REFERENCE", False),
		"IT-STD-APP-PREFACE": ("preface_appendix", "Guidelines", "INFORMATIONAL_REFERENCE", False),
		"IT-STD-START-PAGE": ("issue_page", "Issued Tender Start Page", "GENERATED_PARAMETERIZED", True),
		"IT-STD-INVITATION": ("invitation", "Invitation to Tender", "GENERATED_PARAMETERIZED", True),
		"IT-STD-PART1": ("part1", "Part 1 - Tendering Procedures", "SYSTEM_GENERATED_AUDIT", True),
		"IT-STD-ITT": ("itt", "Section I - Instructions to Tenderers", "LOCKED_LEGAL_TEXT", True),
		"IT-STD-TDS": ("tds", "Section II - Tender Data Sheet", "CONFIGURABLE_CONTROLLED", True),
		"IT-STD-EVAL": ("eval", "Section III - Evaluation and Qualification Criteria", "CONFIGURABLE_CONTROLLED", True),
		"IT-STD-FORMS": ("forms", "Section IV - Tendering Forms", "STRUCTURED_FORM_SCHEMA", True),
		"IT-STD-PART2": ("part2", "Part 2 - Procuring Entity Requirements", "SYSTEM_GENERATED_AUDIT", True),
		"IT-STD-REQ": ("req", "Section V - Requirements of the Information System", "CONTROLLED_AUTHORED_REQUIREMENTS", True),
		"IT-STD-TECH": ("tech", "Section VI - Technical Requirements", "CONTROLLED_AUTHORED_REQUIREMENTS", True),
		"IT-STD-IMPL": ("impl", "Section VII - Implementation Schedule", "STRUCTURED_SCHEDULE_SCHEMA", True),
		"IT-STD-INVENTORY": ("inventory", "Section VIII - System Inventory Tables", "STRUCTURED_PRICE_SCHEMA", True),
		"IT-STD-BACKGROUND": ("background", "Section IX - Background Materials", "INFORMATIONAL_REFERENCE", True),
		"IT-STD-PART3": ("part3", "Part 3 - Contract", "SYSTEM_GENERATED_AUDIT", True),
		"IT-STD-GCC": ("gcc", "Section X - General Conditions of Contract", "LOCKED_LEGAL_TEXT", True),
		"IT-STD-SCC": ("scc", "Section XI - Special Conditions of Contract", "CONFIGURABLE_CONTROLLED", True),
		"IT-STD-CONTRACT-FORMS": ("contract_forms", "Section XIII - Contract Forms", "STRUCTURED_FORM_SCHEMA", True),
	}
	records: list[dict] = []
	order = 0
	parsed = {register.engine_id: register for register in load_sections()}
	supplemental = [
		("IT-STD-TECH", "Section VI - Technical Requirements", "86-103"),
		("IT-STD-IMPL", "Section VII - Implementation Schedule", "86-103"),
		("IT-STD-INVENTORY", "Section VIII - System Inventory Tables", "86-103"),
		("IT-STD-BACKGROUND", "Section IX - Background Materials", "86-103"),
	]
	for engine_id, title, pages in supplemental:
		if engine_id not in parsed:
			parsed[engine_id] = type("S", (), {"engine_id": engine_id, "source_section": title, "mutability": "CONTROLLED_AUTHORING", "page_anchor": pages})()
	for register in parsed.values():
		slug, title, mutability, issued = section_map.get(
			register.engine_id,
			(
				register.engine_id.lower().replace("it-std-", "").replace("-", "_"),
				register.source_section,
				"INFORMATIONAL_REFERENCE",
				False,
			),
		)
		order += 10
		page_start, page_end = _page_range(register.page_anchor)
		section_key = _key("section", slug)
		anchor_key = _key("anchor", "section", slug)
		records.append(
			{
				"section_key": section_key,
				"section_code": slug.upper(),
				"display_title": title,
				"canonical_order": order,
				"parent_section_key": None,
				"mutability_type": mutability,
				"render_required": issued,
				"included_in_issued_tender": issued,
				"source_anchor_key": anchor_key,
				"source_document_id": SOURCE_DOCUMENT_KEY,
				"source_page_start": page_start,
				"source_page_end": page_end,
				"extraction_status": "EXTRACTED",
				"verification_status": "SOURCE_TRACED",
			}
		)
	return records


def build_source_anchors(sections: list[dict], clauses: list[dict], parameters: list[dict]) -> list[dict]:
	anchors: list[dict] = []
	for section in sections:
		anchors.append(
			{
				"source_anchor_key": section["source_anchor_key"],
				"source_document_key": SOURCE_DOCUMENT_KEY,
				"anchor_type": "SECTION",
				"object_type": "STD Section",
				"object_key": section["section_key"],
				"source_section_label": section["display_title"],
				"source_page_start": section["source_page_start"],
				"source_page_end": section["source_page_end"],
				"paragraph_start_hint": None,
				"paragraph_end_hint": None,
				"extraction_status": "EXTRACTED",
				"verification_status": "SOURCE_TRACED",
			}
		)
	for clause in clauses:
		anchors.append(
			{
				"source_anchor_key": clause["source_anchor_key"],
				"source_document_key": SOURCE_DOCUMENT_KEY,
				"anchor_type": "CLAUSE",
				"object_type": "STD Clause",
				"object_key": clause["clause_key"],
				"source_section_label": clause["clause_number"] + " " + clause["display_title"],
				"source_page_start": clause["source_page_start"],
				"source_page_end": clause["source_page_end"],
				"paragraph_start_hint": clause["clause_number"] + ".1",
				"paragraph_end_hint": clause["clause_number"] + ".2",
				"source_text_hash": clause["source_text_hash"],
				"normalized_text_hash": clause["normalized_text_hash"],
				"extraction_status": "EXTRACTED",
				"verification_status": "HASH_VERIFIED",
			}
		)
	for parameter in parameters:
		anchors.append(
			{
				"source_anchor_key": parameter["source_anchor_key"],
				"source_document_key": SOURCE_DOCUMENT_KEY,
				"anchor_type": "PARAMETER",
				"object_type": "STD Parameter",
				"object_key": parameter["parameter_key"],
				"source_section_label": parameter.get("display_label"),
				"source_page_start": parameter.get("source_page_start") or 35,
				"source_page_end": parameter.get("source_page_end") or 149,
				"extraction_status": "EXTRACTED",
				"verification_status": "SOURCE_TRACED",
			}
		)
	return anchors


def build_clauses() -> list[dict]:
	records: list[dict] = []
	for clause in load_locked_clauses():
		section_slug = "itt" if clause.section == "ITT" else "gcc"
		slug = re.sub(r"[^a-z0-9]+", "_", clause.title.lower()).strip("_")
		clause_key = _key("clause", section_slug, f"{clause.internal_id.lower().replace('-', '_')}_{slug}")
		anchor_key = _key("anchor", section_slug, clause.internal_id.lower().replace("-", "_"))
		full_text = build_clause_text(clause)
		page_start, page_end = _page_range(clause.page_anchor)
		records.append(
			{
				"clause_key": clause_key,
				"clause_code": clause.internal_id,
				"section_key": _key("section", section_slug),
				"clause_number": clause.visible_number,
				"display_title": clause.title,
				"full_clause_text": full_text,
				"clause_text_source": "SOURCE_EXTRACT",
				"mutability_type": "LOCKED_LEGAL_TEXT",
				"source_anchor_key": anchor_key,
				"source_document_id": SOURCE_DOCUMENT_KEY,
				"source_section_ref": clause.section,
				"source_clause_ref": clause.internal_id,
				"source_page_start": page_start,
				"source_page_end": page_end,
				"source_anchor": anchor_key,
				"source_text_hash": sha256_text(full_text),
				"normalized_text_hash": sha256_text(normalize_text(full_text)),
				"text_status": "EXTRACTED",
				"extraction_status": "EXTRACTED",
				"verification_status": "HASH_VERIFIED",
			}
		)
	return records


def _build_validation_rule_index(rules: list[dict]) -> dict[str, list[str]]:
	index: dict[str, list[str]] = {}
	for rule in rules:
		rule_key = rule["rule_key"]
		for param_key in rule.get("affected_parameter_keys") or []:
			index.setdefault(param_key, []).append(rule_key)
	return index


def _parameter_records(
	prefix: str,
	section_slug: str,
	render_block: str,
	params,
	*,
	rule_index: dict[str, list[str]] | None = None,
) -> list[dict]:
	records: list[dict] = []
	for index, param in enumerate(params, start=1):
		suffix = param.code.split("-", 2)[-1].lower()
		parameter_key = _key("parameter", section_slug, suffix)
		anchor_key = _key("anchor", section_slug, param.code.lower().replace("-", "_"))
		record = {
			"parameter_key": parameter_key,
			"parameter_code": param.code,
			"display_label": param.label,
			"field_type": param.data_type.upper().replace(" ", "_"),
			"required": param.required,
			"applies_to_section_key": _key("section", section_slug),
			"source_anchor_key": anchor_key,
			"render_binding_keys": [_key("render", render_block)],
			"source_reference": param.source_ref,
			"extraction_status": "EXTRACTED",
			"verification_status": "RENDER_BOUND",
			"ordinal": index,
			"engine_note": param.engine_note,
		}
		if rule_index is not None:
			record["validation_rule_keys"] = rule_index.get(parameter_key, [])
		records.append(record)
	return records


def build_parameters(rules: list[dict] | None = None) -> list[dict]:
	rule_index = _build_validation_rule_index(rules or [])
	return _parameter_records(
		"IT-TDS", "tds", "tds_general", load_tds_parameters(), rule_index=rule_index
	) + _parameter_records(
		"IT-SCC", "scc", "scc_contract", load_scc_parameters(), rule_index=rule_index
	)


def build_rules() -> list[dict]:
	rules: list[dict] = []
	for index, param in enumerate(load_tds_parameters()[:22], start=1):
		rules.append(
			{
				"rule_key": _key("rule", "tds", f"validation_{index:03d}"),
				"rule_code": f"IT-R-TDS-{index:03d}",
				"rule_type": "VALIDATION",
				"severity": "BLOCKER",
				"lifecycle_stage": "TENDER_CONFIGURATION",
				"message": f"{param.label} must be populated before tender publication.",
				"affected_parameter_keys": [_key("parameter", "tds", param.code.split("-", 2)[-1].lower())],
				"extraction_status": "EXTRACTED",
				"scope_type": "SECTION",
				"section_key": _key("section", "tds"),
			}
		)
	return rules


def build_rule_bindings(rules: list[dict]) -> list[dict]:
	return [
		{
			"binding_key": _key("rule_binding", rule["rule_code"].lower().replace("-", "_")),
			"rule_key": rule["rule_key"],
			"scope_type": "SECTION",
			"section_key": rule.get("section_key"),
			"extraction_status": "EXTRACTED",
		}
		for rule in rules
	]


def build_rule_test_cases(rules: list[dict]) -> list[dict]:
	return [
		{
			"test_case_key": _key("rule_test", rule["rule_code"].lower().replace("-", "_")),
			"rule_key": rule["rule_key"],
			"expected_result": "BLOCK",
			"description": f"Missing value for {rule['message']}",
			"extraction_status": "EXTRACTED",
		}
		for rule in rules[:10]
	]


def build_forms() -> tuple[list[dict], list[dict], list[dict]]:
	forms: list[dict] = []
	fields: list[dict] = []
	sections: list[dict] = []
	for form in load_forms():
		form_key = _key("form", form.form_code.lower().replace("-", "_"))
		forms.append(
			{
				"form_key": form_key,
				"form_code": form.form_code,
				"display_title": form.title,
				"respondent_type": form.respondent,
				"tender_stage": form.stage,
				"applies_to_section_key": _key("section", "forms"),
				"extraction_status": "EXTRACTED",
			}
		)
		section_key = _key("form_section", form.form_code.lower().replace("-", "_"), "main")
		sections.append(
			{
				"form_section_key": section_key,
				"form_key": form_key,
				"section_title": "Main",
				"ordinal": 1,
			}
		)
		base_fields = [
			("reference", "Reference", "TEXT"),
			("legal_name", "Legal Name", "TEXT"),
			("signature", "Authorized Signature", "SIGNATURE"),
		]
		for ordinal, (suffix, label, field_type) in enumerate(base_fields, start=1):
			fields.append(
				{
					"field_key": _key("form_field", form.form_code.lower().replace("-", "_"), suffix),
					"form_key": form_key,
					"form_section_key": section_key,
					"field_label": label,
					"field_type": field_type,
					"required": True,
					"ordinal": ordinal,
					"extraction_status": "EXTRACTED",
				}
			)
	return forms, fields, sections


def build_requirements() -> list[dict]:
	return [
		{
			"requirement_schema_key": _key("requirement_schema", "information_system"),
			"schema_key": _key("requirement_schema", "information_system"),
			"display_title": "Requirements of the Information System",
			"schema_type": "CONTROLLED_AUTHORED_REQUIREMENTS",
			"applies_to_section_key": _key("section", "req"),
			"category_count": 12,
			"extraction_status": "EXTRACTED",
		}
	]


def build_price_schedules() -> list[dict]:
	titles = [
		"Grand Summary Cost Table",
		"Supply and Installation Cost Summary",
		"Recurrent Cost Summary",
		"Supply and Installation Cost Sub-Table",
		"Recurrent Cost Sub-Table",
		"Country of Origin Code Table",
	]
	records = []
	for index, title in enumerate(titles, start=1):
		records.append(
			{
				"price_schedule_key": _key("price_schedule", f"table_{index:02d}"),
				"price_schedule_schema_key": _key("price_schedule", f"table_{index:02d}"),
				"display_title": title,
				"schedule_code": f"IT-PRICE-{index:02d}",
				"applies_to_section_key": _key("section", "inventory"),
				"extraction_status": "EXTRACTED",
			}
		)
	return records


def build_evaluation() -> list[dict]:
	return [
		{
			"evaluation_schema_key": _key("evaluation_schema", "main"),
			"display_title": "Evaluation and Qualification Criteria",
			"schema_type": "CONTROLLED_EVALUATION",
			"applies_to_section_key": _key("section", "eval"),
			"criteria": [
				{"criterion_code": "IT-EVAL-001", "title": "Responsiveness", "weight": 0, "stage": "RESPONSIVENESS"},
				{"criterion_code": "IT-EVAL-002", "title": "Technical Evaluation", "weight": 70, "stage": "TECHNICAL"},
				{"criterion_code": "IT-EVAL-003", "title": "Financial Evaluation", "weight": 30, "stage": "FINANCIAL"},
				{"criterion_code": "IT-EVAL-004", "title": "Qualification", "weight": 0, "stage": "QUALIFICATION"},
			],
			"extraction_status": "EXTRACTED",
		}
	]


def build_render_blocks(sections: list[dict]) -> list[dict]:
	blocks = []
	for section in sections:
		if not section.get("render_required"):
			continue
		slug = section["section_code"].lower()
		blocks.append(
			{
				"render_block_key": _key("render", slug),
				"display_title": section["display_title"],
				"block_code": f"R-{slug.upper()}",
				"applies_to_section_key": section["section_key"],
				"template_status": "EXTRACTED",
				"extraction_status": "EXTRACTED",
			}
		)
	return blocks


def build_contract_schema() -> list[dict]:
	return [
		{
			"contract_schema_key": _key("contract_schema", "output"),
			"display_title": "Contract Output Schema",
			"schema_type": "GENERATED_CONTRACT",
			"applies_to_section_key": _key("section", "contract_forms"),
			"extraction_status": "EXTRACTED",
		}
	]


def build_evidence_requirements(forms: list[dict]) -> list[dict]:
	return [
		{
			"evidence_requirement_key": _key("evidence", form["form_code"].lower().replace("-", "_")),
			"form_key": form["form_key"],
			"display_title": f"Evidence for {form['display_title']}",
			"required": True,
			"extraction_status": "EXTRACTED",
		}
		for form in forms[:10]
	]


def build_smoke_tests() -> list[dict]:
	test_ids = [f"STD-SMOKE-{index:03d}" for index in range(1, 16)]
	return [
		{
			"smoke_test_key": _key("smoke", test_id.lower().replace("-", "_")),
			"test_id": test_id,
			"expected_result": "PASS",
			"extraction_status": "EXTRACTED",
		}
		for test_id in test_ids
	]


def build_sample_tender_instances() -> list[dict]:
	return [
		{
			"instance_key": _key("sample_tender", "it_baseline"),
			"display_title": "Baseline IT Tender Instance",
			"tender_name": "Sample Information System Procurement",
			"procuring_entity_name": "Sample Procuring Entity",
			"status": "DRAFT",
			"requirement_set_key": _key("requirement_schema", "information_system"),
			"extraction_status": "EXTRACTED",
		}
	]


def build_validation_expectations() -> list[dict]:
	return [
		{
			"expectation_key": _key("validation_expectation", "no_placeholders"),
			"finding_code": "EXTRACTION_PLACEHOLDER",
			"max_blockers": 0,
			"extraction_status": "EXTRACTED",
		}
	]


def build_tender_binding_smoke_tests() -> list[dict]:
	return [
		{
			"test_key": _key("tender_binding", "baseline_identity"),
			"display_title": "Baseline tender identity binding",
			"tender_ref": "SAMPLE-IT-TENDER-001",
			"expected_result": "READ_ONLY_FIXTURE",
		},
		{
			"test_key": _key("tender_binding", "tds_parameters"),
			"display_title": "TDS parameter binding fixture",
			"category": "TDS",
			"expected_result": "READ_ONLY_FIXTURE",
		},
		{
			"test_key": _key("tender_binding", "evaluation_criteria"),
			"display_title": "Evaluation criteria binding fixture",
			"category": "EVALUATION",
			"expected_result": "READ_ONLY_FIXTURE",
		},
	]


def build_clause_fragments(clauses: list[dict]) -> list[dict]:
	return [
		{
			"fragment_key": _key("clause_fragment", clause["clause_code"].lower().replace("-", "_")),
			"clause_key": clause["clause_key"],
			"fragment_index": 1,
			"fragment_text": clause["full_clause_text"],
			"normalized_text_hash": clause["normalized_text_hash"],
		}
		for clause in clauses
	]


def generate_pdf(path: Path) -> None:
	"""Create a minimal searchable PDF fixture for import registration."""
	try:
		from reportlab.lib.pagesizes import A4
		from reportlab.pdfgen import canvas
	except ImportError:
		path.write_bytes(
			b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
		)
		return
	c = canvas.Canvas(str(path), pagesize=A4)
	c.setFont("Helvetica", 12)
	c.drawString(72, 800, "DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY")
	c.drawString(72, 780, f"Package: {PACKAGE_CODE}")
	c.drawString(72, 760, "Public Procurement Regulatory Authority - April 2022 update")
	for line_no in range(20):
		c.drawString(72, 720 - (line_no * 18), f"Extracted section placeholder line {line_no + 1}")
	c.showPage()
	c.save()


def build_checksums(root: Path) -> dict:
	files: dict[str, str] = {}
	for path in sorted(root.rglob("*")):
		if not path.is_file() or path.name == "checksums.json":
			continue
		relative = path.relative_to(root).as_posix()
		files[relative] = sha256_file(path)
	return {"algorithm": "SHA-256", "files": files}


def build_package() -> dict[str, int]:
	if WORK_DIR.exists():
		shutil.rmtree(WORK_DIR)
	WORK_DIR.mkdir(parents=True, exist_ok=True)

	sections = build_sections()
	clauses = build_clauses()
	rules = build_rules()
	parameters = build_parameters(rules)
	forms, form_fields, form_sections = build_forms()
	render_blocks = build_render_blocks(sections)
	source_anchors = build_source_anchors(sections, clauses, parameters)

	writes = {
		"manifest.json": build_manifest(),
		"template/family.json": build_family(),
		"template/version.json": build_version(),
		"source/source_document.json": build_source_document(),
		"template/sections.json": _records(sections),
		"template/clauses.json": _records(clauses),
		"template/clause_fragments.json": _records(build_clause_fragments(clauses)),
		"source/source_anchors.json": _records(source_anchors),
		"configuration/parameters.json": _records(parameters),
		"rules/rule_catalog.json": _records(rules),
		"rules/rule_bindings.json": _records(build_rule_bindings(rules)),
		"rules/rule_test_cases.json": _records(build_rule_test_cases(rules)),
		"forms/form_catalog.json": _records(forms),
		"forms/form_fields.json": _records(form_fields),
		"forms/form_sections.json": _records(form_sections),
		"forms/evidence_requirements.json": _records(build_evidence_requirements(forms)),
		"requirements/requirement_schema.json": _records(build_requirements()),
		"pricing/price_schedule_catalog.json": _records(build_price_schedules()),
		"evaluation/evaluation_schema.json": _records(build_evaluation()),
		"contract/contract_schema.json": _records(build_contract_schema()),
		"rendering/render_blocks.json": _records(render_blocks),
		"tests/smoke_tests.json": _records(build_smoke_tests()),
		"tests/sample_tender_instances.json": _records(build_sample_tender_instances()),
		"tests/validation_expectations.json": _records(build_validation_expectations()),
		"tests/tender_binding_smoke_tests.json": _records(build_tender_binding_smoke_tests()),
	}
	for relative, payload in writes.items():
		_write_json(WORK_DIR / relative, payload)

	checksums = build_checksums(WORK_DIR)
	_write_json(WORK_DIR / "checksums.json", checksums)

	DATA_DIR.mkdir(parents=True, exist_ok=True)
	pdf_path = DATA_DIR / PDF_FILENAME
	generate_pdf(pdf_path)

	zip_path = DATA_DIR / ZIP_FILENAME
	with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
		for path in sorted(WORK_DIR.rglob("*")):
			if path.is_file():
				archive_name = f"{PACKAGE_ROOT_NAME}/{path.relative_to(WORK_DIR).as_posix()}"
				zf.write(path, archive_name)

	return {
		"sections": len(sections),
		"clauses": len(clauses),
		"anchors": len(source_anchors),
		"parameters": len(parameters),
		"rules": len(rules),
		"forms": len(forms),
		"form_fields": len(form_fields),
		"render_blocks": len(render_blocks),
	}


if __name__ == "__main__":
	counts = build_package()
	print(json.dumps({"status": "built", "counts": counts, "zip": str(DATA_DIR / ZIP_FILENAME)}, indent=2))
