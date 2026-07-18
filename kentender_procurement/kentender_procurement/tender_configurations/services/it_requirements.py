# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-03 IT Requirements GET/POST (C2-CFG3 §19 + column-clarity amendment).

Table instruction/method columns show **content** only.
Setup completeness diagnostics belong in Setup Status / issue summary / Action —
never words like "missing", "defined", or "valid" inside instruction columns.
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
	STEP_NEEDS_ATTENTION,
	STEP_NOT_STARTED,
)

CATEGORIES = (
	"Business Objective",
	"Functional Requirement",
	"Technical Requirement",
	"Security & Compliance",
	"Integration",
	"Implementation Support",
	"Support & Warranty",
	"Deliverable / Acceptance",
	"Background / Informational",
)
TREATMENTS = ("Mandatory", "Evaluation-linked", "Informational")
RESPONSE_FORMATS = (
	"Yes/No confirmation",
	"Compliance statement",
	"Numeric value",
	"Narrative response",
	"Completed table",
	"Not required",
)
EVIDENCE_REQUIREMENTS = (
	"Evidence required",
	"Evidence optional",
	"No evidence required",
)

# Suggested methods (free text also allowed); never diagnostic phrases.
DELIVERY_METHOD_SUGGESTIONS = (
	"Inspection at delivery",
	"Commissioning test report",
	"Signed support SLA",
	"Training attendance and completion report",
	"Migration reconciliation report",
	"Hosting location declaration / audit evidence",
	"Not required",
)

SETUP_COMPLETE = "Complete"
SETUP_NEEDS_ATTENTION = "Needs attention"
SETUP_DRAFT = "Draft"
SETUP_NOT_APPLICABLE = "Not applicable"

TREATMENT_INFORMATIONAL = "Informational"
RESPONSE_NOT_REQUIRED = "Not required"
EVIDENCE_REQUIRED = "Evidence required"
EVIDENCE_OPTIONAL = "Evidence optional"
EVIDENCE_NONE = "No evidence required"
METHOD_NOT_REQUIRED = "Not required"

# Banned diagnostic fragments inside instruction/method columns
_DIAGNOSTIC_RE = re.compile(
	r"\b(missing|defined|valid|acceptance defined|delivery check missing)\b",
	re.I,
)

EDITABLE_KEYS = frozenset(
	{
		"requirement_id",
		"title",
		"description",
		"category_label",
		"treatment_label",
		"bidder_response_format",
		"bidder_response_instruction",
		"evidence_requirement",
		"evidence_instruction",
		"delivery_confirmation_method",
	}
)
BANNED_KEYS = frozenset(
	{
		"std_version_hash",
		"binding_id",
		"clause_hash",
		"schema_version",
		"rule_id",
		"score",
		"marks",
		"pass_mark",
	}
)

MSG_EMPTY = "Add at least one IT requirement before continuing."
MSG_TITLE = "Add a requirement title before continuing."
MSG_CATEGORY = "Confirm the requirement category before continuing."
MSG_TREATMENT = "Confirm the requirement treatment before continuing."
MSG_RESPONSE_FORMAT = "Confirm the bidder response format before continuing."
MSG_RESPONSE_INSTRUCTION = "Add a bidder response instruction before continuing."
MSG_EVIDENCE = "Confirm the evidence requirement before continuing."
MSG_EVIDENCE_INSTRUCTION = "Add an evidence instruction before continuing."
MSG_DELIVERY_METHOD = "Add a delivery confirmation method before continuing."
MSG_DIAGNOSTIC_IN_METHOD = (
	"Use a delivery confirmation method (how delivery will later be checked), "
	"not a setup-status phrase."
)


def _parse_requirements(raw: Any) -> list[dict[str, Any]]:
	if not raw:
		return []
	if isinstance(raw, str):
		try:
			raw = json.loads(raw)
		except (TypeError, ValueError):
			return []
	if not isinstance(raw, list):
		return []
	out: list[dict[str, Any]] = []
	for row in raw:
		if not isinstance(row, dict):
			continue
		cleaned: dict[str, Any] = {}
		for key, val in row.items():
			k = cstr(key).strip()
			if not k or k in BANNED_KEYS:
				continue
			# Legacy acceptance_* → delivery_confirmation_method (content only)
			if k in ("acceptance_expectation", "acceptance_description", "acceptance_label"):
				continue
			if k not in EDITABLE_KEYS and k not in (
				"setup_status_label",
				"status_label",
				"action_label",
				"issue_summary",
			):
				continue
			if isinstance(val, (dict, list)):
				continue
			cleaned[k] = cstr(val).strip() if val is not None else ""
		# Migrate legacy description into method when new field empty
		legacy_desc = cstr(row.get("acceptance_description") or "").strip()
		legacy_exp = cstr(row.get("acceptance_expectation") or "").strip()
		if not cleaned.get("delivery_confirmation_method"):
			if legacy_desc and not _DIAGNOSTIC_RE.search(legacy_desc):
				cleaned["delivery_confirmation_method"] = legacy_desc
			elif legacy_exp == "Not applicable":
				cleaned["delivery_confirmation_method"] = METHOD_NOT_REQUIRED
		out.append(cleaned)
	return out


def _v(row: dict[str, Any], key: str) -> str:
	return cstr(row.get(key) or "").strip()


def _next_requirement_id(rows: list[dict[str, Any]]) -> str:
	max_n = 0
	for row in rows:
		rid = _v(row, "requirement_id")
		m = re.match(r"^REQ-(\d+)$", rid, re.I)
		if m:
			max_n = max(max_n, int(m.group(1)))
	return f"REQ-{max_n + 1:03d}"


def _is_diagnostic_phrase(text: str) -> bool:
	t = cstr(text or "").strip().lower()
	if not t:
		return False
	banned_exact = {
		"acceptance defined",
		"missing acceptance",
		"delivery check missing",
		"delivery check defined",
		"missing evidence instruction",
		"missing",
		"defined",
		"valid",
	}
	return t in banned_exact


def _row_unmet(row: dict[str, Any]) -> list[dict[str, str]]:
	"""Return unmet required conditions for one requirement."""
	unmet: list[dict[str, str]] = []
	title = _v(row, "title")
	treatment = _v(row, "treatment_label")
	category = _v(row, "category_label")
	resp_fmt = _v(row, "bidder_response_format")
	resp_instr = _v(row, "bidder_response_instruction")
	ev_req = _v(row, "evidence_requirement")
	ev_instr = _v(row, "evidence_instruction")
	method = _v(row, "delivery_confirmation_method")
	rid = _v(row, "requirement_id") or "requirement"

	def add(code: str, message: str):
		unmet.append({"code": f"{rid}:{code}", "message": message})

	if not title:
		add("title", MSG_TITLE)
	if not category or category not in CATEGORIES:
		add("category", MSG_CATEGORY)
	if not treatment or treatment not in TREATMENTS:
		add("treatment", MSG_TREATMENT)

	informational = treatment == TREATMENT_INFORMATIONAL
	if not informational:
		if not resp_fmt or resp_fmt not in RESPONSE_FORMATS:
			add("bidder_response_format", MSG_RESPONSE_FORMAT)
		elif resp_fmt != RESPONSE_NOT_REQUIRED and not resp_instr:
			add("bidder_response_instruction", MSG_RESPONSE_INSTRUCTION)
		if not method:
			add("delivery_confirmation_method", MSG_DELIVERY_METHOD)
		elif _is_diagnostic_phrase(method):
			add("delivery_confirmation_method", MSG_DIAGNOSTIC_IN_METHOD)
	else:
		if resp_fmt and resp_fmt not in RESPONSE_FORMATS:
			add("bidder_response_format", MSG_RESPONSE_FORMAT)
		if resp_fmt and resp_fmt != RESPONSE_NOT_REQUIRED and not resp_instr:
			add("bidder_response_instruction", MSG_RESPONSE_INSTRUCTION)
		if method and _is_diagnostic_phrase(method):
			add("delivery_confirmation_method", MSG_DIAGNOSTIC_IN_METHOD)

	if not ev_req or ev_req not in EVIDENCE_REQUIREMENTS:
		add("evidence_requirement", MSG_EVIDENCE)
	elif ev_req in (EVIDENCE_REQUIRED, EVIDENCE_OPTIONAL) and not ev_instr:
		add("evidence_instruction", MSG_EVIDENCE_INSTRUCTION)

	return unmet


def _any_content(row: dict[str, Any]) -> bool:
	for key in (
		"title",
		"description",
		"category_label",
		"treatment_label",
		"bidder_response_format",
		"bidder_response_instruction",
		"evidence_requirement",
		"evidence_instruction",
		"delivery_confirmation_method",
	):
		if _v(row, key):
			return True
	return False


def _derive_setup_status(row: dict[str, Any], unmet: list[dict[str, str]]) -> str:
	"""Setup Status = whether the requirement *definition* is complete enough."""
	if not _any_content(row):
		return SETUP_DRAFT
	if not unmet:
		return SETUP_COMPLETE
	if _v(row, "title"):
		return SETUP_NEEDS_ATTENTION
	return SETUP_DRAFT


def _action_for_setup(status: str, treatment: str) -> str:
	if status == SETUP_COMPLETE and treatment == TREATMENT_INFORMATIONAL:
		return "Review"
	return {
		SETUP_COMPLETE: "Edit",
		SETUP_NEEDS_ATTENTION: "Fix",
		SETUP_DRAFT: "Continue",
		SETUP_NOT_APPLICABLE: "Review",
	}.get(status, "Edit")


def _table_content_cells(row: dict[str, Any]) -> dict[str, str]:
	"""Instruction/method columns: content only — never diagnostic labels."""
	resp_fmt = _v(row, "bidder_response_format")
	resp_instr = _v(row, "bidder_response_instruction")
	if resp_fmt == RESPONSE_NOT_REQUIRED or (
		not resp_instr and resp_fmt == RESPONSE_NOT_REQUIRED
	):
		bidder_cell = RESPONSE_NOT_REQUIRED
	elif resp_instr:
		bidder_cell = resp_instr
	else:
		bidder_cell = "—"

	ev_req = _v(row, "evidence_requirement")
	ev_instr = _v(row, "evidence_instruction")
	if ev_req == EVIDENCE_NONE:
		evidence_cell = "Not required"
	elif ev_instr:
		evidence_cell = ev_instr
	else:
		evidence_cell = "—"

	method = _v(row, "delivery_confirmation_method")
	if method and not _is_diagnostic_phrase(method):
		delivery_cell = method
	else:
		delivery_cell = "—"

	return {
		"bidder_response_instruction_display": bidder_cell,
		"evidence_instruction_display": evidence_cell,
		"delivery_confirmation_method_display": delivery_cell,
	}


def enrich_requirement(row: dict[str, Any]) -> dict[str, Any]:
	unmet = _row_unmet(row)
	setup = _derive_setup_status(row, unmet)
	cells = _table_content_cells(row)
	action = _action_for_setup(setup, _v(row, "treatment_label"))
	issue = unmet[0]["message"] if unmet else ""
	out = {
		"requirement_id": _v(row, "requirement_id"),
		"title": _v(row, "title"),
		"description": _v(row, "description"),
		"category_label": _v(row, "category_label"),
		"treatment_label": _v(row, "treatment_label"),
		"bidder_response_format": _v(row, "bidder_response_format"),
		"bidder_response_instruction": _v(row, "bidder_response_instruction"),
		"evidence_requirement": _v(row, "evidence_requirement"),
		"evidence_instruction": _v(row, "evidence_instruction"),
		"delivery_confirmation_method": _v(row, "delivery_confirmation_method"),
		"setup_status_label": setup,
		# Alias for progress/step sync (Complete | Needs attention | Draft)
		"status_label": setup if setup != SETUP_NOT_APPLICABLE else SETUP_COMPLETE,
		"action_label": action,
		"issue_summary": issue,
		**cells,
	}
	return out


def validate_requirements(
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
		if (
			_v(row, "treatment_label") != TREATMENT_INFORMATIONAL
			and _v(row, "title")
			and not _v(row, "description")
		):
			warnings.append(
				{
					"code": f"{_v(row, 'requirement_id')}:description",
					"message": "Review the requirement description for clarity.",
				}
			)

	can_continue = len(blockers) == 0
	return blockers, warnings, can_continue


def requirements_has_progress(rows: list[dict[str, Any]]) -> bool:
	return any(_any_content(r) for r in rows)


def requirements_exit_conditions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	conds: list[dict[str, Any]] = [
		{
			"key": "has_requirements",
			"label": "At least one IT requirement",
			"met": bool(rows),
		}
	]
	for row in rows:
		rid = _v(row, "requirement_id") or "REQ"
		unmet = _row_unmet(row)
		conds.append(
			{
				"key": f"req_{rid}",
				"label": f"{rid} setup complete",
				"met": len(unmet) == 0 and _any_content(row),
			}
		)
	return conds


def requirements_exit_conditions_for_doc(doc) -> list[dict[str, Any]]:
	rows = _parse_requirements(getattr(doc, "it_requirements", None))
	return requirements_exit_conditions(rows)


def _references_for_row(row: dict[str, Any]) -> dict[str, str]:
	treatment = _v(row, "treatment_label")
	ev = _v(row, "evidence_requirement")
	eval_ref = (
		"Linked in Evaluation Setup"
		if treatment == "Evaluation-linked"
		else "Not linked to evaluation"
	)
	forms_ref = (
		"Evidence item will be configured in Forms & Evidence"
		if ev in (EVIDENCE_REQUIRED, EVIDENCE_OPTIONAL)
		else "No evidence item required"
	)
	contract_ref = (
		"May carry into contract values"
		if treatment == "Mandatory"
		else "No contract carry-forward expected"
	)
	return {
		"evaluation_setup": eval_ref,
		"forms_and_evidence": forms_ref,
		"contract_values": contract_ref,
	}


def _sync_cfg03_steps_state(doc, *, can_continue: bool, has_progress: bool, progress: dict) -> None:
	state = _parse_steps_state(getattr(doc, "steps_state", None))
	cfg = dict(state.get("CFG-03") or {})
	if can_continue:
		cfg["status_label"] = STEP_COMPLETE
	elif has_progress:
		cfg["status_label"] = STEP_IN_PROGRESS
	else:
		cfg["status_label"] = STEP_NOT_STARTED
	cfg["progress_pct"] = progress.get("progress_pct", 0)
	cfg["progress_met_count"] = progress.get("met_count", 0)
	cfg["progress_required_count"] = progress.get("required_count", 0)
	state["CFG-03"] = cfg
	doc.steps_state = json.dumps(state)


def get_configuration_requirements(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	raw_rows = _parse_requirements(getattr(doc, "it_requirements", None))
	enriched = [enrich_requirement(r) for r in raw_rows]
	blockers, warnings, can_continue = validate_requirements(raw_rows)
	has_progress = requirements_has_progress(raw_rows)
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")

	requirements_out = []
	for row in enriched:
		item = dict(row)
		item["references"] = _references_for_row(row)
		requirements_out.append(item)

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
		"requirements": requirements_out,
		"context": context,
		"options": {
			"category_label": list(CATEGORIES),
			"treatment_label": list(TREATMENTS),
			"bidder_response_format": list(RESPONSE_FORMATS),
			"evidence_requirement": list(EVIDENCE_REQUIREMENTS),
			"delivery_confirmation_method": list(DELIVERY_METHOD_SUGGESTIONS),
		},
		"column_contract": {
			"note": (
				"Instruction/method columns show content only. "
				"Never put missing/defined/valid in those columns — use Setup Status."
			),
			"columns": [
				"ID",
				"Requirement",
				"Category",
				"Treatment",
				"Bidder Response Instruction",
				"Evidence Instruction",
				"Delivery Confirmation Method",
				"Setup Status",
				"Action",
			],
		},
		"guidance": {
			"title": "IT Requirements Guidance",
			"body": (
				"Focus on what bidders must supply, deliver, integrate, support, or prove. "
				"Define response instructions, evidence instructions, and how delivery will "
				"later be confirmed. Evaluation scores, price lines, and contract values "
				"are configured in later steps."
			),
			"what_this_affects": (
				"Bidder responses, evidence expectations, evaluation setup, forms, "
				"contract values, and tender preview."
			),
			"used_later_by": (
				"Implementation Schedule, System Inventory & Bidder Background, Price Schedule, "
				"Evaluation Setup, Forms & Evidence, and Contract Values."
			),
			"not_configured_here": (
				"Scores, prices, actual bidder submissions, contract clauses, "
				"delivery execution, and publication actions."
			),
		},
	}


def save_configuration_requirements(
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
	if isinstance(payload.get("requirements"), (list, str)):
		incoming = _parse_requirements(payload.get("requirements"))
	else:
		incoming = _parse_requirements(payload if isinstance(payload, list) else [])

	persist: list[dict[str, str]] = []
	for row in incoming:
		item = {k: _v(row, k) for k in EDITABLE_KEYS}
		if not item.get("requirement_id"):
			item["requirement_id"] = _next_requirement_id(persist)
		persist.append(item)

	blockers, warnings, can_continue = validate_requirements(persist)
	has_progress = requirements_has_progress(persist)

	from kentender_procurement.tender_configurations.services.step_progress import (
		evaluate_conditions,
	)

	progress = evaluate_conditions(requirements_exit_conditions(persist))

	doc.it_requirements = json.dumps(persist)
	doc.blocker_count = len(blockers)
	doc.warning_count = len(warnings)
	_sync_cfg03_steps_state(
		doc,
		can_continue=can_continue,
		has_progress=has_progress,
		progress=progress,
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return get_configuration_requirements(doc.name)
