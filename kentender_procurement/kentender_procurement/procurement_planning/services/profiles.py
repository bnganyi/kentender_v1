# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.1 / §5.5.3.3 — the Planning-side use of the
Configuration & Governance rule profiles (plan D4, tracker PLN18-206).

Planning reads the versioned **Procurement Method Profile** (eligibility
conditions, evidence, authorisation) and **Procedure Schedule Profile**
(applicable milestones, sequence, counting rule, legally verified limits and
separately labelled planning assumptions) only through
`kentender_core.services.procurement_settings`. Nothing here holds a
universal timing constant, a missing-profile fallback or an Open Tender
substitution: a missing or ambiguous profile permits Draft work and blocks
formal submission (`PLN_REFERENCE_UNAVAILABLE`).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import add_days, cstr, date_diff, flt, getdate

from kentender_core.services import procurement_settings as settings
from kentender_procurement.procurement_planning.errors import fail

PERIOD_KEYS: tuple[str, ...] = (
	"tendering_period_days",
	"evaluation_period_days",
	"award_approval_buffer_days",
	"notification_buffer_days",
	"standstill_period_days",
)
DELIVERY_KEY = "estimated_delivery_period_days"
MILESTONE_BY_PERIOD: dict[str, str] = {period: milestone for milestone, period in settings.PERIOD_BY_MILESTONE.items()}
VERIFIED_STATUSES = (settings.VERIFICATION_FIXTURE, settings.VERIFICATION_VERIFIED)
NOT_FOUND: dict[str, Any] = {"found": False}


# --------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------


def applicability_date(anchor, fiscal_year: str):
	"""The legally applicable date for a package: its planned invitation date
	(the profiles' applicability basis) or, before an anchor exists, the
	first day of the plan's financial year."""
	if anchor:
		return getdate(anchor)
	start = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")
	return getdate(start) if start else None


def _unresolved(exc: Exception) -> bool:
	return getattr(exc, "code", "") == "CFG_RULE_UNRESOLVED"


def resolve(*, procurement_method: str, procurement_category: str, applicability_date) -> dict[str, Any]:
	"""Both profiles for a method/category on the applicable date. An
	ambiguous configuration (two Versions in force) is reported as
	`unresolved`, never guessed."""
	out: dict[str, Any] = {"method": dict(NOT_FOUND), "schedule": dict(NOT_FOUND), "unresolved": [], "applicability_date": str(applicability_date or "")}
	if not procurement_method or not applicability_date:
		return out
	try:
		out["method"] = settings.resolve_method_profile(procurement_method=procurement_method, procurement_category=procurement_category or "", applicability_date=applicability_date)
	except Exception as exc:  # CFG_RULE_UNRESOLVED is a configuration defect Planning surfaces, not swallows
		if not _unresolved(exc):
			raise
		out["unresolved"].append("method")
	try:
		out["schedule"] = settings.resolve_schedule_profile(procurement_method=procurement_method, procurement_category=procurement_category or "", applicability_date=applicability_date)
	except Exception as exc:
		if not _unresolved(exc):
			raise
		out["unresolved"].append("schedule")
	return out


def schedule_profile_by_name(name: str) -> dict[str, Any]:
	"""The frozen profile Version a submitted item references (§5.5.1:
	locked rule-profile evidence)."""
	if not name or not frappe.db.exists(settings.SCHEDULE_PROFILE, name):
		return dict(NOT_FOUND)
	return {**settings.get_schedule_profile(name), "found": True}


def method_profile_by_name(name: str) -> dict[str, Any]:
	if not name or not frappe.db.exists(settings.METHOD_PROFILE, name):
		return dict(NOT_FOUND)
	return {**settings.get_method_profile(name), "found": True}


def is_verified(profile: dict[str, Any]) -> bool:
	return cstr(profile.get("verification_status")) in VERIFIED_STATUSES


# --------------------------------------------------------------------------
# Schedule: periods, baseline, feasibility
# --------------------------------------------------------------------------


def period_rules(schedule: dict[str, Any]) -> dict[str, dict[str, Any]]:
	"""period key → the applicable milestone row (limits, default, basis)."""
	if not schedule.get("found"):
		return {}
	return {key: row for key, row in (schedule.get("periods") or {}).items() if key in PERIOD_KEYS}


def default_period_inputs(schedule: dict[str, Any]) -> dict[str, int | None]:
	rules = period_rules(schedule)
	return {key: (rules[key].get("default_days") if key in rules else None) for key in PERIOD_KEYS}


def applicable_milestones(schedule: dict[str, Any]) -> list[str]:
	"""Milestones in profile sequence; every milestone when no profile is
	resolved so Draft work can continue (readiness reports the gap)."""
	if not schedule.get("found"):
		return list(settings.MILESTONES)
	rows = sorted((r for r in schedule.get("milestones", []) if r.get("applies")), key=lambda r: int(r.get("sequence") or 0))
	return [r["milestone"] for r in rows]


def _period_invalid(period: str, rule: str, limit: int, offered: int, *, field: str | None = None, reference: str = "") -> None:
	label = period.replace("_days", "").replace("_", " ")
	word = "at least" if rule == "minimum" else "at most"
	fail(
		"PLN_PROFILE_PERIOD_INVALID",
		f"The {label} must be {word} {limit} calendar days for the selected procedure; {offered} offered.",
		{"field": field or period, "period": period, "rule": rule, "limit": limit, "offered": offered, "unit": "calendar days", "statutory_reference": reference},
	)


def validate_period_inputs(period_inputs: dict[str, Any], schedule: dict[str, Any]) -> dict[str, int]:
	"""Whole non-negative days per applicable period; the resolved profile's
	minimum/maximum bound each one with labelled parameters. Without a
	profile every offered period is accepted as a Draft value."""
	rules = period_rules(schedule)
	keys = [k for k in PERIOD_KEYS if k in rules] if schedule.get("found") else list(PERIOD_KEYS)
	clean: dict[str, int] = {}
	for key in keys:
		raw = (period_inputs or {}).get(key)
		if raw in (None, ""):
			if schedule.get("found") and rules[key].get("default_days") is not None:
				raw = rules[key]["default_days"]
			else:
				fail("PLN_SCHEDULE_INVALID", f"Enter a whole number of days for {key.replace('_days', '').replace('_', ' ')}.", {"field": key})
		try:
			value = int(raw)
		except (TypeError, ValueError):
			fail("PLN_SCHEDULE_INVALID", f"Enter a whole number of days for {key.replace('_days', '').replace('_', ' ')}.", {"field": key})
		if value < 0:
			fail("PLN_SCHEDULE_INVALID", "Periods cannot be negative.", {"field": key})
		rule = rules.get(key, {})
		minimum, maximum = rule.get("minimum_days"), rule.get("maximum_days")
		if minimum is not None and value < int(minimum):
			_period_invalid(key, "minimum", int(minimum), value, reference=cstr(rule.get("statutory_reference")))
		if maximum is not None and value > int(maximum):
			_period_invalid(key, "maximum", int(maximum), value, reference=cstr(rule.get("statutory_reference")))
		clean[key] = value
	return clean


def derive_baseline(anchor, periods: dict[str, int], boundary, schedule: dict[str, Any]) -> dict[str, Any]:
	"""The applicable baseline dates from the anchor, the entered periods and
	the profile's milestone order; a non-applicable milestone is None
	(`Not applicable`, never zero). The final boundary is the earliest
	source required-by date, never a Requisition value."""
	baseline: dict[str, Any] = {f"baseline_{m}_date": None for m in settings.MILESTONES}
	baseline["baseline_delivery_completion_date"] = getdate(boundary) if boundary else None
	if not anchor:
		return baseline
	current = getdate(anchor)
	baseline["baseline_invitation_date"] = current
	for milestone in applicable_milestones(schedule):
		if milestone in ("invitation", "delivery_completion"):
			continue
		key = settings.PERIOD_BY_MILESTONE.get(milestone)
		if not key or key not in periods:
			continue
		current = add_days(current, int(periods[key]))
		baseline[f"baseline_{milestone}_date"] = getdate(current)
	return baseline


def estimated_completion(baseline: dict[str, Any], delivery_days) -> date | None:
	signing = baseline.get("baseline_contract_signing_date")
	if not signing or delivery_days is None:
		return None
	return getdate(add_days(getdate(signing), int(delivery_days)))


def feasible(baseline: dict[str, Any], delivery_days) -> bool | None:
	"""§5.5.1: signing + estimated delivery period on or before the boundary.
	None when the calculation has no inputs yet."""
	completion = estimated_completion(baseline, delivery_days)
	boundary = baseline.get("baseline_delivery_completion_date")
	if completion is None or not boundary:
		return None
	return date_diff(getdate(boundary), completion) >= 0


def baseline_complete(item, schedule: dict[str, Any]) -> bool:
	return all(item.get(f"baseline_{m}_date") for m in applicable_milestones(schedule))


# --------------------------------------------------------------------------
# Method conditions
# --------------------------------------------------------------------------


def _evidence_by_condition(rows) -> dict[str, dict[str, Any]]:
	out: dict[str, dict[str, Any]] = {}
	for row in rows or []:
		if isinstance(row, dict) and cstr(row.get("condition_id")):
			out[cstr(row["condition_id"])] = row
	return out


def method_conditions(method: dict[str, Any], *, procurement_category: str, planned_value, evidence_rows=None) -> dict[str, Any]:
	"""Evaluate the profile's conditions for one package: known facts are
	checked by the system (category, value against the limits); declarations
	need a structured evidence row (evidence reference, and the specific
	authorisation reference where the profile names an authorising actor).
	A failed mandatory known fact is inadmissible; missing declarations block
	submission only."""
	if not method.get("found"):
		return {"available": False, "admissible": False, "evidence_complete": False, "results": [], "failed": [], "missing_evidence": []}
	value = Decimal(str(flt(planned_value)))
	evidence = _evidence_by_condition(evidence_rows)
	results, failed, missing = [], [], []
	for condition in method.get("conditions", []):
		if condition.get("procurement_category") and condition["procurement_category"] != procurement_category:
			continue
		cid = cstr(condition.get("condition_id"))
		row = {"condition_id": cid, "kind": condition.get("kind"), "description": condition.get("description"), "mandatory": bool(condition.get("mandatory")), "statutory_reference": condition.get("statutory_reference", "")}
		if condition.get("kind") == "Known fact":
			minimum, maximum = Decimal(str(flt(condition.get("minimum_amount")))), Decimal(str(flt(condition.get("maximum_amount"))))
			ok = (minimum <= 0 or value >= minimum) and (maximum <= 0 or value <= maximum)
			row.update(result="Met" if ok else "Not met", limit=str(maximum) if maximum > 0 else "", cumulative_basis=condition.get("cumulative_basis", "None"))
			if not ok and row["mandatory"]:
				failed.append(cid)
		else:
			given = evidence.get(cid)
			needs_authorisation = bool(cstr(condition.get("authorisation_actor")))
			ok = bool(given and cstr(given.get("evidence_reference")).strip() and (not needs_authorisation or cstr(given.get("authorisation_reference")).strip()))
			row.update(
				result="Declared" if ok else "Evidence required",
				required_evidence=condition.get("required_evidence", ""),
				authorisation_actor=condition.get("authorisation_actor", ""),
				authorisation_stage=condition.get("authorisation_stage", ""),
				evidence_reference=cstr(given.get("evidence_reference")) if given else "",
				authorisation_reference=cstr(given.get("authorisation_reference")) if given else "",
			)
			if not ok and row["mandatory"]:
				missing.append(cid)
		results.append(row)
	return {
		"available": True,
		"profile": method.get("profile"),
		"verification_status": method.get("verification_status"),
		"category_supported": bool(method.get("category_supported", True)),
		"admissible": not failed and bool(method.get("category_supported", True)),
		"evidence_complete": not missing,
		"results": results,
		"failed": failed,
		"missing_evidence": missing,
	}


def admissible_methods(*, procurement_category: str, planned_value, applicability_date) -> list[str]:
	"""Every governed method whose profile in force admits this category and
	value on its known facts — the Planner's choice set, in catalogue order.
	No profile in force means the method is not offered."""
	if not applicability_date:
		return []
	out = []
	for method in frappe.get_all("Procurement Method", filters={"status": "Active"}, pluck="name", order_by="creation asc"):
		try:
			profile = settings.resolve_method_profile(procurement_method=method, procurement_category=procurement_category, applicability_date=applicability_date)
		except Exception as exc:
			if _unresolved(exc):
				continue
			raise
		if profile.get("found") and method_conditions(profile, procurement_category=procurement_category, planned_value=planned_value)["admissible"]:
			out.append(method)
	return out
