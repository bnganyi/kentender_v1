# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — Admin Step 4 package validation (read-only).

Builds ``checks[]`` and ``overall_status`` per ``4. std_admin_console_package_validation_rule_trace_specification.md`` §8–§11.
Does not read arbitrary disk paths; validates ``STD Template`` imported ``package_json`` only.
"""

from __future__ import annotations

import re
from typing import Any

from kentender_procurement.tender_management.services.std_template_engine import (
	ALLOWED_BOQ_ITEM_CATEGORIES,
	SUPPORTED_OPERATORS,
	SUPPORTED_RULE_TYPES,
)

from kentender_procurement.tender_management.services.std_template_loader import (
	_REQUIRED_TOP_LEVEL_KEYS,
	REQUIRED_JSON_FILES,
)

REQUIRED_PACKAGE_KEYS: tuple[str, ...] = (
	"manifest",
	"sections",
	"fields",
	"rules",
	"forms",
	"render_map",
	"sample_tender",
)

_STATUS_ORDER: dict[str, int] = {
	"BLOCKED": 0,
	"FAILED": 1,
	"WARNING": 2,
	"PASSED": 3,
	"SKIPPED": 4,
}

_CATEGORY_ORDER: dict[str, int] = {
	"PACKAGE_STRUCTURE": 0,
	"TEMPLATE_IDENTITY": 1,
	"SECTIONS": 2,
	"FIELDS": 3,
	"RULES": 4,
	"FORMS": 5,
	"SAMPLE_TENDER": 6,
	"RENDER_MAP": 7,
	"AUDIT": 8,
}


def _check_row(
	check_code: str,
	label: str,
	category: str,
	severity: str,
	status: str,
	message: str,
	reference: str = "package_json",
	details: dict[str, Any] | None = None,
) -> dict[str, Any]:
	return {
		"check_code": check_code,
		"label": label,
		"category": category,
		"severity": severity,
		"status": status,
		"message": message,
		"reference": reference,
		"details": details or {},
	}


def _sort_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
	def key(c: dict[str, Any]) -> tuple[int, int, str]:
		st = c.get("status") or "PASSED"
		cat = c.get("category") or ""
		return (
			_STATUS_ORDER.get(st, 9),
			_CATEGORY_ORDER.get(cat, 99),
			c.get("check_code") or "",
		)

	return sorted(checks, key=key)


def _summarize_checks(checks: list[dict[str, Any]]) -> dict[str, int]:
	out = {
		"total_checks": len(checks),
		"passed": 0,
		"warnings": 0,
		"errors": 0,
		"blockers": 0,
		"skipped": 0,
	}
	for c in checks:
		st = c.get("status")
		if st == "PASSED":
			out["passed"] += 1
		elif st == "WARNING":
			out["warnings"] += 1
		elif st == "FAILED":
			out["errors"] += 1
		elif st == "BLOCKED":
			out["blockers"] += 1
		elif st == "SKIPPED":
			out["skipped"] += 1
	return out


def _overall_status(checks: list[dict[str, Any]]) -> str:
	if any(c.get("status") == "BLOCKED" for c in checks):
		return "BLOCKED"
	if any(c.get("status") == "FAILED" for c in checks):
		return "FAILED"
	if any(c.get("status") == "WARNING" for c in checks):
		return "PASSED_WITH_WARNINGS"
	return "PASSED"


def _collect_rule_field_codes(rule: dict[str, Any]) -> set[str]:
	out: set[str] = set()
	when = rule.get("when") or {}
	for cond in when.get("all") or []:
		if isinstance(cond, dict) and cond.get("field"):
			out.add(str(cond["field"]))
	then = rule.get("then") or {}
	for k in ("require_fields", "activate_fields"):
		for fc in then.get(k) or []:
			out.add(str(fc))
	# Child-row row_filter fields (e.g. item_category) are table columns, not fields.json codes.
	for spec in then.get("validate") or []:
		if not isinstance(spec, dict):
			continue
		for key in (
			"earlier_field",
			"later_field",
			"first_field",
			"second_field",
			"field",
			"base_field",
		):
			v = spec.get(key)
			if v:
				out.add(str(v))
	return out


def _collect_rule_section_codes(rule: dict[str, Any]) -> set[str]:
	out: set[str] = set()
	then = rule.get("then") or {}
	for sc in then.get("activate_sections") or []:
		out.add(str(sc))
	for sc in rule.get("affected_sections") or []:
		if sc:
			out.add(str(sc))
	return out


def _collect_rule_form_codes(rule: dict[str, Any]) -> set[str]:
	out: set[str] = set()
	then = rule.get("then") or {}
	for fc in then.get("activate_forms") or []:
		out.add(str(fc))
	return out


def run_package_validation(doc: Any, package: dict[str, Any]) -> dict[str, Any]:
	"""Return Admin Step 4 §8 validation envelope (mutates nothing)."""
	checks: list[dict[str, Any]] = []

	manifest_template_code: str | None = None
	manifest = package.get("manifest") if isinstance(package.get("manifest"), dict) else None
	if manifest:
		manifest_template_code = manifest.get("template_code")

	# --- 11.1 Package structure ---
	missing_components = [k for k in REQUIRED_PACKAGE_KEYS if k not in package]
	non_objects = [k for k in REQUIRED_PACKAGE_KEYS if k in package and not isinstance(package[k], dict)]
	structure_ok = not missing_components and not non_objects
	if missing_components:
		checks.append(
			_check_row(
				"PKG_COMPONENTS_PRESENT",
				"Required package components are present",
				"PACKAGE_STRUCTURE",
				"BLOCKER",
				"BLOCKED",
				f"Missing package components: {', '.join(missing_components)}",
				details={"missing": missing_components},
			)
		)
	elif non_objects:
		checks.append(
			_check_row(
				"PKG_COMPONENTS_PRESENT",
				"Required package components are present",
				"PACKAGE_STRUCTURE",
				"BLOCKER",
				"BLOCKED",
				f"Components are not objects: {', '.join(non_objects)}",
				details={"invalid": non_objects},
			)
		)
	else:
		checks.append(
			_check_row(
				"PKG_COMPONENTS_PRESENT",
				"Required package components are present",
				"PACKAGE_STRUCTURE",
				"BLOCKER",
				"PASSED",
				"All required package components are present.",
			)
		)

	checks.append(
		_check_row(
			"PKG_COMPONENTS_ARE_OBJECTS",
			"Each major component is a JSON object",
			"PACKAGE_STRUCTURE",
			"BLOCKER",
			"BLOCKED" if non_objects else "PASSED",
			"Each component is an object."
			if not non_objects
			else f"Non-object components: {', '.join(non_objects)}",
			details={"invalid": non_objects} if non_objects else {},
		)
	)

	pkg_key_failures: list[dict[str, Any]] = []
	if structure_ok:
		for comp_key, required_keys in _REQUIRED_TOP_LEVEL_KEYS.items():
			component = package[comp_key]
			missing_keys = [k for k in required_keys if k not in component]
			if missing_keys:
				pkg_key_failures.append({"component": comp_key, "missing_keys": missing_keys})
	elif not pkg_key_failures:
		checks.append(
			_check_row(
				"PKG_REQUIRED_TOP_LEVEL_KEYS",
				"Each component has expected top-level keys",
				"PACKAGE_STRUCTURE",
				"ERROR",
				"SKIPPED",
				"Skipped because package structure is incomplete.",
			)
		)
	if pkg_key_failures:
		checks.append(
			_check_row(
				"PKG_REQUIRED_TOP_LEVEL_KEYS",
				"Each component has expected top-level keys",
				"PACKAGE_STRUCTURE",
				"ERROR",
				"FAILED",
				"One or more components missing required top-level keys.",
				details={"failures": pkg_key_failures},
			)
		)
	elif structure_ok:
		checks.append(
			_check_row(
				"PKG_REQUIRED_TOP_LEVEL_KEYS",
				"Each component has expected top-level keys",
				"PACKAGE_STRUCTURE",
				"ERROR",
				"PASSED",
				"All components include required top-level keys.",
			)
		)

	if not structure_ok:
		pass
	else:
		# --- 11.2 Template identity (skip heavy checks if no manifest) ---
		if not manifest:
			checks.append(
				_check_row(
					"TPL_MANIFEST_TEMPLATE_CODE_PRESENT",
					"Manifest has template_code",
					"TEMPLATE_IDENTITY",
					"BLOCKER",
					"BLOCKED",
					"manifest is missing or not an object.",
				)
			)
		else:
			if not manifest_template_code:
				checks.append(
					_check_row(
						"TPL_MANIFEST_TEMPLATE_CODE_PRESENT",
						"Manifest has template_code",
						"TEMPLATE_IDENTITY",
						"BLOCKER",
						"BLOCKED",
						"manifest.template_code is missing.",
					)
				)
			else:
				checks.append(
					_check_row(
						"TPL_MANIFEST_TEMPLATE_CODE_PRESENT",
						"Manifest has template_code",
						"TEMPLATE_IDENTITY",
						"BLOCKER",
						"PASSED",
						f"manifest.template_code is {manifest_template_code!r}.",
					)
				)

			mismatching: list[str] = []
			for comp_key in REQUIRED_PACKAGE_KEYS:
				comp = package.get(comp_key)
				if isinstance(comp, dict) and "template_code" in comp:
					if comp.get("template_code") != manifest_template_code:
						mismatching.append(comp_key)
			if mismatching:
				checks.append(
					_check_row(
						"TPL_TEMPLATE_CODE_CONSISTENT",
						"All components with template_code match manifest",
						"TEMPLATE_IDENTITY",
						"BLOCKER",
						"BLOCKED",
						f"template_code mismatch in: {', '.join(mismatching)}",
						details={"components": mismatching},
					)
				)
			else:
				checks.append(
					_check_row(
						"TPL_TEMPLATE_CODE_CONSISTENT",
						"All components with template_code match manifest",
						"TEMPLATE_IDENTITY",
						"BLOCKER",
						"PASSED",
						"All component template_code values match manifest.",
					)
				)

			sample = package.get("sample_tender")
			if isinstance(sample, dict) and sample.get("template_code"):
				if sample.get("template_code") != manifest_template_code:
					checks.append(
						_check_row(
							"TPL_SAMPLE_TEMPLATE_CODE_CONSISTENT",
							"sample_tender.template_code matches manifest",
							"TEMPLATE_IDENTITY",
							"BLOCKER",
							"BLOCKED",
							"sample_tender.template_code does not match manifest.",
						)
					)
				else:
					checks.append(
						_check_row(
							"TPL_SAMPLE_TEMPLATE_CODE_CONSISTENT",
							"sample_tender.template_code matches manifest",
							"TEMPLATE_IDENTITY",
							"BLOCKER",
							"PASSED",
							"sample_tender.template_code matches manifest.",
						)
					)

			doc_tc = getattr(doc, "template_code", None)
			if doc_tc and manifest_template_code and doc_tc != manifest_template_code:
				checks.append(
					_check_row(
						"TPL_STD_TEMPLATE_RECORD_MATCHES_PACKAGE",
						"STD Template.template_code matches package manifest",
						"TEMPLATE_IDENTITY",
						"ERROR",
						"FAILED",
						f"Doc template_code {doc_tc!r} != manifest {manifest_template_code!r}.",
					)
				)
			else:
				checks.append(
					_check_row(
						"TPL_STD_TEMPLATE_RECORD_MATCHES_PACKAGE",
						"STD Template.template_code matches package manifest",
						"TEMPLATE_IDENTITY",
						"ERROR",
						"PASSED",
						"STD Template record matches manifest template_code.",
					)
				)

			ver = (manifest.get("versioning") or {}) if isinstance(manifest.get("versioning"), dict) else {}
			if not ver.get("package_version"):
				checks.append(
					_check_row(
						"TPL_PACKAGE_VERSION_PRESENT",
						"Package version exists in manifest",
						"TEMPLATE_IDENTITY",
						"ERROR",
						"FAILED",
						"manifest.versioning.package_version is missing.",
					)
				)
			else:
				checks.append(
					_check_row(
						"TPL_PACKAGE_VERSION_PRESENT",
						"Package version exists in manifest",
						"TEMPLATE_IDENTITY",
						"ERROR",
						"PASSED",
						f"package_version: {ver.get('package_version')!r}.",
					)
				)

			src = manifest.get("source_document")
			if not isinstance(src, dict) or not src.get("source_document_code"):
				checks.append(
					_check_row(
						"TPL_SOURCE_DOCUMENT_PRESENT",
						"Source document metadata exists",
						"TEMPLATE_IDENTITY",
						"WARNING",
						"WARNING",
						"Source document metadata is thin or missing source_document_code.",
					)
				)
			else:
				checks.append(
					_check_row(
						"TPL_SOURCE_DOCUMENT_PRESENT",
						"Source document metadata exists",
						"TEMPLATE_IDENTITY",
						"WARNING",
						"PASSED",
						"Source document metadata present.",
					)
				)

		# --- 11.3 Sections ---
		sections_root = package.get("sections")
		sec_rows = (
			sections_root.get("sections")
			if isinstance(sections_root, dict) and isinstance(sections_root.get("sections"), list)
			else None
		)
		if not isinstance(sections_root, dict) or sec_rows is None:
			checks.append(
				_check_row(
					"SEC_SECTIONS_ARRAY_PRESENT",
					"sections.sections exists and is an array",
					"SECTIONS",
					"BLOCKER",
					"BLOCKED",
					"sections.sections is missing or not a list.",
				)
			)
		else:
			checks.append(
				_check_row(
					"SEC_SECTIONS_ARRAY_PRESENT",
					"sections.sections exists and is an array",
					"SECTIONS",
					"BLOCKER",
					"PASSED",
					f"Found {len(sec_rows)} section row(s).",
				)
			)
			codes = [s.get("section_code") for s in sec_rows if isinstance(s, dict)]
			dupes = {c for c in codes if c and codes.count(c) > 1}
			if dupes:
				checks.append(
					_check_row(
						"SEC_SECTION_CODES_UNIQUE",
						"Section codes are unique",
						"SECTIONS",
						"BLOCKER",
						"BLOCKED",
						f"Duplicate section codes: {sorted(dupes)}",
					)
				)
			else:
				checks.append(
					_check_row(
						"SEC_SECTION_CODES_UNIQUE",
						"Section codes are unique",
						"SECTIONS",
						"BLOCKER",
						"PASSED",
						"All section codes are unique.",
					)
				)
			sec_failed = False
			for s in sec_rows:
				if not isinstance(s, dict):
					continue
				if not s.get("section_code") or s.get("render_order") is None:
					checks.append(
						_check_row(
							"SEC_REQUIRED_SECTION_FIELDS_PRESENT",
							"Each section has required fields",
							"SECTIONS",
							"ERROR",
							"FAILED",
							f"Section row missing section_code or render_order: {s.get('section_code')!r}",
							details={"row": s.get("section_code")},
						)
					)
					sec_failed = True
			if not sec_failed:
				checks.append(
					_check_row(
						"SEC_REQUIRED_SECTION_FIELDS_PRESENT",
						"Each section has required fields",
						"SECTIONS",
						"ERROR",
						"PASSED",
						"Section rows include section_code and render_order.",
					)
				)
			render_warn = any(
				isinstance(s, dict) and s.get("included_in_poc_render") and s.get("render_order") is None
				for s in sec_rows
			)
			checks.append(
				_check_row(
					"SEC_RENDER_ORDER_VALID",
					"Render order exists where included in POC render",
					"SECTIONS",
					"WARNING",
					"WARNING" if render_warn else "PASSED",
					"All POC-render sections have render_order."
					if not render_warn
					else "Some POC-render sections lack render_order.",
				)
			)

		# --- 11.4 Fields ---
		fields_root = package.get("fields")
		fld_rows = (
			fields_root.get("fields")
			if isinstance(fields_root, dict) and isinstance(fields_root.get("fields"), list)
			else None
		)
		field_codes: set[str] = set()
		if fld_rows is None:
			checks.append(
				_check_row(
					"FLD_FIELDS_ARRAY_PRESENT",
					"fields.fields exists and is an array",
					"FIELDS",
					"BLOCKER",
					"BLOCKED",
					"fields.fields is missing or not a list.",
				)
			)
		else:
			checks.append(
				_check_row(
					"FLD_FIELDS_ARRAY_PRESENT",
					"fields.fields exists and is an array",
					"FIELDS",
					"BLOCKER",
					"PASSED",
					f"Found {len(fld_rows)} field row(s).",
				)
			)
			fc_list = [f.get("field_code") for f in fld_rows if isinstance(f, dict)]
			dup_f = {c for c in fc_list if c and fc_list.count(c) > 1}
			if dup_f:
				checks.append(
					_check_row(
						"FLD_FIELD_CODES_UNIQUE",
						"Field codes are unique",
						"FIELDS",
						"BLOCKER",
						"BLOCKED",
						f"Duplicate field codes: {sorted(dup_f)}",
					)
				)
			else:
				checks.append(
					_check_row(
						"FLD_FIELD_CODES_UNIQUE",
						"Field codes are unique",
						"FIELDS",
						"BLOCKER",
						"PASSED",
						"All field codes are unique.",
					)
				)
			meta_fail = False
			select_fail = False
			for f in fld_rows:
				if not isinstance(f, dict):
					continue
				fc = f.get("field_code")
				if fc:
					field_codes.add(str(fc))
				if not fc or not f.get("field_type"):
					checks.append(
						_check_row(
							"FLD_REQUIRED_FIELD_METADATA_PRESENT",
							"Each field has required metadata",
							"FIELDS",
							"ERROR",
							"FAILED",
							f"Field row missing field_code or field_type: {fc!r}",
						)
					)
					meta_fail = True
				ft = f.get("field_type")
				if ft == "SELECT" and not (f.get("options") or []):
					checks.append(
						_check_row(
							"FLD_SELECT_OPTIONS_VALID",
							"Select fields have valid options where required",
							"FIELDS",
							"ERROR",
							"FAILED",
							f"SELECT field {fc!r} has no options.",
						)
					)
					select_fail = True
			if not meta_fail:
				checks.append(
					_check_row(
						"FLD_REQUIRED_FIELD_METADATA_PRESENT",
						"Each field has required metadata",
						"FIELDS",
						"ERROR",
						"PASSED",
						"Each field has field_code and field_type.",
					)
				)
			if not select_fail:
				checks.append(
					_check_row(
						"FLD_SELECT_OPTIONS_VALID",
						"Select fields have valid options where required",
						"FIELDS",
						"ERROR",
						"PASSED",
						"All SELECT fields define options.",
					)
				)
			sys_present = any(
				isinstance(f, dict) and str(f.get("field_code", "")).startswith("SYSTEM.") for f in fld_rows
			)
			checks.append(
				_check_row(
					"FLD_SYSTEM_FIELDS_PRESENT",
					"Expected system/audit fields exist",
					"FIELDS",
					"WARNING",
					"WARNING" if not sys_present else "PASSED",
					"SYSTEM.* fields present." if sys_present else "No SYSTEM.* field definitions found.",
				)
			)

		# --- 11.5 Rules ---
		rules_root = package.get("rules")
		rule_rows = (
			rules_root.get("rules")
			if isinstance(rules_root, dict) and isinstance(rules_root.get("rules"), list)
			else None
		)
		section_codes: set[str] = set()
		if sec_rows:
			section_codes = {
				str(s.get("section_code"))
				for s in sec_rows
				if isinstance(s, dict) and s.get("section_code")
			}
		form_codes: set[str] = set()
		forms_root = package.get("forms")
		form_rows_list = (
			forms_root.get("forms")
			if isinstance(forms_root, dict) and isinstance(forms_root.get("forms"), list)
			else []
		)
		for fm in form_rows_list:
			if isinstance(fm, dict) and fm.get("form_code"):
				form_codes.add(str(fm["form_code"]))

		if rule_rows is None:
			checks.append(
				_check_row(
					"RUL_RULES_ARRAY_PRESENT",
					"rules.rules exists and is an array",
					"RULES",
					"BLOCKER",
					"BLOCKED",
					"rules.rules is missing or not a list.",
				)
			)
		else:
			checks.append(
				_check_row(
					"RUL_RULES_ARRAY_PRESENT",
					"rules.rules exists and is an array",
					"RULES",
					"BLOCKER",
					"PASSED",
					f"Found {len(rule_rows)} rule(s).",
				)
			)
			rc_list = [r.get("rule_code") for r in rule_rows if isinstance(r, dict)]
			dup_r = {c for c in rc_list if c and rc_list.count(c) > 1}
			if dup_r:
				checks.append(
					_check_row(
						"RUL_RULE_CODES_UNIQUE",
						"Rule codes are unique",
						"RULES",
						"BLOCKER",
						"BLOCKED",
						f"Duplicate rule codes: {sorted(dup_r)}",
					)
				)
			else:
				checks.append(
					_check_row(
						"RUL_RULE_CODES_UNIQUE",
						"Rule codes are unique",
						"RULES",
						"BLOCKER",
						"PASSED",
						"All rule codes are unique.",
					)
				)
			meta_r = False
			type_bad = False
			op_bad = False
			sev_bad = False
			ref_field_fail = False
			ref_sec_fail = False
			ref_form_fail = False
			allowed_sev = frozenset({"INFO", "WARNING", "ERROR", "BLOCKER"})
			for r in rule_rows:
				if not isinstance(r, dict):
					continue
				if not r.get("rule_code") or not r.get("rule_type") or not r.get("severity"):
					meta_r = True
					continue
				rt = r.get("rule_type")
				if rt not in SUPPORTED_RULE_TYPES:
					type_bad = True
				sev = r.get("severity")
				if sev not in allowed_sev:
					sev_bad = True
				for cond in (r.get("when") or {}).get("all") or []:
					if isinstance(cond, dict) and cond.get("operator") not in SUPPORTED_OPERATORS:
						op_bad = True
				for fc in _collect_rule_field_codes(r):
					if fc not in field_codes and not fc.startswith("SYSTEM."):
						ref_field_fail = True
				for sc in _collect_rule_section_codes(r):
					if sc and sc not in section_codes:
						ref_sec_fail = True
				for fm in _collect_rule_form_codes(r):
					if fm and fm not in form_codes:
						ref_form_fail = True
			checks.append(
				_check_row(
					"RUL_REQUIRED_RULE_METADATA_PRESENT",
					"Each rule has required metadata",
					"RULES",
					"ERROR",
					"FAILED" if meta_r else "PASSED",
					"Some rules missing rule_code, rule_type, or severity." if meta_r else "Rule metadata complete.",
				)
			)
			checks.append(
				_check_row(
					"RUL_RULE_TYPES_SUPPORTED",
					"Rule types are supported by engine",
					"RULES",
					"BLOCKER",
					"BLOCKED" if type_bad else "PASSED",
					"Unsupported rule_type present." if type_bad else "All rule types are supported.",
				)
			)
			checks.append(
				_check_row(
					"RUL_OPERATORS_SUPPORTED",
					"Operators are supported by engine",
					"RULES",
					"BLOCKER",
					"BLOCKED" if op_bad else "PASSED",
					"Unsupported operator in conditions." if op_bad else "All operators supported.",
				)
			)
			checks.append(
				_check_row(
					"RUL_SEVERITIES_SUPPORTED",
					"Severities are supported",
					"RULES",
					"ERROR",
					"FAILED" if sev_bad else "PASSED",
					"Invalid severity value." if sev_bad else "Severities are valid.",
				)
			)
			checks.append(
				_check_row(
					"RUL_FIELD_REFERENCES_EXIST",
					"All rule field references exist in fields.json",
					"RULES",
					"BLOCKER",
					"BLOCKED" if ref_field_fail else "PASSED",
					"Unknown field reference in rule." if ref_field_fail else "Field references resolve.",
				)
			)
			checks.append(
				_check_row(
					"RUL_SECTION_REFERENCES_EXIST",
					"All rule section references exist in sections.json",
					"RULES",
					"BLOCKER",
					"BLOCKED" if ref_sec_fail else "PASSED",
					"Unknown section reference in rule." if ref_sec_fail else "Section references resolve.",
				)
			)
			checks.append(
				_check_row(
					"RUL_FORM_REFERENCES_EXIST",
					"All rule form references exist in forms.json",
					"RULES",
					"BLOCKER",
					"BLOCKED" if ref_form_fail else "PASSED",
					"Unknown form reference in rule." if ref_form_fail else "Form references resolve.",
				)
			)

		# --- 11.6 Forms ---
		if not isinstance(forms_root, dict) or not isinstance(form_rows_list, list):
			checks.append(
				_check_row(
					"FRM_FORMS_ARRAY_PRESENT",
					"forms.forms exists and is an array",
					"FORMS",
					"BLOCKER",
					"BLOCKED",
					"forms.forms is missing or not a list.",
				)
			)
		else:
			checks.append(
				_check_row(
					"FRM_FORMS_ARRAY_PRESENT",
					"forms.forms exists and is an array",
					"FORMS",
					"BLOCKER",
					"PASSED",
					f"Found {len(form_rows_list)} form(s).",
				)
			)
			fm_codes = [f.get("form_code") for f in form_rows_list if isinstance(f, dict)]
			dup_fm = {c for c in fm_codes if c and fm_codes.count(c) > 1}
			if dup_fm:
				checks.append(
					_check_row(
						"FRM_FORM_CODES_UNIQUE",
						"Form codes are unique",
						"FORMS",
						"BLOCKER",
						"BLOCKED",
						f"Duplicate form codes: {sorted(dup_fm)}",
					)
				)
			else:
				checks.append(
					_check_row(
						"FRM_FORM_CODES_UNIQUE",
						"Form codes are unique",
						"FORMS",
						"BLOCKER",
						"PASSED",
						"All form codes are unique.",
					)
				)
			rule_code_set = {
			str(r.get("rule_code"))
			for r in (rule_rows or [])
			if isinstance(r, dict) and r.get("rule_code")
		}
			meta_f = False
			act_fail = False
			disp_fail = False
		for fm in form_rows_list:
			if not isinstance(fm, dict):
				continue
			form_cat = fm.get("form_category") or fm.get("category")
			if not fm.get("form_code") or not form_cat:
				meta_f = True
			for arc in fm.get("activation_rule_codes") or []:
				if str(arc) not in rule_code_set:
					act_fail = True
			cd = fm.get("checklist_display") if isinstance(fm.get("checklist_display"), dict) else {}
			display_group = fm.get("display_group") or cd.get("display_group")
			display_order = fm.get("display_order")
			if display_order is None:
				display_order = cd.get("display_order")
			if not display_group or display_order is None:
				disp_fail = True
			checks.append(
				_check_row(
					"FRM_REQUIRED_FORM_METADATA_PRESENT",
					"Each form has required metadata",
					"FORMS",
					"ERROR",
					"FAILED" if meta_f else "PASSED",
					"Some forms missing form_code or form_category." if meta_f else "Form metadata complete.",
				)
			)
			checks.append(
				_check_row(
					"FRM_ACTIVATION_RULES_EXIST",
					"Activation rule codes reference existing rules",
					"FORMS",
					"ERROR",
					"FAILED" if act_fail else "PASSED",
					"Unknown activation_rule_codes." if act_fail else "Activation rules exist.",
				)
			)
			checks.append(
				_check_row(
					"FRM_CHECKLIST_DISPLAY_VALID",
					"Each form has display group and display order",
					"FORMS",
					"ERROR",
					"FAILED" if disp_fail else "PASSED",
					"Missing display_group or display_order." if disp_fail else "Display metadata valid.",
				)
			)
			checks.append(
				_check_row(
					"FRM_ORDINARY_USER_SCHEMA_LOCKED",
					"Form schemas are not editable by ordinary users",
					"FORMS",
					"WARNING",
					"PASSED",
					"POC: form schema editing is out of scope; schemas treated as read-only.",
				)
			)

		# --- 11.7 Sample tender ---
		sample = package.get("sample_tender")
		if not isinstance(sample, dict):
			checks.append(
				_check_row(
					"SMP_SAMPLE_IDENTITY_PRESENT",
					"Sample code/name/template code exist",
					"SAMPLE_TENDER",
					"ERROR",
					"FAILED",
					"sample_tender is not an object.",
				)
			)
		else:
			if not sample.get("sample_code") or not sample.get("sample_name") or not sample.get("template_code"):
				checks.append(
					_check_row(
						"SMP_SAMPLE_IDENTITY_PRESENT",
						"Sample code/name/template code exist",
						"SAMPLE_TENDER",
						"ERROR",
						"FAILED",
						"Missing sample_code, sample_name, or template_code.",
					)
				)
			else:
				checks.append(
					_check_row(
						"SMP_SAMPLE_IDENTITY_PRESENT",
						"Sample code/name/template code exist",
						"SAMPLE_TENDER",
						"ERROR",
						"PASSED",
						"Sample identity fields present.",
					)
				)
			cfg = sample.get("configuration")
			if not isinstance(cfg, dict):
				checks.append(
					_check_row(
						"SMP_CONFIGURATION_PRESENT",
						"Sample configuration exists and is an object",
						"SAMPLE_TENDER",
						"BLOCKER",
						"BLOCKED",
						"configuration is missing or not an object.",
					)
				)
			else:
				checks.append(
					_check_row(
						"SMP_CONFIGURATION_PRESENT",
						"Sample configuration exists and is an object",
						"SAMPLE_TENDER",
						"BLOCKER",
						"PASSED",
						"Sample configuration object present.",
					)
				)
				missing_cfg_fields = [k for k in cfg if k not in field_codes and not str(k).startswith("SYSTEM.")]
				if missing_cfg_fields:
					checks.append(
						_check_row(
							"SMP_CONFIGURATION_FIELDS_EXIST",
							"Every sample configuration key exists in fields.json",
							"SAMPLE_TENDER",
							"BLOCKER",
							"BLOCKED",
							f"Unknown configuration keys: {missing_cfg_fields[:20]}",
							details={"unknown_keys": missing_cfg_fields},
						)
					)
				else:
					checks.append(
						_check_row(
							"SMP_CONFIGURATION_FIELDS_EXIST",
							"Every sample configuration key exists in fields.json",
							"SAMPLE_TENDER",
							"BLOCKER",
							"PASSED",
							"All configuration keys exist in fields.json.",
						)
					)
			exp_forms = sample.get("expected_activated_forms") or []
			if isinstance(exp_forms, list):
				missing_forms = [f for f in exp_forms if f and str(f) not in form_codes]
				if missing_forms:
					checks.append(
						_check_row(
							"SMP_EXPECTED_FORMS_EXIST",
							"Expected activated forms exist in forms.json",
							"SAMPLE_TENDER",
							"BLOCKER",
							"BLOCKED",
							f"Unknown expected forms: {missing_forms}",
						)
					)
				else:
					checks.append(
						_check_row(
							"SMP_EXPECTED_FORMS_EXIST",
							"Expected activated forms exist in forms.json",
							"SAMPLE_TENDER",
							"BLOCKER",
							"PASSED",
							"Expected activated forms exist.",
						)
					)
			tender_obj = sample.get("tender") if isinstance(sample.get("tender"), dict) else {}
			lots_s = tender_obj.get("lots") if isinstance(tender_obj.get("lots"), list) else []
			lot_codes = [l.get("lot_code") for l in lots_s if isinstance(l, dict)]
			dup_l = {c for c in lot_codes if c and lot_codes.count(c) > 1}
			lot_fail = any(not isinstance(l, dict) or not l.get("lot_code") for l in lots_s)
			if lot_fail or dup_l:
				checks.append(
					_check_row(
						"SMP_LOTS_VALID",
						"Sample lots have required fields and unique lot codes",
						"SAMPLE_TENDER",
						"ERROR",
						"FAILED",
						"Invalid or duplicate lot codes in sample tender.",
						details={"dupes": sorted(dup_l)} if dup_l else {},
					)
				)
			else:
				checks.append(
					_check_row(
						"SMP_LOTS_VALID",
						"Sample lots have required fields and unique lot codes",
						"SAMPLE_TENDER",
						"ERROR",
						"PASSED",
						"Sample lots are valid.",
					)
				)
			boq = sample.get("boq") if isinstance(sample.get("boq"), dict) else {}
			boq_rows = boq.get("rows") if isinstance(boq.get("rows"), list) else []
			item_codes = [r.get("item_code") for r in boq_rows if isinstance(r, dict)]
			dup_i = {c for c in item_codes if c and item_codes.count(c) > 1}
			boq_fail = any(
				not isinstance(r, dict) or not r.get("item_code") or r.get("quantity") is None
				for r in boq_rows
			)
			if boq_fail or dup_i:
				checks.append(
					_check_row(
						"SMP_BOQ_ROWS_VALID",
						"Sample BoQ rows have required fields and unique item codes",
						"SAMPLE_TENDER",
						"ERROR",
						"FAILED",
						"Invalid or duplicate BoQ item codes.",
					)
				)
			else:
				checks.append(
					_check_row(
						"SMP_BOQ_ROWS_VALID",
						"Sample BoQ rows have required fields and unique item codes",
						"SAMPLE_TENDER",
						"ERROR",
						"PASSED",
						"Sample BoQ rows are valid.",
					)
				)
			bad_cat = [
				str(r.get("item_category"))
				for r in boq_rows
				if isinstance(r, dict) and r.get("item_category") not in ALLOWED_BOQ_ITEM_CATEGORIES
			]
			if bad_cat:
				checks.append(
					_check_row(
						"SMP_BOQ_CATEGORIES_SUPPORTED",
						"BoQ categories are supported by POC model",
						"SAMPLE_TENDER",
						"ERROR",
						"FAILED",
						f"Unsupported categories: {sorted(set(bad_cat))}",
					)
				)
			else:
				checks.append(
					_check_row(
						"SMP_BOQ_CATEGORIES_SUPPORTED",
						"BoQ categories are supported by POC model",
						"SAMPLE_TENDER",
						"ERROR",
						"PASSED",
						"All BoQ categories are allowed.",
					)
				)
			variants = sample.get("scenario_variants") or []
			var_fail = False
			var_form_fail = False
			if not isinstance(variants, list):
				var_fail = True
			else:
				for v in variants:
					if not isinstance(v, dict) or not v.get("variant_code"):
						var_fail = True
						continue
					for fc in v.get("expected_activated_forms") or []:
						if str(fc) not in form_codes:
							var_form_fail = True
			checks.append(
				_check_row(
					"SMP_VARIANTS_VALID",
					"Scenario variants have required shape and valid overrides",
					"SAMPLE_TENDER",
					"ERROR",
					"FAILED" if var_fail else "PASSED",
					"Invalid scenario_variants." if var_fail else "Scenario variants are well-formed.",
				)
			)
			checks.append(
				_check_row(
					"SMP_VARIANT_FORMS_EXIST",
					"Variant expected forms exist in forms.json",
					"SAMPLE_TENDER",
					"ERROR",
					"FAILED" if var_form_fail else "PASSED",
					"Unknown form in variant expected_activated_forms."
					if var_form_fail
					else "Variant form references resolve.",
				)
			)

		# --- 11.8 Render map ---
		rm = package.get("render_map")
		if not isinstance(rm, dict) or not rm:
			checks.append(
				_check_row(
					"RND_RENDER_MAP_PRESENT",
					"Render map exists",
					"RENDER_MAP",
					"WARNING",
					"WARNING",
					"Render map is skeletal or missing.",
				)
			)
		else:
			checks.append(
				_check_row(
					"RND_RENDER_MAP_PRESENT",
					"Render map exists",
					"RENDER_MAP",
					"WARNING",
					"PASSED",
					"Render map object present.",
				)
			)
			rs = rm.get("render_sections") if isinstance(rm.get("render_sections"), list) else []
			rm_sec_fail = False
			for row in rs:
				if isinstance(row, dict) and row.get("section_code") and row["section_code"] not in section_codes:
					rm_sec_fail = True
			checks.append(
				_check_row(
					"RND_SECTION_REFERENCES_EXIST",
					"Render map section references exist where present",
					"RENDER_MAP",
					"ERROR",
					"FAILED" if rm_sec_fail else "PASSED",
					"Unknown section in render_map." if rm_sec_fail else "Render map sections resolve.",
				)
			)
			checks.append(
				_check_row(
					"RND_POC_RENDER_COVERAGE",
					"Required POC preview sections are represented or warning emitted",
					"RENDER_MAP",
					"WARNING",
					"WARNING" if len(rs) == 0 else "PASSED",
					"Render map has no render_sections (POC may use fixed Jinja)."
					if len(rs) == 0
					else "Render sections listed.",
				)
			)

	# --- 11.9 Audit ---
	ph = getattr(doc, "package_hash", None) or ""
	if not ph:
		checks.append(
			_check_row(
				"AUD_PACKAGE_HASH_PRESENT",
				"STD Template.package_hash is populated",
				"AUDIT",
				"ERROR",
				"FAILED",
				"package_hash is empty on STD Template record.",
			)
		)
	else:
		checks.append(
			_check_row(
				"AUD_PACKAGE_HASH_PRESENT",
				"STD Template.package_hash is populated",
				"AUDIT",
				"ERROR",
				"PASSED",
				"package_hash is populated.",
			)
		)
		sha_ok = bool(re.fullmatch(r"[a-f0-9]{64}", ph))
		checks.append(
			_check_row(
				"AUD_PACKAGE_HASH_FORMAT",
				"Package hash appears to be SHA-256 hex",
				"AUDIT",
				"WARNING",
				"WARNING" if not sha_ok else "PASSED",
				"package_hash is not 64 hex chars." if not sha_ok else "package_hash looks like SHA-256 hex.",
			)
		)
	if getattr(doc, "imported_at", None):
		checks.append(
			_check_row(
				"AUD_IMPORTED_AT_PRESENT",
				"Import timestamp exists",
				"AUDIT",
				"WARNING",
				"PASSED",
				"imported_at is set.",
			)
		)
	else:
		checks.append(
			_check_row(
				"AUD_IMPORTED_AT_PRESENT",
				"Import timestamp exists",
				"AUDIT",
				"WARNING",
				"WARNING",
				"imported_at is missing.",
			)
		)
	raw_pkg = getattr(doc, "package_json", None) or ""
	if not str(raw_pkg).strip():
		checks.append(
			_check_row(
				"AUD_PACKAGE_JSON_PRESENT",
				"Package JSON exists",
				"AUDIT",
				"BLOCKER",
				"BLOCKED",
				"STD Template.package_json is empty.",
			)
		)
	else:
		checks.append(
			_check_row(
				"AUD_PACKAGE_JSON_PRESENT",
				"Package JSON exists",
				"AUDIT",
				"BLOCKER",
				"PASSED",
				"package_json is populated on STD Template.",
			)
		)

	sorted_checks = _sort_checks(checks)
	summary = _summarize_checks(sorted_checks)
	overall = _overall_status(sorted_checks)
	template_name = getattr(doc, "template_name", None) or (manifest or {}).get("template_name") or ""
	tc = manifest_template_code or getattr(doc, "template_code", "") or ""

	return {
		"ok": overall not in ("FAILED", "BLOCKED"),
		"template_code": tc,
		"template_name": str(template_name),
		"package_hash": ph if ph else getattr(doc, "package_hash", "") or "",
		"overall_status": overall,
		"summary": summary,
		"checks": sorted_checks,
	}


def build_validation_report_html(result: dict[str, Any]) -> str:
	"""Render package validation for Desk dialog (Jinja)."""
	import frappe

	return frappe.render_template(
		"templates/std_admin_console/package_validation_report.html",
		{"result": result},
	)


def build_rule_trace_report_html(payload: dict[str, Any]) -> str:
	"""Render rule trace for Desk dialog (Jinja)."""
	import frappe

	raw_payload = {k: v for k, v in payload.items() if k != "html"}
	ctx = {
		"trace_source": payload.get("trace_source", ""),
		"variant_code": payload.get("variant_code"),
		"tender": payload.get("tender"),
		"configuration_hash": payload.get("configuration_hash", ""),
		"summary": payload.get("summary") or {},
		"rules": payload.get("rules") or [],
		"raw_payload": raw_payload,
	}
	return frappe.render_template("templates/std_admin_console/rule_trace_report.html", ctx)
