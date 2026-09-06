# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §5.3 invariants 24–26 / §7.5 — Plan readiness.

Readiness is an exact blocker list, never a score (§1.1). Blocking: every
item has an Objective, a reservation category, the regulation 41 contents,
a complete baseline that meets the governed periods and the delivery
boundary, and a method admissible for its planned value under the threshold
matrix in force for the plan's Fiscal Year (fail closed with
`PLN_REFERENCE_UNAVAILABLE` when that matrix is absent). Advisory, never
blocking: the reserved share against the statutory target, the county
resident-tenderer share, and the contract-splitting advisory (section 54(1)),
which the Planner confirms or resolves by aggregation.

Regulator reference data is read from Configuration & Governance's
effective-dated register for the plan's Fiscal Year — never today's (§7.5).
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
PLAN_HORIZONS = ("Single year", "Multi-year")
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
# Threshold matrix (invariant 25; PLN-AC-070/071/091/102/103)
# --------------------------------------------------------------------------


def resolve_band(reference: dict[str, Any], category: str, planned_value: float) -> dict[str, Any]:
	"""The value band and admissible methods for one category and value.

	A method is admissible when its band carries no fixed maximum (funds
	allocated / section conditions) or the planned value is within it. The
	server proposes Open Tender (section 91(1) preferred method) whenever it
	is admissible, which under the Second Schedule is always.
	"""
	if not reference.get("available"):
		return {"available": False, "band_label": "", "admissible_methods": [], "proposed_method": "", "caps": {}}
	rows = [r for r in reference["threshold_matrix"] if r["procurement_category"] == category]
	admissible, caps = [], {}
	for row in rows:
		cap = flt(row["max_amount"])
		caps[row["procurement_method"]] = cap
		if cap <= 0 or flt(planned_value) <= cap:
			admissible.append(row["procurement_method"])
	capped_below = sorted(cap for cap in caps.values() if 0 < cap < flt(planned_value))
	capped_at_or_above = sorted(cap for cap in caps.values() if cap >= flt(planned_value) > 0)
	if capped_below:
		label = f"Above {money(capped_below[-1])}"
	elif capped_at_or_above:
		label = f"Up to {money(capped_at_or_above[0])}"
	else:
		label = "No fixed threshold"
	proposed = OPEN_TENDER if OPEN_TENDER in admissible else (admissible[0] if admissible else "")
	if proposed:
		label = f"{label} · {proposed} admissible"
	# Present the eleven methods in the catalogue's own order.
	catalogue = frappe.get_all("Procurement Method", filters={"status": "Active"}, pluck="name", order_by="creation asc")
	ordered = [m for m in catalogue if m in admissible] + [m for m in admissible if m not in catalogue]
	return {"available": True, "band_label": label, "admissible_methods": ordered, "proposed_method": proposed, "caps": caps}


def require_method_admissible(reference: dict[str, Any], category: str, planned_value: float, method: str) -> dict[str, Any]:
	band = resolve_band(reference, category, planned_value)
	if not band["available"]:
		fail("PLN_REFERENCE_UNAVAILABLE")
	if cstr(method) and cstr(method) not in band["admissible_methods"]:
		fail(
			"PLN_METHOD_NOT_ADMISSIBLE",
			f"{method} is not admissible for {money(planned_value)} ({band['band_label']}). "
			f"Admissible: {', '.join(band['admissible_methods'])}.",
			{"band_label": band["band_label"], "admissible_methods": band["admissible_methods"], "field": "procurement_method"},
		)
	return band


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
# Preference and reservation (invariants 24, 24aa, 24a; §4.9)
# --------------------------------------------------------------------------


def reservation_categories(reference: dict[str, Any]) -> list[dict[str, Any]]:
	rows = reference.get("reservation", {}).get("categories", [])
	if rows:
		return rows
	return [{"category": NONE_RESERVATION, "advantage_rank": 0, "is_regional": False}]


def highest_advantage(reference: dict[str, Any]) -> str:
	"""The server's proposal where more than one scheme could apply (section
	156 / regulation 153): the lowest positive advantage rank."""
	ranked = [r for r in reservation_categories(reference) if int(r.get("advantage_rank") or 0) > 0]
	if not ranked:
		return NONE_RESERVATION
	return sorted(ranked, key=lambda r: (int(r["advantage_rank"]), r["category"]))[0]["category"]


def exclusive_preference_applies(reference: dict[str, Any], category: str, planned_value: float, funding_source: str) -> bool:
	"""Regulation 163 — derived: wholly national/county funding and value
	below KES 1bn (works) or KES 500m (goods/services)."""
	ex = reference.get("exclusive_preference", {})
	if not ex.get("published"):
		return False
	if funding_source and "donor" in funding_source.lower():
		return False
	cap = ex.get("works_amount") if category == "Works" else ex.get("goods_services_amount")
	return bool(cap) and flt(planned_value) < flt(cap)


# --------------------------------------------------------------------------
# Item contents (invariant 24b; PLN-AC-089/121)
# --------------------------------------------------------------------------


def contents_gaps(item) -> list[str]:
	gaps = []
	if cstr(item.get("plan_horizon")) not in PLAN_HORIZONS:
		gaps.append("plan_horizon")
	if item.get("plan_horizon") == "Multi-year" and not (20 <= len(cstr(item.get("multi_year_justification")).strip()) <= 500):
		gaps.append("multi_year_justification")
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


def reserved_share(version_name: str) -> dict[str, Any]:
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")},
		fields=["name", "reservation_category", "county_resident_reservation"],
	)
	total = reserved = county = 0.0
	for item in items:
		value = item_value(item.name)
		total += value
		if cstr(item.reservation_category) and item.reservation_category != NONE_RESERVATION:
			reserved += value
		if item.county_resident_reservation:
			county += value
	pct = (reserved / total * 100.0) if total else 0.0
	county_pct = (county / total * 100.0) if total else 0.0
	return {"total": total, "reserved": reserved, "percent": pct, "county_percent": county_pct}


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


def item_blockers(item, allocations: list, reference: dict[str, Any], *, objective_eligible: bool) -> list[dict[str, str]]:
	"""Exact per-item blockers, each bound to a field (§12.8)."""
	blockers: list[dict[str, str]] = []
	if not objective_eligible:
		blockers.append({"code": "PLN_OBJECTIVE_INELIGIBLE", "field": "strategic_objective"})
	if not cstr(item.get("reservation_category")):
		blockers.append({"code": "PLN_RESERVATION_REQUIRED", "field": "reservation_category"})
	for gap in contents_gaps(item):
		blockers.append({"code": "PLN_PLAN_CONTENTS_INCOMPLETE", "field": gap})
	if len(allocations) > 1 and not (20 <= len(cstr(item.get("aggregation_reason")).strip()) <= 500):
		blockers.append({"code": "PLN_ENTRY_INCOMPLETE", "field": "aggregation_reason"})
	if not schedule.baseline_complete(item):
		blockers.append({"code": "PLN_SCHEDULE_INVALID", "field": "baseline_invitation_date"})
	elif not schedule.delivery_boundary_ok({f: item.get(f) for f in schedule.BASELINE_FIELDS}):
		blockers.append({"code": "PLN_DELIVERY_BOUNDARY_INSUFFICIENT", "field": "baseline_invitation_date"})
	value = sum(flt(a.indicative_amount) for a in allocations)
	band = resolve_band(reference, cstr(item.get("procurement_category")) or "Services", value)
	if not band["available"]:
		blockers.append({"code": "PLN_REFERENCE_UNAVAILABLE", "field": "procurement_method"})
	elif cstr(item.get("procurement_method")) not in band["admissible_methods"]:
		blockers.append({"code": "PLN_METHOD_NOT_ADMISSIBLE", "field": "procurement_method"})
	return blockers


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
