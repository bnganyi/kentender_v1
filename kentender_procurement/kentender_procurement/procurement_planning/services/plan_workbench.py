# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.6 / §7.2 — Annual Plan workbench commands.

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
	dpp_classification,
	envelope,
	plan_read,
	profiles,
	readiness,
	references,
	schedule,
	scope_lock,
	strategy_gateway,
)
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER

PLAN_ITEM_FIELDS = (
	"title", "description", "strategic_objective", "aggregation_reason",
	"plan_horizon", "aggregation_indicator", "lotting_indicator", "lot_count",
	"reservation_category", "county_resident_reservation",
	"procurement_method", "method_condition_evidence",
	"estimate_basis", "estimate_basis_reference",
	"baseline_invitation_date", "period_inputs", "estimated_delivery_period_days", *schedule.PERIOD_FIELDS,
)
VERSION_DETAIL_FIELDS = ("project_name", "change_reason")


def _authorise(actor: str):
	return authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)


def _item_doc_name(plan_item_id: str) -> str:
	return plan_read.resolve_item_doc_name(plan_item_id)


def _entry_doc(dpp_entry: str, fiscal_year: str, plan_version: str = ""):
	entry = frappe.db.get_value(
		"Departmental Plan Entry",
		dpp_entry,
		["name", "entry_id", "dpp_version", "title", "description", "source_origin", "direct_source_id", "need", "need_revision",
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
	# on dissolve). An allocation pinned to an earlier DPP copy of the same
	# unchanged source is the same claim (§7.1).
	live = {"dpp_entry": ("in", plan_read.same_source_lineage(entry.name)), "allocation_state": ("in", ("Draft", "Active"))}
	if plan_version:
		live["plan_version"] = plan_version
	if frappe.db.exists("Plan Source Allocation", live):
		fail("PLN_SOURCE_UNAVAILABLE")
	entry.organisation_unit = dpp_root.organisation_unit
	return entry


def _entry_budget(entry) -> str:
	return cstr(frappe.db.get_value("Procurement Budget Line", entry.budget_line, "budget"))


#: Invariant 8 — the dimensions that must match for sources to become one
#: purchase, and what each one is called where a Planner has to read it. The
#: Fiscal Year is implicit; the Procurement Budget (not the individual line)
#: carries the currency.
COMBINATION_DIMENSIONS: tuple[tuple[str, str], ...] = (
	("budget", "They draw on different budgets."),
	("classification", "They are different requirement types."),
	("unit", "They are measured in different units."),
	("origin", "They come from different kinds of requirement."),
)


def combination_key(entry) -> dict[str, str]:
	"""One source's combinable identity, from the same rule the command
	enforces — so a screen can offer the choice only where the command would
	accept it, and name the actual difference where it would not."""
	return {
		"budget": _entry_budget(entry),
		"classification": cstr(entry.get("classification")),
		"unit": cstr(entry.get("unit")),
		"origin": cstr(entry.get("source_origin")),
	}


def combination_conflicts(entries: list) -> list[str]:
	"""Which of the dimensions actually differ across these sources."""
	keys = [combination_key(e) for e in entries]
	return [
		reason for dimension, reason in COMBINATION_DIMENSIONS
		if len({k[dimension] for k in keys}) > 1
	]


def _compatible(entries: list) -> bool:
	return not combination_conflicts(entries)


def _create_item(*, version, plan, entries: list, combined: bool, fixture_namespace: str = "", combination_reason: str = "", title_override: str = ""):
	"""A formed item carries the §4.6 defaults: category from the accepted
	classification, Open Tender proposed (section 91(1)), Single year / Not
	aggregated (Aggregated for a combined item) / Single lot, the resolved
	schedule profile's default periods where one is in force (no periods
	otherwise — the profile, not a constant, supplies them) and its stable
	`Plan Item` root."""
	plan_item_id = references.plan_item_id(plan.fiscal_year)
	# §10.7 — a combined purchase is named by the Planner who combined it; the
	# joined source titles are only the offered default.
	title = cstr(title_override).strip()[:160] or (" + ".join(e.title for e in entries)[:160] if combined else entries[0].title)
	requirement_type = entries[0].get("classification")
	# §4.4 — derived from the governed catalogue entry, never a local mapping.
	category = dpp_classification.category_for(requirement_type)
	method = readiness.OPEN_TENDER if frappe.db.exists("Procurement Method", readiness.OPEN_TENDER) else None
	delivery = min((getdate(e.required_by_date) for e in entries if e.required_by_date), default=None)
	resolved = profiles.resolve(procurement_method=method or "", procurement_category=category, applicability_date=profiles.applicability_date(None, plan.fiscal_year))
	defaults = profiles.default_period_inputs(resolved["schedule"])
	period_inputs = {k: v for k, v in defaults.items() if v is not None}
	delivery_default = resolved["schedule"].get("estimated_delivery_period_default_days") if resolved["schedule"].get("found") else None
	if delivery_default is not None:
		period_inputs[profiles.DELIVERY_KEY] = int(delivery_default)
	root = frappe.get_doc({
		"doctype": "Plan Item", "plan_item_id": plan_item_id, "plan_item_reference": plan_item_id, "annual_plan": plan.name,
		"authorisation_hold": 0, "open_correction_requests": 0, "record_version": 0, "fixture_namespace": fixture_namespace,
	}).insert(ignore_permissions=True)
	item = frappe.get_doc(
		{
			"doctype": "Annual Plan Item",
			"plan_item_id": plan_item_id,
			"plan_item": root.name,
			"plan_version": version.name,
			"title": title,
			"description": entries[0].description,
			"requirement_type": requirement_type,
			"procurement_category": category,
			"procurement_method": method,
			"method_profile_version": resolved["method"].get("profile") if resolved["method"].get("found") else None,
			"schedule_profile_version": resolved["schedule"].get("profile") if resolved["schedule"].get("found") else None,
			# §10.7 U08-COMBINE — the reason is asked at the moment of combining,
			# where the Planner actually holds it, not left as a blocker to be
			# discovered later in the editor.
			"aggregation_reason": cstr(combination_reason).strip() if combined else "",
			"plan_horizon": "Single year",
			"aggregation_indicator": "Aggregated into this package" if combined else "Not aggregated",
			"lotting_indicator": "Single lot",
			"item_state": "Draft",
			"item_status": "Not started",
			"baseline_delivery_completion_date": delivery,
			"period_inputs": json.dumps(period_inputs),
			"estimated_delivery_period_days": int(delivery_default or 0),
			**{f: int(period_inputs.get(f) or 0) for f in schedule.PERIOD_FIELDS},
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
				"source_key": f"need:{entry.need}" if entry.need else f"direct:{cstr(entry.direct_source_id) or entry.entry_id}",
				# §4.6 — the exact effective classification evidence this
				# allocation was formed from. A later correction appends new
				# evidence; it never rewrites this snapshot.
				"classification_evidence": cstr((entry.get("classification_evidence") or {}).get("evidence_id")),
				"classification_requirement_type": cstr((entry.get("classification_evidence") or {}).get("requirement_type")),
				"classification_procurement_category": cstr((entry.get("classification_evidence") or {}).get("procurement_category")),
				"need": entry.need or None,
				"need_revision": entry.need_revision or None,
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
	elif version.funding_state == "Awaiting confirmation":
		for task in frappe.get_all("Plan Finance Task", filters={"plan_version": version.name, "status": "Open"}, pluck="name"):
			frappe.db.set_value("Plan Finance Task", task, "status", "Cancelled", update_modified=False)
		frappe.db.set_value("Annual Plan Version", version.name, "funding_state", "Not requested", update_modified=False)


def form_plan_items(
	*, plan_version: str, dpp_entries: list[str] | str, mode: str = "each", combination_reason: str = "",
	combined_title: str = "", expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = authz.actor(user)
	if isinstance(dpp_entries, str):
		dpp_entries = json.loads(dpp_entries)
	dpp_entries = [cstr(e) for e in dpp_entries if cstr(e)]
	combination_reason = cstr(combination_reason).strip()
	combined_title = cstr(combined_title).strip()
	payload = {
		"plan_version": plan_version, "dpp_entries": sorted(dpp_entries), "mode": mode,
		"combination_reason": combination_reason, "combined_title": combined_title,
	}
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
	# §5.4.6 — a source already held by a scope-locked stable item cannot be
	# re-formed under a new identity
	locked = scope_lock.locked_items_for_sources(plan.fiscal_year, dpp_entries)
	if locked:
		fail("PLN_ITEM_SCOPE_LOCKED", detail={"plan_item_ids": locked, "action": "form"})

	entries = []
	for name in dpp_entries:
		entry = _entry_doc(name, plan.fiscal_year, version.name)
		evidence = plan_read._classification_evidence(entry.dpp_version).get(entry.entry_id) or {}
		entry["classification"] = cstr(evidence.get("requirement_type"))
		entry["classification_evidence"] = evidence
		entries.append(entry)
	# §5.4.2 — a correction Draft admits only the returned Version's stable source cohort
	cohort = set(json.loads(version.source_cohort or "[]")) if cstr(version.correction_of_plan_version) else set()
	if cohort:
		strangers = [e.entry_id for e in entries if (f"need:{e.need}" if e.need else f"direct:{cstr(e.direct_source_id) or e.entry_id}") not in cohort]
		if strangers:
			fail("PLN_CORRECTION_COHORT_VIOLATION", detail={"entry_ids": strangers})

	if len(entries) == 1:
		item = _create_item(version=version, plan=plan, entries=entries, combined=False, fixture_namespace=cstr(plan.fixture_namespace))
		created = [item.plan_item_id]
	elif mode == "each":
		created = []
		for entry in entries:
			item = _create_item(version=version, plan=plan, entries=[entry], combined=False, fixture_namespace=cstr(plan.fixture_namespace))
			created.append(item.plan_item_id)
	elif mode == "combined":
		if not _compatible(entries):
			fail("PLN_SOURCE_INCOMPATIBLE")
		# The same 20–500 the readiness gate requires of a combined package
		# (§4.6), enforced where the Planner is actually asked for it.
		if not (20 <= len(combination_reason) <= 500):
			fail("PLN_ENTRY_INCOMPLETE", "State why these requirements are being combined into one purchase (20–500 characters).")
		item = _create_item(
			version=version, plan=plan, entries=entries, combined=True, fixture_namespace=cstr(plan.fixture_namespace),
			combination_reason=combination_reason, title_override=combined_title,
		)
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
	# §5.6.3 / §5.4.6 — a locked item cannot gain capacity by dissolve-and-re-form
	scope_lock.require_unlocked(item.plan_item_id, action="dissolve")
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


def _validate_reservation(reference: dict[str, Any], category: str) -> str:
	"""§5.5.3.2 — the planned designation is a governed catalogue choice
	(`None` explicit); no advantage ranking and no reason-only override."""
	category = cstr(category).strip()
	if not category:
		return ""
	allowed = {row["category"] for row in readiness.reservation_categories(reference)}
	if category not in allowed:
		fail("PLN_RESERVATION_REQUIRED", "Select a governed reservation designation; choose None where no designation applies.", {"field": "reservation_category"})
	return category


def save_plan_item(*, plan_item: str, values: dict[str, Any] | str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if isinstance(values, str):
		values = json.loads(values)
	unknown = set(values) - set(PLAN_ITEM_FIELDS)
	if unknown:
		if unknown & (set(schedule.BASELINE_FIELDS) - {"baseline_invitation_date"}):
			fail("PLN_SCHEDULE_INVALID", "Baseline milestone dates are derived, never entered.", {"fields": sorted(unknown)})
		# PLN-CHG-001 v1.23 §5.5.1A — an actual date only ever arrives from the
		# module that owns the real event. A Planner save naming one is refused
		# by name so the message says why, not just "unexpected field".
		if any(f.startswith("actual_") for f in unknown):
			fail("PLN_ACTUAL_NOT_WRITABLE")
		# §15.3 — the forecast facility is deferred in full; there is no command
		# that would accept these either (PLN23-CHG-001).
		if any(f.startswith("forecast_") for f in unknown):
			fail("PLN_SCHEDULE_INVALID", "The approved schedule cannot be changed. Expected dates are not maintained in this release.", {"fields": sorted(unknown)})
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
	if version.funding_state == "Awaiting confirmation":
		fail("PLN_STALE_WRITE", "The Plan Version is awaiting Finance confirmation. Wait for the decision before editing.")
	envelope.check_record_version(item, expected_record_version)

	allocations = readiness._allocations(item.name)
	if any(plan_read.source_correction_required(a.dpp_entry) for a in allocations):
		fail("PLN_SOURCE_CORRECTION_REQUIRED")
	# §5.4.6 — a scope-locked stable item (any authorised Requisition) keeps
	# its package, structure, designation and method; schedule, estimate and
	# Strategy fields stay editable
	changed = scope_lock.scope_changes(values, item)
	if changed and scope_lock.is_locked(item.plan_item_id):
		fail("PLN_ITEM_SCOPE_LOCKED", detail={"plan_item_id": item.plan_item_id, "fields": changed})
	reference = readiness.reference_for(plan.fiscal_year)
	planned_value = sum(flt(a.indicative_amount) for a in allocations)
	category = cstr(item.procurement_category) or "Services"

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

	# §4.6 — the horizon is a fixed literal; any other payload is unsupported
	if "plan_horizon" in values and cstr(values["plan_horizon"]) not in readiness.PLAN_HORIZONS:
		fail("PLN_MULTI_YEAR_UNSUPPORTED", detail={"field": "plan_horizon", "offered": cstr(values["plan_horizon"])})
	for field, allowed in (("aggregation_indicator", readiness.AGGREGATION_INDICATORS), ("lotting_indicator", readiness.LOTTING_INDICATORS)):
		if field in values:
			if cstr(values[field]) not in allowed:
				fail("PLN_PLAN_CONTENTS_INCOMPLETE", detail={"field": field})
			updates[field] = cstr(values[field])
	if "lot_count" in values:
		updates["lot_count"] = int(values["lot_count"] or 0)
	lotting = updates.get("lotting_indicator", item.lotting_indicator)
	if lotting == "Packaged into lots" and int(updates.get("lot_count", item.lot_count) or 0) <= 0:
		fail("PLN_PLAN_CONTENTS_INCOMPLETE", "State the intended number of lots.", {"field": "lot_count"})
	if lotting != "Packaged into lots":
		updates["lot_count"] = 0

	# §4.6 estimate basis (market survey and included incidental costs)
	if "estimate_basis" in values:
		basis = cstr(values["estimate_basis"]).strip()
		if basis and not (20 <= len(basis) <= 1000):
			fail("PLN_PLAN_CONTENTS_INCOMPLETE", "The estimate basis identifies the market survey and included incidental costs (20–1,000 characters).", {"field": "estimate_basis"})
		updates["estimate_basis"] = basis
	if "estimate_basis_reference" in values:
		updates["estimate_basis_reference"] = cstr(values["estimate_basis_reference"]).strip()[:140]

	# §5.5.3.2 planned designation; county obligation only for a county entity
	if "reservation_category" in values:
		updates["reservation_category"] = _validate_reservation(reference, values.get("reservation_category"))
	if "county_resident_reservation" in values:
		is_county = bool(frappe.db.get_single_value("Site Procuring Entity", "entity_is_county"))
		updates["county_resident_reservation"] = 1 if (is_county and values["county_resident_reservation"] in (True, 1, "1", "true", "True")) else 0

	# §5.5.3.3 method conditions: the profile in force on the applicable date
	method = cstr(values.get("procurement_method", item.procurement_method)).strip()
	if "procurement_method" in values:
		if method and not frappe.db.exists("Procurement Method", {"name": method, "status": "Active"}):
			fail("PLN_METHOD_NOT_ADMISSIBLE", f"{method} is not a governed procurement method.", {"field": "procurement_method"})
	evidence_rows = values.get("method_condition_evidence", readiness.item_evidence(item))
	if isinstance(evidence_rows, str):
		evidence_rows = json.loads(evidence_rows) if evidence_rows.strip() else []
	if not isinstance(evidence_rows, list) or any(not isinstance(r, dict) or not cstr(r.get("condition_id")) for r in evidence_rows):
		fail("PLN_ENTRY_INCOMPLETE", "Method condition evidence is a list of {condition_id, evidence_reference, authorisation_reference} rows.", {"field": "method_condition_evidence"})
	anchor = values.get("baseline_invitation_date", item.baseline_invitation_date) or None
	resolved = profiles.resolve(procurement_method=method, procurement_category=category, applicability_date=profiles.applicability_date(anchor, plan.fiscal_year))
	if method and ("procurement_method" in values or "method_condition_evidence" in values) and resolved["method"].get("found"):
		readiness.require_method_admissible(resolved, category, planned_value, method, evidence_rows)
	updates["procurement_method"] = method or None
	updates["method_condition_evidence"] = json.dumps([{"condition_id": cstr(r.get("condition_id")), "evidence_reference": cstr(r.get("evidence_reference")).strip(), "authorisation_reference": cstr(r.get("authorisation_reference")).strip()} for r in evidence_rows])
	updates["method_profile_version"] = resolved["method"].get("profile") if resolved["method"].get("found") else None
	updates["schedule_profile_version"] = resolved["schedule"].get("profile") if resolved["schedule"].get("found") else None
	if resolved["method"].get("found"):
		updates["mandatory_restriction_results"] = json.dumps(profiles.method_conditions(resolved["method"], procurement_category=category, planned_value=planned_value, evidence_rows=evidence_rows)["results"])

	# §5.5.1 schedule: entered periods against the resolved profile, the
	# Planner's estimated delivery period, feasibility against the boundary
	period_inputs = dict(readiness.item_period_inputs(item))
	offered = values.get("period_inputs")
	if isinstance(offered, str):
		offered = json.loads(offered) if offered.strip() else {}
	if offered:
		if not isinstance(offered, dict):
			fail("PLN_SCHEDULE_INVALID", "Period inputs are a map of period key to whole days.", {"field": "period_inputs"})
		period_inputs.update({k: v for k, v in offered.items() if k in (*profiles.PERIOD_KEYS, profiles.DELIVERY_KEY)})
	for field in schedule.PERIOD_FIELDS:  # the v1.12 per-field shape still offered by the current editor
		if field in values:
			period_inputs[field] = values[field]
	if "estimated_delivery_period_days" in values:
		period_inputs[profiles.DELIVERY_KEY] = values["estimated_delivery_period_days"]
	delivery_days = period_inputs.get(profiles.DELIVERY_KEY)
	if delivery_days not in (None, ""):
		try:
			delivery_days = int(delivery_days)
		except (TypeError, ValueError):
			fail("PLN_DELIVERY_PERIOD_REQUIRED", detail={"field": "estimated_delivery_period_days"})
		if delivery_days < 0:
			fail("PLN_DELIVERY_PERIOD_REQUIRED", "The estimated delivery period is a non-negative number of calendar days.", {"field": "estimated_delivery_period_days"})
		period_inputs[profiles.DELIVERY_KEY] = delivery_days
	else:
		period_inputs.pop(profiles.DELIVERY_KEY, None)
		delivery_days = None
	clean = schedule.validate_periods(period_inputs, resolved["schedule"])
	period_inputs.update(clean)
	delivery = min((getdate(a.required_by_date) for a in allocations if a.required_by_date), default=None)
	baseline = schedule.derive_baseline(anchor, clean, delivery, resolved["schedule"])
	updates.update({f: int(clean.get(f) or 0) for f in schedule.PERIOD_FIELDS})
	updates["period_inputs"] = json.dumps(period_inputs)
	updates["estimated_delivery_period_days"] = int(delivery_days or 0)
	updates["baseline_milestones"] = json.dumps({k: cstr(v) for k, v in baseline.items()})
	updates["estimated_completion_date"] = profiles.estimated_completion(baseline, delivery_days)
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


def save_plan_version_details(*, plan_version: str, values: dict[str, Any] | str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""PLN-CHG-001 v1.18 §4.5 / §7.2 `SavePlanVersionDetails` — the whole-Plan
	`project_name` (optional, ≤ 160) and the successor's `change_reason`
	(20–1,000; a correction inherits its issue context). Planner, Draft only."""
	actor = authz.actor(user)
	if isinstance(values, str):
		values = json.loads(values)
	unknown = set(values) - set(VERSION_DETAIL_FIELDS)
	if unknown:
		fail("PLN_ENTRY_INCOMPLETE", f"Plan Version details are limited to {', '.join(VERSION_DETAIL_FIELDS)}; unexpected: {sorted(unknown)}.")
	payload = {"plan_version": plan_version, **{k: cstr(values.get(k)) for k in VERSION_DETAIL_FIELDS}}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise(actor)
	if version.version_status != "Draft":
		fail("PLN_STALE_WRITE")
	envelope.check_record_version(version, expected_record_version)
	updates: dict[str, Any] = {}
	if "project_name" in values:
		project_name = " ".join(cstr(values["project_name"]).split())
		if len(project_name) > 160:
			fail("PLN_ENTRY_INCOMPLETE", "The project name is at most 160 characters; leave it blank for a mixed portfolio.", {"field": "project_name"})
		updates["project_name"] = project_name
	if "change_reason" in values:
		reason = " ".join(cstr(values["change_reason"]).split())
		if reason and not (20 <= len(reason) <= 1000):
			fail("PLN_ENTRY_INCOMPLETE", "The change reason explains the substantive update (20–1,000 characters).", {"field": "change_reason"})
		updates["change_reason"] = reason
	envelope.bump(version, **updates)
	result = {"ok": True, "idempotent": False, "action": "details_saved", "record_version": int(version.record_version or 0), **updates}
	envelope.record_command(
		idempotency_key=idempotency_key, command="SavePlanVersionDetails", payload=payload, result=result,
		document_type="Annual Plan Version", document_name=version.name, actor=actor,
		fixture_namespace=cstr(plan.fixture_namespace),
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
