# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.3 / §5.6 — Plan readiness.

Readiness is an exact blocker list, never a score. Pre-Finance (§5.6.4):
every item has an Objective, a planned designation, the contents, an
estimate basis, an estimated delivery period and a calculable schedule
from its resolved schedule profile. Formal submission adds: verified method
and schedule profiles in force (no Open Tender fallback), the method's
mandatory conditions and evidence, feasibility against the source boundary,
and the planned reservation allocations against the **annual procurement
budget** (§5.5.3.1). Advisory: the contract-splitting assessment, which the
Planner confirms or resolves by aggregation.

Regulator reference data (reservation target, threshold matrix for the
splitting assessment) is read from the effective-dated register for the
plan's Fiscal Year — never today's.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_core.services.regulatory_reference import get_regulatory_reference
from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import schedule

CATEGORY_BY_TYPE = {"Goods": "Goods", "Works": "Works"}
NONE_RESERVATION = "None"
# PLN-CHG-001 v1.18 §4.6 — a fixed literal; unsupported horizons are rejected (PLN_MULTI_YEAR_UNSUPPORTED)
PLAN_HORIZONS = ("Single year",)
AGGREGATION_INDICATORS = ("Not aggregated", "Aggregated into this package", "Common-user item arrangement")
LOTTING_INDICATORS = ("Single lot", "Packaged into lots")
OPEN_TENDER = "Open Tender"


def procurement_category_for(requirement_type: str) -> str:
	"""§4.9 — goods, works or services from the accepted classification."""
	return CATEGORY_BY_TYPE.get(cstr(requirement_type), "Services")


def reference_for(fiscal_year: str) -> dict[str, Any]:
	return get_regulatory_reference(fiscal_year)


def money(amount: float) -> str:
	from frappe.utils import fmt_money

	return f"KES {fmt_money(flt(amount), precision=0, currency=None).strip()}"


# --------------------------------------------------------------------------
# Method eligibility (v1.18 §5.5.3.3) and the threshold matrix kept for the
# anti-splitting assessment (§5.6.6)
# --------------------------------------------------------------------------


def method_profile_for(item, fiscal_year: str, *, method: str | None = None) -> dict[str, Any]:
	"""Both resolved profiles for an item (its own method unless another is
	offered) on the item's applicable date."""
	from kentender_procurement.procurement_planning.services import profiles

	return profiles.resolve(
		procurement_method=cstr(method if method is not None else item.get("procurement_method")),
		procurement_category=cstr(item.get("procurement_category")) or "Services",
		applicability_date=profiles.applicability_date(item.get("baseline_invitation_date"), fiscal_year),
	)


def require_method_admissible(resolved: dict[str, Any], category: str, planned_value: float, method: str, evidence_rows=None) -> dict[str, Any]:
	"""A method the Planner selects must have a profile in force whose
	mandatory known facts hold for the package; declarations are due at
	submission, not at every Draft save."""
	from kentender_procurement.procurement_planning.services import profiles

	if "method" in resolved.get("unresolved", []):
		fail("PLN_REFERENCE_UNAVAILABLE", "More than one eligibility profile is in force for this method; correct the configuration.", {"field": "procurement_method"})
	profile = resolved.get("method") or {}
	if not profile.get("found"):
		fail("PLN_REFERENCE_UNAVAILABLE", f"No eligibility profile is in force for {method} on the package's applicable date.", {"field": "procurement_method", "procurement_method": method})
	outcome = profiles.method_conditions(profile, procurement_category=category, planned_value=planned_value, evidence_rows=evidence_rows)
	if not outcome["admissible"]:
		fail(
			"PLN_METHOD_NOT_ADMISSIBLE",
			f"{method} does not meet its mandatory conditions for {money(planned_value)} of {category.lower()}.",
			{"field": "procurement_method", "failed_conditions": outcome["failed"], "results": outcome["results"]},
		)
	return outcome


def low_value_cap(reference: dict[str, Any], category: str) -> float:
	for row in reference.get("threshold_matrix", []):
		if row["procurement_category"] == category and row["procurement_method"] == "Low Value Procurement":
			return flt(row["max_amount"])
	return 0.0


def open_tender_threshold(reference: dict[str, Any], category: str) -> float:
	"""The highest capped band for the category — above it only the uncapped
	methods (open tender and its peers) remain admissible."""
	caps = [flt(r["max_amount"]) for r in reference.get("threshold_matrix", []) if r["procurement_category"] == category and flt(r["max_amount"]) > 0]
	return max(caps) if caps else 0.0


# --------------------------------------------------------------------------
# Planned designation (v1.18 §5.5.3.2): a governed catalogue choice, no
# ranking, no override
# --------------------------------------------------------------------------


def reservation_categories(reference: dict[str, Any]) -> list[dict[str, Any]]:
	rows = reference.get("reservation", {}).get("categories", [])
	if rows:
		return rows
	return [{"category": NONE_RESERVATION, "is_regional": False}]


# --------------------------------------------------------------------------
# Item contents (invariant 24b; PLN-AC-089/121)
# --------------------------------------------------------------------------


def contents_gaps(item) -> list[str]:
	gaps = []
	if cstr(item.get("plan_horizon")) not in PLAN_HORIZONS:
		gaps.append("plan_horizon")
	if cstr(item.get("aggregation_indicator")) not in AGGREGATION_INDICATORS:
		gaps.append("aggregation_indicator")
	if cstr(item.get("lotting_indicator")) not in LOTTING_INDICATORS:
		gaps.append("lotting_indicator")
	if item.get("lotting_indicator") == "Packaged into lots" and int(item.get("lot_count") or 0) <= 0:
		gaps.append("lot_count")
	return gaps


# --------------------------------------------------------------------------
# Version-level readiness (PLN-DES-07 card)
# --------------------------------------------------------------------------


def _allocations(item_name: str) -> list:
	return frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item_name, "allocation_state": ("in", ("Draft", "Active"))},
		fields=["name", "dpp_entry", "budget_line", "indicative_amount", "required_by_date", "quantity", "unit"],
		order_by="creation asc",
	)


def item_value(item_name: str) -> float:
	return sum(flt(a.indicative_amount) for a in _allocations(item_name))


def line_totals(version_name: str) -> dict[str, float]:
	"""Per-Procurement-Budget-Line planned totals for the whole Version — the
	input to `check_plan_affordability` (§7.3)."""
	items = frappe.get_all("Annual Plan Item", filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")}, pluck="name")
	totals: dict[str, float] = {}
	for a in frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": ("in", items or ("",)), "allocation_state": ("in", ("Draft", "Active"))},
		fields=["budget_line", "indicative_amount"],
	):
		totals[a.budget_line] = totals.get(a.budget_line, 0.0) + flt(a.indicative_amount)
	return totals


def line_totals_hash(totals: dict[str, float]) -> str:
	import hashlib
	import json

	return hashlib.sha256(json.dumps({k: f"{v:.2f}" for k, v in sorted(totals.items())}).encode()).hexdigest()[:32]


def reservation_allocations(version_name: str, fiscal_year: str, reference: dict[str, Any] | None = None) -> dict[str, Any]:
	"""§5.5.3.1 — each obligation with its own calculation. The denominator
	is the complete approved annual procurement budget from Budget & Funding
	(exact Version), never the Plan total or the lines the Plan uses. Money
	is exact Decimal at the boundary; amounts are returned as decimal strings."""
	from decimal import Decimal

	from kentender_procurement.procurement_planning.services import budget_gateway, money as money_boundary, profiles

	reference = reference if reference is not None else reference_for(fiscal_year)
	rules = reference.get("reservation", {}) or {}
	target = rules.get("target_percent")
	county_target = rules.get("county_target_percent")
	is_county = bool(frappe.db.get_single_value("Site Procuring Entity", "entity_is_county"))
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")},
		fields=["name", "plan_item_id", "reservation_category", "county_resident_reservation"],
	)
	plan_total = qualifying = county_qualifying = Decimal(0)
	qualifying_items, county_items = [], []
	for item in items:
		value = money_boundary.sum_money(a.indicative_amount for a in _allocations(item.name))
		plan_total += value
		if cstr(item.reservation_category) and item.reservation_category != NONE_RESERVATION:
			qualifying += value
			qualifying_items.append(item.plan_item_id)
		if item.county_resident_reservation:
			county_qualifying += value
			county_items.append(item.plan_item_id)
	basis = budget_gateway.annual_budget_basis(fiscal_year)
	annual = money_boundary.parse_money(basis.get("annual_approved_amount"), allow_zero=True, allow_blank=True) if basis.get("available") else None
	required = (annual * Decimal(str(target)) / Decimal(100)).quantize(Decimal("0.01")) if (annual is not None and target) else None
	shortfall = max(Decimal(0), required - qualifying) if required is not None else None
	county_required = (annual * Decimal(str(county_target)) / Decimal(100)).quantize(Decimal("0.01")) if (annual is not None and county_target and is_county) else None
	county_shortfall = max(Decimal(0), county_required - county_qualifying) if county_required is not None else None
	verified = cstr(reference.get("verification_status")) in profiles.VERIFIED_STATUSES
	fmt = money_boundary.money_text
	return {
		"plan_total": fmt(plan_total),
		"qualifying": fmt(qualifying),
		"qualifying_items": qualifying_items,
		"percent_of_plan": float((qualifying / plan_total * 100) if plan_total else 0),
		"percent_of_annual": float((qualifying / annual * 100) if annual else 0),
		"target_percent": target,
		"required": fmt(required) if required is not None else "",
		"shortfall": fmt(shortfall) if shortfall is not None else "",
		"met": bool(required is not None and shortfall == 0),
		"mandatory": bool(target),
		"verified": verified,
		"basis": {
			"available": bool(basis.get("available")),
			"annual_approved_amount": fmt(annual) if annual is not None else "",
			"budget_reference": basis.get("budget_reference", ""),
			"version_reference": basis.get("version_reference", ""),
			"budget_version": basis.get("budget_version", ""),
			"rule_version": reference.get("version", "") or reference.get("name", ""),
			"verification_status": cstr(reference.get("verification_status")),
		},
		"county": {
			"applicable": is_county,
			"target_percent": county_target,
			"qualifying": fmt(county_qualifying),
			"qualifying_items": county_items,
			"required": fmt(county_required) if county_required is not None else "",
			"shortfall": fmt(county_shortfall) if county_shortfall is not None else "",
			"met": bool(county_required is not None and county_shortfall == 0),
		},
		# retained for the transitional readers of the v1.12 share
		"percent": float((qualifying / plan_total * 100) if plan_total else 0),
		"county_percent": float((county_qualifying / plan_total * 100) if plan_total else 0),
	}


def splitting_advisory(version_name: str, reference: dict[str, Any]) -> list[dict[str, Any]]:
	"""Invariant 26 — items sharing one Procurement Budget Line and
	requirement type, each below the open-tender threshold for their
	category, whose combined value exceeds it."""
	if not reference.get("available"):
		return []
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")},
		fields=["name", "plan_item_id", "title", "requirement_type", "procurement_category"],
	)
	groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
	for item in items:
		allocations = _allocations(item.name)
		lines = {a.budget_line for a in allocations}
		if len(lines) != 1:
			continue
		value = sum(flt(a.indicative_amount) for a in allocations)
		threshold = open_tender_threshold(reference, cstr(item.procurement_category) or "Services")
		if not threshold or value > threshold:
			continue
		groups.setdefault((next(iter(lines)), cstr(item.requirement_type)), []).append(
			{"plan_item_id": item.plan_item_id, "title": item.title, "value": value, "threshold": threshold}
		)
	advisories = []
	for (line, requirement_type), members in groups.items():
		if len(members) < 2:
			continue
		combined = sum(m["value"] for m in members)
		threshold = members[0]["threshold"]
		if combined > threshold:
			advisories.append(
				{
					"budget_line": line,
					"requirement_type": requirement_type,
					"items": [m["plan_item_id"] for m in members],
					"combined_value": combined,
					"threshold": threshold,
					"text": (
						f"{len(members)} Plan Items on {line} ({requirement_type}) each fall below {money(threshold)} "
						f"but total {money(combined)}. Confirm they are legitimately separate or aggregate them."
					),
				}
			)
	return advisories


def item_blockers(item, allocations: list, fiscal_year: str, *, objective_eligible: bool, stage: str = "pre_finance") -> list[dict[str, Any]]:
	"""Exact per-item blockers, each bound to a field. `pre_finance` (§5.6.4):
	package, classification, Strategy, designation, structure and a valid
	calculable schedule. `submission` adds the verified method/schedule
	profiles, complete method evidence and the feasibility gate."""
	from kentender_procurement.procurement_planning.services import profiles

	blockers: list[dict[str, Any]] = []
	if not objective_eligible:
		blockers.append({"code": "PLN_OBJECTIVE_INELIGIBLE", "field": "strategic_objective"})
	if not cstr(item.get("reservation_category")):
		blockers.append({"code": "PLN_RESERVATION_REQUIRED", "field": "reservation_category"})
	for gap in contents_gaps(item):
		blockers.append({"code": "PLN_PLAN_CONTENTS_INCOMPLETE", "field": gap})
	if len(allocations) > 1 and not (20 <= len(cstr(item.get("aggregation_reason")).strip()) <= 500):
		blockers.append({"code": "PLN_ENTRY_INCOMPLETE", "field": "aggregation_reason"})
	if not (20 <= len(cstr(item.get("estimate_basis")).strip()) <= 1000):
		blockers.append({"code": "PLN_PLAN_CONTENTS_INCOMPLETE", "field": "estimate_basis"})
	if not cstr(item.get("estimate_basis_reference")).strip():
		blockers.append({"code": "PLN_PLAN_CONTENTS_INCOMPLETE", "field": "estimate_basis_reference"})
	value = sum(flt(a.indicative_amount) for a in allocations)
	category = cstr(item.get("procurement_category")) or "Services"
	resolved = method_profile_for(item, fiscal_year)
	method_profile, schedule_profile = resolved["method"], resolved["schedule"]
	if "method" in resolved["unresolved"] or not method_profile.get("found"):
		blockers.append({"code": "PLN_REFERENCE_UNAVAILABLE", "field": "procurement_method"})
	else:
		outcome = profiles.method_conditions(method_profile, procurement_category=category, planned_value=value, evidence_rows=item_evidence(item))
		if not outcome["admissible"]:
			blockers.append({"code": "PLN_METHOD_NOT_ADMISSIBLE", "field": "procurement_method"})
		if stage == "submission":
			if not outcome["evidence_complete"]:
				blockers.append({"code": "PLN_METHOD_EVIDENCE_REQUIRED", "field": "method_condition_evidence"})
			if not profiles.is_verified(method_profile):
				blockers.append({"code": "PLN_REFERENCE_UNAVAILABLE", "field": "method_profile_version"})
	if "schedule" in resolved["unresolved"] or not schedule_profile.get("found"):
		blockers.append({"code": "PLN_REFERENCE_UNAVAILABLE", "field": "schedule_profile_version"})
	elif stage == "submission" and (not schedule_profile.get("complete") or not profiles.is_verified(schedule_profile)):
		blockers.append({"code": "PLN_REFERENCE_UNAVAILABLE", "field": "schedule_profile_version"})
	delivery_days = item_delivery_days(item)
	if delivery_days is None:
		blockers.append({"code": "PLN_DELIVERY_PERIOD_REQUIRED", "field": "estimated_delivery_period_days"})
	if not schedule.baseline_complete(item, schedule_profile):
		blockers.append({"code": "PLN_SCHEDULE_INVALID", "field": "baseline_invitation_date"})
	elif delivery_days is not None and not schedule.delivery_boundary_ok({f: item.get(f) for f in schedule.BASELINE_FIELDS}, delivery_days):
		blockers.append({"code": "PLN_DELIVERY_BOUNDARY_INSUFFICIENT", "field": "baseline_invitation_date"})
	return blockers


def item_evidence(item) -> list[dict[str, Any]]:
	import json

	raw = item.get("method_condition_evidence")
	if not raw:
		return []
	try:
		rows = json.loads(raw) if isinstance(raw, str) else raw
	except ValueError:
		return []
	return rows if isinstance(rows, list) else []


def item_period_inputs(item) -> dict[str, Any]:
	"""The entered periods: `period_inputs` (v1.18) with the five legacy
	columns as the fallback for rows saved before it existed."""
	import json

	raw = item.get("period_inputs")
	if raw:
		try:
			data = json.loads(raw) if isinstance(raw, str) else raw
			if isinstance(data, dict):
				return data
		except ValueError:
			pass
	return {f: item.get(f) for f in schedule.PERIOD_FIELDS if item.get(f)}


def item_delivery_days(item) -> int | None:
	"""§5.5.1: zero is an explicit same-day estimate; a missing value is
	missing (the Int column's 0 is not enough — the entered value lives in
	`period_inputs`)."""
	inputs = item_period_inputs(item)
	value = inputs.get("estimated_delivery_period_days")
	if value is None or value == "":
		return None
	try:
		return int(value)
	except (TypeError, ValueError):
		return None


def low_value_cumulative_breaches(version_name: str, reference: dict[str, Any]) -> list[str]:
	"""PLN-AC-104 — the low-value limit is per item per financial year."""
	if not reference.get("available"):
		return []
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version_name, "item_state": ("!=", "Dissolved"), "procurement_method": "Low Value Procurement"},
		fields=["name", "plan_item_id", "title", "procurement_category"],
	)
	totals: dict[tuple[str, str], float] = {}
	members: dict[tuple[str, str], list[str]] = {}
	for item in items:
		key = (cstr(item.procurement_category) or "Services", " ".join(cstr(item.title).lower().split()))
		totals[key] = totals.get(key, 0.0) + item_value(item.name)
		members.setdefault(key, []).append(item.plan_item_id)
	breaches = []
	for key, total in totals.items():
		cap = low_value_cap(reference, key[0])
		if cap and total > cap:
			breaches.extend(members[key])
	return breaches
