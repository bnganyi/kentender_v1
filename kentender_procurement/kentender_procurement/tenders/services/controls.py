# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §5.2 — the officer control catalogue (plan D23),
enforced identically on the server for every write and rendered by the
client from the same table. `SaveTenderDraft` accepts only these fields: an
inherited or generated name is `TND_INHERITED_EDIT`; an unknown name, a
wrong type, an out-of-range value, an unknown option or a value for a
conditional field while it is inapplicable is `TND_CONTROL_INVALID`
(TPR08-AC-013/014/015). Drafts may be incomplete: `missing()` reports
required-but-empty fields for the review result, `validate()` only rejects
what was sent. Comparable-contract count and experience period are free
positive whole numbers — no preset menu (§16(22)).

Two visible preparation tasks own these controls: `details` (Tender dates,
security, meeting) and `requirements` (supplier evidence and contract
terms); `review` is the third task and owns no control (§10.4–10.6).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, getdate

TEXT, DATE, DATETIME, INT, DECIMAL, MONEY, BOOL, SELECT, LINK = "text", "date", "datetime", "int", "decimal", "money", "bool", "select", "link"
TASK_DETAILS, TASK_REQUIREMENTS, TASK_REVIEW = "details", "requirements", "review"
TASKS = (TASK_DETAILS, TASK_REQUIREMENTS, TASK_REVIEW)
TASK_LABELS = {TASK_DETAILS: "Tender details", TASK_REQUIREMENTS: "Supplier and contract requirements", TASK_REVIEW: "Review and submit"}

AFTER_SALES_OPTIONS = (
	"Kenya service-centre details and escalation contacts",
	"Manufacturer or authorised service-partner commitment",
	"Both",
)
DEFAULT_VALIDITY_DAYS = 120

# field -> spec. `when`: (other_field, value) the field applies under. `group`
# is the §5.2 sub-table the field belongs to (details / supplier / contract).
CATALOGUE: dict[str, dict[str, Any]] = {
	# --- Tender details (§5.2 "Tender details") ---
	"tender_title": {"task": TASK_DETAILS, "group": "details", "type": TEXT, "max_length": 160, "min_length": 3, "required": True, "label": "Tender title"},
	"issue_date": {"task": TASK_DETAILS, "group": "details", "type": DATE, "required": True, "label": "Issue date"},
	"clarification_deadline": {"task": TASK_DETAILS, "group": "details", "type": DATETIME, "required": True, "label": "Clarification deadline"},
	"submission_deadline": {"task": TASK_DETAILS, "group": "details", "type": DATETIME, "required": True, "label": "Submission deadline"},
	"tender_validity_days": {"task": TASK_DETAILS, "group": "details", "type": INT, "min": 1, "max": 365, "default": DEFAULT_VALIDITY_DAYS, "required": True, "label": "Tender validity"},
	"tender_security_amount": {"task": TASK_DETAILS, "group": "details", "type": MONEY, "min_exclusive": 0, "required": True, "label": "Tender security amount"},
	"pre_tender_meeting": {"task": TASK_DETAILS, "group": "details", "type": BOOL, "default": False, "required": True, "label": "Pre-tender meeting"},
	"meeting_datetime": {"task": TASK_DETAILS, "group": "details", "type": DATETIME, "when": ("pre_tender_meeting", True), "required": True, "label": "Meeting date/time"},
	"meeting_mode": {"task": TASK_DETAILS, "group": "details", "type": SELECT, "options": ("Physical", "Online"), "when": ("pre_tender_meeting", True), "required": True, "label": "Meeting mode"},
	"meeting_venue": {"task": TASK_DETAILS, "group": "details", "type": LINK, "doctype": "Delivery Location", "when": ("meeting_mode", "Physical"), "required": True, "label": "Meeting venue"},
	"online_joining_information": {"task": TASK_DETAILS, "group": "details", "type": TEXT, "max_length": 240, "min_length": 3, "when": ("meeting_mode", "Online"), "required": True, "label": "Online joining information"},
	# --- Supplier requirements (§5.2 "Supplier requirements") ---
	"manufacturer_authorisation_required": {"task": TASK_REQUIREMENTS, "group": "supplier", "type": BOOL, "default": True, "required": True, "label": "Manufacturer authorisation required"},
	"datasheets_required": {"task": TASK_REQUIREMENTS, "group": "supplier", "type": BOOL, "default": True, "required": True, "label": "Product datasheets or brochures required"},
	"past_experience_required": {"task": TASK_REQUIREMENTS, "group": "supplier", "type": BOOL, "default": False, "required": True, "label": "Past supply experience required"},
	"minimum_comparable_contracts": {"task": TASK_REQUIREMENTS, "group": "supplier", "type": INT, "min": 1, "max": 1000, "when": ("past_experience_required", True), "required": True, "label": "Minimum comparable contracts"},
	"experience_period_years": {"task": TASK_REQUIREMENTS, "group": "supplier", "type": INT, "min": 1, "max": 50, "when": ("past_experience_required", True), "required": True, "label": "Within the last ___ years"},
	"after_sales_evidence_required": {"task": TASK_REQUIREMENTS, "group": "supplier", "type": BOOL, "default": None, "required": True, "label": "After-sales support evidence required"},
	"after_sales_evidence": {"task": TASK_REQUIREMENTS, "group": "supplier", "type": SELECT, "options": AFTER_SALES_OPTIONS, "when": ("after_sales_evidence_required", True), "required": True, "label": "After-sales evidence"},
	# --- Contract terms (§5.2 "Contract terms") ---
	"inspection_location": {"task": TASK_REQUIREMENTS, "group": "contract", "type": LINK, "doctype": "Delivery Location", "required": True, "label": "Inspection and acceptance location"},
	"payment_timing_days": {"task": TASK_REQUIREMENTS, "group": "contract", "type": SELECT, "options": ("30", "45", "60"), "default": "30", "required": True, "label": "Payment timing"},
	"performance_security_required": {"task": TASK_REQUIREMENTS, "group": "contract", "type": BOOL, "default": True, "required": True, "label": "Performance security required"},
	"performance_security_percent": {"task": TASK_REQUIREMENTS, "group": "contract", "type": DECIMAL, "min": 1, "max": 10, "default": 10, "when": ("performance_security_required", True), "required": True, "label": "Performance security percentage"},
	"delay_damages_per_week_percent": {"task": TASK_REQUIREMENTS, "group": "contract", "type": DECIMAL, "min": 0.1, "max": 1.0, "default": 0.5, "required": True, "label": "Delay damages per week"},
	"maximum_delay_damages_percent": {"task": TASK_REQUIREMENTS, "group": "contract", "type": INT, "min": 5, "max": 10, "default": 10, "required": True, "label": "Maximum delay damages"},
	"contract_contact_office": {"task": TASK_REQUIREMENTS, "group": "contract", "type": LINK, "doctype": "Contact Office", "required": True, "label": "Contract contact office"},
}

FIELDS_BY_TASK: dict[str, tuple[str, ...]] = {
	task: tuple(name for name, spec in CATALOGUE.items() if spec["task"] == task) for task in (TASK_DETAILS, TASK_REQUIREMENTS)
}

# Names a payload may never carry: inherited (§4.3), template-fixed or
# generated (§4.5) values, supplier responses and lifecycle columns. Any of
# these in a write is `TND_INHERITED_EDIT` (TPR08-AC-009/017).
INHERITED_OR_GENERATED: frozenset[str] = frozenset(
	{
		"requisition_snapshot_json", "requisition_snapshot_digest", "snapshot_json", "items", "technical_requirements", "related_services",
		"acceptance_requirements", "supporting_materials", "requirement_title", "latest_delivery_date", "delivery_location",
		"minimum_warranty_months", "onsite_support_required", "maximum_support_response_hours", "manufacturer_support_required",
		"quantity", "unit", "item_name", "required_value", "required_value_json", "reservation_category", "reservation_category_value",
		"lotting_indicator", "plan_item_id", "requisition_reference", "requisition_handoff", "requisition_version", "strategic_objective",
		"strategic_objective_path", "plan_horizon", "multi_year_justification", "authorised_value", "drawdown_lines", "reservation_id",
		"tender_reference", "opening_datetime", "tender_security_currency", "tender_security_treatment", "currency", "template_release_id",
		"template_key", "template_version", "bundle_digest", "official_source_digest", "validity_date", "unit_price", "line_total", "tax",
		"tender_total", "warranty_confirmation_required", "price_schedule", "package_digest", "review_findings", "status", "overall_status",
		"record_version", "published_at", "publication_id", "evidence_requirements",
	}
)

_TRUE = {True, 1, "1", "true", "True"}
_FALSE = {False, 0, "0", "false", "False"}


def _is_blank(value: Any) -> bool:
	return value is None or (isinstance(value, str) and not value.strip())


def coerce(field: str, value: Any) -> tuple[Any, str]:
	"""(clean value, error message) for one control; error '' when valid."""
	spec = CATALOGUE[field]
	kind = spec["type"]
	if kind == BOOL:
		if isinstance(value, bool) or value in _TRUE or value in _FALSE:
			return (value in _TRUE if not isinstance(value, bool) else value), ""
		return None, "Choose Yes or No."
	if kind == SELECT:
		text = cstr(value).strip()
		if text not in spec["options"]:
			return None, "Choose one of: " + ", ".join(spec["options"]) + "."
		return text, ""
	if kind == TEXT:
		if not isinstance(value, str):
			return None, "Enter plain text."
		text = value.strip()
		if any(token in text for token in ("<", ">", "</", "**", "```", "&lt;")):
			return None, "Plain text only; no HTML or Markdown."
		if len(text) < spec.get("min_length", 1):
			return None, f"Enter at least {spec.get('min_length', 1)} characters."
		if len(text) > spec["max_length"]:
			return None, f"Enter at most {spec['max_length']} characters."
		return text, ""
	if kind == INT:
		if isinstance(value, bool) or not (isinstance(value, int) or (isinstance(value, str) and value.strip().lstrip("-").isdigit()) or (isinstance(value, float) and float(value).is_integer())):
			return None, "Enter a whole number."
		number = int(value)
		if number < spec["min"] or number > spec["max"]:
			return None, f"Enter a whole number from {spec['min']} to {spec['max']}."
		return number, ""
	if kind in (DECIMAL, MONEY):
		if isinstance(value, bool):
			return None, "Enter a number."
		try:
			number = Decimal(str(value).replace(",", "").strip())
		except (InvalidOperation, ValueError):
			return None, "Enter a number."
		if number != number:  # NaN
			return None, "Enter a number."
		if "min_exclusive" in spec and number <= Decimal(str(spec["min_exclusive"])):
			return None, "Enter a positive amount."
		if "min" in spec and number < Decimal(str(spec["min"])):
			return None, f"Enter a value from {spec['min']} to {spec['max']}."
		if "max" in spec and number > Decimal(str(spec["max"])):
			return None, f"Enter a value from {spec['min']} to {spec['max']}."
		if kind == MONEY and number != number.quantize(Decimal("0.01")):
			return None, "Enter an amount with at most two decimal places."
		return float(number), ""
	if kind == DATE:
		try:
			return str(getdate(value)), ""
		except Exception:
			return None, "Enter a valid date."
	if kind == DATETIME:
		try:
			return get_datetime(value).isoformat(sep=" "), ""
		except Exception:
			return None, "Enter a valid date and time."
	if kind == LINK:
		name = cstr(value).strip()
		status = frappe.db.get_value(spec["doctype"], name, "status") if name else None
		if not status:
			return None, f"Choose an Active {spec['doctype']}."
		if status != "Active":
			return None, f"This {spec['doctype']} is not Active."
		return name, ""
	return None, "Unsupported control."


def applies(field: str, state: dict[str, Any]) -> bool:
	when = CATALOGUE[field].get("when")
	if not when:
		return True
	other, wanted = when
	return applies(other, state) and state.get(other) == wanted


def validate(values: dict[str, Any], current: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
	"""Clean the sent values against the merged state. Raises
	`TND_INHERITED_EDIT` for an inherited/generated name; returns field
	errors for everything a user can correct (AGENTS.md §6.10)."""
	from kentender_procurement.tenders.services.errors import fail

	if not isinstance(values, dict):
		fail("TND_CONTROL_INVALID", "Draft values must be an object of task fields.")
	inherited = sorted(set(values) & INHERITED_OR_GENERATED)
	if inherited:
		fail("TND_INHERITED_EDIT", "These values are inherited or generated and cannot be changed: " + ", ".join(inherited), {"fields": inherited})
	clean: dict[str, Any] = {}
	errors: dict[str, str] = {}
	unknown = sorted(set(values) - set(CATALOGUE))
	for name in unknown:
		errors[name] = "Unknown field."
	merged = dict(current)
	for field in CATALOGUE:
		if field not in values or field in unknown:
			continue
		value = values[field]
		if _is_blank(value):
			clean[field] = None
			merged[field] = None
			continue
		coerced, error = coerce(field, value)
		if error:
			errors[field] = error
			continue
		clean[field] = coerced
		merged[field] = coerced
	for field in list(clean):
		if clean[field] is not None and not applies(field, merged):
			errors[field] = "Not applicable with the current selections."
			clean.pop(field)
	return clean, errors


def missing(state: dict[str, Any]) -> list[tuple[str, str, str]]:
	"""(task, field, label) for every applicable required control still empty."""
	out = []
	for field, spec in CATALOGUE.items():
		if spec.get("required") and applies(field, state) and _is_blank(state.get(field)):
			out.append((spec["task"], field, spec["label"]))
	return out


def defaults(snapshot: dict[str, Any]) -> dict[str, Any]:
	"""Initial Draft values (§5.2): catalogue defaults, the Tender title
	seeded from the requirement title, and after-sales evidence defaulted
	from the authorised support need."""
	out = {field: spec["default"] for field, spec in CATALOGUE.items() if spec.get("default") is not None}
	out["tender_title"] = (snapshot.get("requirement_title") or "")[:160]
	out["after_sales_evidence_required"] = bool(snapshot.get("onsite_support_required") or snapshot.get("manufacturer_support_required"))
	if out["after_sales_evidence_required"]:
		out["after_sales_evidence"] = AFTER_SALES_OPTIONS[0]
	return out


def normalise(state: dict[str, Any]) -> dict[str, Any]:
	"""Canonical Python types for every catalogue field (None when absent),
	so a digest computed from an in-memory Draft equals one computed after
	reload. Stored as `officer_payload_json` (plan D4)."""
	out: dict[str, Any] = {}
	for field in CATALOGUE:
		value = state.get(field)
		if _is_blank(value):
			out[field] = None
			continue
		coerced, error = coerce(field, value) if CATALOGUE[field]["type"] != LINK else (cstr(value), "")
		out[field] = coerced if not error else value
	return out


def task_status(state: dict[str, Any], task: str, *, baseline: dict[str, Any] | None = None) -> str:
	"""§10.4 progress row vocabulary: `Not started` / `Needs attention` /
	`Complete` for one preparation task. A task is started once any of its
	values differs from the Draft's initial defaults (`baseline`); the
	details task is the first screen and is always at least `Needs
	attention` while incomplete."""
	fields = FIELDS_BY_TASK[task]
	baseline = normalise(baseline or {})
	touched = any(state.get(f) != baseline.get(f) for f in fields)
	if any(t == task for t, _f, _l in missing(state)):
		return "Needs attention" if touched or task == TASK_DETAILS else "Not started"
	return "Complete"


def catalogue_for_client() -> dict[str, Any]:
	"""The same catalogue the client renders from (§5.2: identical rules)."""
	return {
		field: {k: (list(v) if isinstance(v, tuple) else v) for k, v in spec.items()}
		for field, spec in CATALOGUE.items()
	}
