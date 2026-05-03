# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 5 §23 tender-stage snapshot + SHA-256 (WH-009, WH-011).

WH-011: validation reference, preview/source hashes, planning lineage counts,
``boq.bills`` grouping, BoQ items content digest (doc 4 §17.2 audit reconstruction).
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any

from frappe.utils import now_datetime

_BOQ_DIGEST_FIELDS = (
	"item_code",
	"bill_code",
	"item_number",
	"quantity",
	"formula_type",
	"item_category",
	"lot_code",
)


def _row_dicts(rows: list[Any] | None) -> list[dict[str, Any]]:
	if not rows:
		return []
	out: list[dict[str, Any]] = []
	for row in rows:
		ad = getattr(row, "as_dict", None)
		if callable(ad):
			out.append(ad())
		elif isinstance(row, dict):
			out.append(dict(row))
		else:
			out.append(dict(row))
	return out


def _sha256_utf8(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_validation_reference(tender_doc: Any) -> dict[str, Any]:
	raw = getattr(tender_doc, "works_hardening_validation_json", None) or ""
	s = str(raw).strip()
	if not s:
		return {
			"present": False,
			"status": None,
			"boundary_code": None,
			"critical_count": 0,
			"high_count": 0,
			"medium_count": 0,
			"low_count": 0,
			"info_count": 0,
			"finding_codes": [],
			"validation_json_sha256": None,
		}
	try:
		env = json.loads(s)
	except json.JSONDecodeError:
		return {
			"present": True,
			"status": None,
			"boundary_code": None,
			"critical_count": 0,
			"high_count": 0,
			"medium_count": 0,
			"low_count": 0,
			"info_count": 0,
			"finding_codes": [],
			"validation_json_sha256": _sha256_utf8(s),
			"parse_error": True,
		}
	findings = env.get("findings") if isinstance(env, dict) else None
	codes: list[str] = []
	if isinstance(findings, list):
		for f in findings:
			if isinstance(f, dict):
				c = f.get("finding_code")
				if c:
					codes.append(str(c))
	codes = sorted(set(codes))
	return {
		"present": True,
		"status": env.get("status") if isinstance(env, dict) else None,
		"boundary_code": env.get("boundary_code") if isinstance(env, dict) else None,
		"critical_count": int(env.get("critical_count") or 0) if isinstance(env, dict) else 0,
		"high_count": int(env.get("high_count") or 0) if isinstance(env, dict) else 0,
		"medium_count": int(env.get("medium_count") or 0) if isinstance(env, dict) else 0,
		"low_count": int(env.get("low_count") or 0) if isinstance(env, dict) else 0,
		"info_count": int(env.get("info_count") or 0) if isinstance(env, dict) else 0,
		"finding_codes": codes,
		"validation_json_sha256": _sha256_utf8(s),
	}


def _build_preview_reference(tender_doc: Any) -> dict[str, Any]:
	val_raw = getattr(tender_doc, "works_hardening_validation_json", None) or ""
	return {
		"generated_tender_pack_html_len": len(
			getattr(tender_doc, "generated_tender_pack_html", "") or ""
		),
		"configuration_hash": getattr(tender_doc, "configuration_hash", None) or "",
		"source_package_hash": getattr(tender_doc, "source_package_hash", None) or "",
		"package_hash": getattr(tender_doc, "package_hash", None) or "",
		"works_hardening_validation_json_len": len(str(val_raw)),
	}


def _build_bills_from_items(boq_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	by_bill: dict[str, list[dict[str, Any]]] = defaultdict(list)
	for r in boq_rows:
		bc = str(r.get("bill_code") or "").strip() or "__NO_BILL__"
		by_bill[bc].append(r)
	out: list[dict[str, Any]] = []
	for bill_code in sorted(by_bill.keys()):
		rows = by_bill[bill_code]
		title = ""
		for r in rows:
			t = str(r.get("bill_title") or "").strip()
			if t:
				title = t
				break
		item_codes = sorted(
			{str(r.get("item_code") or "").strip() for r in rows if str(r.get("item_code") or "").strip()}
		)
		out.append(
			{
				"bill_code": bill_code if bill_code != "__NO_BILL__" else "",
				"bill_title": title,
				"item_count": len(rows),
				"item_codes": item_codes,
			}
		)
	return out


def _boq_items_content_digest(boq_rows: list[dict[str, Any]]) -> str:
	rows_sorted = sorted(boq_rows, key=lambda r: str(r.get("item_code") or ""))
	canonical: list[dict[str, Any]] = []
	for r in rows_sorted:
		canonical.append(
			{k: r.get(k) for k in _BOQ_DIGEST_FIELDS},
		)
	serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)
	return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_snapshot(tender_doc: Any) -> dict[str, Any]:
	"""Assemble §23 baseline JSON (sorted keys at hash time only)."""
	cfg: dict[str, Any] = {}
	raw = getattr(tender_doc, "configuration_json", None)
	if raw and str(raw).strip():
		try:
			parsed = json.loads(raw)
			if isinstance(parsed, dict):
				cfg = parsed
		except json.JSONDecodeError:
			cfg = {}

	tender_header = {
		"name": tender_doc.name,
		"tender_title": getattr(tender_doc, "tender_title", None),
		"tender_reference": getattr(tender_doc, "tender_reference", None),
		"std_template": getattr(tender_doc, "std_template", None),
		"template_code": getattr(tender_doc, "template_code", None),
		"procurement_category": getattr(tender_doc, "procurement_category", None),
		"tender_status": getattr(tender_doc, "tender_status", None),
		"validation_status": getattr(tender_doc, "validation_status", None),
		"works_hardening_status": getattr(tender_doc, "works_hardening_status", None),
		"configuration_hash": getattr(tender_doc, "configuration_hash", None) or "",
		"works_hardening_checked_at": getattr(tender_doc, "works_hardening_checked_at", None),
	}

	boq_rows = _row_dicts(getattr(tender_doc, "boq_items", None))
	bills = _build_bills_from_items(boq_rows)
	items_digest = _boq_items_content_digest(boq_rows) if boq_rows else ""
	boq = {
		"boq_code": next((r.get("boq_code") for r in boq_rows if r.get("boq_code")), ""),
		"version": next((r.get("boq_version") for r in boq_rows if r.get("boq_version")), "V1"),
		"bills": bills,
		"items": boq_rows,
		"items_content_sha256": items_digest,
	}

	forms_rows = _row_dicts(getattr(tender_doc, "required_forms", None))
	form_codes = sorted(
		{str(r.get("form_code") or "").strip() for r in forms_rows if str(r.get("form_code") or "").strip()}
	)
	validation_block = _build_validation_reference(tender_doc)
	validation_block["required_forms_count"] = len(forms_rows)
	validation_block["required_forms_codes"] = form_codes

	return {
		"snapshot_type": "WORKS_TENDER_STAGE_BASELINE",
		"snapshot_version": "V1",
		"tender": tender_header,
		"planning_lineage": {
			"procurement_plan": getattr(tender_doc, "procurement_plan", None),
			"procurement_package": getattr(tender_doc, "procurement_package", None),
			"procurement_template": getattr(tender_doc, "procurement_template", None),
			"source_package_code": getattr(tender_doc, "source_package_code", None),
			"source_package_hash": getattr(tender_doc, "source_package_hash", None),
			"source_demand_count": getattr(tender_doc, "source_demand_count", None),
			"source_budget_line_count": getattr(tender_doc, "source_budget_line_count", None),
		},
		"std_binding": {
			"std_template": getattr(tender_doc, "std_template", None),
			"template_code": getattr(tender_doc, "template_code", None),
			"template_version": getattr(tender_doc, "template_version", None),
			"package_hash": getattr(tender_doc, "package_hash", None),
		},
		"configuration": cfg,
		"works_requirements": _row_dicts(getattr(tender_doc, "works_requirements", None)),
		"section_attachments": _row_dicts(getattr(tender_doc, "section_attachments", None)),
		"lots": _row_dicts(getattr(tender_doc, "lots", None)),
		"boq": boq,
		"required_forms": forms_rows,
		"derived_model_readiness": _row_dicts(
			getattr(tender_doc, "derived_model_readiness", None)
		),
		"validation": validation_block,
		"preview": _build_preview_reference(tender_doc),
		"generated_at": now_datetime().isoformat(),
		"generated_by": getattr(tender_doc, "modified_by", None) or "Administrator",
	}


def hash_snapshot(payload: dict[str, Any]) -> str:
	"""Deterministic SHA-256 hex digest (sorted JSON keys)."""
	serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
	return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
