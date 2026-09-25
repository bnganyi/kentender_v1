# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.3 / §5.6 — Plan readiness.

Readiness is an exact blocker list, never a score. Pre-Finance (§5.6.4):
every item has an Objective, a planned designation, the contents, an
estimate basis, an estimated delivery period and a calculable schedule
from its resolved schedule profile. Formal submission adds: verified method
and schedule profiles in force (no Open Tender fallback), the method's
mandatory conditions and evidence, feasibility against the source boundary,
and the planned reservation allocations against the **eligible value of the
current complete plan Version** (PLN v1.25 §5.5.3.1 — never the approved
budget, which is only the funding ceiling). Advisory: the contract-splitting assessment, which the
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

NONE_RESERVATION = "None"
# PLN v1.25 / RES-IMP-001 §1.1 — the planned base designations. County
# residents is a separate measure, not a fifth category; the governed
# catalogue's other entries are not Planning designations.
BASE_RESERVATION_CATEGORIES = (NONE_RESERVATION, "Youth", "Women", "Persons with disabilities")
INCLUDED = "Included"
NO_ADDITIONAL_RESTRICTION = "No additional restriction applies"
# PLN-CHG-001 v1.18 §4.6 — a fixed literal; unsupported horizons are rejected (PLN_MULTI_YEAR_UNSUPPORTED)
PLAN_HORIZONS = ("Single year",)
AGGREGATION_INDICATORS = ("Not aggregated", "Aggregated into this package", "Common-user item arrangement")
LOTTING_INDICATORS = ("Single lot", "Packaged into lots")
OPEN_TENDER = "Open Tender"


# PLN-CHG-001 v1.23 §4.4 — category derivation moved to
# `dpp_classification.category_for`, which reads the governed Requirement Type
# catalogue. The local `CATEGORY_BY_TYPE` mapping that used to live here was a
# hard-coded substitute for that catalogue and silently defaulted anything it
# did not recognise to Services.


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
	"""The base designations the governed catalogue carries, in their fixed
	order. Nothing outside `BASE_RESERVATION_CATEGORIES` is offered or
	accepted, whatever else the catalogue lists."""
	rows = {r.get("category"): r for r in reference.get("reservation", {}).get("categories", [])}
	base = [rows[c] for c in BASE_RESERVATION_CATEGORIES if c in rows]
	return base or [{"category": NONE_RESERVATION, "is_regional": False}]


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


def item_applicability(item, rules: dict[str, Any]) -> tuple[str, str]:
	"""Whether one Plan Item counts towards the reservation measure, and why.

	The single place exclusions belong. The verified rule in force names no
	exclusions, so every current purchase is included under it; a rule that
	later names some (by category, method or funding) is applied here, and
	the excluded row keeps its reason — it never silently leaves the plan
	(PLN25-AC-003)."""
	return INCLUDED, "Counted: the reservation rule includes all planned procurement"


def measure_row(plan_item_id: str, title: str, value, designation: str, applicability: str = INCLUDED, reason: str = "") -> dict[str, Any]:
	return {
		"plan_item_id": plan_item_id,
		"title": title,
		"value": value,
		"applicability": applicability,
		"reason": reason,
		"designation": cstr(designation) or NONE_RESERVATION,
	}


def reservation_measure(rows: list[dict[str, Any]], target_percent) -> dict[str, Any]:
	"""PLN v1.25 §5.5.3.1, in exact Decimal:

	eligible  = sum of the included purchases' estimated values
	required  = target% × eligible
	remaining = max(required − qualifying, 0)
	share     = qualifying ÷ eligible, to two places

	Sets each row's own `qualifying` amount. `target_percent` None means no
	published target: required and remaining are None."""
	from decimal import ROUND_HALF_UP, Decimal

	cent = Decimal("0.01")
	eligible = qualifying = Decimal(0)
	for row in rows:
		included = row["applicability"] == INCLUDED
		counts = included and row["designation"] != NONE_RESERVATION
		row["qualifying"] = row["value"] if counts else Decimal(0)
		if included:
			eligible += row["value"]
		qualifying += row["qualifying"]
	required = (eligible * Decimal(str(target_percent)) / Decimal(100)).quantize(cent, ROUND_HALF_UP) if target_percent else None
	return {
		"eligible": eligible.quantize(cent),
		"qualifying": qualifying.quantize(cent),
		"required": required,
		"remaining": max(Decimal(0), required - qualifying).quantize(cent) if required is not None else None,
		"share": (qualifying / eligible * 100).quantize(cent, ROUND_HALF_UP) if eligible else Decimal("0.00"),
	}


def rule_version_label(reference: dict[str, Any]) -> str:
	if not reference.get("reference"):
		return ""
	number = reference.get("version_number")
	return f"Reservation rules, Version {number}" if number else "Reservation rules"


def reservation_allocations(version_name: str, fiscal_year: str, reference: dict[str, Any] | None = None) -> dict[str, Any]:
	"""The plan-level reservation measure for one Plan Version (PLN v1.25
	§5.5.3.1 / §7.3 reservation-measure resolver).

	The denominator is the eligible value of this exact current plan
	Version — the purchases the rule includes, each listed with its reason —
	never the approved annual budget. The budget authorises spending; it
	does not oblige it, and measuring against it once turned unused
	headroom into a compulsory target (a KES 464,980 plan under a KES
	160,000,000 ceiling was asked for KES 48,000,000). The ceiling's own job
	belongs to the affordability check, and no Budget contract is read here.

	The result names the Plan Version and rule Version it was made under;
	frozen at submission into the Version's snapshot, it is that Version's
	immutable calculation. County residents is a separate measure with its
	own target. Amounts are decimal strings."""
	from decimal import Decimal

	from kentender_procurement.procurement_planning.services import money as money_boundary, profiles

	reference = reference if reference is not None else reference_for(fiscal_year)
	rules = reference.get("reservation", {}) or {}
	target = rules.get("target_percent")
	county_target = rules.get("county_target_percent")
	is_county = bool(frappe.db.get_single_value("Site Procuring Entity", "entity_is_county"))
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")},
		fields=["name", "plan_item_id", "title", "reservation_category", "county_resident_reservation"],
		order_by="creation asc",
	)
	rows, county_rows = [], []
	for item in items:
		value = money_boundary.sum_money(a.indicative_amount for a in _allocations(item.name))
		applicability, reason = item_applicability(item, rules)
		rows.append(measure_row(item.plan_item_id, cstr(item.title), value, item.reservation_category, applicability, reason))
		# County residents: its own measure over the same included purchases.
		county_rows.append(measure_row(item.plan_item_id, "", value, "County" if item.county_resident_reservation else NONE_RESERVATION, applicability, reason))
	measure = reservation_measure(rows, target)
	county = reservation_measure(county_rows, county_target if is_county else None)
	version = frappe.db.get_value("Annual Plan Version", version_name, ["annual_plan", "version_number"], as_dict=True) or {}
	plan_reference = frappe.db.get_value("Annual Plan", version.get("annual_plan"), "plan_reference") if version.get("annual_plan") else ""
	verified = cstr(reference.get("verification_status")) in profiles.VERIFIED_STATUSES
	fmt = money_boundary.money_text
	required, remaining = measure["required"], measure["remaining"]
	return {
		"plan_basis": f"{plan_reference}, Version {version.get('version_number')}" if plan_reference else "",
		"rule_reference": cstr(reference.get("reference")),
		"rule_version": rule_version_label(reference),
		"verification_status": cstr(reference.get("verification_status")),
		"plan_total": fmt(sum((r["value"] for r in rows), Decimal(0))),
		"eligible_value": fmt(measure["eligible"]),
		"qualifying": fmt(measure["qualifying"]),
		"qualifying_items": [r["plan_item_id"] for r in rows if r["qualifying"]],
		"qualifying_share_percent": fmt(measure["share"]),
		"target_percent": target,
		"required": fmt(required) if required is not None else "",
		"remaining": fmt(remaining) if remaining is not None else "",
		"met": bool(required is not None and remaining == 0),
		"mandatory": bool(target),
		"verified": verified,
		"mandatory_restrictions": NO_ADDITIONAL_RESTRICTION,
		"items": [{**r, "value": fmt(r["value"]), "qualifying": fmt(r["qualifying"])} for r in rows],
		"county": {
			"applicable": is_county,
			"target_percent": county_target,
			"qualifying": fmt(county["qualifying"]),
			"qualifying_items": [r["plan_item_id"] for r in county_rows if r["qualifying"]],
			"required": fmt(county["required"]) if county["required"] is not None else "",
			"remaining": fmt(county["remaining"]) if county["remaining"] is not None else "",
			"met": bool(county["required"] is not None and county["remaining"] == 0),
		},
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
	submission = stage == "submission"
	# PLN v1.27 D2 (§5.6 item 4): every purchase needs a selected method before
	# the funding request — it is purchase content, so an unselected method is
	# `PLN_PLAN_CONTENTS_INCOMPLETE` on that purchase, never a missing rule or
	# setting. It used to surface as `PLN_REFERENCE_UNAVAILABLE`, which the
	# issue list then suppressed as panel-owned, so the refusal blamed "the
	# setting shown" for a purchase that simply had no method yet.
	method_selected = bool(cstr(item.get("procurement_method")).strip())
	if not method_selected:
		blockers.append({"code": "PLN_PLAN_CONTENTS_INCOMPLETE", "field": "procurement_method"})
	elif "method" in resolved["unresolved"] or not method_profile.get("found"):
		# A selected method whose profile is missing or unverified blocks only
		# Sign and submit Annual Plan (§5.5.1, §5.5.3.3).
		if submission:
			blockers.append({"code": "PLN_REFERENCE_UNAVAILABLE", "field": "procurement_method"})
	elif submission:
		# Method conditions and their evidence gate submission, not the funding
		# request: §5.5.3.3 permits Draft work and blocks submission where the
		# method's eligibility or evidence is incomplete.
		outcome = profiles.method_conditions(method_profile, procurement_category=category, planned_value=value, evidence_rows=item_evidence(item))
		if not outcome["admissible"]:
			blockers.append({"code": "PLN_METHOD_NOT_ADMISSIBLE", "field": "procurement_method"})
		if not outcome["evidence_complete"]:
			blockers.append({"code": "PLN_METHOD_EVIDENCE_REQUIRED", "field": "method_condition_evidence"})
		if not profiles.is_verified(method_profile):
			blockers.append({"code": "PLN_REFERENCE_UNAVAILABLE", "field": "method_profile_version"})
	# The schedule is calculated from the method's profile, so it can only be
	# assessed once a method with a found schedule profile exists. Before that
	# it is not a separate failure (the U07 BASE Schedule result: "calculated
	# once a procurement method is chosen").
	schedule_calculable = method_selected and "schedule" not in resolved["unresolved"] and bool(schedule_profile.get("found"))
	if not schedule_calculable:
		if submission and method_selected:
			blockers.append({"code": "PLN_REFERENCE_UNAVAILABLE", "field": "schedule_profile_version"})
	elif submission and (not schedule_profile.get("complete") or not profiles.is_verified(schedule_profile)):
		blockers.append({"code": "PLN_REFERENCE_UNAVAILABLE", "field": "schedule_profile_version"})
	delivery_days = item_delivery_days(item)
	if delivery_days is None:
		blockers.append({"code": "PLN_DELIVERY_PERIOD_REQUIRED", "field": "estimated_delivery_period_days"})
	if schedule_calculable:
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
