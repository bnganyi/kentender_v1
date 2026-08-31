# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §5.2/§8.2 — Annual Plan workbench commands.

`FormPlanItems` creates one item per selected source or one compatible
combined item, allocating each source atomically under the Phase 1 DB unique
(`pln_uniq_entry_per_version`) that makes double-use of one accepted entry
impossible even under a race — the same invariant-24-family defence used for
the Annual Plan root itself. `DissolvePlanItem` and `SavePlanItem` are scoped
to a mutable Draft item in a Draft Version only; Phase 6 creates no Finance
task, so dissolution here never has a reservation to release (§4.11's release
path is Phase 7 — `PLN-707`). `SavePlanItem` refuses any further edit once
`source_correction_required` is true (§12.7): the Planner's only route is
`DissolvePlanItem` and re-formation from the current source.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, getdate

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import (
	authority,
	budget_gateway,
	envelope,
	plan_read,
	references,
	strategy_gateway,
)
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_PROCUREMENT_PLANNER,
)

PLAN_ITEM_FIELDS = (
	"title", "description", "strategic_objective", "aggregation_reason",
	"invitation_date", "bid_opening_date", "evaluation_completion_date",
	"award_approval_date", "award_notification_date", "contract_signing_date",
	"delivery_completion_date",
)
SCHEDULE_FIELDS = PLAN_ITEM_FIELDS[4:]


def _authorise(actor: str, procuring_entity: str) -> None:
	authority.require_scope(
		actor, roles=(ROLE_PROCUREMENT_PLANNER,), procuring_entity=procuring_entity,
	)


def _item_doc_name(plan_item_id: str) -> str:
	"""Delegates to `plan_read.resolve_item_doc_name` — see its docstring:
	a bare `plan_item_id` can name two live docs at once from the moment a
	Draft successor exists alongside its Active predecessor."""
	return plan_read.resolve_item_doc_name(plan_item_id)


def _open_tender_method() -> str:
	return frappe.db.get_value("Procurement Method", {"status": "Active"}) or ""


def _entry_doc(dpp_entry: str, pe_fy_context: str):
	entry = frappe.db.get_value(
		"Departmental Plan Entry",
		dpp_entry,
		["name", "entry_id", "dpp_version", "title", "description", "source_origin",
		 "need", "need_version", "quantity", "unit", "required_by_date",
		 "budget_line", "indicative_amount"],
		as_dict=True,
	)
	if not entry:
		fail("PLN_SOURCE_UNAVAILABLE", "One or more selected departmental entries are no longer available for Plan Item formation.")
	dpp_root_ctx = frappe.db.get_value(
		"Departmental Plan",
		frappe.db.get_value("Departmental Plan Version", entry.dpp_version, "departmental_plan"),
		["pe_fy_context", "organisation_unit", "current_accepted_version"],
		as_dict=True,
	)
	if (
		not dpp_root_ctx
		or dpp_root_ctx.pe_fy_context != pe_fy_context
		or dpp_root_ctx.current_accepted_version != entry.dpp_version
	):
		fail("PLN_SOURCE_UNAVAILABLE", "One or more selected departmental entries are no longer available for Plan Item formation.")
	if frappe.db.exists(
		"Plan Source Allocation",
		{"dpp_entry": entry.name, "allocation_state": ("in", ("Draft", "Active"))},
	):
		fail("PLN_SOURCE_UNAVAILABLE", "One or more selected departmental entries are no longer available for Plan Item formation.")
	entry.organisation_unit = dpp_root_ctx.organisation_unit
	return entry


def _entry_budget(entry) -> str:
	return cstr(frappe.db.get_value("Budget Line", entry.budget_line, "budget"))


def _compatible(entries: list) -> bool:
	"""§5.3 invariant 8 / §12.7 — same PE/FY (implicit: one context), Budget,
	currency (same Budget implies same Budget currency), requirement type
	and unit; "procurement treatment" is read as `source_origin`, the only
	other categorical dimension a source carries."""
	budgets = {_entry_budget(e) for e in entries}
	classifications = {cstr(e.get("classification")) for e in entries}
	units = {e.unit for e in entries}
	origins = {e.source_origin for e in entries}
	return len(budgets) == 1 and len(classifications) == 1 and len(units) == 1 and len(origins) == 1


def _create_item(*, version, plan, entries: list, combined: bool, fixture_namespace: str = ""):
	plan_item_id = references.plan_item_id(plan.procuring_entity, plan.financial_year)
	if combined:
		title = " + ".join(e.title for e in entries)[:160]
		description = entries[0].description
	else:
		title = entries[0].title
		description = entries[0].description
	item = frappe.get_doc(
		{
			"doctype": "Annual Plan Item",
			"plan_item_id": plan_item_id,
			"plan_version": version.name,
			"title": title,
			"description": description,
			# Requirement Type autonames itself `field:title`; the classification
			# string recorded on the acceptance decision is already its name.
			"requirement_type": entries[0].get("classification"),
			"procurement_method": _open_tender_method(),
			"aggregation_reason": "",
			"item_state": "Draft",
			"finance_state": "Not requested",
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


def form_plan_items(
	*,
	plan_version: str,
	dpp_entries: list[str] | str,
	mode: str = "each",
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	import json

	actor = cstr(user or frappe.session.user)
	if isinstance(dpp_entries, str):
		dpp_entries = json.loads(dpp_entries)
	dpp_entries = [cstr(e) for e in dpp_entries if cstr(e)]
	payload = {
		"plan_version": plan_version, "dpp_entries": sorted(dpp_entries), "mode": mode,
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not dpp_entries:
		fail("PLN_ENTRY_INCOMPLETE", "Select at least one accepted departmental entry to form a Plan Item.")

	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise(actor, plan.procuring_entity)
	if version.version_status != "Draft":
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")
	envelope.check_record_version(version, expected_record_version)

	entries = []
	for name in dpp_entries:
		entry = _entry_doc(name, plan.pe_fy_context)
		# each entry may belong to a different DPP submission/decision
		decision_classifications = plan_read._classifications(entry.dpp_version)
		entry["classification"] = decision_classifications.get(entry.entry_id, "")
		entries.append(entry)

	if len(entries) == 1:
		item = _create_item(
			version=version, plan=plan, entries=entries, combined=False,
			fixture_namespace=cstr(plan.fixture_namespace),
		)
		created = [item.plan_item_id]
	elif mode == "each":
		created = []
		for entry in entries:
			item = _create_item(
				version=version, plan=plan, entries=[entry], combined=False,
				fixture_namespace=cstr(plan.fixture_namespace),
			)
			created.append(item.plan_item_id)
	elif mode == "combined":
		if not _compatible(entries):
			fail(
				"PLN_SOURCE_INCOMPATIBLE",
				"The selected entries cannot form one Plan Item. Create separate items.",
			)
		item = _create_item(
			version=version, plan=plan, entries=entries, combined=True,
			fixture_namespace=cstr(plan.fixture_namespace),
		)
		created = [item.plan_item_id]
	else:
		fail(
			"PLN_ENTRY_INCOMPLETE",
			"Choose whether to create one Plan Item for each entry or one combined Plan Item.",
		)

	envelope.bump(version)
	result = {
		"ok": True, "idempotent": False, "action": "formed",
		"created_items": created, "single": len(created) == 1,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="FormPlanItems", payload=payload,
		result=result, document_type="Annual Plan Version", document_name=version.name,
		actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


def dissolve_plan_item(
	*, plan_item: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {"plan_item": plan_item}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	item = envelope.locked("Annual Plan Item", _item_doc_name(plan_item))
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise(actor, plan.procuring_entity)
	if item.item_state != "Draft" or version.version_status != "Draft":
		fail("PLN_DISSOLUTION_BLOCKED", "This Plan Item is no longer in a mutable Draft and cannot be dissolved.")
	envelope.check_record_version(item, expected_record_version)

	# §7.3/PLN-707: release the unconverted remainder of every *effective*
	# reservation first — a release failure must roll back the whole
	# dissolution (the ProcurementPlanningError from release_planning_
	# reservations propagates and aborts this request's transaction) rather
	# than leave allocations Released with an unreleased reservation behind.
	reservation_refs = frappe.get_all(
		"Plan Reservation Reference", filters={"plan_item": item.name}, fields=["name", "reservation"]
	)
	if reservation_refs:
		correlation_id = f"dissolve:{item.plan_item_id}:{idempotency_key}"
		released = budget_gateway.release_planning_reservations(
			reservation_refs=[{"reservation": r.reservation} for r in reservation_refs],
			correlation_id=correlation_id, event_type="PlanItemDissolved",
		)
		for ref, outcome in zip(reservation_refs, released):
			frappe.db.set_value(
				"Plan Reservation Reference", ref.name,
				{
					"release_reference": outcome["reservation"]["reservation_code"],
					"release_correlation": correlation_id,
				},
				update_modified=False,
			)

	open_tasks = frappe.get_all(
		"Plan Finance Task", filters={"plan_item": item.name, "status": "Open"}, pluck="name"
	)
	for task in open_tasks:
		frappe.db.set_value("Plan Finance Task", task, "status", "Cancelled", update_modified=False)
	frappe.db.set_value(
		"Plan Source Allocation",
		{"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
		"allocation_state", "Released", update_modified=False,
	)
	envelope.bump(item, item_state="Dissolved")
	result = {"ok": True, "idempotent": False, "action": "dissolved", "plan_item": item.plan_item_id}
	envelope.record_command(
		idempotency_key=idempotency_key, command="DissolvePlanItem", payload=payload,
		result=result, document_type="Annual Plan Item", document_name=item.name,
		actor=actor, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def _validate_schedule(values: dict, earliest_required_by) -> None:
	dates: dict[str, Any] = {}
	for field in SCHEDULE_FIELDS:
		raw = values.get(field)
		if cstr(raw).strip():
			dates[field] = getdate(raw)
	ordered = [dates[f] for f in SCHEDULE_FIELDS if f in dates]
	if ordered != sorted(ordered):
		fail(
			"PLN_SCHEDULE_INVALID",
			"Correct the highlighted dates so the schedule is chronological and meets the required-by date.",
		)
	delivery = dates.get("delivery_completion_date")
	if delivery and earliest_required_by and delivery > getdate(earliest_required_by):
		fail(
			"PLN_SCHEDULE_INVALID",
			"Correct the highlighted dates so the schedule is chronological and meets the required-by date.",
		)


def save_plan_item(
	*,
	plan_item: str,
	values: dict[str, Any] | str,
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	import json

	actor = cstr(user or frappe.session.user)
	if isinstance(values, str):
		values = json.loads(values)
	unknown = set(values) - set(PLAN_ITEM_FIELDS)
	if unknown:
		fail(
			"PLN_ENTRY_INCOMPLETE",
			f"Plan Item input is limited to the defined allow-list; unexpected: {sorted(unknown)}.",
		)
	payload = {"plan_item": plan_item, **{k: cstr(values.get(k)) for k in PLAN_ITEM_FIELDS}}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	item = envelope.locked("Annual Plan Item", _item_doc_name(plan_item))
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise(actor, plan.procuring_entity)
	if item.item_state != "Draft" or version.version_status != "Draft":
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")
	envelope.check_record_version(item, expected_record_version)

	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
		fields=["dpp_entry", "required_by_date"],
	)
	if any(plan_read.source_correction_required(a.dpp_entry) for a in allocations):
		fail(
			"PLN_SOURCE_CORRECTION_REQUIRED",
			"A departmental source changed. Dissolve and re-form the affected Draft item before continuing.",
		)

	title = cstr(values.get("title")).strip()
	description = cstr(values.get("description")).strip()
	if not (5 <= len(title) <= 160):
		fail("PLN_ENTRY_INCOMPLETE", "Plan Item title must be 5-160 characters.")
	if not (10 <= len(description) <= 1000):
		fail("PLN_ENTRY_INCOMPLETE", "Procurement description must be 10-1,000 characters.")

	aggregation_reason = cstr(values.get("aggregation_reason")).strip()
	combined = len(allocations) > 1
	if aggregation_reason and not (20 <= len(aggregation_reason) <= 500):
		fail("PLN_ENTRY_INCOMPLETE", "Aggregation reason must be 20-500 characters when provided.")
	if not combined:
		aggregation_reason = ""

	earliest_required_by = min(
		(getdate(a.required_by_date) for a in allocations if a.required_by_date), default=None
	)
	_validate_schedule(values, earliest_required_by)

	updates: dict[str, Any] = {
		"title": title, "description": description, "aggregation_reason": aggregation_reason,
		**{field: values.get(field) or None for field in SCHEDULE_FIELDS},
	}

	objective_id = cstr(values.get("strategic_objective")).strip()
	if objective_id and objective_id != cstr(item.strategic_objective):
		snapshot = strategy_gateway.snapshot_objective(
			procuring_entity=plan.procuring_entity, objective_id=objective_id,
			correlation_key=f"{item.plan_item_id}:{idempotency_key}",
		)
		updates.update(
			strategic_objective=objective_id,
			objective_path=snapshot["path_display"],
			strategy_plan=snapshot["strategy_plan"],
			strategy_plan_version=snapshot["strategy_plan_version"],
		)
	elif not objective_id:
		updates.update(strategic_objective=None, objective_path="", strategy_plan=None, strategy_plan_version=None)

	envelope.bump(item, **updates)
	result = {"ok": True, "idempotent": False, "action": "saved", "plan_item": item.plan_item_id}
	envelope.record_command(
		idempotency_key=idempotency_key, command="SavePlanItem", payload=payload,
		result=result, document_type="Annual Plan Item", document_name=item.name,
		actor=actor, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result
