# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §5.2/§8.2 — Annual Plan workbench commands.

`FormPlanItems` creates one item per selected source or one compatible
combined item, allocating each source atomically under the Annual Plan
Version row lock (invariant 7). A formed item carries the §4.9 defaults —
category from the accepted classification, Open Tender as the proposed
method (section 91(1)), Single year / Not aggregated (or Aggregated into this
package for a combined item) / Single lot, and the governed schedule periods
— with `reservation_category` deliberately empty until the Planner records
one (invariant 24). `SavePlanItem` saves only the §12.8 allow-list, derives
the seven baseline dates from the anchor and periods (invariant 12), admits a
method only inside the resolved threshold band (invariant 25) and refuses
any edit once `source_correction_required` is true. `DissolvePlanItem`
returns the sources to the unallocated list; Budget balances are untouched
(invariant 21). `ConfirmSplittingAdvisory` records the Planner's
confirmation (owner default O1).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, getdate

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import (
	envelope,
	plan_read,
	readiness,
	references,
	schedule,
	strategy_gateway,
)
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER

PLAN_ITEM_FIELDS = (
	"title", "description", "strategic_objective", "aggregation_reason",
	"plan_horizon", "multi_year_justification", "aggregation_indicator", "lotting_indicator", "lot_count",
	"reservation_category", "reservation_category_reason", "county_resident_reservation",
	"procurement_method",
	"baseline_invitation_date", *schedule.PERIOD_FIELDS,
)


def _authorise(actor: str):
	return authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)


def _item_doc_name(plan_item_id: str) -> str:
	return plan_read.resolve_item_doc_name(plan_item_id)


def _entry_doc(dpp_entry: str, fiscal_year: str, plan_version: str = ""):
	entry = frappe.db.get_value(
		"Departmental Plan Entry",
		dpp_entry,
		["name", "entry_id", "dpp_version", "title", "description", "source_origin", "need", "need_version",
		 "quantity", "unit", "required_by_date", "budget_line", "indicative_amount", "not_proceeding_reason"],
		as_dict=True,
	)
	if not entry or cstr(entry.not_proceeding_reason).strip():
		fail("PLN_SOURCE_UNAVAILABLE")
	dpp_root = frappe.db.get_value(
		"Departmental Plan",
		frappe.db.get_value("Departmental Plan Version", entry.dpp_version, "departmental_plan"),
		["fiscal_year", "organisation_unit", "current_accepted_version"],
		as_dict=True,
	)
	if not dpp_root or dpp_root.fiscal_year != fiscal_year or dpp_root.current_accepted_version != entry.dpp_version:
		fail("PLN_SOURCE_UNAVAILABLE")
	# a live allocation in the version being formed into blocks re-use; rows
	# on a returned predecessor or the Active plan are history, not a claim
	# (a correction/successor copies its own allocations and releases them
	# on dissolve)
	live = {"dpp_entry": entry.name, "allocation_state": ("in", ("Draft", "Active"))}
	if plan_version:
		live["plan_version"] = plan_version
	if frappe.db.exists("Plan Source Allocation", live):
		fail("PLN_SOURCE_UNAVAILABLE")
	entry.organisation_unit = dpp_root.organisation_unit
	return entry


def _entry_budget(entry) -> str:
	return cstr(frappe.db.get_value("Procurement Budget Line", entry.budget_line, "budget"))


def _compatible(entries: list) -> bool:
	"""Invariant 8 — same Fiscal Year (implicit), Procurement Budget (hence
	currency), requirement type, unit and treatment (source origin)."""
	budgets = {_entry_budget(e) for e in entries}
	classifications = {cstr(e.get("classification")) for e in entries}
	units = {e.unit for e in entries}
	origins = {e.source_origin for e in entries}
	return len(budgets) == 1 and len(classifications) == 1 and len(units) == 1 and len(origins) == 1


def _create_item(*, version, plan, entries: list, combined: bool, reference: dict[str, Any], fixture_namespace: str = ""):
	plan_item_id = references.plan_item_id(plan.fiscal_year)
	title = " + ".join(e.title for e in entries)[:160] if combined else entries[0].title
	requirement_type = entries[0].get("classification")
	category = readiness.procurement_category_for(requirement_type)
	periods = schedule.default_periods(reference, category, readiness.OPEN_TENDER)
	delivery = min((getdate(e.required_by_date) for e in entries if e.required_by_date), default=None)
	item = frappe.get_doc(
		{
			"doctype": "Annual Plan Item",
			"plan_item_id": plan_item_id,
			"plan_version": version.name,
			"title": title,
			"description": entries[0].description,
			"requirement_type": requirement_type,
			"procurement_category": category,
			"procurement_method": readiness.OPEN_TENDER if frappe.db.exists("Procurement Method", readiness.OPEN_TENDER) else None,
			"aggregation_reason": "",
			"plan_horizon": "Single year",
			"aggregation_indicator": "Aggregated into this package" if combined else "Not aggregated",
			"lotting_indicator": "Single lot",
			"item_state": "Draft",
			"item_status": "Not started",
			"baseline_delivery_completion_date": delivery,
			**periods,
			"record_version": 0,
			"fixture_namespace": fixture_namespace,
		}
	).insert(ignore_permissions=True)
	for entry in entries:
		frappe.get_doc(
			{
				"doctype": "Plan Source Allocation",
				"allocation_id": references.allocation_id(plan_item_id),
				"plan_item": item.name,
				"plan_item_id": plan_item_id,
				"plan_version": version.name,
				"dpp_entry": entry.name,
				"source_origin": entry.source_origin,
				"need": entry.need or None,
				"need_version": entry.need_version or None,
				"organisation_unit": entry.organisation_unit,
				"quantity": flt(entry.quantity),
				"unit": entry.unit,
				"required_by_date": entry.required_by_date,
				"budget_line": entry.budget_line,
				"indicative_amount": flt(entry.indicative_amount),
				"allocation_state": "Draft",
				"fixture_namespace": fixture_namespace,
			}
		).insert(ignore_permissions=True)
	return item


def _mark_funding_changed(version) -> None:
	"""§4.11 — a change to the plan's per-line totals makes a prior funding
	confirmation Stale; an open request is cancelled and must be repeated."""
	if version.funding_state == "Confirmed":
		frappe.db.set_value("Annual Plan Version", version.name, "funding_state", "Stale", update_modified=False)
	elif version.funding_state == "Awaiting Finance":
		for task in frappe.get_all("Plan Finance Task", filters={"plan_version": version.name, "status": "Open"}, pluck="name"):
			frappe.db.set_value("Plan Finance Task", task, "status", "Cancelled", update_modified=False)
		frappe.db.set_value("Annual Plan Version", version.name, "funding_state", "Not requested", update_modified=False)


def form_plan_items(
	*, plan_version: str, dpp_entries: list[str] | str, mode: str = "each", expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = authz.actor(user)
	if isinstance(dpp_entries, str):
		dpp_entries = json.loads(dpp_entries)
	dpp_entries = [cstr(e) for e in dpp_entries if cstr(e)]
	payload = {"plan_version": plan_version, "dpp_entries": sorted(dpp_entries), "mode": mode}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not dpp_entries:
		fail("PLN_ENTRY_INCOMPLETE", "Select at least one accepted departmental entry to form a Plan Item.")

	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise(actor)
	if version.version_status != "Draft":
		fail("PLN_STALE_WRITE")
	envelope.check_record_version(version, expected_record_version)
	reference = readiness.reference_for(plan.fiscal_year)

	entries = []
	for name in dpp_entries:
		entry = _entry_doc(name, plan.fiscal_year, version.name)
		entry["classification"] = plan_read._classifications(entry.dpp_version).get(entry.entry_id, "")
		entries.append(entry)

	if len(entries) == 1:
		item = _create_item(version=version, plan=plan, entries=entries, combined=False, reference=reference, fixture_namespace=cstr(plan.fixture_namespace))
		created = [item.plan_item_id]
	elif mode == "each":
		created = []
		for entry in entries:
			item = _create_item(version=version, plan=plan, entries=[entry], combined=False, reference=reference, fixture_namespace=cstr(plan.fixture_namespace))
			created.append(item.plan_item_id)
	elif mode == "combined":
		if not _compatible(entries):
			fail("PLN_SOURCE_INCOMPATIBLE")
		item = _create_item(version=version, plan=plan, entries=entries, combined=True, reference=reference, fixture_namespace=cstr(plan.fixture_namespace))
		created = [item.plan_item_id]
	else:
		fail("PLN_ENTRY_INCOMPLETE", "Choose whether to create one Plan Item for each entry or one combined Plan Item.")

	_mark_funding_changed(version)
	envelope.bump(version)
	result = {"ok": True, "idempotent": False, "action": "formed", "created_items": created, "single": len(created) == 1}
	envelope.record_command(
		idempotency_key=idempotency_key, command="FormPlanItems", payload=payload, result=result,
		document_type="Annual Plan Version", document_name=version.name, actor=actor,
		fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


def dissolve_plan_item(*, plan_item: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"plan_item": plan_item}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	item = envelope.locked("Annual Plan Item", _item_doc_name(plan_item))
	version = envelope.locked("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise(actor)
	if item.item_state != "Draft" or version.version_status != "Draft":
		fail("PLN_DISSOLUTION_BLOCKED")
	envelope.check_record_version(item, expected_record_version)

	frappe.db.set_value(
		"Plan Source Allocation",
		{"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
		"allocation_state", "Released", update_modified=False,
	)
	envelope.bump(item, item_state="Dissolved")
	_mark_funding_changed(version)
	result = {"ok": True, "idempotent": False, "action": "dissolved", "plan_item": item.plan_item_id}
	envelope.record_command(
		idempotency_key=idempotency_key, command="DissolvePlanItem", payload=payload, result=result,
		document_type="Annual Plan Item", document_name=item.name, actor=actor,
		fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def _validate_reservation(reference: dict[str, Any], values: dict[str, Any]) -> tuple[str, str]:
	category = cstr(values.get("reservation_category")).strip()
	reason = cstr(values.get("reservation_category_reason")).strip()
	if not category:
		return "", ""
	allowed = {row["category"] for row in readiness.reservation_categories(reference)}
	if category not in allowed:
		fail("PLN_ENTRY_INCOMPLETE", "Select a governed preference and reservation category.", {"field": "reservation_category"})
	# Invariant 24aa — a scheme other than the server's highest-advantage
	# proposal needs a retained reason. `None` is an explicit choice.
	proposal = readiness.highest_advantage(reference)
	if category not in (proposal, readiness.NONE_RESERVATION) and not (10 <= len(reason) <= 500):
		fail(
			"PLN_ENTRY_INCOMPLETE",
			f"State why {category} is recorded instead of the higher-advantage scheme {proposal} (10–500 characters).",
			{"field": "reservation_category_reason"},
		)
	return category, reason if category not in (proposal, readiness.NONE_RESERVATION) else ""


def save_plan_item(*, plan_item: str, values: dict[str, Any] | str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if isinstance(values, str):
		values = json.loads(values)
	unknown = set(values) - set(PLAN_ITEM_FIELDS)
	if unknown:
		if unknown & (set(schedule.BASELINE_FIELDS) - {"baseline_invitation_date"}):
			fail("PLN_SCHEDULE_INVALID", "Baseline milestone dates are derived, never entered.", {"fields": sorted(unknown)})
		if unknown & set(schedule.ACTUAL_FIELDS):
			fail("PLN_ACTUAL_NOT_WRITABLE")
		if unknown & set(schedule.FORECAST_FIELDS):
			fail("PLN_SCHEDULE_INVALID", "Forecast dates change only through the cascade commands.", {"fields": sorted(unknown)})
		fail("PLN_ENTRY_INCOMPLETE", f"Plan Item input is limited to the defined allow-list; unexpected: {sorted(unknown)}.")
	payload = {"plan_item": plan_item, **{k: cstr(values.get(k)) for k in PLAN_ITEM_FIELDS}}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	item = envelope.locked("Annual Plan Item", _item_doc_name(plan_item))
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise(actor)
	if item.item_state != "Draft" or version.version_status != "Draft":
		if version.version_status != "Draft" and any(k in values for k in ("baseline_invitation_date", *schedule.PERIOD_FIELDS)):
			fail("PLN_BASELINE_LOCKED")
		fail("PLN_STALE_WRITE")
	if version.funding_state == "Awaiting Finance":
		fail("PLN_STALE_WRITE", "The Plan Version is awaiting Finance confirmation. Wait for the decision before editing.")
	envelope.check_record_version(item, expected_record_version)

	allocations = readiness._allocations(item.name)
	if any(plan_read.source_correction_required(a.dpp_entry) for a in allocations):
		fail("PLN_SOURCE_CORRECTION_REQUIRED")
	reference = readiness.reference_for(plan.fiscal_year)
	planned_value = sum(flt(a.indicative_amount) for a in allocations)

	title = cstr(values.get("title", item.title)).strip()
	description = cstr(values.get("description", item.description)).strip()
	if not (5 <= len(title) <= 160):
		fail("PLN_ENTRY_INCOMPLETE", "Plan Item title must be 5-160 characters.", {"field": "title"})
	if not (10 <= len(description) <= 1000):
		fail("PLN_ENTRY_INCOMPLETE", "Procurement description must be 10-1,000 characters.", {"field": "description"})
	aggregation_reason = cstr(values.get("aggregation_reason", item.aggregation_reason)).strip()
	combined = len(allocations) > 1
	if aggregation_reason and not (20 <= len(aggregation_reason) <= 500):
		fail("PLN_ENTRY_INCOMPLETE", "Aggregation reason must be 20-500 characters when provided.", {"field": "aggregation_reason"})
	if not combined:
		aggregation_reason = ""

	updates: dict[str, Any] = {"title": title, "description": description, "aggregation_reason": aggregation_reason}

	# regulation 41 contents (invariant 24b)
	for field, allowed in (("plan_horizon", readiness.PLAN_HORIZONS), ("aggregation_indicator", readiness.AGGREGATION_INDICATORS), ("lotting_indicator", readiness.LOTTING_INDICATORS)):
		if field in values:
			if cstr(values[field]) not in allowed:
				fail("PLN_PLAN_CONTENTS_INCOMPLETE", detail={"field": field})
			updates[field] = cstr(values[field])
	if "multi_year_justification" in values:
		updates["multi_year_justification"] = cstr(values["multi_year_justification"]).strip()
	if "lot_count" in values:
		updates["lot_count"] = int(values["lot_count"] or 0)
	horizon = updates.get("plan_horizon", item.plan_horizon)
	if horizon == "Multi-year" and not (20 <= len(cstr(updates.get("multi_year_justification", item.multi_year_justification)).strip()) <= 500):
		fail("PLN_PLAN_CONTENTS_INCOMPLETE", "A multi-year horizon needs its justification (20–500 characters).", {"field": "multi_year_justification"})
	if horizon != "Multi-year":
		updates["multi_year_justification"] = ""
	lotting = updates.get("lotting_indicator", item.lotting_indicator)
	if lotting == "Packaged into lots" and int(updates.get("lot_count", item.lot_count) or 0) <= 0:
		fail("PLN_PLAN_CONTENTS_INCOMPLETE", "State the intended number of lots.", {"field": "lot_count"})
	if lotting != "Packaged into lots":
		updates["lot_count"] = 0

	# preference and reservation (invariants 24, 24aa, 24a)
	if "reservation_category" in values or "reservation_category_reason" in values:
		category, reason = _validate_reservation(
			reference,
			{"reservation_category": values.get("reservation_category", item.reservation_category), "reservation_category_reason": values.get("reservation_category_reason", item.reservation_category_reason)},
		)
		updates["reservation_category"], updates["reservation_category_reason"] = category, reason
	if "county_resident_reservation" in values:
		is_county = bool(frappe.db.get_single_value("Site Procuring Entity", "entity_is_county"))
		updates["county_resident_reservation"] = 1 if (is_county and values["county_resident_reservation"] in (True, 1, "1", "true", "True")) else 0
	funding_source = ""
	if allocations:
		funding_source = cstr(frappe.db.get_value("Procurement Budget Line Version", {"budget_line": allocations[0].budget_line}, "funding_source"))
	updates["exclusive_preference"] = 1 if readiness.exclusive_preference_applies(reference, cstr(item.procurement_category), planned_value, funding_source) else 0

	# procurement method within the resolved band (invariant 25)
	if "procurement_method" in values:
		method = cstr(values["procurement_method"]).strip()
		if method and not frappe.db.exists("Procurement Method", {"name": method, "status": "Active"}):
			fail("PLN_METHOD_NOT_ADMISSIBLE", f"{method} is not a governed procurement method.", {"field": "procurement_method"})
		band = readiness.require_method_admissible(reference, cstr(item.procurement_category) or "Services", planned_value, method)
		updates["procurement_method"] = method or band["proposed_method"]
		updates["threshold_band_at_readiness"] = band["band_label"]

	# baseline schedule (invariant 12; PLN-AC-114/115)
	periods = {f: values.get(f, item.get(f)) for f in schedule.PERIOD_FIELDS}
	anchor = values.get("baseline_invitation_date", item.baseline_invitation_date)
	delivery = min((getdate(a.required_by_date) for a in allocations if a.required_by_date), default=None)
	baseline = schedule.derive_baseline(anchor or None, periods, delivery)
	updates.update({f: int(periods[f]) for f in schedule.PERIOD_FIELDS})
	updates.update(baseline)

	objective_id = cstr(values.get("strategic_objective", item.strategic_objective)).strip()
	if objective_id and objective_id != cstr(item.strategic_objective):
		snapshot = strategy_gateway.snapshot_objective(objective_id=objective_id, correlation_key=f"{item.plan_item_id}:{idempotency_key}")
		updates.update(
			strategic_objective=objective_id, objective_path=snapshot["path_display"],
			strategy_plan=snapshot["strategy_plan"], strategy_plan_version=snapshot["strategy_plan_version"],
		)
	elif not objective_id:
		updates.update(strategic_objective=None, objective_path="", strategy_plan=None, strategy_plan_version=None)

	envelope.bump(item, **updates)
	result = {"ok": True, "idempotent": False, "action": "saved", "plan_item": item.plan_item_id, "record_version": int(item.record_version or 0)}
	envelope.record_command(
		idempotency_key=idempotency_key, command="SavePlanItem", payload=payload, result=result,
		document_type="Annual Plan Item", document_name=item.name, actor=actor,
		fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def confirm_splitting_advisory(*, plan_version: str, confirmation: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""Invariant 26 / PLN-AC-074 — record the Planner's confirmation that the
	flagged items are legitimately separate (a preference-scheme unbundling
	under regulation 154 counts as such). Never auto-aggregates."""
	actor = authz.actor(user)
	confirmation = cstr(confirmation).strip()
	payload = {"plan_version": plan_version, "confirmation": confirmation}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not (10 <= len(confirmation) <= 500):
		fail("PLN_ENTRY_INCOMPLETE", "State the confirmation (10–500 characters).", {"field": "splitting_confirmation"})
	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise(actor)
	if version.version_status != "Draft":
		fail("PLN_STALE_WRITE")
	envelope.check_record_version(version, expected_record_version)
	envelope.bump(version, splitting_confirmation=confirmation)
	result = {"ok": True, "idempotent": False, "action": "splitting_confirmed", "record_version": int(version.record_version or 0)}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ConfirmSplittingAdvisory", payload=payload, result=result,
		document_type="Annual Plan Version", document_name=version.name, actor=actor,
		fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result
