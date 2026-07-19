# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-05 System Inventory & Bidder Background GET/POST (C2-CFG5 + column-clarity).

Bidder Consideration / Disclosure Status / Price Link show content only.
Setup Status / issues / Action hold completeness. Never put missing/defined/valid
in content columns.
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

CATEGORIES = (
	"Systems in Scope",
	"Infrastructure Environment",
	"Sites & Users",
	"Integrations",
	"Data Migration",
	"Licensing & Support",
	"Background Notes",
	"Out of Scope",
)
CATEGORY_BACKGROUND = "Background Notes"
CATEGORY_OUT_OF_SCOPE = "Out of Scope"

SCOPES = ("In scope", "Context only", "Out of scope")
SCOPE_OUT = "Out of scope"

DISCLOSURE_STATUSES = (
	"Safe to disclose",
	"Needs disclosure review",
	"Remove sensitive detail",
	"Not configured",
)
DISCLOSURE_SAFE = "Safe to disclose"
DISCLOSURE_REVIEW = "Needs disclosure review"
DISCLOSURE_REMOVE = "Remove sensitive detail"
DISCLOSURE_NOT_CONFIGURED = "Not configured"

PRICE_LINKS = (
	"May affect price schedule",
	"Linked in Price Schedule",
	"No price link expected",
	"To be reviewed",
)
PRICE_MAY_AFFECT = "May affect price schedule"
PRICE_NONE = "No price link expected"

SETUP_COMPLETE = "Complete"
SETUP_NEEDS_ATTENTION = "Needs attention"
SETUP_DRAFT = "Draft"
SETUP_IN_PROGRESS = "In progress"
SETUP_NOT_STARTED = "Not started"

EDITABLE_KEYS = frozenset(
	{
		"item_id",
		"item_title",
		"category_label",
		"scope_label",
		"item_description",
		"bidder_consideration",
		"related_requirement_ids",
		"related_milestone_ids",
		"location_site",
		"existing_system_name",
		"estimated_volume_count",
		"integration_point",
		"data_source",
		"support_licence_context",
		"out_of_scope_note",
		"disclosure_status_label",
		"disclosure_note",
		"price_link_label",
	}
)
BANNED_KEYS = frozenset(
	{
		"std_version_hash",
		"binding_id",
		"clause_hash",
		"schema_version",
		"rule_id",
		"password",
		"secret_key",
		"private_ip",
		"vulnerability",
		"price_amount",
		"marks",
		"pass_mark",
	}
)

MSG_EMPTY = "Add at least one inventory or background item before continuing."
MSG_TITLE = "Add an item title before continuing."
MSG_CATEGORY = "Confirm the item category before continuing."
MSG_SCOPE = "Confirm the item scope before continuing."
MSG_DESCRIPTION = "Add an item description before continuing."
MSG_CONSIDERATION = "Add a bidder consideration before continuing."
MSG_DISCLOSURE = "Confirm the disclosure status before continuing."
MSG_DISCLOSURE_NOTE = "Add a disclosure note before continuing."
MSG_OUT_OF_SCOPE = "Add an out-of-scope note before continuing."
MSG_DIAGNOSTIC = (
	"Use a bidder-facing consideration or disclosure value, not a setup-status phrase."
)
MSG_BACKGROUND_OBLIGATION = (
	"1 background note may create a requirement. Move the obligation to IT Requirements."
)

_DIAGNOSTIC_EXACT = {
	"missing",
	"defined",
	"valid",
	"acceptance defined",
	"missing acceptance",
	"complete",
	"incomplete",
	"needs attention",
	"draft",
	"not applicable",
}


def _v(row: dict[str, Any], key: str) -> str:
	return cstr(row.get(key) or "").strip()


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
	return bool(t) and t in _DIAGNOSTIC_EXACT


def _parse_items(raw: Any) -> list[dict[str, Any]]:
	if not raw:
		return []
	if isinstance(raw, str):
		try:
			raw = json.loads(raw)
		except (TypeError, ValueError):
			return []
	if isinstance(raw, dict):
		raw = raw.get("items") or []
	if not isinstance(raw, list):
		return []
	out: list[dict[str, Any]] = []
	for row in raw:
		if isinstance(row, dict):
			out.append(_clean_item(row))
	return out


def _clean_item(row: dict[str, Any]) -> dict[str, Any]:
	cleaned: dict[str, Any] = {}
	for key, val in row.items():
		k = cstr(key).strip()
		if not k or k in BANNED_KEYS or k not in EDITABLE_KEYS:
			continue
		if k in ("related_requirement_ids", "related_milestone_ids"):
			cleaned[k] = _parse_related_ids(val)
			continue
		if isinstance(val, (dict, list)):
			continue
		cleaned[k] = cstr(val).strip() if val is not None else ""
	# Aliases from pack / UI
	if not cleaned.get("item_title") and row.get("title"):
		cleaned["item_title"] = cstr(row.get("title")).strip()
	if "related_requirement_ids" not in cleaned:
		cleaned["related_requirement_ids"] = _parse_related_ids(
			row.get("related_requirement_ids") or row.get("related_requirement_id")
		)
	if "related_milestone_ids" not in cleaned:
		cleaned["related_milestone_ids"] = _parse_related_ids(
			row.get("related_milestone_ids") or row.get("related_milestone_id")
		)
	return cleaned


def _is_background(row: dict[str, Any]) -> bool:
	return _v(row, "category_label") == CATEGORY_BACKGROUND


def _next_item_id(rows: list[dict[str, Any]], *, background: bool) -> str:
	prefix = "BG" if background else "INV"
	max_n = 0
	for row in rows:
		mid = _v(row, "item_id")
		m = re.match(rf"^{prefix}-(\d+)$", mid, re.I)
		if m:
			max_n = max(max_n, int(m.group(1)))
	return f"{prefix}-{max_n + 1:03d}"


def _row_unmet(row: dict[str, Any]) -> list[dict[str, str]]:
	unmet: list[dict[str, str]] = []
	rid = _v(row, "item_id") or "item"

	def add(code: str, message: str):
		unmet.append({"code": f"{rid}:{code}", "message": message})

	if not _v(row, "item_title"):
		add("item_title", MSG_TITLE)
	cat = _v(row, "category_label")
	if not cat or cat not in CATEGORIES:
		add("category_label", MSG_CATEGORY)
	scope = _v(row, "scope_label")
	if not scope or scope not in SCOPES:
		add("scope_label", MSG_SCOPE)
	if not _v(row, "item_description"):
		add("item_description", MSG_DESCRIPTION)
	consideration = _v(row, "bidder_consideration")
	if not consideration:
		add("bidder_consideration", MSG_CONSIDERATION)
	elif _is_diagnostic_phrase(consideration):
		add("bidder_consideration", MSG_DIAGNOSTIC)
	disclosure = _v(row, "disclosure_status_label")
	if not disclosure or disclosure not in DISCLOSURE_STATUSES:
		add("disclosure_status_label", MSG_DISCLOSURE)
	elif disclosure == DISCLOSURE_NOT_CONFIGURED:
		add("disclosure_status_label", MSG_DISCLOSURE)
	elif disclosure in (DISCLOSURE_REVIEW, DISCLOSURE_REMOVE) and not _v(row, "disclosure_note"):
		add("disclosure_note", MSG_DISCLOSURE_NOTE)
	if scope == SCOPE_OUT or cat == CATEGORY_OUT_OF_SCOPE:
		if not _v(row, "out_of_scope_note"):
			add("out_of_scope_note", MSG_OUT_OF_SCOPE)
	return unmet


def _any_content(row: dict[str, Any]) -> bool:
	for key in EDITABLE_KEYS:
		if key in ("item_id", "related_requirement_ids", "related_milestone_ids"):
			if key != "item_id" and _parse_related_ids(row.get(key)):
				return True
			continue
		if _v(row, key):
			return True
	return False


def _derive_setup_status(row: dict[str, Any], unmet: list[dict[str, str]]) -> str:
	if not _any_content(row):
		return SETUP_DRAFT
	if not unmet:
		return SETUP_COMPLETE
	if _v(row, "item_title"):
		return SETUP_NEEDS_ATTENTION
	return SETUP_IN_PROGRESS


def _action_for_setup(status: str, disclosure: str) -> str:
	if status == SETUP_COMPLETE and disclosure == DISCLOSURE_SAFE:
		return "Edit"
	if status == SETUP_COMPLETE:
		return "Review"
	return {
		SETUP_NEEDS_ATTENTION: "Fix",
		SETUP_DRAFT: "Continue",
		SETUP_IN_PROGRESS: "Continue",
		SETUP_NOT_STARTED: "Continue",
	}.get(status, "Edit")


def _default_price_link(row: dict[str, Any]) -> str:
	link = _v(row, "price_link_label")
	if link in PRICE_LINKS:
		return link
	scope = _v(row, "scope_label")
	if scope == SCOPE_OUT or _is_background(row):
		return PRICE_NONE
	return PRICE_MAY_AFFECT


def enrich_item(row: dict[str, Any]) -> dict[str, Any]:
	unmet = _row_unmet(row)
	setup = _derive_setup_status(row, unmet)
	disclosure = _v(row, "disclosure_status_label") or DISCLOSURE_NOT_CONFIGURED
	consideration = _v(row, "bidder_consideration")
	consideration_display = (
		consideration if consideration and not _is_diagnostic_phrase(consideration) else "—"
	)
	disclosure_display = (
		disclosure if disclosure in DISCLOSURE_STATUSES and disclosure != DISCLOSURE_NOT_CONFIGURED else "—"
	)
	price_link = _default_price_link(row)
	req_ids = _parse_related_ids(row.get("related_requirement_ids"))
	ms_ids = _parse_related_ids(row.get("related_milestone_ids"))
	return {
		"item_id": _v(row, "item_id"),
		"item_title": _v(row, "item_title"),
		"category_label": _v(row, "category_label"),
		"scope_label": _v(row, "scope_label"),
		"item_description": _v(row, "item_description"),
		"bidder_consideration": consideration,
		"bidder_consideration_display": consideration_display,
		"related_requirement_ids": req_ids,
		"related_milestone_ids": ms_ids,
		"location_site": _v(row, "location_site"),
		"existing_system_name": _v(row, "existing_system_name"),
		"estimated_volume_count": _v(row, "estimated_volume_count"),
		"integration_point": _v(row, "integration_point"),
		"data_source": _v(row, "data_source"),
		"support_licence_context": _v(row, "support_licence_context"),
		"out_of_scope_note": _v(row, "out_of_scope_note"),
		"disclosure_status_label": disclosure,
		"disclosure_status_display": disclosure_display,
		"disclosure_note": _v(row, "disclosure_note"),
		"price_link_label": price_link,
		"price_link_display": price_link if price_link in PRICE_LINKS else "—",
		"setup_status_label": setup,
		"status_label": setup if setup != SETUP_NOT_STARTED else SETUP_DRAFT,
		"action_label": _action_for_setup(setup, disclosure),
		"issue_summary": unmet[0]["message"] if unmet else "",
		"references": {
			"it_requirements": (
				"Linked to IT Requirement" if req_ids else "No requirement link selected"
			),
			"implementation_schedule": (
				"Linked to milestone" if ms_ids else "No milestone link selected"
			),
			"price_schedule": price_link if price_link in PRICE_LINKS else PRICE_NONE,
			"contract_values": (
				"May carry into contract values"
				if _v(row, "scope_label") == "In scope"
				else "No contract carry-forward expected"
			),
		},
	}


def validate_items(
	rows: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], bool]:
	blockers: list[dict[str, str]] = []
	warnings: list[dict[str, str]] = []
	if not rows:
		blockers.append({"code": "empty", "message": MSG_EMPTY})
		return blockers, warnings, False

	for row in rows:
		blockers.extend(_row_unmet(row))
		if _is_background(row) and _v(row, "scope_label") == "In scope":
			warnings.append(
				{
					"code": f"{_v(row, 'item_id') or 'BG'}:background_obligation",
					"message": MSG_BACKGROUND_OBLIGATION,
				}
			)
		disclosure = _v(row, "disclosure_status_label")
		if disclosure == DISCLOSURE_REVIEW:
			warnings.append(
				{
					"code": f"{_v(row, 'item_id')}:disclosure_review",
					"message": "Items need disclosure review.",
				}
			)

	return blockers, warnings, len(blockers) == 0


def inventory_has_progress(rows: list[dict[str, Any]]) -> bool:
	return any(_any_content(r) for r in rows)


def inventory_exit_conditions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	conds: list[dict[str, Any]] = [
		{
			"key": "has_items",
			"label": "At least one inventory or background item",
			"met": bool(rows),
		}
	]
	for row in rows:
		rid = _v(row, "item_id") or "INV"
		unmet = _row_unmet(row)
		conds.append(
			{
				"key": f"item_{rid}",
				"label": f"{rid} setup complete",
				"met": len(unmet) == 0 and _any_content(row),
			}
		)
	return conds


def inventory_exit_conditions_for_doc(doc) -> list[dict[str, Any]]:
	rows = _parse_items(getattr(doc, "system_inventory", None))
	return inventory_exit_conditions(rows)


def _available_requirements(doc) -> list[dict[str, str]]:
	from kentender_procurement.tender_configurations.services.it_requirements import (
		_parse_requirements,
	)

	out: list[dict[str, str]] = []
	for row in _parse_requirements(getattr(doc, "it_requirements", None)):
		rid = _v(row, "requirement_id")
		title = _v(row, "title")
		if rid:
			out.append({"id": rid, "code": rid, "name": title or rid})
	return out


def _available_milestones(doc) -> list[dict[str, str]]:
	from kentender_procurement.tender_configurations.services.implementation_schedule import (
		_parse_schedule,
	)

	parsed = _parse_schedule(getattr(doc, "implementation_schedule", None))
	out: list[dict[str, str]] = []
	for row in parsed.get("milestones") or []:
		mid = _v(row, "milestone_id")
		name = _v(row, "name")
		if mid:
			out.append({"id": mid, "code": mid, "name": name or mid})
	return out


def _resolve_refs(ids: list[str], available: list[dict[str, str]]) -> list[dict[str, str]]:
	by_id = {cstr(r.get("id") or "").strip(): r for r in available}
	out: list[dict[str, str]] = []
	for rid in ids:
		ref = by_id.get(rid)
		if ref:
			out.append({"id": ref["id"], "code": ref["code"], "name": ref["name"]})
		else:
			out.append({"id": rid, "code": rid, "name": rid})
	return out


def _persist_item(row: dict[str, Any]) -> dict[str, Any]:
	cleaned = _clean_item(row)
	return {
		"item_id": _v(cleaned, "item_id"),
		"item_title": _v(cleaned, "item_title"),
		"category_label": _v(cleaned, "category_label"),
		"scope_label": _v(cleaned, "scope_label"),
		"item_description": _v(cleaned, "item_description"),
		"bidder_consideration": _v(cleaned, "bidder_consideration"),
		"related_requirement_ids": cleaned.get("related_requirement_ids") or [],
		"related_milestone_ids": cleaned.get("related_milestone_ids") or [],
		"location_site": _v(cleaned, "location_site"),
		"existing_system_name": _v(cleaned, "existing_system_name"),
		"estimated_volume_count": _v(cleaned, "estimated_volume_count"),
		"integration_point": _v(cleaned, "integration_point"),
		"data_source": _v(cleaned, "data_source"),
		"support_licence_context": _v(cleaned, "support_licence_context"),
		"out_of_scope_note": _v(cleaned, "out_of_scope_note"),
		"disclosure_status_label": _v(cleaned, "disclosure_status_label"),
		"disclosure_note": _v(cleaned, "disclosure_note"),
		"price_link_label": _default_price_link(cleaned),
	}


def _sync_cfg05_steps_state(doc, *, can_continue: bool, has_progress: bool, progress: dict) -> None:
	state = _parse_steps_state(getattr(doc, "steps_state", None))
	cfg = dict(state.get("CFG-05") or {})
	if can_continue:
		cfg["status_label"] = STEP_COMPLETE
	elif has_progress:
		cfg["status_label"] = STEP_IN_PROGRESS
	else:
		cfg["status_label"] = STEP_NOT_STARTED
	cfg["progress_pct"] = progress.get("progress_pct", 0)
	cfg["progress_met_count"] = progress.get("met_count", 0)
	cfg["progress_required_count"] = progress.get("required_count", 0)
	state["CFG-05"] = cfg
	doc.steps_state = json.dumps(state)


def get_configuration_system_inventory(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	raw_rows = _parse_items(getattr(doc, "system_inventory", None))
	avail_req = _available_requirements(doc)
	avail_ms = _available_milestones(doc)
	enriched = []
	for row in raw_rows:
		item = enrich_item(row)
		item["related_requirement_refs"] = _resolve_refs(
			item.get("related_requirement_ids") or [], avail_req
		)
		item["related_milestone_refs"] = _resolve_refs(
			item.get("related_milestone_ids") or [], avail_ms
		)
		enriched.append(item)

	blockers, warnings, can_continue = validate_items(raw_rows)
	has_progress = inventory_has_progress(raw_rows)
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")

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
		"items": enriched,
		"next_inventory_id": _next_item_id(raw_rows, background=False),
		"next_background_id": _next_item_id(raw_rows, background=True),
		"available_requirements": avail_req,
		"available_milestones": avail_ms,
		"context": context,
		"options": {
			"category_label": list(CATEGORIES),
			"scope_label": list(SCOPES),
			"disclosure_status_label": list(DISCLOSURE_STATUSES),
			"price_link_label": list(PRICE_LINKS),
		},
		"column_contract": {
			"note": (
				"Bidder Consideration, Disclosure Status, and Price Link show content only. "
				"Never put missing/defined/valid in those columns — use Setup Status."
			),
			"columns": [
				"ID",
				"Item",
				"Category",
				"Scope",
				"Bidder Consideration",
				"Disclosure Status",
				"Price Link",
				"Setup Status",
				"Action",
			],
		},
		"guidance": {
			"title": "Inventory & Background Guidance",
			"body": (
				"Describe the environment bidders need to understand. Keep binding "
				"obligations in IT Requirements and commercial pricing in Price Schedule."
			),
			"what_this_affects": (
				"Bidder understanding, price schedule structure, evidence expectations, "
				"contract values, and tender preview."
			),
			"used_later_by": (
				"Price Schedule, Evaluation Setup, Forms & Evidence, Contract Values, "
				"and Readiness Check."
			),
			"not_configured_here": (
				"Technical requirements, price amounts, scoring, submission forms, "
				"SCC values, security secrets, and post-award asset records."
			),
		},
		"disclosure_banner": {
			"primary": (
				"Only include information bidders need to prepare a responsive tender. "
				"Do not disclose passwords, secret keys, private IP addresses, "
				"vulnerability details, or internal security procedures."
			),
			"secondary": (
				"If a detail creates a binding obligation, configure it in IT Requirements "
				"instead of only describing it as background."
			),
		},
	}


def save_configuration_system_inventory(
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
	if isinstance(payload.get("items"), (list, str)):
		incoming = _parse_items(payload.get("items"))
	elif isinstance(payload, list):
		incoming = _parse_items(payload)
	else:
		incoming = _parse_items(payload.get("system_inventory"))

	persist: list[dict[str, Any]] = []
	for row in incoming:
		item = _persist_item(row)
		if not item.get("item_id"):
			item["item_id"] = _next_item_id(persist, background=_is_background(item))
		persist.append(item)

	blockers, warnings, can_continue = validate_items(persist)
	has_progress = inventory_has_progress(persist)

	from kentender_procurement.tender_configurations.services.step_progress import (
		evaluate_conditions,
	)

	progress = evaluate_conditions(inventory_exit_conditions(persist))
	blob = {"items": persist}

	doc.system_inventory = json.dumps(blob)
	doc.blocker_count = len(blockers)
	doc.warning_count = len(warnings)
	_sync_cfg05_steps_state(
		doc,
		can_continue=can_continue,
		has_progress=has_progress,
		progress=progress,
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return get_configuration_system_inventory(doc.name)
