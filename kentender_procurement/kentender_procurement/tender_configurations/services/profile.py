# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-01 Tender Profile GET/POST (C2-CFG1 §13)."""

from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.services.configuration_home import (
	_STATUS_LABELS,
	_entity_display_name,
	_method_label,
	_parse_steps_state,
	build_configuration_context,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_COMPLETE,
	STEP_IN_PROGRESS,
	STEP_NOT_STARTED,
)

LOT_SINGLE = "Single lot"
LOT_MULTIPLE = "Multiple lots"
LOT_NA = "Not applicable"
ALLOWED_LOT_STRUCTURES = frozenset({LOT_SINGLE, LOT_MULTIPLE, LOT_NA})

MSG_TITLE = "Add a tender title before continuing."
MSG_SCOPE = "Add a short scope summary before continuing."
MSG_LOT = "Confirm the lot structure before continuing."
MSG_FAMILY = "Confirm the STD family before continuing."
MSG_STD_DOC = "Confirm the standard tender document before continuing."
MSG_TITLE_WARN = "Review the tender title for clarity."
MSG_SCOPE_WARN = "Review the scope summary so officers can understand the tender context."


def _parse_lots(raw: Any) -> list[dict[str, str]]:
	if not raw:
		return []
	if isinstance(raw, str):
		try:
			raw = json.loads(raw)
		except (TypeError, ValueError):
			return []
	if not isinstance(raw, list):
		return []
	out: list[dict[str, str]] = []
	for i, row in enumerate(raw):
		if not isinstance(row, dict):
			continue
		out.append(
			{
				"lot_no": cstr(row.get("lot_no") or f"Lot {i + 1}").strip(),
				"lot_title": cstr(row.get("lot_title") or "").strip(),
				"short_description": cstr(row.get("short_description") or "").strip(),
			}
		)
	return out


def _std_version_label(doc) -> str:
	label = cstr(getattr(doc, "std_document_label", None) or "")
	# Prefer trailing em-dash segment: "IT Standard … — April 2022"
	if "—" in label:
		tail = label.split("—")[-1].strip()
		if tail:
			return tail
	if "-" in label and re.search(r"\d{4}", label):
		parts = [p.strip() for p in label.split("-") if p.strip()]
		if parts:
			return parts[-1]
	ver = cstr(getattr(doc, "std_version", None) or "")
	if ver and frappe.db.exists("STD Version", ver):
		for field in ("version_label", "version_name", "title"):
			val = frappe.db.get_value("STD Version", ver, field)
			if val:
				return cstr(val)
	return label or ver


def _validate_profile(
	*,
	tender_title: str,
	short_scope_summary: str,
	lot_structure: str,
	lots: list[dict[str, str]],
	std_family: str,
	std_document: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]], bool]:
	blockers: list[dict[str, str]] = []
	warnings: list[dict[str, str]] = []

	if not tender_title:
		blockers.append({"code": "title", "message": MSG_TITLE})
	elif len(tender_title) > 120 or len(tender_title.split()) < 2:
		warnings.append({"code": "title_clarity", "message": MSG_TITLE_WARN})

	if not short_scope_summary:
		blockers.append({"code": "scope", "message": MSG_SCOPE})
	elif len(short_scope_summary.split()) < 6:
		warnings.append({"code": "scope_vague", "message": MSG_SCOPE_WARN})

	if not lot_structure or lot_structure not in ALLOWED_LOT_STRUCTURES:
		blockers.append({"code": "lot_structure", "message": MSG_LOT})
	elif lot_structure == LOT_MULTIPLE:
		usable = [r for r in lots if r.get("lot_title")]
		if not usable:
			blockers.append({"code": "lots", "message": MSG_LOT})

	if not std_family:
		blockers.append({"code": "std_family", "message": MSG_FAMILY})
	if not std_document:
		blockers.append({"code": "std_document", "message": MSG_STD_DOC})

	can_continue = len(blockers) == 0
	return blockers, warnings, can_continue


def _sync_cfg01_steps_state(doc, *, can_continue: bool, has_any_progress: bool) -> None:
	from kentender_procurement.tender_configurations.services.step_progress import (
		compute_step_progress,
	)

	state = _parse_steps_state(getattr(doc, "steps_state", None))
	cfg = dict(state.get("CFG-01") or {})
	if can_continue:
		cfg["status_label"] = STEP_COMPLETE
	elif has_any_progress:
		cfg["status_label"] = STEP_IN_PROGRESS
	else:
		cfg["status_label"] = STEP_NOT_STARTED
	progress = compute_step_progress(
		"CFG-01", status_label=cfg["status_label"], doc=doc, step_state=cfg
	)
	cfg["progress_pct"] = progress["progress_pct"]
	cfg["progress_met_count"] = progress["met_count"]
	cfg["progress_required_count"] = progress["required_count"]
	state["CFG-01"] = cfg
	doc.steps_state = json.dumps(state)


def get_configuration_profile(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	lots = _parse_lots(getattr(doc, "lots", None))
	title = cstr(doc.tender_title or "").strip()
	scope = cstr(getattr(doc, "short_scope_summary", None) or "").strip()
	lot_structure = cstr(getattr(doc, "lot_structure", None) or "").strip()
	family = cstr(doc.std_family_label or "").strip()
	std_doc = cstr(doc.std_document_label or "").strip()
	blockers, warnings, can_continue = _validate_profile(
		tender_title=title,
		short_scope_summary=scope,
		lot_structure=lot_structure,
		lots=lots,
		std_family=family,
		std_document=std_doc,
	)
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")
	return {
		"configuration_id": doc.name,
		"procurement_package_ref": context["procurement_package_ref"],
		"tender_configuration_ref": cstr(doc.configuration_ref or doc.name),
		"tender_title": title,
		"short_scope_summary": scope,
		"procuring_entity_name": context["procuring_entity_name"],
		"procurement_method_label": context["procurement_method_label"],
		"std_family": family,
		"standard_tender_document_label": std_doc,
		"std_version_label": _std_version_label(doc),
		"lot_structure": lot_structure,
		"lots": lots,
		"configuration_note": cstr(getattr(doc, "configuration_note", None) or ""),
		"status_label": _STATUS_LABELS.get(status, status),
		"blocker_count": len(blockers),
		"warning_count": len(warnings),
		"blockers": blockers,
		"warnings": warnings,
		"can_continue": can_continue,
		"context": context,
		"helpers": {
			"tender_title": "Use a clear public-facing title for the tender.",
			"short_scope_summary": "Summarize what is being procured in one or two sentences.",
			"procuring_entity": "Taken from the approved procurement package.",
			"procurement_method": "Taken from the approved procurement package.",
			"lot_structure": "Confirm whether this tender has one lot or multiple lots.",
			"lot_summary": "Describe each lot only if the tender has multiple lots.",
			"std_family": "The STD family determines which configuration steps and rules apply.",
			"standard_tender_document": "The tender will be configured using this standard tender document.",
			"std_version_label": "Shown for traceability; users do not edit the STD master here.",
			"configuration_note": (
				"Add a short internal note for officers working on this configuration. "
				"Do not include bidder-facing requirements here."
			),
		},
	}


def save_configuration_profile(configuration_id: str, payload: dict[str, Any] | str | None = None) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}

	# Ignore forbidden internal fields if posted
	for banned in (
		"std_version_hash",
		"binding_id",
		"std_binding",
		"clause_hash",
		"schema_version",
	):
		payload.pop(banned, None)

	def _field(key: str, current: Any) -> str:
		if key in payload:
			return cstr(payload.get(key) or "").strip()
		return cstr(current or "").strip()

	title = _field("tender_title", doc.tender_title)
	scope = _field("short_scope_summary", getattr(doc, "short_scope_summary", None))
	lot_structure = _field("lot_structure", getattr(doc, "lot_structure", None))
	if "lots" in payload:
		lots = _parse_lots(payload.get("lots"))
	else:
		lots = _parse_lots(getattr(doc, "lots", None))
	note = _field("configuration_note", getattr(doc, "configuration_note", None))

	if lot_structure and lot_structure not in ALLOWED_LOT_STRUCTURES:
		frappe.throw(frappe._(MSG_LOT))

	if lot_structure != LOT_MULTIPLE:
		lots = []

	doc.tender_title = title
	doc.short_scope_summary = scope
	doc.lot_structure = lot_structure
	doc.lots = json.dumps(lots)
	doc.configuration_note = note

	family = cstr(doc.std_family_label or "").strip()
	std_doc = cstr(doc.std_document_label or "").strip()
	blockers, warnings, can_continue = _validate_profile(
		tender_title=title,
		short_scope_summary=scope,
		lot_structure=lot_structure,
		lots=lots,
		std_family=family,
		std_document=std_doc,
	)
	has_progress = bool(title or scope or lot_structure or note or lots)
	_sync_cfg01_steps_state(doc, can_continue=can_continue, has_any_progress=has_progress)

	# Profile save owns issue counters for this configuration (CFG-01 validation).
	doc.blocker_count = len(blockers)
	doc.warning_count = len(warnings)

	# Allow incomplete profile drafts (Continue is gated by can_continue, not DocType mandatory).
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return get_configuration_profile(doc.name)
