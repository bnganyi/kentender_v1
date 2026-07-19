# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-04 Implementation Schedule GET/POST (C2-CFG4 + column-clarity amendment).

Acceptance Method shows content only. Setup Status / issues / Action hold completeness.
Never put missing/defined/valid in the Acceptance Method column.
"""

from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.services.configuration_home import (
	_STATUS_LABELS,
	_parse_steps_state,
	build_configuration_context,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_COMPLETE,
	STEP_IN_PROGRESS,
	STEP_NOT_STARTED,
)

APPROACH_PHASED = "Phased Delivery"
APPROACH_SINGLE = "Single Turnkey Delivery"
APPROACHES = (APPROACH_PHASED, APPROACH_SINGLE)

SETUP_COMPLETE = "Complete"
SETUP_NEEDS_ATTENTION = "Needs attention"
SETUP_DRAFT = "Draft"
SETUP_NOT_APPLICABLE = "Not applicable"

METHOD_NOT_REQUIRED = "Not required"

ACCEPTANCE_METHOD_SUGGESTIONS = (
	"PE confirms approved work plan",
	"Inspection at delivery",
	"Commissioning test report",
	"Training attendance and completion report",
	"Handover pack sign-off",
	"Support commencement confirmation",
	METHOD_NOT_REQUIRED,
)

DURATION_UNITS = ("days", "weeks", "months")
DURATION_UNIT_LABELS = {"days": "days", "weeks": "weeks", "months": "months"}

START_TRIGGER_SUGGESTIONS = (
	"Contract signing and notice to proceed",
	"Approved work plan",
	"Delivery acceptance for equipment",
	"Installation completion",
	"Commissioning acceptance",
	"Final handover acceptance",
	"Completion of previous milestone",
)

MILESTONE_KEYS = frozenset(
	{
		"milestone_id",
		"name",
		"description",
		"sequence",
		"expected_duration",
		"expected_duration_value",
		"expected_duration_unit",
		"start_trigger",
		"key_deliverable",
		"deliverable_description",
		"related_requirements",
		"related_requirement_ids",
		"acceptance_method",
		"evidence_expected",
	}
)
SINGLE_KEYS = frozenset(
	{
		"expected_delivery_duration",
		"expected_duration_value",
		"expected_duration_unit",
		"delivery_trigger",
		"key_deliverables",
		"acceptance_method",
		"evidence_expected",
		"notes_to_bidders",
	}
)
BANNED_KEYS = frozenset(
	{
		"std_version_hash",
		"binding_id",
		"clause_hash",
		"schema_version",
		"rule_id",
		"payment_percent",
		"actual_progress",
	}
)

MSG_EMPTY_PHASED = "Add at least one delivery milestone before continuing."
MSG_NAME = "Add a milestone name before continuing."
MSG_DESCRIPTION = "Add a milestone description before continuing."
MSG_DURATION = "Add an expected duration before continuing."
MSG_TRIGGER = "Add a start trigger before continuing."
MSG_DELIVERABLE = "Add a key deliverable before continuing."
MSG_DELIVERABLE_DESC = "Add a deliverable description before continuing."
MSG_ACCEPTANCE_METHOD = "Add an acceptance method before continuing."
MSG_DIAGNOSTIC = (
	"Use an acceptance method (how the milestone will later be accepted), "
	"not a setup-status phrase."
)
MSG_SINGLE_DURATION = "Add the expected delivery duration before continuing."
MSG_SINGLE_TRIGGER = "Add the delivery trigger before continuing."
MSG_SINGLE_DELIVERABLES = "Add key deliverables before continuing."
MSG_SINGLE_ACCEPTANCE = "Add an acceptance method before continuing."


def _v(row: dict[str, Any], key: str) -> str:
	return cstr(row.get(key) or "").strip()


def _compose_duration(value: str, unit: str) -> str:
	val = cstr(value or "").strip()
	unit_key = cstr(unit or "").strip().lower()
	if not val:
		return ""
	if unit_key not in DURATION_UNITS:
		return val
	label = DURATION_UNIT_LABELS[unit_key]
	# Singular when value is 1
	if val == "1" and label.endswith("s"):
		label = label[:-1]
	return f"{val} {label}"


def _parse_duration_parts(raw: str) -> tuple[str, str]:
	"""Split legacy free-text duration into value + unit."""
	text = cstr(raw or "").strip().lower()
	if not text:
		return "", "weeks"
	m = re.match(r"^(\d+(?:\.\d+)?)\s*(day|days|week|weeks|month|months|wk|wks)?\.?$", text)
	if not m:
		return cstr(raw or "").strip(), "weeks"
	value = m.group(1)
	unit_raw = (m.group(2) or "weeks").rstrip("s")
	unit = {"day": "days", "week": "weeks", "month": "months", "wk": "weeks"}.get(
		unit_raw, "weeks"
	)
	return value, unit


def _parse_related_ids(raw: Any) -> list[str]:
	if not raw:
		return []
	if isinstance(raw, list):
		return [cstr(x).strip() for x in raw if cstr(x).strip()]
	text = cstr(raw).strip()
	if not text:
		return []
	if text.startswith("["):
		try:
			parsed = json.loads(text)
			if isinstance(parsed, list):
				return [cstr(x).strip() for x in parsed if cstr(x).strip()]
		except (TypeError, ValueError):
			pass
	return [p.strip() for p in re.split(r"[,;]", text) if p.strip()]


def _is_diagnostic_phrase(text: str) -> bool:
	t = cstr(text or "").strip().lower()
	if not t:
		return False
	return t in {
		"acceptance defined",
		"missing acceptance",
		"delivery check missing",
		"delivery check defined",
		"missing",
		"defined",
		"valid",
		"complete",
		"incomplete",
		"needs attention",
		"draft",
		"not applicable",
	}


def _parse_json_obj(raw: Any) -> dict[str, Any]:
	if not raw:
		return {}
	if isinstance(raw, str):
		try:
			raw = json.loads(raw)
		except (TypeError, ValueError):
			return {}
	return raw if isinstance(raw, dict) else {}


def _normalize_duration_fields(cleaned: dict[str, Any]) -> None:
	value = cstr(cleaned.get("expected_duration_value") or "").strip()
	unit = cstr(cleaned.get("expected_duration_unit") or "").strip().lower()
	legacy = cstr(cleaned.get("expected_duration") or "").strip()
	# Also accept single-form alias keys already mapped into cleaned
	if not value and not unit and legacy:
		value, unit = _parse_duration_parts(legacy)
	if value and unit not in DURATION_UNITS:
		unit = "weeks"
	if value and unit in DURATION_UNITS:
		cleaned["expected_duration_value"] = value
		cleaned["expected_duration_unit"] = unit
		cleaned["expected_duration"] = _compose_duration(value, unit)
	elif legacy:
		cleaned["expected_duration"] = legacy


def _clean_milestone(row: dict[str, Any]) -> dict[str, Any]:
	cleaned: dict[str, Any] = {}
	for key, val in row.items():
		k = cstr(key).strip()
		if not k or k in BANNED_KEYS:
			continue
		# Legacy pack fields → acceptance_method (content only)
		if k in ("acceptance_expectation", "acceptance_label", "acceptance_description"):
			continue
		if k not in MILESTONE_KEYS:
			continue
		if k == "related_requirement_ids":
			cleaned[k] = _parse_related_ids(val)
			continue
		if isinstance(val, dict):
			continue
		if isinstance(val, list) and k != "related_requirement_ids":
			continue
		cleaned[k] = cstr(val).strip() if val is not None else ""
	legacy_desc = cstr(row.get("acceptance_description") or "").strip()
	legacy_exp = cstr(row.get("acceptance_expectation") or "").strip()
	if not cleaned.get("acceptance_method"):
		if legacy_desc and not _is_diagnostic_phrase(legacy_desc):
			cleaned["acceptance_method"] = legacy_desc
		elif legacy_exp in ("Not applicable", METHOD_NOT_REQUIRED):
			cleaned["acceptance_method"] = METHOD_NOT_REQUIRED
	# Alias pack "Milestone Name"
	if not cleaned.get("name") and row.get("milestone_name"):
		cleaned["name"] = cstr(row.get("milestone_name")).strip()
	# related_requirements free-text → ids
	if "related_requirement_ids" not in cleaned:
		cleaned["related_requirement_ids"] = _parse_related_ids(
			row.get("related_requirement_ids") or row.get("related_requirements")
		)
	_normalize_duration_fields(cleaned)
	return cleaned


def _clean_single(row: dict[str, Any] | None) -> dict[str, Any]:
	if not isinstance(row, dict):
		return {}
	cleaned: dict[str, Any] = {}
	for key, val in row.items():
		k = cstr(key).strip()
		if not k or k in BANNED_KEYS:
			continue
		if k in ("acceptance_expectation", "acceptance_label", "acceptance_description"):
			continue
		if k not in SINGLE_KEYS:
			continue
		if isinstance(val, (dict, list)):
			continue
		cleaned[k] = cstr(val).strip() if val is not None else ""
	legacy_desc = cstr(row.get("acceptance_description") or "").strip()
	legacy_exp = cstr(row.get("acceptance_expectation") or "").strip()
	if not cleaned.get("acceptance_method"):
		if legacy_desc and not _is_diagnostic_phrase(legacy_desc):
			cleaned["acceptance_method"] = legacy_desc
		elif legacy_exp in ("Not applicable", METHOD_NOT_REQUIRED):
			cleaned["acceptance_method"] = METHOD_NOT_REQUIRED
	# Map single duration aliases
	if not cleaned.get("expected_duration_value") and cleaned.get("expected_delivery_duration"):
		cleaned["expected_duration"] = cleaned.get("expected_delivery_duration")
	_normalize_duration_fields(cleaned)
	if cleaned.get("expected_duration"):
		cleaned["expected_delivery_duration"] = cleaned["expected_duration"]
	return cleaned


def _parse_schedule(raw: Any) -> dict[str, Any]:
	data = _parse_json_obj(raw)
	approach = cstr(data.get("delivery_approach") or APPROACH_PHASED).strip()
	if approach not in APPROACHES:
		approach = APPROACH_PHASED
	milestones_raw = data.get("milestones") or []
	if isinstance(milestones_raw, str):
		try:
			milestones_raw = json.loads(milestones_raw)
		except (TypeError, ValueError):
			milestones_raw = []
	milestones: list[dict[str, Any]] = []
	if isinstance(milestones_raw, list):
		for row in milestones_raw:
			if isinstance(row, dict):
				milestones.append(_clean_milestone(row))
	single = _clean_single(data.get("single_delivery") if isinstance(data.get("single_delivery"), dict) else {})
	return {
		"delivery_approach": approach,
		"milestones": milestones,
		"single_delivery": single,
	}


def _next_milestone_id(rows: list[dict[str, Any]]) -> str:
	max_n = 0
	for row in rows:
		mid = _v(row, "milestone_id")
		m = re.match(r"^MS-(\d+)$", mid, re.I)
		if m:
			max_n = max(max_n, int(m.group(1)))
	return f"MS-{max_n + 1:03d}"


def _milestone_unmet(row: dict[str, Any]) -> list[dict[str, str]]:
	unmet: list[dict[str, str]] = []
	mid = _v(row, "milestone_id") or "milestone"

	def add(code: str, message: str):
		unmet.append({"code": f"{mid}:{code}", "message": message})

	if not _v(row, "name"):
		add("name", MSG_NAME)
	if not _v(row, "description"):
		add("description", MSG_DESCRIPTION)
	dur_val = _v(row, "expected_duration_value")
	dur_unit = _v(row, "expected_duration_unit").lower()
	if not dur_val or dur_unit not in DURATION_UNITS:
		if not _v(row, "expected_duration"):
			add("expected_duration", MSG_DURATION)
	if not _v(row, "start_trigger"):
		add("start_trigger", MSG_TRIGGER)
	if not _v(row, "key_deliverable"):
		add("key_deliverable", MSG_DELIVERABLE)
	if not _v(row, "deliverable_description"):
		add("deliverable_description", MSG_DELIVERABLE_DESC)
	method = _v(row, "acceptance_method")
	if not method:
		add("acceptance_method", MSG_ACCEPTANCE_METHOD)
	elif _is_diagnostic_phrase(method):
		add("acceptance_method", MSG_DIAGNOSTIC)
	return unmet


def _single_unmet(row: dict[str, Any]) -> list[dict[str, str]]:
	unmet: list[dict[str, str]] = []

	def add(code: str, message: str):
		unmet.append({"code": f"single:{code}", "message": message})

	dur_val = _v(row, "expected_duration_value")
	dur_unit = _v(row, "expected_duration_unit").lower()
	if not dur_val or dur_unit not in DURATION_UNITS:
		if not _v(row, "expected_delivery_duration") and not _v(row, "expected_duration"):
			add("expected_delivery_duration", MSG_SINGLE_DURATION)
	if not _v(row, "delivery_trigger"):
		add("delivery_trigger", MSG_SINGLE_TRIGGER)
	if not _v(row, "key_deliverables"):
		add("key_deliverables", MSG_SINGLE_DELIVERABLES)
	method = _v(row, "acceptance_method")
	if not method:
		add("acceptance_method", MSG_SINGLE_ACCEPTANCE)
	elif _is_diagnostic_phrase(method):
		add("acceptance_method", MSG_DIAGNOSTIC)
	return unmet


def _any_milestone_content(row: dict[str, Any]) -> bool:
	for key in MILESTONE_KEYS:
		if key in ("milestone_id", "sequence") and not _v(row, "name"):
			continue
		if key == "related_requirement_ids":
			if _parse_related_ids(row.get(key)):
				return True
			continue
		if _v(row, key):
			return True
	return False


def _any_single_content(row: dict[str, Any]) -> bool:
	return any(_v(row, k) for k in SINGLE_KEYS)


def _derive_setup_status(unmet: list, has_content: bool, method: str) -> str:
	if method == METHOD_NOT_REQUIRED and not unmet:
		return SETUP_NOT_APPLICABLE
	if not has_content:
		return SETUP_DRAFT
	if not unmet:
		return SETUP_COMPLETE
	return SETUP_NEEDS_ATTENTION if has_content else SETUP_DRAFT


def _action_for_setup(status: str) -> str:
	return {
		SETUP_COMPLETE: "Edit",
		SETUP_NEEDS_ATTENTION: "Fix",
		SETUP_DRAFT: "Continue",
		SETUP_NOT_APPLICABLE: "Review",
	}.get(status, "Edit")


def enrich_milestone(row: dict[str, Any]) -> dict[str, Any]:
	unmet = _milestone_unmet(row)
	method = _v(row, "acceptance_method")
	setup = _derive_setup_status(unmet, _any_milestone_content(row), method)
	method_display = method if method and not _is_diagnostic_phrase(method) else "—"
	related_ids = _parse_related_ids(row.get("related_requirement_ids") or row.get("related_requirements"))
	dur_val = _v(row, "expected_duration_value")
	dur_unit = _v(row, "expected_duration_unit").lower() or "weeks"
	duration = _v(row, "expected_duration") or _compose_duration(dur_val, dur_unit)
	return {
		"milestone_id": _v(row, "milestone_id"),
		"name": _v(row, "name"),
		"description": _v(row, "description"),
		"sequence": _v(row, "sequence") or "",
		"expected_duration": duration,
		"expected_duration_value": dur_val,
		"expected_duration_unit": dur_unit if dur_unit in DURATION_UNITS else "weeks",
		"start_trigger": _v(row, "start_trigger"),
		"key_deliverable": _v(row, "key_deliverable"),
		"deliverable_description": _v(row, "deliverable_description"),
		"related_requirement_ids": related_ids,
		"acceptance_method": method,
		"acceptance_method_display": method_display,
		"evidence_expected": _v(row, "evidence_expected"),
		"setup_status_label": setup,
		"status_label": setup if setup != SETUP_NOT_APPLICABLE else SETUP_COMPLETE,
		"action_label": _action_for_setup(setup),
		"issue_summary": unmet[0]["message"] if unmet else "",
		"references": {
			"it_requirements": (
				"Linked to IT Requirements" if related_ids else "No requirement link selected"
			),
			"price_schedule": "No price schedule link expected",
			"contract_values": "May carry into contract values",
		},
	}


def _resolve_related_refs(
	related_ids: list[str], available: list[dict[str, str]]
) -> list[dict[str, str]]:
	by_id = {cstr(r.get("id") or "").strip(): r for r in available}
	out: list[dict[str, str]] = []
	for rid in related_ids:
		ref = by_id.get(rid)
		if ref:
			out.append({"id": ref["id"], "code": ref["code"], "name": ref["name"]})
		else:
			out.append({"id": rid, "code": rid, "name": rid})
	return out


def enrich_single(row: dict[str, Any]) -> dict[str, Any]:
	unmet = _single_unmet(row)
	method = _v(row, "acceptance_method")
	setup = _derive_setup_status(unmet, _any_single_content(row), method)
	method_display = method if method and not _is_diagnostic_phrase(method) else "—"
	dur_val = _v(row, "expected_duration_value")
	dur_unit = _v(row, "expected_duration_unit").lower() or "months"
	duration = (
		_v(row, "expected_delivery_duration")
		or _v(row, "expected_duration")
		or _compose_duration(dur_val, dur_unit)
	)
	return {
		"expected_delivery_duration": duration,
		"expected_duration_value": dur_val,
		"expected_duration_unit": dur_unit if dur_unit in DURATION_UNITS else "months",
		"delivery_trigger": _v(row, "delivery_trigger"),
		"key_deliverables": _v(row, "key_deliverables"),
		"acceptance_method": method,
		"acceptance_method_display": method_display,
		"evidence_expected": _v(row, "evidence_expected"),
		"notes_to_bidders": _v(row, "notes_to_bidders"),
		"setup_status_label": setup,
		"status_label": setup if setup != SETUP_NOT_APPLICABLE else SETUP_COMPLETE,
		"issue_summary": unmet[0]["message"] if unmet else "",
	}


def _available_it_requirements(doc) -> list[dict[str, str]]:
	"""Reference options from CFG-03: id/code/name (never show id alone in UI)."""
	from kentender_procurement.tender_configurations.services.it_requirements import (
		_parse_requirements,
	)

	rows = _parse_requirements(getattr(doc, "it_requirements", None))
	out: list[dict[str, str]] = []
	for row in rows:
		rid = _v(row, "requirement_id")
		title = _v(row, "title")
		if not rid:
			continue
		out.append({"id": rid, "code": rid, "name": title or rid})
	return out


def validate_schedule(
	approach: str, milestones: list[dict[str, Any]], single: dict[str, Any]
) -> tuple[list[dict[str, str]], list[dict[str, str]], bool]:
	blockers: list[dict[str, str]] = []
	warnings: list[dict[str, str]] = []
	if approach == APPROACH_SINGLE:
		blockers.extend(_single_unmet(single))
	else:
		if not milestones:
			blockers.append({"code": "empty", "message": MSG_EMPTY_PHASED})
		for row in milestones:
			blockers.extend(_milestone_unmet(row))
			if _v(row, "name") and not _v(row, "evidence_expected"):
				warnings.append(
					{
						"code": f"{_v(row, 'milestone_id')}:evidence",
						"message": "Consider stating evidence expected for this milestone.",
					}
				)
	return blockers, warnings, len(blockers) == 0


def schedule_has_progress(
	approach: str, milestones: list[dict[str, Any]], single: dict[str, Any]
) -> bool:
	if approach == APPROACH_SINGLE:
		return _any_single_content(single)
	return any(_any_milestone_content(r) for r in milestones)


def schedule_exit_conditions(
	approach: str, milestones: list[dict[str, Any]], single: dict[str, Any]
) -> list[dict[str, Any]]:
	conds: list[dict[str, Any]] = [
		{
			"key": "approach_selected",
			"label": "Delivery approach selected",
			"met": approach in APPROACHES,
		}
	]
	if approach == APPROACH_SINGLE:
		unmet = _single_unmet(single)
		conds.append(
			{
				"key": "single_complete",
				"label": "Single turnkey delivery complete",
				"met": len(unmet) == 0 and _any_single_content(single),
			}
		)
	else:
		conds.append(
			{
				"key": "has_milestones",
				"label": "At least one milestone",
				"met": bool(milestones),
			}
		)
		for row in milestones:
			mid = _v(row, "milestone_id") or "MS"
			unmet = _milestone_unmet(row)
			conds.append(
				{
					"key": f"ms_{mid}",
					"label": f"{mid} setup complete",
					"met": len(unmet) == 0 and _any_milestone_content(row),
				}
			)
	return conds


def schedule_exit_conditions_for_doc(doc) -> list[dict[str, Any]]:
	parsed = _parse_schedule(getattr(doc, "implementation_schedule", None))
	return schedule_exit_conditions(
		parsed["delivery_approach"], parsed["milestones"], parsed["single_delivery"]
	)


def _sync_cfg04_steps_state(doc, *, can_continue: bool, has_progress: bool, progress: dict) -> None:
	state = _parse_steps_state(getattr(doc, "steps_state", None))
	cfg = dict(state.get("CFG-04") or {})
	if can_continue:
		cfg["status_label"] = STEP_COMPLETE
	elif has_progress:
		cfg["status_label"] = STEP_IN_PROGRESS
	else:
		cfg["status_label"] = STEP_NOT_STARTED
	cfg["progress_pct"] = progress.get("progress_pct", 0)
	cfg["progress_met_count"] = progress.get("met_count", 0)
	cfg["progress_required_count"] = progress.get("required_count", 0)
	state["CFG-04"] = cfg
	doc.steps_state = json.dumps(state)


def _persist_milestone(row: dict[str, Any]) -> dict[str, Any]:
	cleaned = _clean_milestone(row)
	related = cleaned.get("related_requirement_ids") or []
	if not isinstance(related, list):
		related = _parse_related_ids(related)
	return {
		"milestone_id": _v(cleaned, "milestone_id"),
		"name": _v(cleaned, "name"),
		"description": _v(cleaned, "description"),
		"sequence": _v(cleaned, "sequence"),
		"expected_duration_value": _v(cleaned, "expected_duration_value"),
		"expected_duration_unit": _v(cleaned, "expected_duration_unit") or "weeks",
		"expected_duration": _v(cleaned, "expected_duration"),
		"start_trigger": _v(cleaned, "start_trigger"),
		"key_deliverable": _v(cleaned, "key_deliverable"),
		"deliverable_description": _v(cleaned, "deliverable_description"),
		"related_requirement_ids": related,
		"acceptance_method": _v(cleaned, "acceptance_method"),
		"evidence_expected": _v(cleaned, "evidence_expected"),
	}


def _persist_single(row: dict[str, Any]) -> dict[str, Any]:
	cleaned = _clean_single(row)
	return {
		"expected_duration_value": _v(cleaned, "expected_duration_value"),
		"expected_duration_unit": _v(cleaned, "expected_duration_unit") or "months",
		"expected_delivery_duration": _v(cleaned, "expected_delivery_duration")
		or _v(cleaned, "expected_duration"),
		"delivery_trigger": _v(cleaned, "delivery_trigger"),
		"key_deliverables": _v(cleaned, "key_deliverables"),
		"acceptance_method": _v(cleaned, "acceptance_method"),
		"evidence_expected": _v(cleaned, "evidence_expected"),
		"notes_to_bidders": _v(cleaned, "notes_to_bidders"),
	}


def _persist_blob(
	approach: str, milestones: list[dict[str, Any]], single: dict[str, Any]
) -> dict[str, Any]:
	persisted: list[dict[str, Any]] = []
	for i, row in enumerate(milestones):
		item = _persist_milestone(row)
		if not item.get("sequence"):
			item["sequence"] = str(i + 1)
		persisted.append(item)
	return {
		"delivery_approach": approach,
		"milestones": persisted,
		"single_delivery": _persist_single(single),
	}


def get_configuration_implementation_schedule(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	parsed = _parse_schedule(getattr(doc, "implementation_schedule", None))
	approach = parsed["delivery_approach"]
	milestones = parsed["milestones"]
	single = parsed["single_delivery"]
	enriched_ms = [enrich_milestone(r) for r in milestones]
	enriched_single = enrich_single(single)
	blockers, warnings, can_continue = validate_schedule(approach, milestones, single)
	has_progress = schedule_has_progress(approach, milestones, single)
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")
	available = _available_it_requirements(doc)
	for row in enriched_ms:
		row["related_requirement_refs"] = _resolve_related_refs(
			row.get("related_requirement_ids") or [], available
		)

	return {
		"configuration_id": doc.name,
		"procurement_package_ref": context["procurement_package_ref"],
		"tender_title": cstr(doc.tender_title or ""),
		"procuring_entity_name": context["procuring_entity_name"],
		"procurement_method_label": context["procurement_method_label"],
		"std_family_label": context["std_family_label"],
		"standard_tender_document_label": cstr(doc.std_document_label or ""),
		"configuration_status_label": _STATUS_LABELS.get(status, status),
		"blocker_count": len(blockers),
		"warning_count": len(warnings),
		"blockers": blockers,
		"warnings": warnings,
		"can_continue": can_continue,
		"has_progress": has_progress,
		"delivery_approach": approach,
		"milestones": enriched_ms,
		"single_delivery": enriched_single,
		"available_requirements": available,
		"next_milestone_id": _next_milestone_id(milestones),
		"context": context,
		"options": {
			"delivery_approach": list(APPROACHES),
			"acceptance_method": list(ACCEPTANCE_METHOD_SUGGESTIONS),
			"duration_unit": list(DURATION_UNITS),
			"start_trigger": list(START_TRIGGER_SUGGESTIONS),
		},
		"column_contract": {
			"note": (
				"Acceptance Method shows content only. "
				"Never put missing/defined/valid in that column — use Setup Status."
			),
			"columns": [
				"ID",
				"Milestone",
				"Expected Duration",
				"Trigger",
				"Key Deliverable",
				"Acceptance Method",
				"Setup Status",
				"Action",
			],
		},
		"guidance": {
			"title": "Implementation Schedule Guidance",
			"body": (
				"Define how the successful bidder will deliver, install, configure, test, "
				"train, hand over, and support the solution. This is Section VII schedule "
				"configuration — not post-award tracking or payment certification."
			),
			"what_this_affects": (
				"Bidder delivery expectations, readiness check, tender document preview, "
				"and later inventory, forms, and contract values."
			),
			"used_later_by": (
				"System Inventory & Bidder Background, Price Schedule, Forms & Evidence, "
				"Contract Values, Readiness Check, and Tender Document Preview."
			),
			"not_configured_here": (
				"Payment certificates, actual progress percentages, site inspections, "
				"evaluation marks, price amounts, and post-award contract workflows."
			),
		},
	}


def save_configuration_implementation_schedule(
	configuration_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
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

	# Merge with existing so switching approaches preserves the other draft
	existing = _parse_schedule(getattr(doc, "implementation_schedule", None))
	approach = cstr(payload.get("delivery_approach") or existing["delivery_approach"] or APPROACH_PHASED).strip()
	if approach not in APPROACHES:
		approach = APPROACH_PHASED

	if "milestones" in payload:
		incoming_ms = payload.get("milestones")
		if isinstance(incoming_ms, str):
			try:
				incoming_ms = json.loads(incoming_ms)
			except (TypeError, ValueError):
				incoming_ms = []
		milestones: list[dict[str, Any]] = []
		if isinstance(incoming_ms, list):
			for row in incoming_ms:
				if not isinstance(row, dict):
					continue
				persist_item = _persist_milestone(row)
				if not persist_item.get("milestone_id"):
					persist_item["milestone_id"] = _next_milestone_id(milestones)
				if not persist_item.get("sequence"):
					persist_item["sequence"] = str(len(milestones) + 1)
				milestones.append(persist_item)
	else:
		milestones = existing["milestones"]

	if "single_delivery" in payload:
		single = _persist_single(
			payload.get("single_delivery") if isinstance(payload.get("single_delivery"), dict) else {}
		)
	else:
		single = existing["single_delivery"]

	blockers, warnings, can_continue = validate_schedule(approach, milestones, single)
	has_progress = schedule_has_progress(approach, milestones, single)

	from kentender_procurement.tender_configurations.services.step_progress import (
		evaluate_conditions,
	)

	progress = evaluate_conditions(schedule_exit_conditions(approach, milestones, single))
	blob = _persist_blob(approach, milestones, single)

	doc.implementation_schedule = json.dumps(blob)
	doc.blocker_count = len(blockers)
	doc.warning_count = len(warnings)
	_sync_cfg04_steps_state(
		doc,
		can_continue=can_continue,
		has_progress=has_progress,
		progress=progress,
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return get_configuration_implementation_schedule(doc.name)
