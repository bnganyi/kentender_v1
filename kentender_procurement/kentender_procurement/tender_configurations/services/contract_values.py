# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-09 Contract Values GET/POST (C2-CFG9).

Confirm tender-specific SCC / contract-facing values. Not GCC editing or post-award admin.
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
	"SCC Value",
	"Delivery Obligation",
	"Support & Warranty",
	"Security & Compliance Obligation",
	"Securities & Guarantees",
	"Contract Schedule",
	"Acceptance & Handover",
)
CAT_SCC = "SCC Value"
CAT_DELIVERY = "Delivery Obligation"
CAT_SUPPORT = "Support & Warranty"
CAT_SECURITY = "Security & Compliance Obligation"
CAT_SECURITIES = "Securities & Guarantees"
CAT_SCHEDULE = "Contract Schedule"
CAT_ACCEPTANCE = "Acceptance & Handover"

SOURCES = (
	"Tender Data Sheet",
	"IT Requirements",
	"Implementation Schedule",
	"System Inventory & Bidder Background",
	"Price Schedule",
	"Forms & Evidence",
	"User entered",
	"Standard Tender Document",
)
SOURCE_TDS = "Tender Data Sheet"
SOURCE_REQ = "IT Requirements"
SOURCE_SCHED = "Implementation Schedule"
SOURCE_INV = "System Inventory & Bidder Background"
SOURCE_PRICE = "Price Schedule"
SOURCE_FORMS = "Forms & Evidence"
SOURCE_USER = "User entered"
SOURCE_STD = "Standard Tender Document"

SETUP_COMPLETE = "Complete"
SETUP_NEEDS_ATTENTION = "Needs attention"
SETUP_REVIEW = "Review before handoff"
SETUP_NOT_APPLICABLE = "Not applicable"
SETUP_DRAFT = "Draft"

EDITABLE_KEYS = frozenset(
	{
		"contract_value_id",
		"item_label",
		"category",
		"source_screen",
		"source_item_label",
		"source_value",
		"contract_location",
		"value_or_obligation",
		"not_applicable",
		"not_applicable_reason",
		"review_note",
		"editable_here",
		"read_only_reason",
		"source_route",
	}
)
BANNED_KEYS = frozenset(
	{
		"std_version_hash",
		"binding_id",
		"clause_hash",
		"schema_version",
		"rule_id",
		"gcc_text",
		"award_decision",
		"payment_certificate",
		"variation",
	}
)

MSG_EMPTY = "Confirm at least one contract value before completing this step."
MSG_LABEL = "Add an item name."
MSG_CATEGORY = "Select a category."
MSG_SOURCE = "Select the source screen."
MSG_LOCATION = "Enter the contract location."
MSG_VALUE = "Enter the value or obligation text."
MSG_NA_REASON = "Add the reason this value is not applicable."
MSG_PERF_SECURITY = "Performance security value is missing."
MSG_ATTACHMENTS = "Contract attachment list is incomplete."
MSG_REVIEW = "Data residency obligation should be reviewed before handoff."

TAB_ALL = "all_contract_values"
TAB_SCC = "scc_values"
TAB_DELIVERY = "delivery_obligations"
TAB_SUPPORT = "support_warranty"
TAB_SECURITIES = "securities_guarantees"
TAB_SCHEDULES = "contract_schedules"
TAB_NEEDS = "needs_attention"

SOURCE_ROUTES = {
	SOURCE_TDS: "it-tender-configuration-tds",
	SOURCE_REQ: "it-tender-configuration-it-requirements",
	SOURCE_SCHED: "it-tender-configuration-implementation-schedule",
	SOURCE_INV: "it-tender-configuration-system-inventory",
	SOURCE_PRICE: "it-tender-configuration-price-schedule",
	SOURCE_FORMS: "it-tender-configuration-forms-and-evidence",
}


def _v(row: dict[str, Any], key: str) -> str:
	return cstr(row.get(key) or "").strip()


def _parse_blob(raw: Any) -> dict[str, Any]:
	if not raw:
		return {"contract_values": []}
	if isinstance(raw, str):
		try:
			raw = json.loads(raw)
		except (TypeError, ValueError):
			return {"contract_values": []}
	if isinstance(raw, list):
		return {"contract_values": [_clean_row(r) for r in raw if isinstance(r, dict)]}
	if not isinstance(raw, dict):
		return {"contract_values": []}
	rows = raw.get("contract_values") or raw.get("items") or []
	if not isinstance(rows, list):
		rows = []
	return {"contract_values": [_clean_row(r) for r in rows if isinstance(r, dict)]}


def _parse_rows(raw: Any) -> list[dict[str, Any]]:
	return _parse_blob(raw)["contract_values"]


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
	cleaned: dict[str, Any] = {}
	for key, val in row.items():
		k = cstr(key).strip()
		if not k or k in BANNED_KEYS or k not in EDITABLE_KEYS:
			continue
		if isinstance(val, (dict, list)):
			continue
		if k in ("not_applicable", "editable_here"):
			cleaned[k] = 1 if val in (1, "1", True, "true", "True", "yes", "Yes") else 0
		else:
			cleaned[k] = cstr(val).strip() if val is not None else ""
	if not cleaned.get("item_label") and row.get("item_name"):
		cleaned["item_label"] = cstr(row.get("item_name")).strip()
	return cleaned


def _next_id(rows: list[dict[str, Any]]) -> str:
	max_n = 0
	for row in rows:
		mid = _v(row, "contract_value_id")
		m = re.match(r"^CV-(\d+)$", mid, re.I)
		if m:
			max_n = max(max_n, int(m.group(1)))
	return f"CV-{max_n + 1:03d}"


def _is_na(row: dict[str, Any]) -> bool:
	return bool(row.get("not_applicable")) or _v(row, "value_or_obligation").lower() in (
		"not applicable",
		"n/a",
	)


def _row_unmet(row: dict[str, Any]) -> list[dict[str, str]]:
	unmet: list[dict[str, str]] = []
	rid = _v(row, "contract_value_id") or "item"

	def add(code: str, message: str):
		unmet.append({"code": f"{rid}:{code}", "message": message})

	if not _v(row, "item_label"):
		add("item_label", MSG_LABEL)
	if not _v(row, "category") or _v(row, "category") not in CATEGORIES:
		add("category", MSG_CATEGORY)
	if not _v(row, "source_screen") or _v(row, "source_screen") not in SOURCES:
		add("source_screen", MSG_SOURCE)
	if not _v(row, "contract_location"):
		add("contract_location", MSG_LOCATION)
	if _is_na(row):
		if not _v(row, "not_applicable_reason"):
			add("not_applicable_reason", MSG_NA_REASON)
		return unmet
	if not _v(row, "value_or_obligation"):
		add("value_or_obligation", MSG_VALUE)
	return unmet


def _any_content(row: dict[str, Any]) -> bool:
	for key in EDITABLE_KEYS:
		if key in ("contract_value_id", "editable_here", "not_applicable"):
			continue
		if _v(row, key) or row.get(key):
			return True
	return False


def _derive_status(row: dict[str, Any], unmet: list[dict[str, str]]) -> str:
	if _is_na(row) and not unmet:
		return SETUP_NOT_APPLICABLE
	if not _any_content(row):
		return SETUP_DRAFT
	if unmet:
		return SETUP_NEEDS_ATTENTION
	note = _v(row, "review_note").lower()
	label = _v(row, "item_label").lower()
	if "residency" in label or "review before handoff" in note:
		return SETUP_REVIEW
	return SETUP_COMPLETE


def _action_for(status: str) -> str:
	if status == SETUP_COMPLETE:
		return "Edit"
	if status == SETUP_NEEDS_ATTENTION:
		return "Fix"
	if status in (SETUP_REVIEW, SETUP_NOT_APPLICABLE):
		return "Review"
	return "Continue"


def enrich_row(row: dict[str, Any]) -> dict[str, Any]:
	unmet = _row_unmet(row)
	status = _derive_status(row, unmet)
	source = _v(row, "source_screen")
	editable = row.get("editable_here")
	if editable is None:
		editable = 1 if source in (SOURCE_USER, SOURCE_STD, "") else 1
	return {
		"contract_value_id": _v(row, "contract_value_id"),
		"item_label": _v(row, "item_label"),
		"category": _v(row, "category"),
		"source_screen": source or "Source not set",
		"source_item_label": _v(row, "source_item_label"),
		"source_value": _v(row, "source_value"),
		"contract_location": _v(row, "contract_location"),
		"value_or_obligation": _v(row, "value_or_obligation"),
		"not_applicable": 1 if _is_na(row) else 0,
		"not_applicable_reason": _v(row, "not_applicable_reason"),
		"review_note": _v(row, "review_note"),
		"editable_here": 1 if editable else 0,
		"read_only_reason": _v(row, "read_only_reason"),
		"source_route": _v(row, "source_route") or SOURCE_ROUTES.get(source, ""),
		"setup_status_label": status,
		"status": status,
		"status_label": status if status != SETUP_DRAFT else SETUP_NEEDS_ATTENTION,
		"action_label": _action_for(status),
		"issue_count": len(unmet),
		"issue_summary": unmet[0]["message"] if unmet else "",
	}


def validate_rows(
	rows: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], bool]:
	blockers: list[dict[str, str]] = []
	warnings: list[dict[str, str]] = []
	if not rows:
		blockers.append({"code": "empty", "message": MSG_EMPTY})
		return blockers, warnings, False

	for row in rows:
		blockers.extend(_row_unmet(row))

	labels = {_v(r, "item_label").lower() for r in rows}
	has_perf = any("performance security" in lab for lab in labels)
	if has_perf:
		for row in rows:
			if "performance security" in _v(row, "item_label").lower() and not _is_na(row):
				if not _v(row, "value_or_obligation"):
					blockers.append({"code": "perf_security", "message": MSG_PERF_SECURITY})

	has_attach = any("attachment" in lab for lab in labels)
	if has_attach:
		for row in rows:
			if "attachment" in _v(row, "item_label").lower() and not _is_na(row):
				val = _v(row, "value_or_obligation").lower()
				if not val or "missing" in val:
					blockers.append({"code": "attachments", "message": MSG_ATTACHMENTS})

	for row in rows:
		if "residency" in _v(row, "item_label").lower() and not _is_na(row):
			warnings.append({"code": "residency_review", "message": MSG_REVIEW})

	# Deduplicate by message
	seen_b: set[str] = set()
	uniq_b: list[dict[str, str]] = []
	for b in blockers:
		m = b.get("message") or ""
		if m in seen_b:
			continue
		seen_b.add(m)
		uniq_b.append(b)
	seen_w: set[str] = set()
	uniq_w: list[dict[str, str]] = []
	for w in warnings:
		m = w.get("message") or ""
		if m in seen_w:
			continue
		seen_w.add(m)
		uniq_w.append(w)

	return uniq_b, uniq_w, len(uniq_b) == 0


def contract_values_has_progress(rows: list[dict[str, Any]]) -> bool:
	return any(_any_content(r) for r in rows)


def contract_values_exit_conditions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	conds: list[dict[str, Any]] = [
		{"key": "has_values", "label": "At least one contract value", "met": bool(rows)}
	]
	for row in rows:
		rid = _v(row, "contract_value_id") or "CV"
		unmet = _row_unmet(row)
		conds.append(
			{
				"key": f"value_{rid}",
				"label": f"{rid} setup complete",
				"met": len(unmet) == 0 and _any_content(row),
			}
		)
	return conds


def contract_values_exit_conditions_for_doc(doc) -> list[dict[str, Any]]:
	blob = _parse_blob(getattr(doc, "contract_values", None))
	return contract_values_exit_conditions(blob["contract_values"])


def _persist_row(row: dict[str, Any]) -> dict[str, Any]:
	cleaned = _clean_row(row)
	category = _v(cleaned, "category")
	if category not in CATEGORIES:
		category = ""
	source = _v(cleaned, "source_screen")
	if source not in SOURCES:
		# Keep blank so missing source surfaces as Needs attention (do not invent User entered).
		source = ""
	return {
		"contract_value_id": _v(cleaned, "contract_value_id"),
		"item_label": _v(cleaned, "item_label"),
		"category": category,
		"source_screen": source,
		"source_item_label": _v(cleaned, "source_item_label"),
		"source_value": _v(cleaned, "source_value"),
		"contract_location": _v(cleaned, "contract_location"),
		"value_or_obligation": _v(cleaned, "value_or_obligation"),
		"not_applicable": 1 if cleaned.get("not_applicable") else 0,
		"not_applicable_reason": _v(cleaned, "not_applicable_reason"),
		"review_note": _v(cleaned, "review_note"),
		"editable_here": 0 if cleaned.get("editable_here") == 0 else 1,
		"read_only_reason": _v(cleaned, "read_only_reason"),
		"source_route": _v(cleaned, "source_route") or SOURCE_ROUTES.get(source, ""),
	}


def _suggest_from_upstream(doc, existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""Prepare draft contract values from earlier CFG steps when empty."""
	if existing:
		return []
	drafts = [
		{
			"item_label": "Performance Security",
			"category": CAT_SECURITIES,
			"source_screen": SOURCE_TDS,
			"contract_location": "SCC / Contract Data",
			"value_or_obligation": "",
			"editable_here": 1,
		},
		{
			"item_label": "Delivery Period",
			"category": CAT_SCC,
			"source_screen": SOURCE_SCHED,
			"contract_location": "SCC / Delivery Schedule",
			"value_or_obligation": "",
			"editable_here": 1,
		},
		{
			"item_label": "On-site Support",
			"category": CAT_SUPPORT,
			"source_screen": SOURCE_REQ,
			"contract_location": "Contract Schedule: Support",
			"value_or_obligation": "",
			"editable_here": 1,
		},
		{
			"item_label": "Data Residency",
			"category": CAT_SECURITY,
			"source_screen": SOURCE_REQ,
			"contract_location": "Contract Schedule: Security",
			"value_or_obligation": "Production data must remain in Kenya unless otherwise approved",
			"review_note": "Review before handoff",
			"editable_here": 1,
		},
		{
			"item_label": "Contract Attachments",
			"category": CAT_SCHEDULE,
			"source_screen": SOURCE_FORMS,
			"contract_location": "Contract Appendices",
			"value_or_obligation": "Missing required attachment list",
			"editable_here": 1,
		},
	]
	# Light pull from TDS / schedule if present
	try:
		from kentender_procurement.tender_configurations.services.implementation_schedule import (
			_parse_schedule,
		)

		sched = _parse_schedule(getattr(doc, "implementation_schedule", None))
		ms = (sched.get("milestones") or []) if isinstance(sched, dict) else []
		if ms:
			first = ms[0]
			name = cstr(first.get("name") or "").strip()
			dur = cstr(first.get("expected_duration_value") or "").strip()
			unit = cstr(first.get("expected_duration_unit") or "").strip()
			if dur and unit:
				drafts[1]["value_or_obligation"] = f"{dur} {unit} from notice to proceed"
				drafts[1]["source_item_label"] = name
	except Exception:
		pass
	return [_persist_row(d) for d in drafts]


def _guidance() -> dict[str, Any]:
	return {
		"title": "Contract Values Guidance",
		"body": (
			"Use this screen to confirm the values and obligations that will appear in the "
			"contract documents. Values may come from the Tender Data Sheet, IT Requirements, "
			"Implementation Schedule, Price Schedule, or Forms & Evidence. Edit only the "
			"contract-specific values allowed for this tender configuration."
		),
		"boundary_note": (
			"This screen prepares contract documents. It does not manage the signed contract after award."
		),
	}


def _sync_cfg09_steps_state(
	doc,
	*,
	can_continue: bool,
	has_progress: bool,
	progress: dict[str, Any],
) -> None:
	state = _parse_steps_state(getattr(doc, "steps_state", None))
	if can_continue:
		label = STEP_COMPLETE
	elif has_progress:
		label = STEP_IN_PROGRESS
	else:
		label = STEP_NOT_STARTED
	state["CFG-09"] = {
		"status_label": label,
		"progress_pct": progress.get("progress_pct") or 0,
		"met_count": progress.get("met_count") or 0,
		"required_count": progress.get("required_count") or 0,
	}
	doc.steps_state = json.dumps(state)


def get_configuration_contract_values(
	configuration_id: str, *, hydrate: bool = False
) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	blob = _parse_blob(getattr(doc, "contract_values", None))
	raw_rows = blob["contract_values"]
	if hydrate and not raw_rows:
		raw_rows = _suggest_from_upstream(doc, [])
	enriched = [enrich_row(row) for row in raw_rows]
	blockers, warnings, can_continue = validate_rows(raw_rows)
	has_progress = contract_values_has_progress(raw_rows)
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")

	return {
		"configuration_id": doc.name,
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"procurement_package_ref": context["procurement_package_ref"],
		"tender_title": cstr(doc.tender_title or ""),
		"std_family_label": context["std_family_label"],
		"procuring_entity_name": context["procuring_entity_name"],
		"procurement_method_label": context["procurement_method_label"],
		"wizard_state_label": context.get("wizard_state_label")
		or _STATUS_LABELS.get(status, status),
		"configuration_status_label": _STATUS_LABELS.get(status, status),
		"blocker_count": len(blockers),
		"warning_count": len(warnings),
		"blockers": blockers,
		"warnings": warnings,
		"can_continue": can_continue,
		"has_progress": has_progress,
		"active_tab": TAB_ALL,
		"contract_values": enriched,
		"items": enriched,
		"guidance": _guidance(),
		"next_contract_value_id": _next_id(raw_rows),
		"context": context,
		"tabs": [
			"All Contract Values",
			"SCC Values",
			"Delivery Obligations",
			"Support & Warranty",
			"Securities & Guarantees",
			"Contract Schedules",
			"Needs Attention",
		],
		"options": {
			"category": list(CATEGORIES),
			"source_screen": list(SOURCES),
			"tabs": [
				{"key": TAB_ALL, "label": "All Contract Values"},
				{"key": TAB_SCC, "label": "SCC Values"},
				{"key": TAB_DELIVERY, "label": "Delivery Obligations"},
				{"key": TAB_SUPPORT, "label": "Support & Warranty"},
				{"key": TAB_SECURITIES, "label": "Securities & Guarantees"},
				{"key": TAB_SCHEDULES, "label": "Contract Schedules"},
				{"key": TAB_NEEDS, "label": "Needs Attention"},
			],
		},
		"column_contract": {
			"note": (
				"Status uses Complete / Needs attention / Review before handoff / Not applicable. "
				"Never show GCC hashes, award, or post-award admin."
			),
			"columns": [
				"Item",
				"Category",
				"Source",
				"Contract Location",
				"Value / Obligation",
				"Status",
				"Action",
			],
		},
	}


def save_configuration_contract_values(
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

	do_hydrate = bool(payload.get("hydrate") or payload.get("run_check_hydrate") or payload.get("import"))
	if isinstance(payload.get("contract_values"), (list, str)) or isinstance(
		payload.get("items"), (list, str)
	):
		incoming = _parse_rows(payload.get("contract_values") or payload.get("items"))
	elif isinstance(payload, list):
		incoming = _parse_rows(payload)
	else:
		incoming = _parse_rows(payload.get("contract_values_blob") or payload.get("contract_values"))

	persist: list[dict[str, Any]] = []
	for row in incoming:
		item = _persist_row(row)
		if not item.get("contract_value_id"):
			item["contract_value_id"] = _next_id(persist)
		persist.append(item)

	if do_hydrate and not persist:
		for draft in _suggest_from_upstream(doc, []):
			draft["contract_value_id"] = _next_id(persist)
			persist.append(draft)

	blockers, warnings, can_continue = validate_rows(persist)
	has_progress = contract_values_has_progress(persist)

	from kentender_procurement.tender_configurations.services.step_progress import (
		evaluate_conditions,
	)

	progress = evaluate_conditions(contract_values_exit_conditions(persist))
	blob = {"contract_values": persist}

	doc.contract_values = json.dumps(blob)
	doc.blocker_count = len(blockers)
	doc.warning_count = len(warnings)
	_sync_cfg09_steps_state(
		doc,
		can_continue=can_continue,
		has_progress=has_progress,
		progress=progress,
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return get_configuration_contract_values(doc.name)
