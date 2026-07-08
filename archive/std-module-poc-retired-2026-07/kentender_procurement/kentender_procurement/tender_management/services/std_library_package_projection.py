# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB — project ``package_json`` into Official STD Library detail payloads."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

RAW_JSON_MAX_INLINE = 120_000
SECTION_ROW_LIMIT = 80

_METHOD_LABELS: dict[str, str] = {
	"OPEN_COMPETITIVE_TENDERING": "Open Competitive Tendering",
	"RESTRICTED_COMPETITIVE_TENDERING": "Restricted Competitive Tendering",
	"OPEN_TENDER": "Open Tender",
	"RESTRICTED_TENDER": "Restricted Tender",
	"REQUEST_FOR_QUOTATIONS": "Request for Quotations",
	"DIRECT_PROCUREMENT": "Direct Procurement",
}

_DEFAULT_MAPPING_TARGETS: tuple[dict[str, str], ...] = (
	{"code": "DSM", "label": "Submission Requirements (DSM)"},
	{"code": "DOM", "label": "Opening Register (DOM)"},
	{"code": "DEM", "label": "Evaluation Rules (DEM)"},
	{"code": "DCM", "label": "Contract Carry-Forward (DCM)"},
	{"code": "BUNDLE", "label": "Tender Document Bundle"},
)


def _safe_get(d: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
	cur: Any = d
	for key in keys:
		if not isinstance(cur, dict) or key not in cur:
			return default
		cur = cur[key]
	return cur


def parse_package_json(raw: str | None) -> dict[str, Any] | None:
	text = (raw or "").strip()
	if not text:
		return None
	try:
		parsed = json.loads(text)
	except json.JSONDecodeError:
		return None
	return parsed if isinstance(parsed, dict) else None


def resolve_template_title(doc: Any, package: dict[str, Any] | None = None) -> str:
	manifest = (package or {}).get("manifest") if isinstance(package, dict) else None
	if not isinstance(manifest, dict):
		manifest = {}
	src = manifest.get("source_document") or {}
	source_title = str(src.get("source_title") or "").strip()
	source_subtitle = str(src.get("source_subtitle") or "").strip()
	if source_title and source_subtitle:
		return f"{source_title} — {source_subtitle}"
	for candidate in (
		manifest.get("template_short_name"),
		manifest.get("template_name"),
		getattr(doc, "template_title", None),
		getattr(doc, "template_name", None),
		getattr(doc, "template_code", None),
	):
		text = str(candidate or "").strip()
		if text:
			return text
	return ""


def resolve_template_family(doc: Any, package: dict[str, Any] | None = None) -> str:
	manifest = (package or {}).get("manifest") if isinstance(package, dict) else None
	classification = manifest.get("classification") if isinstance(manifest, dict) else {}
	family = str(classification.get("template_family") or "").strip()
	if family:
		return family.replace("_", " ").title()
	doc_family = str(getattr(doc, "template_family", None) or "").strip()
	if doc_family:
		return doc_family
	source_doc_code = str(getattr(doc, "source_document_code", None) or "").strip()
	return source_doc_code.split("-")[0] if source_doc_code else "STD-GENERAL"


def resolve_procurement_methods(doc: Any, package: dict[str, Any] | None = None) -> list[str]:
	manifest = (package or {}).get("manifest") if isinstance(package, dict) else None
	raw_methods = _safe_get(manifest, "applicability", "allowed_procurement_methods") or []
	labels: list[str] = []
	if isinstance(raw_methods, list):
		for code in raw_methods:
			key = str(code or "").strip()
			if not key:
				continue
			labels.append(_METHOD_LABELS.get(key, key.replace("_", " ").title()))
	if labels:
		return labels
	profile = str(getattr(doc, "procurement_method_profile", None) or "").strip()
	if not profile:
		std_cfg = _safe_get(package, "std_config") if isinstance(package, dict) else None
		method = _safe_get(std_cfg, "metadata", "procurement_method") or _safe_get(
			std_cfg, "applicability", "procurement_method"
		)
		if method:
			return [str(method)]
		return []
	return [m.strip() for m in profile.split(",") if m.strip()]


def format_procurement_method_profile(methods: list[str]) -> str:
	return ", ".join(methods)


def raw_package_json_text(package: dict[str, Any] | None, *, max_chars: int = RAW_JSON_MAX_INLINE) -> tuple[str, bool]:
	if not isinstance(package, dict) or not package:
		return "", False
	text = json.dumps(package, indent=2, ensure_ascii=False, default=str)
	if len(text) <= max_chars:
		return text, False
	return text[: max_chars - 64] + "\n\n/* … truncated for library display … */", True


def _legacy_sections_rows(package: dict[str, Any]) -> list[dict[str, Any]]:
	rows = list(_safe_get(package, "sections", "sections") or [])
	out: list[dict[str, Any]] = []
	for row in rows[:SECTION_ROW_LIMIT]:
		if not isinstance(row, dict):
			continue
		out.append(
			{
				"code": str(row.get("section_code") or ""),
				"title": str(row.get("title") or ""),
				"mutability": str(row.get("mutability") or row.get("mutability_type") or ""),
				"part": str(row.get("part") or ""),
			}
		)
	return out


def _legacy_parameters_rows(package: dict[str, Any]) -> list[dict[str, Any]]:
	rows = list(_safe_get(package, "fields", "fields") or [])
	out: list[dict[str, Any]] = []
	for row in rows[:SECTION_ROW_LIMIT]:
		if not isinstance(row, dict):
			continue
		out.append(
			{
				"code": str(row.get("field_code") or row.get("code") or ""),
				"label": str(row.get("label") or row.get("field_label") or ""),
				"type": str(row.get("field_type") or row.get("type") or ""),
				"group": str(row.get("group_code") or row.get("group") or ""),
			}
		)
	return out


def _legacy_forms_rows(package: dict[str, Any]) -> list[dict[str, Any]]:
	rows = list(_safe_get(package, "forms", "forms") or [])
	out: list[dict[str, Any]] = []
	for row in rows[:SECTION_ROW_LIMIT]:
		if not isinstance(row, dict):
			continue
		out.append(
			{
				"code": str(row.get("form_code") or row.get("code") or ""),
				"label": str(row.get("label") or row.get("name") or ""),
				"category": str(row.get("category_code") or row.get("category") or ""),
				"required": str(row.get("default_required") or row.get("mandatory") or ""),
			}
		)
	return out


def _legacy_rules_rows(package: dict[str, Any], *, boq_only: bool = False) -> list[dict[str, Any]]:
	rows = list(_safe_get(package, "rules", "rules") or [])
	out: list[dict[str, Any]] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		code = str(row.get("rule_code") or row.get("code") or "")
		label = str(row.get("label") or row.get("name") or "")
		blob = f"{code} {label}".upper()
		if boq_only and "BOQ" not in blob and "BILL" not in blob and "QUANTIT" not in blob:
			continue
		if not boq_only and ("BOQ" in blob or "BILL" in blob or "QUANTIT" in blob):
			continue
		out.append(
			{
				"code": code,
				"label": label,
				"type": str(row.get("rule_type") or row.get("type") or ""),
				"enabled": str(row.get("enabled", True)),
			}
		)
		if len(out) >= SECTION_ROW_LIMIT:
			break
	return out


def _legacy_render_mapping_rows(package: dict[str, Any]) -> list[dict[str, Any]]:
	rows = list(_safe_get(package, "render_map", "render_sections") or [])
	out: list[dict[str, Any]] = []
	for row in rows[:SECTION_ROW_LIMIT]:
		if not isinstance(row, dict):
			continue
		out.append(
			{
				"source": str(row.get("source") or row.get("source_section") or row.get("label") or ""),
				"target_code": str(row.get("target_code") or row.get("target") or ""),
				"target_label": str(row.get("target_label") or row.get("target_name") or ""),
				"generated_element": str(row.get("generated_element") or row.get("output_key") or ""),
				"mandatory": str(row.get("mandatory") or "No"),
				"status": str(row.get("status") or "Valid"),
				"last_validated": str(row.get("last_validated") or ""),
			}
		)
	return out


def _std_config_sections_rows(package: dict[str, Any]) -> list[dict[str, Any]]:
	std_config = package.get("std_config")
	if not isinstance(std_config, dict):
		return []
	labels = {
		"metadata": "Metadata",
		"applicability": "Applicability",
		"tender_fields": "Tender Fields",
		"supplier_requirements": "Supplier Requirements",
		"forms_and_attachments": "Forms & Attachments",
		"evaluation_setup": "Evaluation Setup",
		"contract_terms": "Contract Terms",
		"rules": "Rules",
		"validations": "Validations",
	}
	out: list[dict[str, Any]] = []
	for key, label in labels.items():
		if key not in std_config:
			continue
		out.append({"code": key, "title": label, "mutability": "std_config", "part": "Configurator"})
	return out


def _std_config_parameters_rows(package: dict[str, Any]) -> list[dict[str, Any]]:
	fields = _safe_get(package, "std_config", "tender_fields", "fields") or []
	out: list[dict[str, Any]] = []
	for row in fields[:SECTION_ROW_LIMIT]:
		if not isinstance(row, dict):
			continue
		out.append(
			{
				"code": str(row.get("code") or ""),
				"label": str(row.get("label") or ""),
				"type": str(row.get("field_type") or ""),
				"group": str(row.get("group") or row.get("section") or ""),
			}
		)
	return out


def _std_config_forms_rows(package: dict[str, Any]) -> list[dict[str, Any]]:
	forms = _safe_get(package, "std_config", "forms_and_attachments", "forms") or []
	out: list[dict[str, Any]] = []
	for row in forms[:SECTION_ROW_LIMIT]:
		if not isinstance(row, dict):
			continue
		out.append(
			{
				"code": str(row.get("code") or row.get("label") or ""),
				"label": str(row.get("label") or row.get("name") or ""),
				"category": str(row.get("attachment_type") or row.get("purpose") or ""),
				"required": str(row.get("in_package") or ""),
			}
		)
	return out


def _std_config_rules_rows(package: dict[str, Any], *, boq_only: bool = False) -> list[dict[str, Any]]:
	if boq_only:
		return []
	rules = _safe_get(package, "std_config", "rules", "rules") or []
	validations = _safe_get(package, "std_config", "validations", "validations") or []
	out: list[dict[str, Any]] = []
	for row in rules[: SECTION_ROW_LIMIT // 2]:
		if not isinstance(row, dict):
			continue
		out.append(
			{
				"code": str(row.get("code") or ""),
				"label": str(row.get("when") or row.get("name") or ""),
				"type": "rule",
				"enabled": "Yes",
			}
		)
	for row in validations[: SECTION_ROW_LIMIT // 2]:
		if not isinstance(row, dict):
			continue
		out.append(
			{
				"code": str(row.get("code") or ""),
				"label": str(row.get("message") or ""),
				"type": "validation",
				"enabled": "Yes",
			}
		)
	return out[:SECTION_ROW_LIMIT]


def _std_config_mapping_rows(package: dict[str, Any]) -> list[dict[str, Any]]:
	mappings = _safe_get(package, "std_config", "output_mappings", "mappings") or []
	out: list[dict[str, Any]] = []
	for row in mappings[:SECTION_ROW_LIMIT]:
		if not isinstance(row, dict):
			continue
		out.append(
			{
				"source": str(row.get("source") or row.get("from") or ""),
				"target_code": str(row.get("target_code") or row.get("target") or ""),
				"target_label": str(row.get("target_label") or row.get("target_name") or ""),
				"generated_element": str(row.get("generated_element") or row.get("output_key") or ""),
				"mandatory": str(row.get("mandatory") or "No"),
				"status": str(row.get("status") or "Valid"),
				"last_validated": str(row.get("last_validated") or ""),
			}
		)
	return out


def project_advanced_section_content(package: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
	"""Return per-section projection payloads keyed by advanced section key."""
	if not isinstance(package, dict) or not package:
		return {}

	if isinstance(package.get("std_config"), dict):
		return {
			"sections_clauses": {
				"summary": _("Configurator sections present in package JSON."),
				"rows": _std_config_sections_rows(package),
			},
			"parameters": {
				"summary": _("Tender field definitions from std_config."),
				"rows": _std_config_parameters_rows(package),
			},
			"forms": {
				"summary": _("Forms and attachments from std_config."),
				"rows": _std_config_forms_rows(package),
			},
			"boq_rules": {"summary": _("No dedicated BOQ rule list in std_config packages."), "rows": []},
			"readiness_rules": {
				"summary": _("Rules and validations from std_config."),
				"rows": _std_config_rules_rows(package),
			},
			"generated_models": {
				"summary": _("Output mappings from std_config."),
				"rows": _std_config_mapping_rows(package),
			},
		}

	return {
		"sections_clauses": {
			"summary": _("Structured STD sections from the imported package."),
			"rows": _legacy_sections_rows(package),
		},
		"parameters": {
			"summary": _("Officer configuration fields from the imported package."),
			"rows": _legacy_parameters_rows(package),
		},
		"forms": {
			"summary": _("Bidder forms and activation metadata from the imported package."),
			"rows": _legacy_forms_rows(package),
		},
		"boq_rules": {
			"summary": _("BOQ and quantity-related rules from the imported package."),
			"rows": _legacy_rules_rows(package, boq_only=True),
		},
		"readiness_rules": {
			"summary": _("Validation and activation rules from the imported package."),
			"rows": _legacy_rules_rows(package, boq_only=False),
		},
		"generated_models": {
			"summary": _("Render-map targets from the imported package."),
			"rows": _legacy_render_mapping_rows(package),
		},
	}


def project_source_mappings(
	package: dict[str, Any] | None,
	*,
	fallback_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
	targets = [dict(row) for row in _DEFAULT_MAPPING_TARGETS]
	rows: list[dict[str, Any]] = []
	if isinstance(package, dict):
		if isinstance(package.get("std_config"), dict):
			rows = _std_config_mapping_rows(package)
		else:
			rows = _legacy_render_mapping_rows(package)
	if not rows and fallback_rows:
		rows = list(fallback_rows)
	return {"targets": targets, "rows": rows, "read_only": True}


def backfill_std_template_library_display_metadata(template_code: str | None = None) -> dict[str, Any]:
	"""Populate library-facing title/method fields from manifest or package_json."""
	filters: dict[str, Any] = {}
	if template_code:
		filters["template_code"] = template_code
	names = frappe.get_all("STD Template", filters=filters or None, pluck="name")
	updated: list[str] = []
	for name in names:
		doc = frappe.get_doc("STD Template", name)
		package = parse_package_json(doc.package_json)
		title = resolve_template_title(doc, package)
		methods = resolve_procurement_methods(doc, package)
		profile = format_procurement_method_profile(methods)
		changed = False
		if title and (doc.template_title or "").strip() != title:
			doc.template_title = title
			changed = True
		if profile and (doc.procurement_method_profile or "").strip() != profile:
			doc.procurement_method_profile = profile
			changed = True
		if changed:
			doc.flags.skip_std_template_guards = True
			doc.save(ignore_permissions=True)
			updated.append(str(doc.template_code or doc.name))
	if updated:
		frappe.db.commit()
	return {"ok": True, "updated": updated, "count": len(updated)}
