# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 5 §15–§16 Works tender-stage hardening services (WH-009).

Orchestrates normalization (§16.1), validation (§16.2 / §18 via
``works_tender_hardening_validation``), snapshot baseline (§23), and read APIs
(§16.3). ``harden_works_boq_structure`` seeds STD sample BoQ/lots when required
and empty (doc 5 §21). Snapshot depth **WH-011**; Desk entrypoints in
``procurement_tender`` (WH-012).
"""

from __future__ import annotations

import json
from typing import Any, Callable

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.services import std_template_engine as engine
from kentender_procurement.tender_management.services import works_tender_hardening_validation as wv
from kentender_procurement.tender_management.services.works_tender_snapshot import (
	build_snapshot,
	hash_snapshot,
)

# --- §15 constants (doc 5) ---
HARDENING_STATUS_NOT_CHECKED = "Not Checked"
HARDENING_STATUS_PASS = "Pass"
HARDENING_STATUS_WARNING = "Warning"
HARDENING_STATUS_BLOCKED = "Blocked"
HARDENING_STATUS_FAILED = "Failed"
HARDENING_STATUS_DEFERRED = "Deferred"

SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"
SEVERITY_MEDIUM = "Medium"
SEVERITY_LOW = "Low"
SEVERITY_INFO = "Info"

AREA_WORKS_REQUIREMENTS = "Works Requirements"
AREA_ATTACHMENTS = "Attachments"
AREA_BOQ = "BoQ"
AREA_LOTS = "Lots"
AREA_FORMS = "Forms"
AREA_DERIVED_MODELS = "Derived Models"
AREA_AUDIT = "Audit"
AREA_LEGACY_LOCKOUT = "Legacy Lockout"
AREA_PLANNING_HANDOFF = "Planning Handoff"
AREA_STD_BINDING = "STD Binding"

_WORKS_REQUIREMENT_SEED: tuple[
	tuple[str, str, str, int, int, int, int, str | None], ...
] = (
	("WRK_SCOPE", "Scope", "Scope of Works", 1, 1, 1, 10, "WORKS.SCOPE_SUMMARY"),
	("WRK_SITE", "Site Information", "Site Information", 1, 0, 1, 20, None),
	(
		"WRK_SPEC",
		"Technical Specification",
		"Technical Specifications",
		1,
		0,
		1,
		30,
		"WORKS.SPECIFICATION_SUMMARY",
	),
	(
		"WRK_DRAWINGS",
		"Drawing Register",
		"Drawings Register",
		1,
		0,
		1,
		40,
		None,
	),
	(
		"WRK_ESHS",
		"ESHS / HSE",
		"ESHS / HSE Requirements",
		1,
		1,
		1,
		50,
		"WORKS.ESHS_REQUIREMENTS",
	),
	(
		"WRK_PROGRAMME",
		"Work Programme",
		"Work Programme Requirement",
		1,
		1,
		0,
		60,
		None,
	),
	(
		"WRK_PERSONNEL",
		"Key Personnel",
		"Key Personnel Requirement",
		1,
		1,
		0,
		70,
		None,
	),
	(
		"WRK_EQUIPMENT",
		"Equipment",
		"Equipment Requirement",
		1,
		1,
		0,
		80,
		None,
	),
	(
		"WRK_COMPLETION",
		"Completion Period",
		"Completion Period",
		1,
		0,
		1,
		90,
		None,
	),
	(
		"WRK_DLP",
		"Defects Liability",
		"Defects Liability Period",
		1,
		0,
		1,
		100,
		None,
	),
)

_SECTION_ATTACHMENT_SEED: tuple[dict[str, Any], ...] = (
	{
		"attachment_code": "FILE-DWG-MOH-HOSP-001",
		"file_name": "hospital_site_layout_v1.pdf",
		"section_code": "SEC-DRAWINGS",
		"component_code": "WRK_DRAWINGS",
		"attachment_type": "Drawing",
		"supplier_facing": 1,
		"internal_only": 0,
	},
	{
		"attachment_code": "FILE-DWG-MOH-HOSP-002",
		"file_name": "ward_block_renovation_drawings_v1.pdf",
		"section_code": "SEC-DRAWINGS",
		"component_code": "WRK_DRAWINGS",
		"attachment_type": "Drawing",
		"supplier_facing": 1,
		"internal_only": 0,
	},
	{
		"attachment_code": "FILE-SPEC-MOH-HOSP-001",
		"file_name": "hospital_renovation_technical_specifications_v1.pdf",
		"section_code": "SEC-SPECIFICATION",
		"component_code": "WRK_SPEC",
		"attachment_type": "Technical Specification",
		"supplier_facing": 1,
		"internal_only": 0,
	},
)


def _parse_configuration_json_optional(doc: Document) -> dict[str, Any]:
	raw = doc.configuration_json
	if not raw or not str(raw).strip():
		return {}
	try:
		parsed = json.loads(raw)
	except json.JSONDecodeError:
		return {}
	return parsed if isinstance(parsed, dict) else {}


def _cfg_truthy(cfg: dict[str, Any], key: str) -> bool:
	v = cfg.get(key)
	if v in (1, True, "1", "true", "True", "yes", "YES"):
		return True
	if isinstance(v, str) and v.strip().lower() in ("true", "yes", "1"):
		return True
	return False


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


def _load_tender_write(tender_name: str) -> Document:
	if not tender_name:
		frappe.throw(frappe._("tender_name is required."), frappe.ValidationError)
	if not frappe.db.exists("Procurement Tender", tender_name):
		frappe.throw(
			frappe._("Procurement Tender {0} was not found.").format(tender_name),
			frappe.DoesNotExistError,
		)
	doc = frappe.get_doc("Procurement Tender", tender_name)
	doc.check_permission("write")
	return doc


def _load_tender_read(tender_name: str) -> Document:
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


def _result(ok: bool, tender_name: str, *, changed: bool = False, **extra: Any) -> dict[str, Any]:
	return {"ok": ok, "tender": tender_name, "changed": changed, **extra}


def initialize_works_requirements(tender_name: str) -> dict[str, Any]:
	doc = _load_tender_write(tender_name)
	if doc.get("works_requirements"):
		return _result(True, tender_name, changed=False, works_requirements="skipped_nonempty")
	cfg = _parse_configuration_json_optional(doc)
	for (
		code,
		ctype,
		title,
		supplier,
		submission,
		cfwd,
		disp,
		cfg_key,
	) in _WORKS_REQUIREMENT_SEED:
		text = ""
		if cfg_key:
			val = cfg.get(cfg_key)
			if val not in (None, ""):
				text = str(val)
		if not text:
			text = f"Draft placeholder for {code} — populate from tender configuration."
		doc.append(
			"works_requirements",
			{
				"component_code": code,
				"component_type": ctype,
				"title": title,
				"structured_text": text,
				"supplier_facing": supplier,
				"submission_linked": submission,
				"contract_carry_forward": cfwd,
				"status": "Draft",
				"version": "V1",
				"display_order": disp,
			},
		)
	doc.save()
	return _result(
		True, tender_name, changed=True, works_requirements_seeded=len(_WORKS_REQUIREMENT_SEED)
	)


def initialize_section_attachments(tender_name: str) -> dict[str, Any]:
	doc = _load_tender_write(tender_name)
	if doc.get("section_attachments"):
		return _result(True, tender_name, changed=False, section_attachments="skipped_nonempty")
	for row in _SECTION_ATTACHMENT_SEED:
		doc.append(
			"section_attachments",
			{
				**row,
				"version": "V1",
				"status": "Draft",
				"publication_included": 0,
				"notes": "",
			},
		)
	doc.save()
	return _result(
		True, tender_name, changed=True, section_attachments_seeded=len(_SECTION_ATTACHMENT_SEED)
	)


def harden_works_boq_structure(tender_name: str) -> dict[str, Any]:
	"""Doc 5 §21 — normalize BoQ rows; seed STD sample BoQ/lots when required and empty."""
	doc = _load_tender_write(tender_name)
	cfg = _parse_configuration_json_optional(doc)
	seeded = False
	if (
		not (doc.get("boq_items") or [])
		and _cfg_truthy(cfg, "WORKS.BOQ_REQUIRED")
		and getattr(doc, "std_template", None)
	):
		engine.populate_sample_tender(doc)
		seeded = True
	rows = doc.get("boq_items") or []
	if not rows:
		return _result(True, tender_name, changed=False, boq_items="skipped_empty")
	changed = bool(seeded)
	for row in rows:
		d = row.as_dict()
		merged = engine.default_wh007_fields_for_boq_source(d)
		for k, v in merged.items():
			cur = getattr(row, k, None)
			if cur is None or (isinstance(cur, str) and cur.strip() == ""):
				setattr(row, k, v)
				changed = True
	if changed:
		doc.save()
	return _result(
		True,
		tender_name,
		changed=changed,
		boq_items=len(rows),
		sample_boq_seeded=seeded,
	)


def initialize_derived_model_readiness(tender_name: str) -> dict[str, Any]:
	doc = _load_tender_write(tender_name)
	if doc.get("derived_model_readiness"):
		return _result(
			True, tender_name, changed=False, derived_model_readiness="skipped_nonempty"
		)
	slug = engine._sanitize_tender_reference_for_dsm(getattr(doc, "tender_reference", None))
	deferred = "Baseline placeholder (doc 5 §10); full model generation deferred."
	seed = (
		("Submission", f"DSM-{slug}-V1"),
		("Opening", f"DOM-{slug}-V1"),
		("Evaluation", f"DEM-{slug}-V1"),
		("Contract Carry-Forward", f"DCM-{slug}-V1"),
	)
	for model_type, model_code in seed:
		doc.append(
			"derived_model_readiness",
			{
				"model_type": model_type,
				"model_code": model_code,
				"source_std_template": doc.std_template or None,
				"source_tender": doc.name,
				"status": "Placeholder",
				"blocking_for_publication": 1,
				"components_summary": "",
				"deferred_reason": deferred,
				"validation_status": "Warning",
				"version": "V1",
			},
		)
	doc.save()
	return _result(True, tender_name, changed=True, derived_model_readiness_seeded=len(seed))


def link_required_forms_to_submission_components(tender_name: str) -> dict[str, Any]:
	doc = _load_tender_write(tender_name)
	if not doc.std_template:
		return _result(True, tender_name, changed=False, required_forms="skipped_no_std_template")
	cfg = _parse_configuration_json_optional(doc)
	if not doc.get("required_forms"):
		from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
			procurement_tender as procurement_tender_module,
		)

		procurement_tender_module.generate_required_forms(tender_name)
		doc.reload()
	if not doc.get("required_forms"):
		return _result(True, tender_name, changed=False, required_forms="still_empty_after_generate")
	template = engine.load_template(doc.std_template)
	lots = _row_dicts(doc.get("lots"))
	boq_items = _row_dicts(doc.get("boq_items"))
	vr = engine.validate_config(template, cfg, lots=lots, boq_items=boq_items)
	resolved = {r["form_code"]: r for r in engine.resolve_required_forms(template, cfg, vr)}
	changed = False
	for row in doc.required_forms:
		r = resolved.get(row.form_code)
		if not r:
			continue
		for field in (
			"submission_component_code",
			"required_because",
			"source_rule_code",
			"stage",
		):
			val = r.get(field)
			if val not in (None, "") and getattr(row, field, None) != val:
				setattr(row, field, val)
				changed = True
	if changed:
		doc.save()
	return _result(True, tender_name, changed=changed, required_forms_merged=len(resolved))


def generate_works_tender_stage_snapshot(tender_name: str) -> dict[str, Any]:
	doc = _load_tender_write(tender_name)
	payload = build_snapshot(doc)
	digest = hash_snapshot(payload)
	doc.works_hardening_snapshot_json = json.dumps(
		payload, indent=2, sort_keys=True, default=str
	)
	doc.works_hardening_snapshot_hash = digest
	doc.save()
	return _result(
		True,
		tender_name,
		changed=True,
		snapshot_hash=digest,
		snapshot_type=payload.get("snapshot_type"),
	)


def get_works_hardening_summary(tender_name: str) -> dict[str, Any]:
	doc = _load_tender_read(tender_name)
	summary: dict[str, Any] = {
		"works_hardening_status": doc.works_hardening_status,
		"works_requirements_status": doc.works_requirements_status,
		"attachments_status": doc.attachments_status,
		"boq_hardening_status": doc.boq_hardening_status,
		"derived_models_status": doc.derived_models_status,
		"works_hardening_checked_at": getattr(doc, "works_hardening_checked_at", None),
		"works_hardening_snapshot_hash": doc.works_hardening_snapshot_hash,
		"counts": {
			"works_requirements": len(doc.get("works_requirements") or []),
			"section_attachments": len(doc.get("section_attachments") or []),
			"boq_items": len(doc.get("boq_items") or []),
			"required_forms": len(doc.get("required_forms") or []),
			"derived_model_readiness": len(doc.get("derived_model_readiness") or []),
			"hardening_findings": len(doc.get("hardening_findings") or []),
		},
	}
	raw = doc.works_hardening_validation_json
	if raw and str(raw).strip():
		try:
			summary["last_validation"] = json.loads(raw)
		except json.JSONDecodeError:
			summary["last_validation"] = None
	return {"ok": True, "tender": tender_name, "summary": summary}


def get_works_hardening_findings(tender_name: str) -> dict[str, Any]:
	doc = _load_tender_read(tender_name)
	rows = _row_dicts(doc.get("hardening_findings"))
	return {"ok": True, "tender": tender_name, "findings": rows, "count": len(rows)}


def get_works_tender_stage_snapshot(tender_name: str) -> dict[str, Any]:
	doc = _load_tender_read(tender_name)
	raw = doc.works_hardening_snapshot_json
	payload = None
	if raw and str(raw).strip():
		try:
			payload = json.loads(raw)
		except json.JSONDecodeError:
			payload = None
	return {
		"ok": True,
		"tender": tender_name,
		"hash": doc.works_hardening_snapshot_hash,
		"snapshot": payload,
	}


def run_works_tender_stage_hardening(tender_name: str) -> dict[str, Any]:
	"""Doc 5 §16.4 orchestration (permission → normalize → validate → snapshot)."""
	_load_tender_write(tender_name)
	steps: list[dict[str, Any]] = []

	def _run(step: str, fn: Callable[[str], dict[str, Any]]) -> None:
		steps.append({"step": step, "result": fn(tender_name)})

	_run("initialize_works_requirements", initialize_works_requirements)
	_run("initialize_section_attachments", initialize_section_attachments)
	_run("harden_works_boq_structure", harden_works_boq_structure)
	_run("initialize_derived_model_readiness", initialize_derived_model_readiness)
	_run("link_required_forms_to_submission_components", link_required_forms_to_submission_components)

	validation = wv.validate_works_tender_stage(tender_name)
	snapshot_hash = None
	status = validation.get("status") or HARDENING_STATUS_NOT_CHECKED
	if status not in (HARDENING_STATUS_FAILED, HARDENING_STATUS_BLOCKED):
		snap = generate_works_tender_stage_snapshot(tender_name)
		snapshot_hash = snap.get("snapshot_hash")
		steps.append({"step": "generate_works_tender_stage_snapshot", "result": snap})
	else:
		steps.append(
			{
				"step": "generate_works_tender_stage_snapshot",
				"result": {"ok": False, "skipped": True, "reason": "validation_failed_or_blocked"},
			}
		)

	doc = _load_tender_write(tender_name)
	doc.db_set("works_hardening_checked_at", now_datetime(), update_modified=False)

	return {
		"ok": bool(validation.get("ok")),
		"tender": tender_name,
		"steps": steps,
		"validation": validation,
		"snapshot_hash": snapshot_hash,
	}
