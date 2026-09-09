# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §8 — the exact Task 1, 4 and 5 control catalogue,
enforced identically on the server for every write (§8.0): type, source,
options, range, conditionality and default. `SaveTenderDraft` accepts only
these fields; an inherited or generated name is `TPR_INHERITED_EDIT`, an
unknown name, a wrong type, an out-of-range value, an unknown option or a
value for a conditional field while it is inapplicable is
`TPR_CONTROL_INVALID` (TPR-AC-006/008/019/020/021). Drafts may be
incomplete: `missing()` reports required-but-empty fields for readiness,
`validate()` only rejects what was sent."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, getdate

TEXT, DATE, DATETIME, INT, DECIMAL, MONEY, BOOL, SELECT, LINK = "text", "date", "datetime", "int", "decimal", "money", "bool", "select", "link"

AFTER_SALES_OPTIONS = (
	"Kenya service-centre details and escalation contacts",
	"Manufacturer or authorised service-partner commitment",
	"Both",
)

# field -> spec. `when`: (other_field, value) the field applies under.
CATALOGUE: dict[str, dict[str, Any]] = {
	# --- Task 1 — Tender details (§8.1) ---
	"tender_title": {"task": 1, "type": TEXT, "max_length": 160, "min_length": 3, "required": True, "label": "Tender title"},
	"issue_date": {"task": 1, "type": DATE, "required": True, "label": "Issue date"},
	"clarification_deadline": {"task": 1, "type": DATETIME, "required": True, "label": "Clarification deadline"},
	"submission_deadline": {"task": 1, "type": DATETIME, "required": True, "label": "Submission deadline"},
	"tender_validity_days": {"task": 1, "type": INT, "min": 1, "max": 365, "default": 120, "required": True, "label": "Tender validity"},
	"tender_security_amount": {"task": 1, "type": MONEY, "min_exclusive": 0, "required": True, "label": "Tender security amount"},
	"pre_tender_meeting": {"task": 1, "type": BOOL, "default": False, "required": True, "label": "Pre-tender meeting"},
	"meeting_datetime": {"task": 1, "type": DATETIME, "when": ("pre_tender_meeting", True), "required": True, "label": "Meeting date/time"},
	"meeting_mode": {"task": 1, "type": SELECT, "options": ("Physical", "Online"), "when": ("pre_tender_meeting", True), "required": True, "label": "Meeting mode"},
	"meeting_venue": {"task": 1, "type": LINK, "doctype": "Delivery Location", "when": ("meeting_mode", "Physical"), "required": True, "label": "Meeting venue"},
	"online_joining_information": {"task": 1, "type": TEXT, "max_length": 240, "min_length": 3, "when": ("meeting_mode", "Online"), "required": True, "label": "Online joining information"},
	# --- Task 4 — Submission and evaluation (§8.4) ---
	"manufacturer_authorisation_required": {"task": 4, "type": BOOL, "default": True, "required": True, "label": "Manufacturer authorisation required"},
	"datasheets_required": {"task": 4, "type": BOOL, "default": True, "required": True, "label": "Product datasheets or brochures required"},
	"past_experience_required": {"task": 4, "type": BOOL, "default": False, "required": True, "label": "Past supply experience required"},
	"minimum_comparable_contracts": {"task": 4, "type": SELECT, "options": ("1", "2", "3"), "when": ("past_experience_required", True), "required": True, "label": "Minimum comparable contracts"},
	"experience_period_years": {"task": 4, "type": SELECT, "options": ("3", "5"), "when": ("past_experience_required", True), "required": True, "label": "Experience period"},
	"after_sales_evidence_required": {"task": 4, "type": BOOL, "default": None, "required": True, "label": "After-sales support evidence required"},
	"after_sales_evidence": {"task": 4, "type": SELECT, "options": AFTER_SALES_OPTIONS, "when": ("after_sales_evidence_required", True), "required": True, "label": "After-sales evidence"},
	# --- Task 5 — Contract terms (§8.5) ---
	"inspection_location": {"task": 5, "type": LINK, "doctype": "Delivery Location", "required": True, "label": "Inspection and acceptance location"},
	"payment_timing_days": {"task": 5, "type": SELECT, "options": ("30", "45", "60"), "default": "30", "required": True, "label": "Payment timing"},
	"performance_security_required": {"task": 5, "type": BOOL, "default": True, "required": True, "label": "Performance security required"},
	"performance_security_percent": {"task": 5, "type": DECIMAL, "min": 1, "max": 10, "default": 10, "when": ("performance_security_required", True), "required": True, "label": "Performance security percentage"},
	"delay_damages_per_week_percent": {"task": 5, "type": DECIMAL, "min": 0.1, "max": 1.0, "default": 0.5, "required": True, "label": "Delay damages per week"},
	"maximum_delay_damages_percent": {"task": 5, "type": INT, "min": 5, "max": 10, "default": 10, "required": True, "label": "Maximum delay damages"},
	"contract_contact_office": {"task": 5, "type": LINK, "doctype": "Contact Office", "required": True, "label": "Contract contact office"},
}

FIELDS_BY_TASK: dict[int, tuple[str, ...]] = {
	task: tuple(name for name, spec in CATALOGUE.items() if spec["task"] == task) for task in (1, 4, 5)
}

# Names a payload may never carry: inherited (§7.3), template-fixed or
# generated (§8.0/§8.3) values, and supplier responses. Any of these in a
# write is `TPR_INHERITED_EDIT` (TPR-AC-008, SMOKE-03/05).
INHERITED_OR_GENERATED: frozenset[str] = frozenset(
	{
		"snapshot_json", "snapshot_digest", "items", "technical_requirements", "related_services", "acceptance_requirements",
		"supporting_materials", "requirement_title", "latest_delivery_date", "delivery_location", "minimum_warranty_months",
		"onsite_support_required", "maximum_support_response_hours", "manufacturer_support_required", "quantity", "unit",
		"item_name", "required_value", "required_value_json", "reservation_category", "reservation_category_value",
		"lotting_indicator", "plan_item_id", "requisition_reference", "requisition_handoff", "requisition_version",
		"strategic_objective", "strategic_objective_path", "plan_horizon", "multi_year_justification",
		"tender_reference", "opening_datetime", "tender_security_currency", "tender_security_treatment", "currency",
		"template_key", "template_version", "bundle_digest", "official_source_digest", "validity_date",
		"unit_price", "line_total", "tax", "tender_total", "warranty_confirmation_required", "price_schedule",
		"content_digest", "readiness_findings", "version_status", "current_state", "record_version",
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
		return float(number), ""
	if kind == DATE:
		try:
			return getdate(value), ""
		except Exception:
			return None, "Enter a valid date."
	if kind == DATETIME:
		try:
			return get_datetime(value), ""
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
	`TPR_INHERITED_EDIT` for an inherited/generated name; returns field
	errors for everything a user can correct (AGENTS.md §6.10)."""
	from kentender_procurement.tender_preparation.services.errors import fail

	if not isinstance(values, dict):
		fail("TPR_CONTROL_INVALID", "Draft values must be an object of task fields.")
	inherited = sorted(set(values) & INHERITED_OR_GENERATED)
	if inherited:
		fail("TPR_INHERITED_EDIT", "These values are inherited or generated and cannot be changed: " + ", ".join(inherited), {"fields": inherited})
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
	return clean, errors


def missing(state: dict[str, Any]) -> list[tuple[int, str, str]]:
	"""(task, field, label) for every applicable required control still empty."""
	out = []
	for field, spec in CATALOGUE.items():
		if spec.get("required") and applies(field, state) and _is_blank(state.get(field)):
			out.append((spec["task"], field, spec["label"]))
	return out


def defaults(snapshot: dict[str, Any]) -> dict[str, Any]:
	"""Initial Draft values (§8): catalogue defaults, the Tender title seeded
	from the requirement title, and after-sales evidence defaulted from the
	authorised support need."""
	out = {field: spec["default"] for field, spec in CATALOGUE.items() if spec.get("default") is not None}
	out["tender_title"] = (snapshot.get("requirement_title") or "")[:160]
	out["after_sales_evidence_required"] = bool(snapshot.get("onsite_support_required") or snapshot.get("manufacturer_support_required"))
	if out["after_sales_evidence_required"]:
		out["after_sales_evidence"] = AFTER_SALES_OPTIONS[0]
	return out


def catalogue_for_client() -> dict[str, Any]:
	"""The same catalogue the client renders from (§8.0: identical rules)."""
	return {
		field: {k: (list(v) if isinstance(v, tuple) else v) for k, v in spec.items() if k != "doctype"} | ({"doctype": spec["doctype"]} if "doctype" in spec else {})
		for field, spec in CATALOGUE.items()
	}
