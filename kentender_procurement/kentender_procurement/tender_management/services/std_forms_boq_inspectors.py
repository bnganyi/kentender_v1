# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Admin Console Step 6 — read-only Required Forms and BoQ inspectors (structured + HTML)."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

import frappe
from frappe.model.document import Document

from kentender_procurement.tender_management.services import std_template_engine as engine

WORKS_BOQ_CATEGORIES: tuple[str, ...] = (
	"PRELIMINARIES",
	"SUBSTRUCTURE",
	"SUPERSTRUCTURE",
	"ROOFING",
	"FINISHES",
	"EXTERNAL_WORKS",
	"DAYWORKS",
	"PROVISIONAL_SUMS",
	"GRAND_SUMMARY",
)

BOQ_POC_WARNING = (
	"POC BoQ: These rows are representative sample data from STD-WORKS-POC. "
	"They are not a production bill of quantities and must not be used for real pricing, "
	"evaluation, or contract quantities."
)


def _get_tender_read(tender_name: str) -> Document:
	if not tender_name:
		frappe.throw(frappe._("tender_name is required."), frappe.ValidationError)
	if not frappe.db.exists("Procurement Tender", tender_name):
		frappe.throw(
			frappe._("Procurement Tender {0} was not found.").format(tender_name),
			frappe.DoesNotExistError,
		)
	doc = frappe.get_doc("Procurement Tender", tender_name)
	doc.check_permission("read")
	return doc


def _child_rows_to_dicts(child_rows: list[Any] | None) -> list[dict[str, Any]]:
	if not child_rows:
		return []
	out: list[dict[str, Any]] = []
	for row in child_rows:
		ad = getattr(row, "as_dict", None)
		if callable(ad):
			out.append(ad())
		elif isinstance(row, dict):
			out.append(row)
		else:
			out.append(dict(row))
	return out


def _parse_cfg(doc: Document) -> dict[str, Any]:
	raw = getattr(doc, "configuration_json", None) or ""
	if not raw:
		return {}
	try:
		p = json.loads(raw)
		return p if isinstance(p, dict) else {}
	except json.JSONDecodeError:
		return {}


def _load_forms_metadata(template: dict[str, Any]) -> dict[str, dict[str, Any]]:
	try:
		forms_pkg = engine.get_package_component(template, "forms")
	except (ValueError, KeyError):
		return {}
	by_code: dict[str, dict[str, Any]] = {}
	for f in forms_pkg.get("forms") or []:
		code = f.get("form_code")
		if code:
			by_code[str(code)] = f
	return by_code


def _load_sample_tender(template: dict[str, Any]) -> dict[str, Any]:
	try:
		st = engine.get_package_component(template, "sample_tender")
	except (ValueError, KeyError):
		return {}
	return st if isinstance(st, dict) else {}


def _detect_variant_code(cfg: dict[str, Any], sample: dict[str, Any]) -> str | None:
	best: tuple[int, str] | None = None
	for v in sample.get("scenario_variants") or []:
		over = v.get("configuration_overrides") or {}
		if not over:
			continue
		if all(cfg.get(k) == val for k, val in over.items()):
			n = len(over)
			vc = str(v.get("variant_code") or "")
			if vc and (best is None or n > best[0]):
				best = (n, vc)
	return best[1] if best else None


def _expected_form_codes(sample: dict[str, Any], variant_code: str | None) -> list[str]:
	primary = list(sample.get("expected_activated_forms") or [])
	if not variant_code:
		return sorted(primary)
	for v in sample.get("scenario_variants") or []:
		if str(v.get("variant_code") or "") != variant_code:
			continue
		exp = set(primary)
		exp |= set(v.get("expected_additional_forms") or [])
		exp -= set(v.get("expected_inactive_forms") or [])
		return sorted(exp)
	return sorted(primary)


def _activation_explanation(activation_source: str) -> str:
	src = (activation_source or "").strip()
	if not src:
		return "Unknown"
	if src == "DEFAULT" or src.startswith("DEFAULT"):
		return "Default-required form from package (forms.json)."
	parts = [p.strip() for p in src.split(";") if p.strip()]
	readable = []
	for p in parts:
		if p == "DEFAULT":
			readable.append("default-required")
		elif p.startswith("RULE:"):
			readable.append(f"rule {p[5:]}")
		else:
			readable.append(p)
	return "Activation: " + "; ".join(readable) + "."


def _classify_boq_row(row: dict[str, Any]) -> str:
	cat = str(row.get("item_category") or "")
	if cat == "GRAND_SUMMARY":
		return "Summary"
	if row.get("is_priced_by_bidder") in (1, True, "1"):
		return "Bidder priced"
	amt = row.get("amount")
	if amt not in (None, "", 0) and row.get("is_priced_by_bidder") not in (1, True, "1"):
		return "Fixed amount / provisional"
	return "Other"


def get_required_forms_inspection(tender_name: str) -> dict[str, Any]:
	tender = _get_tender_read(tender_name)
	warnings: list[str] = []
	rows_raw = _child_rows_to_dicts(tender.get("required_forms"))
	template: dict[str, Any] | None = None
	forms_meta: dict[str, dict[str, Any]] = {}
	sample: dict[str, Any] = {}

	if tender.std_template:
		try:
			template = engine.load_template(tender.std_template)
			forms_meta = _load_forms_metadata(template)
			sample = _load_sample_tender(template)
		except Exception as e:
			warnings.append(f"Could not load STD Template package metadata: {e}")
	else:
		warnings.append("Tender has no STD Template linked; package metadata unavailable.")

	cfg = _parse_cfg(tender)
	variant_detected = _detect_variant_code(cfg, sample) if sample else None

	form_codes = [str(r.get("form_code") or "") for r in rows_raw]
	code_counts = Counter(c for c in form_codes if c)
	dup_codes = sorted([c for c, n in code_counts.items() if n > 1])
	if dup_codes:
		warnings.append(f"Duplicate form_code rows: {', '.join(dup_codes)}")

	default_n = 0
	rule_n = 0
	by_stage: Counter[str] = Counter()
	by_policy: Counter[str] = Counter()

	rows_out: list[dict[str, Any]] = []
	for r in rows_raw:
		fc = str(r.get("form_code") or "")
		meta = forms_meta.get(fc, {})
		src = str(r.get("activation_source") or "")
		parts = [p.strip() for p in src.split(";") if p.strip()]
		if any(p == "DEFAULT" or p.startswith("DEFAULT") for p in parts):
			default_n += 1
		if any(p.startswith("RULE:") for p in parts):
			rule_n += 1
		stg = str(r.get("workflow_stage") or meta.get("workflow_stage") or "")
		pol = str(r.get("evidence_policy") or meta.get("evidence_policy") or "")
		if stg:
			by_stage[stg] += 1
		if pol:
			by_policy[pol] += 1
		dup = code_counts.get(fc, 0) > 1
		rows_out.append(
			{
				"display_order": r.get("display_order"),
				"display_group": r.get("display_group") or meta.get("display_group"),
				"form_code": fc,
				"form_title": r.get("form_title") or meta.get("title") or meta.get("form_title") or fc,
				"required": bool(r.get("required")),
				"activation_source": src,
				"activation_explanation": _activation_explanation(src),
				"evidence_policy": pol,
				"respondent_type": r.get("respondent_type") or meta.get("respondent_type"),
				"workflow_stage": stg,
				"notes": r.get("notes"),
				"package_source_exists": fc in forms_meta,
				"duplicate_row": dup,
			}
		)

	if not rows_raw:
		warnings.append(
			"No required forms rows on this tender yet. Run Generate Required Forms (STD POC) after validation allows it."
		)

	expected_codes = set(_expected_form_codes(sample, variant_detected)) if sample else set()
	observed = {str(r.get("form_code") or "") for r in rows_raw if r.get("form_code")}
	expected_comparison: list[dict[str, Any]] = []
	if expected_codes:
		all_codes = sorted(expected_codes | observed)
		for code in all_codes:
			exp = code in expected_codes
			obs = code in observed
			if exp and obs:
				status = "match"
			elif exp and not obs:
				status = "missing"
			elif obs and not exp:
				status = "extra"
			else:
				status = "unknown"
			expected_comparison.append(
				{"form_code": code, "expected": exp, "observed": obs, "status": status}
			)

	summary = {
		"total_forms": len(rows_raw),
		"unique_form_codes": len(code_counts),
		"duplicate_form_code_count": len(dup_codes),
		"default_activated_count": default_n,
		"rule_activated_count": rule_n,
		"by_workflow_stage": dict(by_stage),
		"by_evidence_policy": dict(by_policy),
	}

	out_rf: dict[str, Any] = {
		"ok": True,
		"tender": tender.name,
		"template_code": tender.template_code or (tender.std_template or ""),
		"variant_detected": variant_detected,
		"summary": summary,
		"rows": rows_out,
		"expected_comparison": expected_comparison,
		"warnings": warnings,
	}
	out_rf["html"] = render_forms_inspector_html(out_rf)
	return out_rf


def get_boq_inspection(tender_name: str) -> dict[str, Any]:
	tender = _get_tender_read(tender_name)
	warnings: list[str] = []
	boq_rows = _child_rows_to_dicts(tender.get("boq_items"))
	lots_rows = _child_rows_to_dicts(tender.get("lots"))
	lot_map = {str(l.get("lot_code") or ""): str(l.get("lot_title") or "") for l in lots_rows}
	lot_codes = {str(l.get("lot_code") or "") for l in lots_rows if l.get("lot_code")}

	item_codes = [str(r.get("item_code") or "") for r in boq_rows]
	ic_counts = Counter(c for c in item_codes if c)
	dup_items = sorted([c for c, n in ic_counts.items() if n > 1])
	if dup_items:
		warnings.append(f"Duplicate item_code: {', '.join(dup_items)}")

	bidder_priced = sum(
		1 for r in boq_rows if r.get("is_priced_by_bidder") in (1, True, "1")
	)
	fixed_amt = 0
	for r in boq_rows:
		if r.get("is_priced_by_bidder") in (1, True, "1"):
			continue
		if r.get("amount") not in (None, "", 0):
			fixed_amt += 1

	cat_counts: Counter[str] = Counter()
	for r in boq_rows:
		cat = str(r.get("item_category") or "")
		if cat:
			cat_counts[cat] += 1

	category_coverage: list[dict[str, Any]] = []
	for cat in WORKS_BOQ_CATEGORIES:
		n = cat_counts.get(cat, 0)
		category_coverage.append(
			{
				"category": cat,
				"row_count": n,
				"present": n > 0,
			}
		)
	other_n = sum(n for c, n in cat_counts.items() if c not in WORKS_BOQ_CATEGORIES)
	if other_n:
		category_coverage.append(
			{"category": "OTHER", "row_count": other_n, "present": True}
		)

	missing_required = [c["category"] for c in category_coverage if not c["present"] and c["category"] != "OTHER"]

	rows_out: list[dict[str, Any]] = []
	lot_checks: list[dict[str, Any]] = []
	for r in boq_rows:
		lc = str(r.get("lot_code") or "").strip()
		lt = ""
		check_status = "ok"
		note = ""
		if lc:
			if lc in lot_codes:
				lt = lot_map.get(lc, "")
			else:
				check_status = "invalid_lot"
				note = f"lot_code {lc!r} not found on tender lots"
				warnings.append(f"BoQ row {r.get('item_code')}: {note}")
		elif str(r.get("item_category") or "") == "GRAND_SUMMARY":
			check_status = "summary_unlinked"
			note = "Grand summary may omit lot reference (allowed)"
		rows_out.append(
			{
				"item_code": r.get("item_code"),
				"lot_code": lc or None,
				"lot_title": lt,
				"item_category": r.get("item_category"),
				"description": (r.get("description") or "")[:120],
				"unit": r.get("unit"),
				"quantity": r.get("quantity"),
				"rate": r.get("rate"),
				"amount": r.get("amount"),
				"is_priced_by_bidder": bool(r.get("is_priced_by_bidder")),
				"row_type": _classify_boq_row(r),
				"validation_note": note,
				"lot_reference_status": check_status,
			}
		)
		lot_checks.append(
			{
				"item_code": r.get("item_code"),
				"lot_code": lc or None,
				"status": check_status,
			}
		)

	val_rows = _child_rows_to_dicts(tender.get("validation_messages"))
	boq_related_msgs = [
		str(m.get("message") or m.get("title") or "")
		for m in val_rows
		if "boq" in str(m.get("message") or "").lower()
		or "BoQ" in str(m.get("message") or "")
	]

	rule_hints = {
		"boq_rows_present": len(boq_rows) > 0,
		"dayworks_row_present": cat_counts.get("DAYWORKS", 0) > 0,
		"provisional_sums_present": cat_counts.get("PROVISIONAL_SUMS", 0) > 0,
		"multiple_lots": len([c for c in lot_codes if c]) > 1,
		"validation_messages_boq": [x for x in boq_related_msgs if x][:5],
	}

	if not boq_rows:
		warnings.append(
			"No BoQ rows on this tender yet. Run Generate Sample BoQ (STD POC) to load representative rows."
		)

	summary = {
		"row_count": len(boq_rows),
		"unique_item_code_count": len(ic_counts),
		"duplicate_item_code_count": len(dup_items),
		"bidder_priced_count": bidder_priced,
		"fixed_amount_count": fixed_amt,
		"distinct_category_count": len([c for c, n in cat_counts.items() if n]),
		"missing_standard_categories": missing_required,
		"invalid_lot_reference_count": sum(
			1 for x in lot_checks if x.get("status") == "invalid_lot"
		),
	}

	out_bq: dict[str, Any] = {
		"ok": True,
		"tender": tender.name,
		"poc_warning": BOQ_POC_WARNING,
		"summary": summary,
		"rows": rows_out,
		"category_coverage": category_coverage,
		"lot_reference_checks": lot_checks,
		"rule_relationship": rule_hints,
		"warnings": warnings,
	}
	out_bq["html"] = render_boq_inspector_html(out_bq)
	return out_bq


def render_forms_inspector_html(payload: dict[str, Any]) -> str:
	return frappe.render_template(
		"templates/std_admin_console/forms_inspector.html",
		payload,
	)


def render_boq_inspector_html(payload: dict[str, Any]) -> str:
	return frappe.render_template(
		"templates/std_admin_console/boq_inspector.html",
		payload,
	)


def get_demo_inspector_summary(tender_name: str) -> dict[str, Any]:
	"""Single round-trip: structured inspection + HTML fragments for the demo workspace."""
	rf = get_required_forms_inspection(tender_name)
	bq = get_boq_inspection(tender_name)
	return {
		"ok": bool(rf.get("ok") and bq.get("ok")),
		"tender": rf.get("tender") or tender_name,
		"required_forms": rf,
		"boq": bq,
		"forms_html": render_forms_inspector_html(rf),
		"boq_html": render_boq_inspector_html(bq),
	}
