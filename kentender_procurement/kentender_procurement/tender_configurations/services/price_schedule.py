# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-06 Price Schedule GET/POST (C2-CFG6 + column-clarity).

Quantity / Duration, Source, and Evaluated Price show content only.
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

PRICE_GROUPS = (
	"Supply & Installation",
	"Recurrent Cost",
	"Optional / Provisional",
)
GROUP_SUPPLY = "Supply & Installation"
GROUP_RECURRENT = "Recurrent Cost"
GROUP_OPTIONAL = "Optional / Provisional"

PRICING_BASES = (
	"Unit price",
	"Lump sum",
	"Monthly",
	"Annual",
	"Per user",
	"Per site",
	"Per device",
	"Per milestone",
	"As specified",
)
BASIS_LUMP = "Lump sum"
BASIS_AS_SPECIFIED = "As specified"
BASIS_MONTHLY = "Monthly"
BASIS_ANNUAL = "Annual"

EVALUATED_TREATMENTS = ("Included", "Excluded", "Conditional")
EVAL_INCLUDED = "Included"
EVAL_EXCLUDED = "Excluded"
EVAL_CONDITIONAL = "Conditional"

SOURCE_TYPES = ("Requirement", "Inventory", "Schedule", "User added")
SOURCE_REQUIREMENT = "Requirement"
SOURCE_INVENTORY = "Inventory"
SOURCE_SCHEDULE = "Schedule"
SOURCE_USER = "User added"

SETUP_COMPLETE = "Complete"
SETUP_NEEDS_ATTENTION = "Needs attention"
SETUP_DRAFT = "Draft"
SETUP_IN_PROGRESS = "In progress"
SETUP_NOT_STARTED = "Not started"

CURRENCY_FALLBACK = "As specified in TDS"
EDITABLE_KEYS = frozenset(
	{
		"item_id",
		"item_name",
		"price_group",
		"bidder_facing_description",
		"source_type",
		"related_requirement_id",
		"related_inventory_id",
		"related_milestone_id",
		"pricing_basis",
		"quantity",
		"unit",
		"currency",
		"evaluated_price_treatment",
		"conditional_rule",
		"bidder_pricing_instruction",
	}
)
BANNED_KEYS = frozenset(
	{
		"std_version_hash",
		"binding_id",
		"clause_hash",
		"schema_version",
		"rule_id",
		"bidder_price",
		"bid_rank",
		"score",
		"pass_mark",
		"payment_certificate",
		"budget_approval",
	}
)

MSG_EMPTY = "Add at least one price item before continuing."
MSG_NAME = "Add a price item name."
MSG_GROUP = "Select a price group."
MSG_BASIS = "Select how bidders should price this item."
MSG_QUANTITY = "Enter the quantity or duration and unit bidders must price against."
MSG_EVAL = "Choose whether this item is included in the evaluated price."
MSG_CONDITIONAL = "Explain when this item is included in the evaluated price."
MSG_INSTRUCTION = "Add the instruction bidders will see."
MSG_DESCRIPTION = "Add a bidder-facing description."
MSG_DIAGNOSTIC = (
	"Use a bidder-facing value, not a setup-status phrase."
)
MSG_OPTIONAL_INCLUDED = (
	"Confirm that this optional item should be included in the evaluated price."
)
MSG_USER_NO_LINK = "Confirm this item is intentionally user-added."

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

TAB_ALL = "all_price_items"
TAB_SUPPLY = "supply_installation"
TAB_RECURRENT = "recurrent_costs"
TAB_OPTIONAL = "optional_provisional"
TAB_NEEDS = "needs_attention"
TABS = (TAB_ALL, TAB_SUPPLY, TAB_RECURRENT, TAB_OPTIONAL, TAB_NEEDS)


def _v(row: dict[str, Any], key: str) -> str:
	return cstr(row.get(key) or "").strip()


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
		raw = raw.get("items") or raw.get("price_items") or []
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
		if isinstance(val, (dict, list)):
			continue
		cleaned[k] = cstr(val).strip() if val is not None else ""
	if not cleaned.get("item_name") and row.get("item_title"):
		cleaned["item_name"] = cstr(row.get("item_title")).strip()
	if not cleaned.get("price_group") and row.get("price_group_label"):
		cleaned["price_group"] = cstr(row.get("price_group_label")).strip()
	if not cleaned.get("pricing_basis") and row.get("pricing_basis_label"):
		cleaned["pricing_basis"] = cstr(row.get("pricing_basis_label")).strip()
	if not cleaned.get("evaluated_price_treatment") and row.get(
		"evaluated_price_treatment_label"
	):
		cleaned["evaluated_price_treatment"] = cstr(
			row.get("evaluated_price_treatment_label")
		).strip()
	# Legacy: Duration was a separate field; fold into Quantity when empty.
	if not cleaned.get("quantity") and row.get("duration"):
		cleaned["quantity"] = cstr(row.get("duration")).strip()
	if not cleaned.get("source_type") and row.get("source_label"):
		# Map display labels back when needed
		label = cstr(row.get("source_label")).strip()
		if label in SOURCE_TYPES:
			cleaned["source_type"] = label
		elif label == "IT Requirements":
			cleaned["source_type"] = SOURCE_REQUIREMENT
		elif label == "System Inventory":
			cleaned["source_type"] = SOURCE_INVENTORY
		elif label == "Implementation Schedule":
			cleaned["source_type"] = SOURCE_SCHEDULE
	return cleaned


def _next_item_id(rows: list[dict[str, Any]]) -> str:
	max_n = 0
	for row in rows:
		mid = _v(row, "item_id")
		m = re.match(r"^PRI-(\d+)$", mid, re.I)
		if m:
			max_n = max(max_n, int(m.group(1)))
	return f"PRI-{max_n + 1:03d}"


def _needs_quantity(row: dict[str, Any]) -> bool:
	"""Quantity/Duration is one value; Unit differentiates (e.g. 12 units vs 36 months)."""
	basis = _v(row, "pricing_basis")
	if basis in (BASIS_LUMP, BASIS_AS_SPECIFIED, ""):
		return False
	if _v(row, "price_group") == GROUP_RECURRENT:
		return True
	if basis in (BASIS_MONTHLY, BASIS_ANNUAL):
		return True
	return basis in PRICING_BASES


def _row_unmet(row: dict[str, Any]) -> list[dict[str, str]]:
	unmet: list[dict[str, str]] = []
	rid = _v(row, "item_id") or "item"

	def add(code: str, message: str):
		unmet.append({"code": f"{rid}:{code}", "message": message})

	if not _v(row, "item_name"):
		add("item_name", MSG_NAME)
	group = _v(row, "price_group")
	if not group or group not in PRICE_GROUPS:
		add("price_group", MSG_GROUP)
	if not _v(row, "bidder_facing_description"):
		add("bidder_facing_description", MSG_DESCRIPTION)
	elif _is_diagnostic_phrase(_v(row, "bidder_facing_description")):
		add("bidder_facing_description", MSG_DIAGNOSTIC)
	basis = _v(row, "pricing_basis")
	if not basis or basis not in PRICING_BASES:
		add("pricing_basis", MSG_BASIS)
	elif _needs_quantity(row):
		if not _v(row, "quantity") or not _v(row, "unit"):
			add("quantity", MSG_QUANTITY)
	treatment = _v(row, "evaluated_price_treatment")
	if not treatment or treatment not in EVALUATED_TREATMENTS:
		add("evaluated_price_treatment", MSG_EVAL)
	elif treatment == EVAL_CONDITIONAL and not _v(row, "conditional_rule"):
		add("conditional_rule", MSG_CONDITIONAL)
	instruction = _v(row, "bidder_pricing_instruction")
	if not instruction:
		add("bidder_pricing_instruction", MSG_INSTRUCTION)
	elif _is_diagnostic_phrase(instruction):
		add("bidder_pricing_instruction", MSG_DIAGNOSTIC)
	return unmet


def _any_content(row: dict[str, Any]) -> bool:
	for key in EDITABLE_KEYS:
		if key == "item_id":
			continue
		if _v(row, key):
			return True
	return False


def _derive_setup_status(row: dict[str, Any], unmet: list[dict[str, str]]) -> str:
	if not _any_content(row):
		return SETUP_DRAFT
	if not unmet:
		return SETUP_COMPLETE
	if _v(row, "item_name"):
		return SETUP_NEEDS_ATTENTION
	return SETUP_IN_PROGRESS


def _action_for_setup(status: str) -> str:
	if status == SETUP_COMPLETE:
		return "Edit"
	if status == SETUP_NEEDS_ATTENTION:
		return "Fix"
	return "Continue"


def _source_label(source_type: str) -> str:
	return {
		SOURCE_REQUIREMENT: "IT Requirements",
		SOURCE_INVENTORY: "System Inventory",
		SOURCE_SCHEDULE: "Implementation Schedule",
		SOURCE_USER: "User added",
	}.get(source_type, source_type or "—")


def _quantity_display(row: dict[str, Any]) -> str:
	basis = _v(row, "pricing_basis")
	qty = _v(row, "quantity")
	unit = _v(row, "unit")
	if basis == BASIS_LUMP:
		return qty and unit and f"{qty} {unit}" or (qty or unit or "1 lot")
	if basis == BASIS_AS_SPECIFIED:
		return qty or unit or "As specified"
	if qty and unit:
		text = f"{qty} {unit}"
	elif qty:
		text = qty
	elif unit:
		text = unit
	else:
		text = ""
	if text and not _is_diagnostic_phrase(text):
		return text
	return "—" if not text else text


def enrich_item(row: dict[str, Any]) -> dict[str, Any]:
	unmet = _row_unmet(row)
	setup = _derive_setup_status(row, unmet)
	source_type = _v(row, "source_type") or SOURCE_USER
	treatment = _v(row, "evaluated_price_treatment")
	treatment_display = treatment if treatment in EVALUATED_TREATMENTS else "—"
	qty_display = _quantity_display(row)
	if _is_diagnostic_phrase(qty_display):
		qty_display = "—"
	return {
		"item_id": _v(row, "item_id"),
		"item_name": _v(row, "item_name"),
		"price_group": _v(row, "price_group"),
		"price_group_label": _v(row, "price_group"),
		"bidder_facing_description": _v(row, "bidder_facing_description"),
		"source_type": source_type,
		"source_label": _source_label(source_type),
		"related_requirement_id": _v(row, "related_requirement_id"),
		"related_inventory_id": _v(row, "related_inventory_id"),
		"related_milestone_id": _v(row, "related_milestone_id"),
		"pricing_basis": _v(row, "pricing_basis"),
		"pricing_basis_label": _v(row, "pricing_basis"),
		"quantity": _v(row, "quantity"),
		"unit": _v(row, "unit"),
		"quantity_display": qty_display,
		"currency": _v(row, "currency") or CURRENCY_FALLBACK,
		"evaluated_price_treatment": treatment,
		"evaluated_price_treatment_label": treatment,
		"evaluated_price_display": treatment_display,
		"conditional_rule": _v(row, "conditional_rule"),
		"bidder_pricing_instruction": _v(row, "bidder_pricing_instruction"),
		"setup_status_label": setup,
		"status": setup,
		"status_label": setup if setup != SETUP_NOT_STARTED else SETUP_DRAFT,
		"action_label": _action_for_setup(setup),
		"route_or_drawer_action": "edit",
		"issue_summary": unmet[0]["message"] if unmet else "",
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
		rid = _v(row, "item_id") or "PRI"
		if (
			_v(row, "price_group") == GROUP_OPTIONAL
			and _v(row, "evaluated_price_treatment") == EVAL_INCLUDED
		):
			warnings.append(
				{"code": f"{rid}:optional_included", "message": MSG_OPTIONAL_INCLUDED}
			)
		if _v(row, "source_type") == SOURCE_USER and not (
			_v(row, "related_requirement_id")
			or _v(row, "related_inventory_id")
			or _v(row, "related_milestone_id")
		):
			warnings.append({"code": f"{rid}:user_no_link", "message": MSG_USER_NO_LINK})

	return blockers, warnings, len(blockers) == 0


def price_schedule_has_progress(rows: list[dict[str, Any]]) -> bool:
	return any(_any_content(r) for r in rows)


def price_schedule_exit_conditions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	conds: list[dict[str, Any]] = [
		{
			"key": "has_items",
			"label": "At least one price item",
			"met": bool(rows),
		}
	]
	for row in rows:
		rid = _v(row, "item_id") or "PRI"
		unmet = _row_unmet(row)
		conds.append(
			{
				"key": f"item_{rid}",
				"label": f"{rid} setup complete",
				"met": len(unmet) == 0 and _any_content(row),
			}
		)
	return conds


def price_schedule_exit_conditions_for_doc(doc) -> list[dict[str, Any]]:
	rows = _parse_items(getattr(doc, "price_schedule", None))
	return price_schedule_exit_conditions(rows)


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


def _available_inventory(doc) -> list[dict[str, str]]:
	from kentender_procurement.tender_configurations.services.system_inventory import (
		CATEGORY_BACKGROUND,
		CATEGORY_OUT_OF_SCOPE,
		SCOPE_OUT,
		_parse_items as _parse_inv,
		_v as _inv_v,
	)

	out: list[dict[str, str]] = []
	for row in _parse_inv(getattr(doc, "system_inventory", None)):
		iid = _inv_v(row, "item_id")
		title = _inv_v(row, "item_title")
		cat = _inv_v(row, "category_label")
		scope = _inv_v(row, "scope_label")
		if not iid:
			continue
		if cat in (CATEGORY_BACKGROUND, CATEGORY_OUT_OF_SCOPE) or scope == SCOPE_OUT:
			continue
		out.append({"id": iid, "code": iid, "name": title or iid})
	return out


def _resolve_ref(rid: str, available: list[dict[str, str]]) -> dict[str, str] | None:
	if not rid:
		return None
	by_id = {cstr(r.get("id") or "").strip(): r for r in available}
	ref = by_id.get(rid)
	if ref:
		return {"id": ref["id"], "code": ref["code"], "name": ref["name"]}
	return {"id": rid, "code": rid, "name": rid}


def _tds_currency(doc) -> str:
	from kentender_procurement.tender_configurations.services.tds import (
		_parse_tds_values,
		normalize_display_values,
	)

	values = normalize_display_values(doc, _parse_tds_values(getattr(doc, "tds_values", None)))
	cur = cstr(values.get("tender_currency") or "").strip()
	return cur or CURRENCY_FALLBACK


def _persist_item(row: dict[str, Any], *, default_currency: str) -> dict[str, Any]:
	cleaned = _clean_item(row)
	currency = _v(cleaned, "currency") or default_currency or CURRENCY_FALLBACK
	source = _v(cleaned, "source_type") or SOURCE_USER
	if source not in SOURCE_TYPES:
		source = SOURCE_USER
	return {
		"item_id": _v(cleaned, "item_id"),
		"item_name": _v(cleaned, "item_name"),
		"price_group": _v(cleaned, "price_group"),
		"bidder_facing_description": _v(cleaned, "bidder_facing_description"),
		"source_type": source,
		"related_requirement_id": _v(cleaned, "related_requirement_id"),
		"related_inventory_id": _v(cleaned, "related_inventory_id"),
		"related_milestone_id": _v(cleaned, "related_milestone_id"),
		"pricing_basis": _v(cleaned, "pricing_basis"),
		"quantity": _v(cleaned, "quantity"),
		"unit": _v(cleaned, "unit"),
		"currency": currency,
		"evaluated_price_treatment": _v(cleaned, "evaluated_price_treatment"),
		"conditional_rule": _v(cleaned, "conditional_rule"),
		"bidder_pricing_instruction": _v(cleaned, "bidder_pricing_instruction"),
	}


def _build_import_drafts(
	doc,
	existing: list[dict[str, Any]],
	*,
	default_currency: str,
) -> list[dict[str, Any]]:
	"""Draft price items from CFG-03/04/05 that are not already linked."""
	used_req = {_v(r, "related_requirement_id") for r in existing if _v(r, "related_requirement_id")}
	used_inv = {_v(r, "related_inventory_id") for r in existing if _v(r, "related_inventory_id")}
	used_ms = {_v(r, "related_milestone_id") for r in existing if _v(r, "related_milestone_id")}
	drafts: list[dict[str, Any]] = []

	for ref in _available_inventory(doc):
		if ref["id"] in used_inv:
			continue
		drafts.append(
			_persist_item(
				{
					"item_name": ref["name"],
					"price_group": GROUP_SUPPLY,
					"bidder_facing_description": f"Price for inventory context: {ref['name']}",
					"source_type": SOURCE_INVENTORY,
					"related_inventory_id": ref["id"],
					"pricing_basis": "Unit price",
					"currency": default_currency,
				},
				default_currency=default_currency,
			)
		)

	for ref in _available_requirements(doc):
		if ref["id"] in used_req:
			continue
		drafts.append(
			_persist_item(
				{
					"item_name": ref["name"],
					"price_group": GROUP_SUPPLY,
					"bidder_facing_description": f"Price for requirement: {ref['name']}",
					"source_type": SOURCE_REQUIREMENT,
					"related_requirement_id": ref["id"],
					"pricing_basis": BASIS_LUMP,
					"quantity": "1",
					"unit": "lot",
					"currency": default_currency,
				},
				default_currency=default_currency,
			)
		)

	for ref in _available_milestones(doc):
		if ref["id"] in used_ms:
			continue
		drafts.append(
			_persist_item(
				{
					"item_name": ref["name"],
					"price_group": GROUP_SUPPLY,
					"bidder_facing_description": f"Price for milestone: {ref['name']}",
					"source_type": SOURCE_SCHEDULE,
					"related_milestone_id": ref["id"],
					"pricing_basis": "Per milestone",
					"quantity": "1",
					"unit": "milestone",
					"currency": default_currency,
				},
				default_currency=default_currency,
			)
		)

	return drafts


def _summary(rows: list[dict[str, Any]], enriched: list[dict[str, Any]]) -> dict[str, int]:
	supply = sum(1 for r in rows if _v(r, "price_group") == GROUP_SUPPLY)
	recurrent = sum(1 for r in rows if _v(r, "price_group") == GROUP_RECURRENT)
	optional = sum(1 for r in rows if _v(r, "price_group") == GROUP_OPTIONAL)
	needs = sum(
		1
		for e in enriched
		if e.get("setup_status_label") in (SETUP_NEEDS_ATTENTION, SETUP_DRAFT, SETUP_IN_PROGRESS)
	)
	return {
		"total_items": len(rows),
		"supply_installation_count": supply,
		"recurrent_cost_count": recurrent,
		"optional_provisional_count": optional,
		"needs_attention_count": needs,
	}


def _sync_cfg06_steps_state(doc, *, can_continue: bool, has_progress: bool, progress: dict) -> None:
	state = _parse_steps_state(getattr(doc, "steps_state", None))
	cfg = dict(state.get("CFG-06") or {})
	if can_continue:
		cfg["status_label"] = STEP_COMPLETE
	elif has_progress:
		cfg["status_label"] = STEP_IN_PROGRESS
	else:
		cfg["status_label"] = STEP_NOT_STARTED
	cfg["progress_pct"] = progress.get("progress_pct", 0)
	cfg["progress_met_count"] = progress.get("met_count", 0)
	cfg["progress_required_count"] = progress.get("required_count", 0)
	state["CFG-06"] = cfg
	doc.steps_state = json.dumps(state)


def get_configuration_price_schedule(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	raw_rows = _parse_items(getattr(doc, "price_schedule", None))
	avail_req = _available_requirements(doc)
	avail_ms = _available_milestones(doc)
	avail_inv = _available_inventory(doc)
	currency = _tds_currency(doc)
	enriched = []
	for row in raw_rows:
		item = enrich_item(row)
		if not item.get("currency"):
			item["currency"] = currency
		item["related_requirement_ref"] = _resolve_ref(
			item.get("related_requirement_id") or "", avail_req
		)
		item["related_inventory_ref"] = _resolve_ref(
			item.get("related_inventory_id") or "", avail_inv
		)
		item["related_milestone_ref"] = _resolve_ref(
			item.get("related_milestone_id") or "", avail_ms
		)
		enriched.append(item)

	blockers, warnings, can_continue = validate_items(raw_rows)
	has_progress = price_schedule_has_progress(raw_rows)
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")
	import_candidates = _build_import_drafts(doc, raw_rows, default_currency=currency)

	return {
		"configuration_id": doc.name,
		"procurement_package_ref": context["procurement_package_ref"],
		"tender_title": cstr(doc.tender_title or ""),
		"procuring_entity_name": context["procuring_entity_name"],
		"procurement_method_label": context["procurement_method_label"],
		"std_family_label": context["std_family_label"],
		"standard_tender_document_label": cstr(doc.std_document_label or ""),
		"configuration_status_label": _STATUS_LABELS.get(status, status),
		"wizard_state_label": context.get("wizard_state_label")
		or _STATUS_LABELS.get(status, status),
		"blocker_count": len(blockers),
		"warning_count": len(warnings),
		"blockers": blockers,
		"warnings": warnings,
		"can_continue": can_continue,
		"has_progress": has_progress,
		"active_tab": TAB_ALL,
		"price_items": enriched,
		"items": enriched,
		"summary": _summary(raw_rows, enriched),
		"next_item_id": _next_item_id(raw_rows),
		"available_requirements": avail_req,
		"available_milestones": avail_ms,
		"available_inventory": avail_inv,
		"import_candidate_count": len(import_candidates),
		"currency_default": currency,
		"context": context,
		"options": {
			"price_group": list(PRICE_GROUPS),
			"pricing_basis": list(PRICING_BASES),
			"evaluated_price_treatment": list(EVALUATED_TREATMENTS),
			"source_type": list(SOURCE_TYPES),
			"tabs": [
				{"key": TAB_ALL, "label": "All Price Items"},
				{"key": TAB_SUPPLY, "label": "Supply & Installation"},
				{"key": TAB_RECURRENT, "label": "Recurrent Costs"},
				{"key": TAB_OPTIONAL, "label": "Optional / Provisional Items"},
				{"key": TAB_NEEDS, "label": "Needs Attention"},
			],
		},
		"column_contract": {
			"note": (
				"Quantity / Duration, Source, and Evaluated Price show content only. "
				"Never put missing/defined/valid in those columns — use Setup Status."
			),
			"columns": [
				"ID",
				"Price Item",
				"Price Group",
				"Pricing Basis",
				"Quantity / Duration",
				"Source",
				"Evaluated Price",
				"Setup Status",
				"Action",
			],
		},
	}


def save_configuration_price_schedule(
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
	currency = _tds_currency(doc)

	do_import = bool(payload.get("import") or payload.get("action") == "import")
	if isinstance(payload.get("items"), (list, str)) or isinstance(
		payload.get("price_items"), (list, str)
	):
		incoming = _parse_items(payload.get("items") or payload.get("price_items"))
	elif isinstance(payload, list):
		incoming = _parse_items(payload)
	else:
		incoming = _parse_items(payload.get("price_schedule"))

	persist: list[dict[str, Any]] = []
	for row in incoming:
		item = _persist_item(row, default_currency=currency)
		if not item.get("item_id"):
			item["item_id"] = _next_item_id(persist)
		persist.append(item)

	if do_import:
		for draft in _build_import_drafts(doc, persist, default_currency=currency):
			draft["item_id"] = _next_item_id(persist)
			persist.append(draft)

	blockers, warnings, can_continue = validate_items(persist)
	has_progress = price_schedule_has_progress(persist)

	from kentender_procurement.tender_configurations.services.step_progress import (
		evaluate_conditions,
	)

	progress = evaluate_conditions(price_schedule_exit_conditions(persist))
	blob = {"items": persist}

	doc.price_schedule = json.dumps(blob)
	doc.blocker_count = len(blockers)
	doc.warning_count = len(warnings)
	_sync_cfg06_steps_state(
		doc,
		can_continue=can_continue,
		has_progress=has_progress,
		progress=progress,
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return get_configuration_price_schedule(doc.name)
