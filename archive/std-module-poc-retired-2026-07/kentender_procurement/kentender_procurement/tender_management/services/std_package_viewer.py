# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Administration Console POC — read-only package viewer summaries.

Builds structured data + HTML for ``STD Template`` admin inspection (Admin Step 3).
Does not mutate packages; parsing only.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

import frappe

DISPLAY_NA = "Not specified"
RAW_JSON_MAX_INLINE = 120_000


def _disp(val: Any) -> str:
	if val is None or val == "":
		return DISPLAY_NA
	if isinstance(val, bool):
		return "Yes" if val else "No"
	return str(val)


def _safe_get(d: dict, *keys: str, default: Any = None) -> Any:
	cur: Any = d
	for k in keys:
		if not isinstance(cur, dict) or k not in cur:
			return default
		cur = cur[k]
	return cur


def build_viewer_context(doc: Any, package: dict[str, Any]) -> dict[str, Any]:
	"""Return a dict for Jinja ``package_viewer.html`` and API responses."""
	manifest = package.get("manifest") or {}
	m_status = _safe_get(manifest, "status") or {}
	m_class = _safe_get(manifest, "classification") or {}
	m_src = _safe_get(manifest, "source_document") or {}
	m_auth = _safe_get(manifest, "authority") or {}
	m_jur = _safe_get(manifest, "jurisdiction") or {}
	m_ver = _safe_get(manifest, "versioning") or {}

	sections_root = package.get("sections") or {}
	section_rows = list(sections_root.get("sections") or [])
	section_rows.sort(key=lambda r: (r.get("render_order") is None, r.get("render_order") or 0))

	fields_root = package.get("fields") or {}
	field_rows = list(fields_root.get("fields") or [])
	fields_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
	for f in field_rows:
		g = f.get("group_code") or "UNGROUPED"
		fields_by_group[str(g)].append(f)

	rules_root = package.get("rules") or {}
	rule_rows = list(rules_root.get("rules") or [])
	enabled_rules = [r for r in rule_rows if r.get("enabled", True)]

	forms_root = package.get("forms") or {}
	form_rows = list(forms_root.get("forms") or [])
	default_req_forms = [f for f in form_rows if f.get("default_required")]

	sample = package.get("sample_tender") or {}
	tender_obj = sample.get("tender") or {}
	variants = list(sample.get("scenario_variants") or [])
	lots = list((tender_obj.get("lots") or [])) if isinstance(tender_obj.get("lots"), list) else []
	boq = list((sample.get("boq") or {}).get("rows") or [])
	exp_forms = list((sample.get("expected_outputs") or {}).get("expected_activated_forms") or [])

	render_map = package.get("render_map") or {}
	render_sections = list(render_map.get("render_sections") or [])
	render_minimal = len(render_sections) == 0

	structure = {
		"manifest_present": bool(manifest),
		"sections_count": len(section_rows),
		"fields_count": len(field_rows),
		"rules_count": len(rule_rows),
		"rules_enabled_count": len(enabled_rules),
		"forms_count": len(form_rows),
		"forms_default_required_count": len(default_req_forms),
		"sample_variant_count": len(variants),
		"sample_lot_count": len(lots),
		"sample_boq_row_count": len(boq),
	}

	overview_identity = {
		"template_code": _disp(manifest.get("template_code") or doc.template_code),
		"template_name": _disp(manifest.get("template_name") or doc.template_name),
		"template_short_name": _disp(manifest.get("template_short_name") or doc.template_short_name),
		"authority_name": _disp(m_auth.get("name")),
		"country_code": _disp(m_jur.get("country_code")),
		"procurement_category": _disp(m_class.get("procurement_category") or doc.procurement_category),
		"template_family": _disp(m_class.get("template_family") or doc.template_family),
		"source_document_code": _disp(m_src.get("source_document_code") or doc.source_document_code),
		"source_file_name": _disp(m_src.get("source_file_name") or doc.source_file_name),
		"source_file_hash": _disp(m_src.get("source_file_hash") or doc.source_file_hash),
		"source_version_label": _disp(m_ver.get("source_version_label") or doc.version_label),
		"package_version": _disp(m_ver.get("package_version") or doc.package_version),
		"manifest_package_status": _disp(m_status.get("package_status") or doc.status),
		"allowed_for_import": _disp(m_status.get("allowed_for_import")),
		"allowed_for_tender_creation": _disp(m_status.get("allowed_for_tender_creation")),
	}

	overview_audit = {
		"package_hash": _disp(doc.package_hash),
		"imported_at": _disp(getattr(doc, "imported_at", None)),
		"imported_by": _disp(getattr(doc, "imported_by", None)),
		"package_json_present": "Yes" if (doc.package_json or "").strip() else "No",
		"manifest_json_present": "Yes" if (doc.manifest_json or "").strip() else "No",
		"package_hash_length": str(len(doc.package_hash or "")),
	}

	rule_summaries: list[dict[str, Any]] = []
	for r in rule_rows[:500]:
		when = r.get("when") or {}
		then = r.get("then") or {}
		rule_summaries.append(
			{
				"rule_code": _disp(r.get("rule_code")),
				"label": _disp(r.get("label")),
				"rule_type": _disp(r.get("rule_type")),
				"enabled": _disp(r.get("enabled", True)),
				"severity": _disp(r.get("severity")),
				"conditions_summary": json.dumps(when, sort_keys=True)[:240],
				"effects_summary": json.dumps(then, sort_keys=True)[:240],
			}
		)

	form_summaries: list[dict[str, Any]] = []
	for f in form_rows[:500]:
		act = f.get("activation_rule_codes") or f.get("activation_rules") or []
		if isinstance(act, list):
			act_s = ", ".join(str(x) for x in act[:12])
		else:
			act_s = _disp(act)
		cd = f.get("checklist_display") if isinstance(f.get("checklist_display"), dict) else {}
		disp_o = cd.get("display_order")
		form_summaries.append(
			{
				"display_order": disp_o,
				"display_group": _disp(cd.get("display_group")),
				"form_code": _disp(f.get("form_code")),
				"title": _disp(f.get("title")),
				"default_required": _disp(f.get("default_required", False)),
				"activation_rules": act_s or DISPLAY_NA,
				"evidence_policy": _disp(f.get("evidence_policy")),
			}
		)
	form_summaries.sort(
		key=lambda x: (
			x["display_order"] is None,
			x["display_order"] if isinstance(x["display_order"], int) else 9999,
			x["form_code"],
		)
	)

	variant_rows: list[dict[str, Any]] = []
	for v in variants:
		variant_rows.append(
			{
				"variant_code": _disp(v.get("variant_code")),
				"description": _disp(v.get("description")),
				"expected_blockers": v.get("expected_blockers", 0),
			}
		)

	render_rows: list[dict[str, Any]] = []
	for rs in render_sections[:200]:
		render_rows.append(
			{
				"component_code": _disp(rs.get("render_component_code") or rs.get("component_code")),
				"section_code": _disp(rs.get("section_code")),
				"template_partial": _disp(rs.get("template_partial") or rs.get("partial")),
				"render_order": _disp(rs.get("render_order")),
				"included_in_poc": _disp(rs.get("included_in_poc_render", rs.get("included_in_poc"))),
				"notes": _disp(rs.get("notes")),
			}
		)

	full_pkg_text = json.dumps(package, indent=2, sort_keys=True, default=str)
	raw_truncated = len(full_pkg_text) > RAW_JSON_MAX_INLINE
	raw_display = full_pkg_text[:RAW_JSON_MAX_INLINE] + (
		"\n\n… truncated for inline viewer …" if raw_truncated else ""
	)

	return {
		"doc": doc,
		"overview_cards": {
			"template_code": _disp(doc.template_code),
			"template_name": _disp(doc.template_name),
			"package_version": _disp(doc.package_version),
			"source_version": _disp(doc.version_label),
			"procurement_category": _disp(doc.procurement_category),
			"status": _disp(doc.status),
			"package_hash": _disp(doc.package_hash),
			"imported_at": _disp(getattr(doc, "imported_at", None)),
		},
		"overview_identity": overview_identity,
		"overview_audit": overview_audit,
		"structure": structure,
		"section_rows": section_rows,
		"fields_by_group": dict(fields_by_group),
		"rule_summaries": rule_summaries,
		"form_summaries": form_summaries,
		"sample": sample,
		"tender_obj": tender_obj,
		"sample_lots": lots,
		"sample_boq": boq,
		"expected_forms": exp_forms,
		"variant_rows": variant_rows,
		"render_rows": render_rows,
		"render_minimal": render_minimal,
		"raw_display": raw_display,
		"raw_truncated": raw_truncated,
	}


def render_package_viewer_html(doc: Any, package: dict[str, Any]) -> str:
	ctx = build_viewer_context(doc, package)
	ctx["package"] = package
	return frappe.render_template("templates/std_admin_console/package_viewer.html", ctx)


def build_api_payload(doc: Any, package: dict[str, Any]) -> dict[str, Any]:
	"""Shape aligned with Admin Step 3 spec §20.1 (+ ``html`` for Desk)."""
	ctx = build_viewer_context(doc, package)
	html = frappe.render_template("templates/std_admin_console/package_viewer.html", ctx)
	return {
		"ok": True,
		"html": html,
		"template": {
			"name": doc.name,
			"template_code": doc.template_code,
		},
		"overview": {
			"cards": ctx["overview_cards"],
			"identity": ctx["overview_identity"],
			"audit": ctx["overview_audit"],
		},
		"structure": ctx["structure"],
		"sections": ctx["section_rows"],
		"fields": ctx["fields_by_group"],
		"rules": ctx["rule_summaries"],
		"forms": ctx["form_summaries"],
		"sample_tender": {
			"meta": ctx["sample"],
			"tender": ctx["tender_obj"],
			"lots": ctx["sample_lots"],
			"boq_rows": ctx["sample_boq"],
			"expected_activated_forms": ctx["expected_forms"],
			"variants": ctx["variant_rows"],
		},
		"render_map": {
			"rows": ctx["render_rows"],
			"minimal": ctx["render_minimal"],
		},
		"raw_components": {
			"keys": ["manifest", "sections", "fields", "rules", "forms", "render_map", "sample_tender", "full_package"],
			"inline_preview_truncated": ctx["raw_truncated"],
		},
	}
