# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-08 Forms & Evidence GET/POST (C2-CFG8).

Defines what bidders must submit (non-price Section IV forms/evidence).
Never expose actual uploads, evaluation scores, or price forms.
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
	"Standard Form",
	"Declaration",
	"Qualification Evidence",
	"Technical Evidence",
	"Tender Security",
	"Conditional Item",
)
CAT_STANDARD = "Standard Form"
CAT_DECLARATION = "Declaration"
CAT_QUAL = "Qualification Evidence"
CAT_TECH = "Technical Evidence"
CAT_SECURITY = "Tender Security"
CAT_CONDITIONAL = "Conditional Item"

SOURCES = (
	"STD",
	"TDS",
	"IT Requirements",
	"Evaluation Setup",
	"User Added",
)
SOURCE_STD = "STD"
SOURCE_TDS = "TDS"
SOURCE_REQ = "IT Requirements"
SOURCE_EVAL = "Evaluation Setup"
SOURCE_USER = "User Added"

REQUIREMENTS = (
	"Mandatory",
	"Conditional",
	"Optional",
	"Not Applicable",
)
REQ_MANDATORY = "Mandatory"
REQ_CONDITIONAL = "Conditional"
REQ_OPTIONAL = "Optional"
REQ_NA = "Not Applicable"

RESPONSE_FORMATS = (
	"Form",
	"PDF attachment",
	"certificate",
	"declaration",
	"table",
	"narrative",
	"other",
)

SETUP_COMPLETE = "Complete"
SETUP_NEEDS_ATTENTION = "Needs attention"
SETUP_NOT_APPLICABLE = "Not applicable"
SETUP_DRAFT = "Draft"

EDITABLE_KEYS = frozenset(
	{
		"item_id",
		"item_name",
		"category",
		"source",
		"requirement",
		"bidder_instruction",
		"accepted_response_format",
		"accepted_file_type",
		"condition_text",
		"condition_source",
		"related_requirement_id",
		"related_criterion_id",
		"related_tds_key",
		"not_applicable_reason",
	}
)
BANNED_KEYS = frozenset(
	{
		"std_version_hash",
		"binding_id",
		"clause_hash",
		"schema_version",
		"rule_id",
		"bidder_upload",
		"upload_status",
		"compliance_result",
		"bidder_score",
		"award_recommendation",
	}
)

MSG_EMPTY = "Add at least one submission item before continuing."
MSG_NAME = "Add a submission item name."
MSG_CATEGORY = "Select a category."
MSG_SOURCE = "Select the source or mark the item as user added."
MSG_REQUIREMENT = "Select whether the item is mandatory, conditional, optional, or not applicable."
MSG_INSTRUCTION = "Add a clear bidder instruction."
MSG_CONDITION = "Add the condition text for this conditional item."
MSG_NA_REASON = "Add the reason this item is not applicable."
MSG_MANDATORY_INSTR = "Mandatory submission items must have bidder instructions."
MSG_CONDITIONAL_INSTR = "Conditional items must have condition text and bidder instructions."
MSG_EVAL_WARN = "Some evidence items may change after Evaluation Setup is completed."
MSG_DIAGNOSTIC = "Use a bidder-facing value, not a setup-status phrase."

_DIAGNOSTIC_EXACT = {
	"missing",
	"defined",
	"valid",
	"complete",
	"incomplete",
	"needs attention",
	"draft",
	"not applicable",
	"passed",
	"failed",
	"ready",
	"locked",
	"submitted",
	"received",
	"compliant",
}

TAB_ALL = "all_items"
TAB_STANDARD = "standard_forms"
TAB_DECLARATIONS = "declarations"
TAB_QUAL = "qualification_evidence"
TAB_TECH = "technical_evidence"
TAB_SECURITY = "tender_security"
TAB_CONDITIONAL = "conditional_items"

STD_IMPORT_FORMS = (
	{
		"item_name": "Form of Tender",
		"category": CAT_STANDARD,
		"requirement": REQ_MANDATORY,
		"bidder_instruction": "Bidder must complete and sign the Form of Tender.",
		"accepted_response_format": "Form",
	},
	{
		"item_name": "Confidential Business Questionnaire",
		"category": CAT_STANDARD,
		"requirement": REQ_MANDATORY,
		"bidder_instruction": "Bidder must complete the Confidential Business Questionnaire.",
		"accepted_response_format": "Form",
	},
	{
		"item_name": "Certificate of Independent Tender Determination",
		"category": CAT_DECLARATION,
		"requirement": REQ_MANDATORY,
		"bidder_instruction": (
			"Bidder must complete and sign the Certificate of Independent Tender Determination."
		),
		"accepted_response_format": "declaration",
	},
	{
		"item_name": "Self-Declaration on Eligibility",
		"category": CAT_DECLARATION,
		"requirement": REQ_MANDATORY,
		"bidder_instruction": "Bidder must declare eligibility as required by the tender document.",
		"accepted_response_format": "declaration",
	},
	{
		"item_name": "Tender Security / Securing Declaration",
		"category": CAT_SECURITY,
		"requirement": REQ_CONDITIONAL,
		"condition_text": "Required where the Tender Data Sheet specifies tender security.",
		"condition_source": SOURCE_TDS,
		"bidder_instruction": (
			"Provide tender security or a securing declaration in the form stated in the TDS."
		),
		"accepted_response_format": "PDF attachment",
	},
)


def _v(row: dict[str, Any], key: str) -> str:
	return cstr(row.get(key) or "").strip()


def _is_diagnostic_phrase(text: str) -> bool:
	t = cstr(text or "").strip().lower()
	return bool(t) and t in _DIAGNOSTIC_EXACT


def _parse_blob(raw: Any) -> dict[str, Any]:
	if not raw:
		return {"submission_items": []}
	if isinstance(raw, str):
		try:
			raw = json.loads(raw)
		except (TypeError, ValueError):
			return {"submission_items": []}
	if isinstance(raw, list):
		return {"submission_items": [_clean_item(r) for r in raw if isinstance(r, dict)]}
	if not isinstance(raw, dict):
		return {"submission_items": []}
	rows = raw.get("submission_items") or raw.get("items") or raw.get("criteria") or []
	if not isinstance(rows, list):
		rows = []
	return {"submission_items": [_clean_item(r) for r in rows if isinstance(r, dict)]}


def _parse_items(raw: Any) -> list[dict[str, Any]]:
	return _parse_blob(raw)["submission_items"]


def _clean_item(row: dict[str, Any]) -> dict[str, Any]:
	cleaned: dict[str, Any] = {}
	for key, val in row.items():
		k = cstr(key).strip()
		if not k or k in BANNED_KEYS or k not in EDITABLE_KEYS:
			continue
		if isinstance(val, (dict, list)):
			continue
		cleaned[k] = cstr(val).strip() if val is not None else ""
	if not cleaned.get("item_name") and row.get("name"):
		cleaned["item_name"] = cstr(row.get("name")).strip()
	if not cleaned.get("source") and row.get("source_label"):
		label = cstr(row.get("source_label")).strip()
		if label in SOURCES:
			cleaned["source"] = label
	return cleaned


def _next_item_id(rows: list[dict[str, Any]]) -> str:
	max_n = 0
	for row in rows:
		mid = _v(row, "item_id")
		m = re.match(r"^FE-(\d+)$", mid, re.I)
		if m:
			max_n = max(max_n, int(m.group(1)))
	return f"FE-{max_n + 1:03d}"


def _row_unmet(row: dict[str, Any]) -> list[dict[str, str]]:
	unmet: list[dict[str, str]] = []
	rid = _v(row, "item_id") or "item"

	def add(code: str, message: str):
		unmet.append({"code": f"{rid}:{code}", "message": message})

	if not _v(row, "item_name"):
		add("item_name", MSG_NAME)
	category = _v(row, "category")
	if not category or category not in CATEGORIES:
		add("category", MSG_CATEGORY)
	source = _v(row, "source")
	if not source or source not in SOURCES:
		add("source", MSG_SOURCE)
	requirement = _v(row, "requirement")
	if not requirement or requirement not in REQUIREMENTS:
		add("requirement", MSG_REQUIREMENT)

	if requirement == REQ_NA:
		if not _v(row, "not_applicable_reason"):
			add("not_applicable_reason", MSG_NA_REASON)
		return unmet

	instruction = _v(row, "bidder_instruction")
	if not instruction:
		add("bidder_instruction", MSG_INSTRUCTION)
	elif _is_diagnostic_phrase(instruction):
		add("bidder_instruction", MSG_DIAGNOSTIC)

	if requirement == REQ_CONDITIONAL and not _v(row, "condition_text"):
		add("condition_text", MSG_CONDITION)

	return unmet


def _any_content(row: dict[str, Any]) -> bool:
	for key in EDITABLE_KEYS:
		if key == "item_id":
			continue
		if _v(row, key):
			return True
	return False


def _derive_setup_status(row: dict[str, Any], unmet: list[dict[str, str]]) -> str:
	if _v(row, "requirement") == REQ_NA and not unmet:
		return SETUP_NOT_APPLICABLE
	if not _any_content(row):
		return SETUP_DRAFT
	if not unmet:
		return SETUP_COMPLETE
	return SETUP_NEEDS_ATTENTION


def _action_for_setup(status: str) -> str:
	if status == SETUP_COMPLETE:
		return "Edit"
	if status == SETUP_NOT_APPLICABLE:
		return "Review"
	if status == SETUP_NEEDS_ATTENTION:
		return "Fix"
	return "Continue"


def enrich_item(row: dict[str, Any]) -> dict[str, Any]:
	unmet = _row_unmet(row)
	setup = _derive_setup_status(row, unmet)
	instruction = _v(row, "bidder_instruction")
	return {
		"item_id": _v(row, "item_id"),
		"item_name": _v(row, "item_name"),
		"category": _v(row, "category"),
		"category_label": _v(row, "category"),
		"source": _v(row, "source"),
		"source_label": _v(row, "source"),
		"requirement": _v(row, "requirement"),
		"requirement_label": _v(row, "requirement"),
		"bidder_instruction": instruction,
		"accepted_response_format": _v(row, "accepted_response_format"),
		"accepted_file_type": _v(row, "accepted_file_type"),
		"condition_text": _v(row, "condition_text"),
		"condition_source": _v(row, "condition_source"),
		"related_requirement_id": _v(row, "related_requirement_id"),
		"related_criterion_id": _v(row, "related_criterion_id"),
		"related_tds_key": _v(row, "related_tds_key"),
		"not_applicable_reason": _v(row, "not_applicable_reason"),
		"setup_status_label": setup,
		"status": setup,
		"status_label": setup if setup != SETUP_DRAFT else SETUP_NEEDS_ATTENTION,
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
		unmet = _row_unmet(row)
		blockers.extend(unmet)
		rid = _v(row, "item_id") or "FE"
		requirement = _v(row, "requirement")
		if requirement == REQ_MANDATORY and not _v(row, "bidder_instruction"):
			# Also covered by _row_unmet; keep explicit Continue messaging path.
			if not any(b.get("code", "").endswith(":bidder_instruction") for b in unmet):
				blockers.append({"code": f"{rid}:mandatory_instruction", "message": MSG_MANDATORY_INSTR})
		if requirement == REQ_CONDITIONAL and not _v(row, "condition_text"):
			if not any(b.get("code", "").endswith(":condition_text") for b in unmet):
				blockers.append({"code": f"{rid}:conditional", "message": MSG_CONDITIONAL_INSTR})

	warnings.append({"code": "eval_upstream", "message": MSG_EVAL_WARN})
	return blockers, warnings, len(blockers) == 0


def forms_and_evidence_has_progress(rows: list[dict[str, Any]]) -> bool:
	return any(_any_content(r) for r in rows)


def forms_and_evidence_exit_conditions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	conds: list[dict[str, Any]] = [
		{"key": "has_items", "label": "At least one submission item", "met": bool(rows)}
	]
	for row in rows:
		rid = _v(row, "item_id") or "FE"
		unmet = _row_unmet(row)
		conds.append(
			{
				"key": f"item_{rid}",
				"label": f"{rid} setup complete",
				"met": len(unmet) == 0 and _any_content(row),
			}
		)
	mandatory_ok = all(
		_v(r, "requirement") != REQ_MANDATORY or bool(_v(r, "bidder_instruction")) for r in rows
	)
	conditional_ok = all(
		_v(r, "requirement") != REQ_CONDITIONAL
		or (bool(_v(r, "condition_text")) and bool(_v(r, "bidder_instruction")))
		for r in rows
	)
	conds.append(
		{"key": "mandatory_instructions", "label": "Mandatory items have instructions", "met": mandatory_ok}
	)
	conds.append(
		{
			"key": "conditional_conditions",
			"label": "Conditional items have conditions",
			"met": conditional_ok,
		}
	)
	return conds


def forms_and_evidence_exit_conditions_for_doc(doc) -> list[dict[str, Any]]:
	blob = _parse_blob(getattr(doc, "forms_and_evidence", None))
	return forms_and_evidence_exit_conditions(blob["submission_items"])


def _summary(rows: list[dict[str, Any]], enriched: list[dict[str, Any]]) -> dict[str, Any]:
	return {
		"total_items": len(rows),
		"mandatory_items": sum(1 for r in rows if _v(r, "requirement") == REQ_MANDATORY),
		"conditional_items": sum(1 for r in rows if _v(r, "requirement") == REQ_CONDITIONAL),
		"needs_attention": sum(
			1 for r in enriched if r.get("setup_status_label") == SETUP_NEEDS_ATTENTION
		),
		"not_applicable": sum(1 for r in rows if _v(r, "requirement") == REQ_NA),
	}


def _guidance(summary: dict[str, Any]) -> dict[str, Any]:
	return {
		"title": "Forms & Evidence Guidance",
		"body": (
			"Use this screen to define what bidders must submit with their tender. "
			"Keep instructions clear, bidder-facing, and limited to forms, declarations, "
			"certificates, qualification evidence, and technical proof. Price forms are "
			"configured in Price Schedule. Evaluation scores are configured in Evaluation Setup."
		),
		"mandatory_items": summary.get("mandatory_items") or 0,
		"conditional_items": summary.get("conditional_items") or 0,
		"items_needing_attention": summary.get("needs_attention") or 0,
		"not_applicable_items": summary.get("not_applicable") or 0,
	}


def _persist_item(row: dict[str, Any]) -> dict[str, Any]:
	cleaned = _clean_item(row)
	category = _v(cleaned, "category")
	if category not in CATEGORIES:
		category = ""
	source = _v(cleaned, "source")
	if source not in SOURCES:
		source = SOURCE_USER if _any_content(cleaned) else ""
	requirement = _v(cleaned, "requirement")
	if requirement not in REQUIREMENTS:
		requirement = ""
	fmt = _v(cleaned, "accepted_response_format")
	if fmt and fmt not in RESPONSE_FORMATS:
		fmt = ""
	return {
		"item_id": _v(cleaned, "item_id"),
		"item_name": _v(cleaned, "item_name"),
		"category": category,
		"source": source,
		"requirement": requirement,
		"bidder_instruction": _v(cleaned, "bidder_instruction"),
		"accepted_response_format": fmt,
		"accepted_file_type": _v(cleaned, "accepted_file_type"),
		"condition_text": _v(cleaned, "condition_text"),
		"condition_source": _v(cleaned, "condition_source"),
		"related_requirement_id": _v(cleaned, "related_requirement_id"),
		"related_criterion_id": _v(cleaned, "related_criterion_id"),
		"related_tds_key": _v(cleaned, "related_tds_key"),
		"not_applicable_reason": _v(cleaned, "not_applicable_reason"),
	}


def _build_import_drafts(existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
	existing_names = {_v(r, "item_name").lower() for r in existing}
	out: list[dict[str, Any]] = []
	for template in STD_IMPORT_FORMS:
		name = cstr(template.get("item_name") or "").strip()
		if name.lower() in existing_names:
			continue
		draft = _persist_item(
			{
				**template,
				"source": SOURCE_STD,
			}
		)
		out.append(draft)
	return out


def _sync_cfg08_steps_state(
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
	state["CFG-08"] = {
		"status_label": label,
		"progress_pct": progress.get("progress_pct") or 0,
		"met_count": progress.get("met_count") or 0,
		"required_count": progress.get("required_count") or 0,
	}
	# Unlock CFG-09 when CFG-08 can continue.
	if can_continue:
		cfg09 = state.get("CFG-09") or {}
		if cstr(cfg09.get("status_label") or "") in ("", "Not available yet"):
			state["CFG-09"] = {**cfg09, "status_label": STEP_NOT_STARTED}
	doc.steps_state = json.dumps(state)


def get_configuration_forms_and_evidence(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	blob = _parse_blob(getattr(doc, "forms_and_evidence", None))
	raw_rows = blob["submission_items"]
	enriched = [enrich_item(row) for row in raw_rows]
	blockers, warnings, can_continue = validate_items(raw_rows)
	has_progress = forms_and_evidence_has_progress(raw_rows)
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")
	summary = _summary(raw_rows, enriched)
	import_candidates = _build_import_drafts(raw_rows)

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
		"submission_items": enriched,
		"items": enriched,
		"summary": summary,
		"guidance": _guidance(summary),
		"next_item_id": _next_item_id(raw_rows),
		"import_candidate_count": len(import_candidates),
		"context": context,
		"options": {
			"category": list(CATEGORIES),
			"source": list(SOURCES),
			"requirement": list(REQUIREMENTS),
			"accepted_response_format": list(RESPONSE_FORMATS),
			"tabs": [
				{"key": TAB_ALL, "label": "All Items"},
				{"key": TAB_STANDARD, "label": "Standard Forms"},
				{"key": TAB_DECLARATIONS, "label": "Declarations"},
				{"key": TAB_QUAL, "label": "Qualification Evidence"},
				{"key": TAB_TECH, "label": "Technical Evidence"},
				{"key": TAB_SECURITY, "label": "Tender Security"},
				{"key": TAB_CONDITIONAL, "label": "Conditional Items"},
			],
		},
		"column_contract": {
			"note": (
				"Status uses Complete / Needs attention / Not applicable only. "
				"Never show uploads, scores, or award outcomes."
			),
			"columns": [
				"Submission Item",
				"Category",
				"Source",
				"Requirement",
				"Bidder Instruction",
				"Status",
				"Actions",
			],
		},
	}


def save_configuration_forms_and_evidence(
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

	do_import = bool(payload.get("import") or payload.get("action") == "import")
	if isinstance(payload.get("submission_items"), (list, str)) or isinstance(
		payload.get("items"), (list, str)
	):
		incoming = _parse_items(payload.get("submission_items") or payload.get("items"))
	elif isinstance(payload, list):
		incoming = _parse_items(payload)
	else:
		incoming = _parse_items(payload.get("forms_and_evidence"))

	persist: list[dict[str, Any]] = []
	for row in incoming:
		item = _persist_item(row)
		if not item.get("item_id"):
			item["item_id"] = _next_item_id(persist)
		persist.append(item)

	if do_import:
		for draft in _build_import_drafts(persist):
			draft["item_id"] = _next_item_id(persist)
			persist.append(draft)

	blockers, warnings, can_continue = validate_items(persist)
	has_progress = forms_and_evidence_has_progress(persist)

	from kentender_procurement.tender_configurations.services.step_progress import (
		evaluate_conditions,
	)

	progress = evaluate_conditions(forms_and_evidence_exit_conditions(persist))
	blob = {"submission_items": persist}

	doc.forms_and_evidence = json.dumps(blob)
	doc.blocker_count = len(blockers)
	doc.warning_count = len(warnings)
	_sync_cfg08_steps_state(
		doc,
		can_continue=can_continue,
		has_progress=has_progress,
		progress=progress,
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return get_configuration_forms_and_evidence(doc.name)
