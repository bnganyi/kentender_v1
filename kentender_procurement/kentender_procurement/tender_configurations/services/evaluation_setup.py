# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-07 Evaluation Setup GET/POST (C2-CFG7).

Defines how bids will be evaluated (framework only). Never expose bidder scores,
rankings, award recommendations, or committee decisions.
"""

from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe.utils import cstr, flt

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

STAGES = (
	"Preliminary",
	"Qualification",
	"Technical",
	"Financial",
	"Preference",
)
STAGE_PRELIM = "Preliminary"
STAGE_QUAL = "Qualification"
STAGE_TECH = "Technical"
STAGE_FIN = "Financial"
STAGE_PREF = "Preference"

BASES = (
	"Pass/Fail",
	"Scored",
	"Lowest evaluated price",
	"Preference rule",
	"Post-qualification",
)
BASIS_PASS = "Pass/Fail"
BASIS_SCORED = "Scored"
BASIS_LOWEST = "Lowest evaluated price"
BASIS_PREF = "Preference rule"
BASIS_POST = "Post-qualification"

SOURCE_TYPES = (
	"TDS",
	"IT Requirement",
	"Implementation Schedule",
	"Price Schedule",
	"Forms & Evidence",
	"User added",
	"Standard IT STD",
)
SOURCE_TDS = "TDS"
SOURCE_REQ = "IT Requirement"
SOURCE_SCHED = "Implementation Schedule"
SOURCE_PRICE = "Price Schedule"
SOURCE_FORMS = "Forms & Evidence"
SOURCE_USER = "User added"
SOURCE_STD = "Standard IT STD"

EVIDENCE_OPTS = (
	"Required",
	"Not required",
	"To be configured in Forms & Evidence",
)
EVIDENCE_REQUIRED = "Required"
EVIDENCE_NOT = "Not required"
EVIDENCE_FORMS = "To be configured in Forms & Evidence"

SETUP_COMPLETE = "Complete"
SETUP_NEEDS_ATTENTION = "Needs attention"
SETUP_DRAFT = "Draft"
SETUP_IN_PROGRESS = "In progress"

EDITABLE_KEYS = frozenset(
	{
		"criterion_id",
		"criterion_name",
		"stage",
		"evaluation_basis",
		"source_type",
		"bidder_facing_wording",
		"pass_fail_rule",
		"marks",
		# technical_pass_mark is tender-level (blob), not per criterion — intentionally omitted
		"financial_evaluation_rule",
		"preference_rule",
		"bidder_evidence",
		"evidence_instruction",
		"evaluator_guidance",
		"related_requirement_id",
		"related_price_item_id",
		"related_milestone_id",
		"related_tds_key",
	}
)
BANNED_KEYS = frozenset(
	{
		"std_version_hash",
		"binding_id",
		"clause_hash",
		"schema_version",
		"rule_id",
		"bidder_score",
		"bidder_rank",
		"award_recommendation",
		"committee_decision",
		"bid_data",
	}
)

MSG_EMPTY = "Add at least one evaluation criterion before continuing."
MSG_NAME = "Add a criterion name."
MSG_STAGE = "Select the evaluation stage."
MSG_BASIS = "Select how this criterion will be evaluated."
MSG_SOURCE = "Select the source or mark the criterion as user added."
MSG_WORDING = "Add the wording bidders will see."
MSG_PASS_RULE = "Add the pass/fail rule."
MSG_MARKS = "Enter the marks for this scored criterion."
MSG_TECH_PASS = "Enter the minimum technical score."
MSG_FIN_RULE = "Define how evaluated prices will be compared."
MSG_PREF_RULE = "Add the preference or reservation rule."
MSG_EVIDENCE = "Select whether bidder evidence is required."
MSG_EVIDENCE_INSTR = "Add the evidence instruction or link it to Forms & Evidence."
MSG_TECH_TOTAL = (
	"Complete the remaining technical scored criteria so allocated marks equal {total}."
)
MSG_USER = "Confirm why this criterion is needed."
MSG_DIAGNOSTIC = "Use a bidder-facing value, not a setup-status phrase."


def _fmt_marks(value: float | int | str) -> str:
	n = flt(value)
	if abs(n - int(n)) < 0.001:
		return str(int(n))
	return cstr(n)


def tech_total_blocker_message(*, configured: float, total: float) -> str:
	"""Blocker when allocated scored-technical marks do not equal the scoring total."""
	return MSG_TECH_TOTAL.format(total=_fmt_marks(total))


def _lift_pass_mark_from_rows(rows: list[dict[str, Any]]) -> str:
	"""Legacy: older saves stored pass mark on criteria; lift once to tender-level."""
	for row in rows:
		if not isinstance(row, dict):
			continue
		pm = cstr(row.get("technical_pass_mark") or "").strip()
		if pm:
			return pm
	return ""

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
}

TAB_ALL = "all_criteria"
TAB_PRELIM = "preliminary_checks"
TAB_QUAL = "qualification"
TAB_TECH = "technical_evaluation"
TAB_FIN = "financial_evaluation"
TAB_PREF = "preferences_reservations"
TAB_NEEDS = "needs_attention"

TECHNICAL_MARKS_TOTAL_DEFAULT = 100


def _v(row: dict[str, Any], key: str) -> str:
	return cstr(row.get(key) or "").strip()


def _is_diagnostic_phrase(text: str) -> bool:
	t = cstr(text or "").strip().lower()
	return bool(t) and t in _DIAGNOSTIC_EXACT


def _parse_blob(raw: Any) -> dict[str, Any]:
	if not raw:
		return {
			"criteria": [],
			"technical_marks_total": TECHNICAL_MARKS_TOTAL_DEFAULT,
			"technical_pass_mark": "",
		}
	if isinstance(raw, str):
		try:
			raw = json.loads(raw)
		except (TypeError, ValueError):
			return {
				"criteria": [],
				"technical_marks_total": TECHNICAL_MARKS_TOTAL_DEFAULT,
				"technical_pass_mark": "",
			}
	if isinstance(raw, list):
		return {
			"criteria": [_clean_criterion(r) for r in raw if isinstance(r, dict)],
			"technical_marks_total": TECHNICAL_MARKS_TOTAL_DEFAULT,
			"technical_pass_mark": "",
		}
	if not isinstance(raw, dict):
		return {
			"criteria": [],
			"technical_marks_total": TECHNICAL_MARKS_TOTAL_DEFAULT,
			"technical_pass_mark": "",
		}
	rows = raw.get("criteria") or raw.get("items") or []
	if not isinstance(rows, list):
		rows = []
	total = flt(raw.get("technical_marks_total") or TECHNICAL_MARKS_TOTAL_DEFAULT)
	if total <= 0:
		total = TECHNICAL_MARKS_TOTAL_DEFAULT
	cleaned_rows = [_clean_criterion(r) for r in rows if isinstance(r, dict)]
	# Prefer blob-level minimum; fall back to legacy per-row values for migration.
	pass_mark = cstr(raw.get("technical_pass_mark") or raw.get("minimum_technical_score") or "").strip()
	if not pass_mark:
		pass_mark = _lift_pass_mark_from_rows(rows if isinstance(rows, list) else [])
	return {
		"criteria": cleaned_rows,
		"technical_marks_total": total,
		"technical_pass_mark": pass_mark,
	}


def _parse_criteria(raw: Any) -> list[dict[str, Any]]:
	return _parse_blob(raw)["criteria"]


def _clean_criterion(row: dict[str, Any]) -> dict[str, Any]:
	cleaned: dict[str, Any] = {}
	for key, val in row.items():
		k = cstr(key).strip()
		if not k or k in BANNED_KEYS or k not in EDITABLE_KEYS:
			continue
		if isinstance(val, (dict, list)):
			continue
		cleaned[k] = cstr(val).strip() if val is not None else ""
	if not cleaned.get("criterion_name") and row.get("name"):
		cleaned["criterion_name"] = cstr(row.get("name")).strip()
	if not cleaned.get("stage") and row.get("stage_label"):
		cleaned["stage"] = cstr(row.get("stage_label")).strip()
	if not cleaned.get("evaluation_basis") and row.get("evaluation_basis_label"):
		cleaned["evaluation_basis"] = cstr(row.get("evaluation_basis_label")).strip()
	if not cleaned.get("source_type") and row.get("source_label"):
		label = cstr(row.get("source_label")).strip()
		if label in SOURCE_TYPES:
			cleaned["source_type"] = label
	return cleaned


def _next_criterion_id(rows: list[dict[str, Any]]) -> str:
	max_n = 0
	for row in rows:
		mid = _v(row, "criterion_id")
		m = re.match(r"^EVAL-(\d+)$", mid, re.I)
		if m:
			max_n = max(max_n, int(m.group(1)))
	return f"EVAL-{max_n + 1:03d}"


def _row_unmet(row: dict[str, Any]) -> list[dict[str, str]]:
	unmet: list[dict[str, str]] = []
	rid = _v(row, "criterion_id") or "criterion"

	def add(code: str, message: str):
		unmet.append({"code": f"{rid}:{code}", "message": message})

	if not _v(row, "criterion_name"):
		add("criterion_name", MSG_NAME)
	stage = _v(row, "stage")
	if not stage or stage not in STAGES:
		add("stage", MSG_STAGE)
	basis = _v(row, "evaluation_basis")
	if not basis or basis not in BASES:
		add("basis", MSG_BASIS)
	source = _v(row, "source_type")
	if not source or source not in SOURCE_TYPES:
		add("source", MSG_SOURCE)
	wording = _v(row, "bidder_facing_wording")
	if not wording:
		add("wording", MSG_WORDING)
	elif _is_diagnostic_phrase(wording):
		add("wording", MSG_DIAGNOSTIC)

	if basis == BASIS_PASS and not _v(row, "pass_fail_rule"):
		add("pass_fail_rule", MSG_PASS_RULE)
	if basis == BASIS_SCORED and not _v(row, "marks"):
		add("marks", MSG_MARKS)
	if basis == BASIS_LOWEST and not _v(row, "financial_evaluation_rule"):
		add("financial_rule", MSG_FIN_RULE)
	if basis == BASIS_PREF and not _v(row, "preference_rule"):
		add("preference_rule", MSG_PREF_RULE)

	evidence = _v(row, "bidder_evidence")
	if not evidence or evidence not in EVIDENCE_OPTS:
		add("evidence", MSG_EVIDENCE)
	elif evidence == EVIDENCE_REQUIRED and not _v(row, "evidence_instruction"):
		add("evidence_instruction", MSG_EVIDENCE_INSTR)

	return unmet


def _any_content(row: dict[str, Any]) -> bool:
	for key in EDITABLE_KEYS:
		if key in ("criterion_id", "technical_marks_total"):
			continue
		if _v(row, key):
			return True
	return False


def _derive_setup_status(row: dict[str, Any], unmet: list[dict[str, str]]) -> str:
	if not _any_content(row):
		return SETUP_DRAFT
	if not unmet:
		return SETUP_COMPLETE
	if _v(row, "criterion_name"):
		return SETUP_NEEDS_ATTENTION
	return SETUP_IN_PROGRESS


def _action_for_setup(status: str) -> str:
	if status == SETUP_COMPLETE:
		return "Edit"
	if status == SETUP_NEEDS_ATTENTION:
		return "Fix"
	return "Continue"


def _marks_or_rule_display(row: dict[str, Any]) -> str:
	basis = _v(row, "evaluation_basis")
	if basis == BASIS_SCORED:
		marks = _v(row, "marks")
		return f"{marks} marks" if marks else "—"
	if basis == BASIS_PASS:
		return _v(row, "pass_fail_rule") or "—"
	if basis == BASIS_LOWEST:
		return _v(row, "financial_evaluation_rule") or "—"
	if basis == BASIS_PREF:
		return _v(row, "preference_rule") or "—"
	if basis == BASIS_POST:
		return _v(row, "pass_fail_rule") or "Post-qualification"
	return "—"


def enrich_criterion(row: dict[str, Any]) -> dict[str, Any]:
	unmet = _row_unmet(row)
	setup = _derive_setup_status(row, unmet)
	wording = _v(row, "bidder_facing_wording")
	disclosure = "Complete" if wording and not _is_diagnostic_phrase(wording) else "Incomplete"
	return {
		"criterion_id": _v(row, "criterion_id"),
		"criterion_name": _v(row, "criterion_name"),
		"stage": _v(row, "stage"),
		"stage_label": _v(row, "stage"),
		"evaluation_basis": _v(row, "evaluation_basis"),
		"evaluation_basis_label": _v(row, "evaluation_basis"),
		"source_type": _v(row, "source_type"),
		"source_label": _v(row, "source_type"),
		"bidder_facing_wording": wording,
		"pass_fail_rule": _v(row, "pass_fail_rule"),
		"marks": _v(row, "marks"),
		"financial_evaluation_rule": _v(row, "financial_evaluation_rule"),
		"preference_rule": _v(row, "preference_rule"),
		"bidder_evidence": _v(row, "bidder_evidence"),
		"bidder_evidence_label": _v(row, "bidder_evidence") or "—",
		"evidence_instruction": _v(row, "evidence_instruction"),
		"evaluator_guidance": _v(row, "evaluator_guidance"),
		"disclosure_check": disclosure,
		"related_requirement_id": _v(row, "related_requirement_id"),
		"related_price_item_id": _v(row, "related_price_item_id"),
		"related_milestone_id": _v(row, "related_milestone_id"),
		"related_tds_key": _v(row, "related_tds_key"),
		"marks_or_rule_display": _marks_or_rule_display(row),
		"setup_status_label": setup,
		"status": setup,
		"status_label": setup if setup != SETUP_DRAFT else SETUP_NEEDS_ATTENTION,
		"action_label": _action_for_setup(setup),
		"route_or_drawer_action": "edit",
		"issue_summary": unmet[0]["message"] if unmet else "",
	}


def _scored_technical_marks(rows: list[dict[str, Any]]) -> float:
	total = 0.0
	for row in rows:
		if _v(row, "stage") == STAGE_TECH and _v(row, "evaluation_basis") == BASIS_SCORED:
			total += flt(_v(row, "marks"))
	return total


def _uses_scored_technical(rows: list[dict[str, Any]]) -> bool:
	return any(
		_v(r, "stage") == STAGE_TECH and _v(r, "evaluation_basis") == BASIS_SCORED for r in rows
	)


def _scoring_summary(
	rows: list[dict[str, Any]],
	*,
	technical_marks_total: float,
	technical_pass_mark: str = "",
) -> dict[str, Any]:
	show = _uses_scored_technical(rows)
	allocated = _scored_technical_marks(rows)
	min_score = cstr(technical_pass_mark or "").strip()
	remaining = max(0.0, flt(technical_marks_total) - flt(allocated))
	status = SETUP_COMPLETE
	if show:
		if not min_score:
			status = SETUP_NEEDS_ATTENTION
		elif allocated + 0.001 < technical_marks_total:
			status = SETUP_NEEDS_ATTENTION
	allocation_hint = (
		tech_total_blocker_message(configured=allocated, total=technical_marks_total)
		if show and remaining > 0.001
		else ""
	)
	return {
		"show_scoring_summary": show,
		# Canonical labels (UI contract)
		"technical_scoring_total": technical_marks_total,
		"minimum_technical_score": min_score or "",
		"allocated_technical_marks": allocated,
		"setup_status": status if show else "",
		# Compat aliases used by earlier CFG-07 clients/tests
		"technical_marks_total": technical_marks_total,
		"technical_pass_mark": min_score or "",
		"configured_scored_marks": allocated,
		"marks_remaining": remaining,
		"status_label": status if show else "",
		"allocation_hint": allocation_hint,
		"pass_fail_message": (
			""
			if show
			else "Technical evaluation is configured as pass/fail."
			if any(_v(r, "stage") == STAGE_TECH for r in rows)
			else ""
		),
	}


def validate_criteria(
	rows: list[dict[str, Any]],
	*,
	technical_marks_total: float = TECHNICAL_MARKS_TOTAL_DEFAULT,
	technical_pass_mark: str = "",
) -> tuple[list[dict[str, str]], list[dict[str, str]], bool]:
	blockers: list[dict[str, str]] = []
	warnings: list[dict[str, str]] = []
	if not rows:
		blockers.append({"code": "empty", "message": MSG_EMPTY})
		return blockers, warnings, False

	min_score = cstr(technical_pass_mark or "").strip()
	for row in rows:
		blockers.extend(_row_unmet(row))
		rid = _v(row, "criterion_id") or "EVAL"
		if _v(row, "source_type") == SOURCE_USER:
			warnings.append({"code": f"{rid}:user_source", "message": MSG_USER})

	if _uses_scored_technical(rows):
		if not min_score:
			blockers.append({"code": "tech_pass_mark", "message": MSG_TECH_PASS})
		configured = _scored_technical_marks(rows)
		if configured + 0.001 < technical_marks_total:
			blockers.append(
				{
					"code": "tech_total",
					"message": tech_total_blocker_message(
						configured=configured, total=technical_marks_total
					),
				}
			)

	has_financial = any(_v(r, "stage") == STAGE_FIN for r in rows)
	if not has_financial:
		blockers.append({"code": "financial_missing", "message": MSG_FIN_RULE})

	return blockers, warnings, len(blockers) == 0


def evaluation_setup_has_progress(rows: list[dict[str, Any]]) -> bool:
	return any(_any_content(r) for r in rows)


def evaluation_setup_exit_conditions(
	rows: list[dict[str, Any]],
	*,
	technical_marks_total: float = TECHNICAL_MARKS_TOTAL_DEFAULT,
	technical_pass_mark: str = "",
) -> list[dict[str, Any]]:
	conds: list[dict[str, Any]] = [
		{"key": "has_criteria", "label": "At least one evaluation criterion", "met": bool(rows)}
	]
	min_score = cstr(technical_pass_mark or "").strip()
	for row in rows:
		rid = _v(row, "criterion_id") or "EVAL"
		unmet = _row_unmet(row)
		conds.append(
			{
				"key": f"criterion_{rid}",
				"label": f"{rid} setup complete",
				"met": len(unmet) == 0 and _any_content(row),
			}
		)
	if _uses_scored_technical(rows):
		conds.append(
			{
				"key": "tech_pass_mark",
				"label": "Minimum technical score set",
				"met": bool(min_score),
			}
		)
		conds.append(
			{
				"key": "tech_marks_total",
				"label": "Technical marks allocation complete",
				"met": _scored_technical_marks(rows) + 0.001 >= technical_marks_total,
			}
		)
	conds.append(
		{
			"key": "has_financial",
			"label": "Financial evaluation basis defined",
			"met": any(_v(r, "stage") == STAGE_FIN for r in rows),
		}
	)
	return conds


def evaluation_setup_exit_conditions_for_doc(doc) -> list[dict[str, Any]]:
	blob = _parse_blob(getattr(doc, "evaluation_setup", None))
	return evaluation_setup_exit_conditions(
		blob["criteria"],
		technical_marks_total=blob["technical_marks_total"],
		technical_pass_mark=cstr(blob.get("technical_pass_mark") or "").strip(),
	)


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


def _available_price_items(doc) -> list[dict[str, str]]:
	from kentender_procurement.tender_configurations.services.price_schedule import (
		_parse_items,
	)

	out: list[dict[str, str]] = []
	for row in _parse_items(getattr(doc, "price_schedule", None)):
		iid = _v(row, "item_id")
		name = _v(row, "item_name")
		if iid:
			out.append({"id": iid, "code": iid, "name": name or iid})
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


def _resolve_ref(rid: str, available: list[dict[str, str]]) -> dict[str, str] | None:
	if not rid:
		return None
	by_id = {cstr(r.get("id") or "").strip(): r for r in available}
	ref = by_id.get(rid)
	if ref:
		return {"id": ref["id"], "code": ref["code"], "name": ref["name"]}
	return {"id": rid, "code": rid, "name": rid}


def _persist_criterion(row: dict[str, Any]) -> dict[str, Any]:
	cleaned = _clean_criterion(row)
	stage = _v(cleaned, "stage")
	if stage not in STAGES:
		stage = ""
	basis = _v(cleaned, "evaluation_basis")
	if basis not in BASES:
		basis = ""
	source = _v(cleaned, "source_type")
	if source not in SOURCE_TYPES:
		source = SOURCE_USER if _any_content(cleaned) else ""
	evidence = _v(cleaned, "bidder_evidence")
	if evidence not in EVIDENCE_OPTS:
		evidence = ""
	return {
		"criterion_id": _v(cleaned, "criterion_id"),
		"criterion_name": _v(cleaned, "criterion_name"),
		"stage": stage,
		"evaluation_basis": basis,
		"source_type": source,
		"bidder_facing_wording": _v(cleaned, "bidder_facing_wording"),
		"pass_fail_rule": _v(cleaned, "pass_fail_rule"),
		"marks": _v(cleaned, "marks"),
		"financial_evaluation_rule": _v(cleaned, "financial_evaluation_rule"),
		"preference_rule": _v(cleaned, "preference_rule"),
		"bidder_evidence": evidence,
		"evidence_instruction": _v(cleaned, "evidence_instruction"),
		"evaluator_guidance": _v(cleaned, "evaluator_guidance"),
		"related_requirement_id": _v(cleaned, "related_requirement_id"),
		"related_price_item_id": _v(cleaned, "related_price_item_id"),
		"related_milestone_id": _v(cleaned, "related_milestone_id"),
		"related_tds_key": _v(cleaned, "related_tds_key"),
	}


def _build_import_drafts(doc, existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
	used_req = {
		_v(r, "related_requirement_id") for r in existing if _v(r, "related_requirement_id")
	}
	used_price = {
		_v(r, "related_price_item_id") for r in existing if _v(r, "related_price_item_id")
	}
	used_ms = {
		_v(r, "related_milestone_id") for r in existing if _v(r, "related_milestone_id")
	}
	drafts: list[dict[str, Any]] = []

	# Always suggest a financial comparison basis if missing.
	if not any(_v(r, "stage") == STAGE_FIN for r in existing):
		drafts.append(
			_persist_criterion(
				{
					"criterion_name": "Financial comparison",
					"stage": STAGE_FIN,
					"evaluation_basis": BASIS_LOWEST,
					"source_type": SOURCE_PRICE,
					"bidder_facing_wording": (
						"Bids will be compared using the lowest evaluated price "
						"based on the Price Schedule."
					),
					"financial_evaluation_rule": (
						"Compare evaluated price including required recurrent costs."
					),
					"bidder_evidence": EVIDENCE_NOT,
				}
			)
		)

	if not any(_v(r, "source_type") == SOURCE_TDS for r in existing):
		drafts.append(
			_persist_criterion(
				{
					"criterion_name": "Tender security submitted",
					"stage": STAGE_PRELIM,
					"evaluation_basis": BASIS_PASS,
					"source_type": SOURCE_TDS,
					"bidder_facing_wording": (
						"The tender security must be submitted in the required form and amount."
					),
					"pass_fail_rule": "Must be submitted in required form and amount",
					"bidder_evidence": EVIDENCE_REQUIRED,
					"evidence_instruction": "Provide tender security as specified in the TDS.",
					"related_tds_key": "tender_security",
				}
			)
		)

	for ref in _available_requirements(doc):
		if ref["id"] in used_req:
			continue
		drafts.append(
			_persist_criterion(
				{
					"criterion_name": ref["name"],
					"stage": STAGE_TECH,
					"evaluation_basis": BASIS_SCORED,
					"source_type": SOURCE_REQ,
					"related_requirement_id": ref["id"],
					"bidder_facing_wording": f"Technical compliance for: {ref['name']}",
					"marks": "10",
					"bidder_evidence": EVIDENCE_REQUIRED,
					"evidence_instruction": f"Provide evidence for {ref['name']}.",
				}
			)
		)

	for ref in _available_milestones(doc):
		if ref["id"] in used_ms:
			continue
		drafts.append(
			_persist_criterion(
				{
					"criterion_name": f"Delivery approach — {ref['name']}",
					"stage": STAGE_TECH,
					"evaluation_basis": BASIS_SCORED,
					"source_type": SOURCE_SCHED,
					"related_milestone_id": ref["id"],
					"bidder_facing_wording": (
						f"Implementation approach covering: {ref['name']}"
					),
					"marks": "5",
					"bidder_evidence": EVIDENCE_REQUIRED,
					"evidence_instruction": f"Describe approach for {ref['name']}.",
				}
			)
		)

	for ref in _available_price_items(doc):
		if ref["id"] in used_price:
			continue
		# Only suggest one price-linked draft beyond the financial row
		break

	return drafts


def _summary(rows: list[dict[str, Any]], enriched: list[dict[str, Any]]) -> dict[str, int]:
	return {
		"total_criteria": len(rows),
		"preliminary_count": sum(1 for r in rows if _v(r, "stage") == STAGE_PRELIM),
		"qualification_count": sum(1 for r in rows if _v(r, "stage") == STAGE_QUAL),
		"technical_count": sum(1 for r in rows if _v(r, "stage") == STAGE_TECH),
		"financial_count": sum(1 for r in rows if _v(r, "stage") == STAGE_FIN),
		"preference_count": sum(1 for r in rows if _v(r, "stage") == STAGE_PREF),
		"needs_attention_count": sum(
			1
			for e in enriched
			if e.get("setup_status_label")
			in (SETUP_NEEDS_ATTENTION, SETUP_DRAFT, SETUP_IN_PROGRESS)
		),
	}


def _sync_cfg07_steps_state(doc, *, can_continue: bool, has_progress: bool, progress: dict) -> None:
	state = _parse_steps_state(getattr(doc, "steps_state", None))
	cfg = dict(state.get("CFG-07") or {})
	if can_continue:
		cfg["status_label"] = STEP_COMPLETE
	elif has_progress:
		cfg["status_label"] = STEP_IN_PROGRESS
	else:
		cfg["status_label"] = STEP_NOT_STARTED
	cfg["progress_pct"] = progress.get("progress_pct", 0)
	cfg["progress_met_count"] = progress.get("met_count", 0)
	cfg["progress_required_count"] = progress.get("required_count", 0)
	state["CFG-07"] = cfg
	doc.steps_state = json.dumps(state)


def get_configuration_evaluation_setup(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	blob = _parse_blob(getattr(doc, "evaluation_setup", None))
	raw_rows = blob["criteria"]
	tech_total = blob["technical_marks_total"]
	pass_mark = cstr(blob.get("technical_pass_mark") or "").strip()
	avail_req = _available_requirements(doc)
	avail_price = _available_price_items(doc)
	avail_ms = _available_milestones(doc)

	enriched = []
	for row in raw_rows:
		item = enrich_criterion(row)
		item["related_requirement_ref"] = _resolve_ref(
			item.get("related_requirement_id") or "", avail_req
		)
		item["related_price_item_ref"] = _resolve_ref(
			item.get("related_price_item_id") or "", avail_price
		)
		item["related_milestone_ref"] = _resolve_ref(
			item.get("related_milestone_id") or "", avail_ms
		)
		enriched.append(item)

	blockers, warnings, can_continue = validate_criteria(
		raw_rows,
		technical_marks_total=tech_total,
		technical_pass_mark=pass_mark,
	)
	has_progress = evaluation_setup_has_progress(raw_rows)
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")
	import_candidates = _build_import_drafts(doc, raw_rows)
	scoring = _scoring_summary(
		raw_rows, technical_marks_total=tech_total, technical_pass_mark=pass_mark
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
		"wizard_state_label": context.get("wizard_state_label")
		or _STATUS_LABELS.get(status, status),
		"blocker_count": len(blockers),
		"warning_count": len(warnings),
		"blockers": blockers,
		"warnings": warnings,
		"can_continue": can_continue,
		"has_progress": has_progress,
		"active_tab": TAB_ALL,
		"evaluation_mode": "scored_technical" if scoring["show_scoring_summary"] else "pass_fail",
		"scoring_summary": scoring,
		"criteria": enriched,
		"items": enriched,
		"summary": _summary(raw_rows, enriched),
		"next_criterion_id": _next_criterion_id(raw_rows),
		"available_requirements": avail_req,
		"available_price_items": avail_price,
		"available_milestones": avail_ms,
		"import_candidate_count": len(import_candidates),
		"technical_marks_total": tech_total,
		"technical_pass_mark": pass_mark,
		"minimum_technical_score": pass_mark,
		"context": context,
		"options": {
			"stage": list(STAGES),
			"evaluation_basis": list(BASES),
			"source_type": list(SOURCE_TYPES),
			"bidder_evidence": list(EVIDENCE_OPTS),
			"tabs": [
				{"key": TAB_ALL, "label": "All Criteria"},
				{"key": TAB_PRELIM, "label": "Preliminary Checks"},
				{"key": TAB_QUAL, "label": "Qualification"},
				{"key": TAB_TECH, "label": "Technical Evaluation"},
				{"key": TAB_FIN, "label": "Financial Evaluation"},
				{"key": TAB_PREF, "label": "Preferences & Reservations"},
				{"key": TAB_NEEDS, "label": "Needs Attention"},
			],
		},
		"column_contract": {
			"note": (
				"Status uses Complete / Needs attention only. "
				"Never show bidder scores, rankings, or award outcomes."
			),
			"columns": [
				"Criterion ID",
				"Criterion",
				"Stage",
				"Evaluation Basis",
				"Source / Link",
				"Marks / Rule",
				"Bidder Evidence",
				"Status",
				"Action",
			],
		},
	}


def save_configuration_evaluation_setup(
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

	existing_blob = _parse_blob(getattr(doc, "evaluation_setup", None))
	tech_total = flt(
		payload.get("technical_marks_total")
		if payload.get("technical_marks_total") is not None
		else existing_blob["technical_marks_total"]
	)
	if tech_total <= 0:
		tech_total = TECHNICAL_MARKS_TOTAL_DEFAULT

	do_import = bool(payload.get("import") or payload.get("action") == "import")
	if isinstance(payload.get("criteria"), (list, str)) or isinstance(
		payload.get("items"), (list, str)
	):
		incoming = _parse_criteria(payload.get("criteria") or payload.get("items"))
	elif isinstance(payload, list):
		incoming = _parse_criteria(payload)
	else:
		incoming = _parse_criteria(payload.get("evaluation_setup"))

	persist: list[dict[str, Any]] = []
	for row in incoming:
		item = _persist_criterion(row)
		if not item.get("criterion_id"):
			item["criterion_id"] = _next_criterion_id(persist)
		persist.append(item)

	if do_import:
		for draft in _build_import_drafts(doc, persist):
			draft["criterion_id"] = _next_criterion_id(persist)
			persist.append(draft)

	# Tender-level minimum technical score only (never stored per criterion).
	global_pass = cstr(
		payload.get("minimum_technical_score")
		or payload.get("technical_pass_mark")
		or ""
	).strip()
	if not global_pass:
		# One-time lift from legacy per-row values on the incoming payload rows.
		global_pass = _lift_pass_mark_from_rows(
			payload.get("criteria") or payload.get("items") or []
		)
	if not global_pass:
		global_pass = cstr(existing_blob.get("technical_pass_mark") or "").strip()

	blockers, warnings, can_continue = validate_criteria(
		persist,
		technical_marks_total=tech_total,
		technical_pass_mark=global_pass,
	)
	has_progress = evaluation_setup_has_progress(persist)

	from kentender_procurement.tender_configurations.services.step_progress import (
		evaluate_conditions,
	)

	progress = evaluate_conditions(
		evaluation_setup_exit_conditions(
			persist,
			technical_marks_total=tech_total,
			technical_pass_mark=global_pass,
		)
	)
	blob = {
		"criteria": persist,
		"technical_marks_total": tech_total,
		"technical_pass_mark": global_pass,
	}

	doc.evaluation_setup = json.dumps(blob)
	doc.blocker_count = len(blockers)
	doc.warning_count = len(warnings)
	_sync_cfg07_steps_state(
		doc,
		can_continue=can_continue,
		has_progress=has_progress,
		progress=progress,
	)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return get_configuration_evaluation_setup(doc.name)
