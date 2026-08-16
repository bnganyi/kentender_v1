"""Atomic Approved-Demand formation into Draft Plan Items."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import ALLOC_DRAFT, DRAFT_CHANGE_ADDED, ITEM_PROPOSED, VALIDATION_NOT_RUN
from kentender_procurement.procurement_planning.services._invariants import assert_version_concurrency, new_concurrency_token, next_plan_item_code
from kentender_procurement.procurement_planning.services.list_eligible_demands import list_eligible_demands
from kentender_procurement.procurement_planning.services.planning_permissions import assert_can_add_demand, assert_planning_scope

FORMATION_SEPARATE = "separate"
FORMATION_COMBINED = "combined"


def _parse_demands(value: list[str] | str | None) -> list[str]:
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except json.JSONDecodeError:
			value = [part.strip() for part in value.split(",")]
	names = [name for raw in (value or []) if (name := cstr(raw).strip())]
	if len(names) != len(set(names)):
		frappe.throw(frappe._("A Demand may be selected only once."), title="PLN_FORMATION_DUPLICATE_DEMAND")
	return names


def _replay(plan: str, key: str) -> dict[str, Any] | None:
	items = frappe.get_all(
		"Procurement Plan Item", filters={"plan": plan, "formation_idempotency_key": key},
		fields=["name", "plan_item_code", "formation_batch_index"], order_by="formation_batch_index asc",
	)
	if not items:
		return None
	first = items[0]
	has_approved = bool(frappe.db.get_value("Procurement Plan", plan, "current_approved_version"))
	return {
		"ok": True, "replayed": True, "plan": plan, "plan_item": first.name,
		"plan_item_code": first.plan_item_code, "plan_items": [r.name for r in items],
		"editor_route": f"/app/procurement-plan-item-editor/{first.name}" if len(items) == 1 else None,
		"builder_route": (
			f"/app/procurement-plan-builder?plan={plan}"
			if has_approved else f"/app/procurement-plan-builder?plan={plan}"
		),
	}


def _strategy_snapshots(demands: list[str]) -> tuple[str, str]:
	strategies = frappe.get_all("Demand Strategy Reference", filters={"demand": ["in", demands]}, pluck="snapshot_label") if frappe.db.exists("DocType", "Demand Strategy Reference") else []
	pvcs = frappe.get_all("Demand Value Treatment", filters={"demand": ["in", demands]}, pluck="pvc_snapshot") if frappe.db.exists("DocType", "Demand Value Treatment") else []
	return "; ".join(dict.fromkeys(filter(None, map(cstr, strategies)))), "; ".join(dict.fromkeys(filter(None, map(cstr, pvcs))))


def _create_item(
	*, plan_doc: Any, version: Any, sources: list[dict[str, Any]], owner_ou: str | None,
	key: str, index: int, combined: bool, reason: str,
) -> dict[str, Any]:
	code = next_plan_item_code(plan_doc.plan_code)
	item = frappe.get_doc({
		"doctype": "Procurement Plan Item", "plan": plan_doc.name, "plan_item_code": code,
		"procuring_entity": plan_doc.procuring_entity, "owner_org_unit": owner_ou,
		"delivery_org_unit": sources[0].get("delivery_org_unit"), "baseline_state": ITEM_PROPOSED,
		"formation_idempotency_key": key, "formation_batch_index": index,
	}).insert(ignore_permissions=True)
	total = sum(flt(need["available_amount"]) for source in sources for need in source["need_items"])
	title = sources[0]["title"] if len(sources) == 1 else "Combined requirements: " + "; ".join(s["title"] for s in sources)
	strategy, pvc = _strategy_snapshots([s["demand"] for s in sources])
	item_version = frappe.get_doc({
		"doctype": "Procurement Plan Item Version", "plan_item": item.name, "plan_version": version.name,
		"item_version_code": f"{code}-{version.version_number}", "carry_forward_unchanged": 0,
		"draft_change_label": DRAFT_CHANGE_ADDED if plan_doc.current_approved_version else "",
		"requirement_title": title[:140], "requirement_description": cstr(sources[0].get("need_statement"))[:500],
		"confirmed_estimate": total, "currency": plan_doc.currency,
		"procurement_category": cstr(sources[0].get("category")),
		"aggregation_decision": "Combine" if combined else "", "aggregation_reason": reason if combined else "",
		"reservation_reference": cstr((sources[0].get("funding") or {}).get("reservation_reference")),
		"strategy_snapshot": strategy, "pvc_snapshot": pvc, "validation_projection": VALIDATION_NOT_RUN,
	}).insert(ignore_permissions=True)
	frappe.db.set_value("Procurement Plan Item", item.name, "draft_item_version", item_version.name, update_modified=False)
	allocations: list[str] = []
	for source in sources:
		funding = source.get("funding") or {}
		for need in source["need_items"]:
			allocation = frappe.get_doc({
				"doctype": "Plan Demand Allocation", "plan_item": item.name,
				"demand": source["demand"], "demand_item": need["id"],
				"source_org_unit": source["organisation_unit"],
				"source_funding_allocation": funding.get("allocation"),
				"active_hold_key": need["id"], "status": ALLOC_DRAFT,
				"allocated_amount": need["available_amount"], "currency": need["currency"],
				"allocated_quantity": need.get("quantity"), "proposed_in_version": version.name,
				"reservation_reference": funding.get("reservation_reference"), "reason": reason if combined else "",
			}).insert(ignore_permissions=True)
			allocations.append(allocation.name)
	return {"plan_item": item.name, "plan_item_code": code, "item_version": item_version.name, "allocations": allocations, "allocated_amount": total}


def add_demand_to_plan(
	*, plan: str, demands: list[str] | str | None, expected_version_token: str | None,
	formation_mode: str | None = None, formation_reason: str | None = None,
	idempotency_key: str | None = None, user: str | None = None,
) -> dict[str, Any]:
	actor = assert_can_add_demand(user)
	plan_name = cstr(plan).strip()
	names = _parse_demands(demands)
	key = cstr(idempotency_key).strip()
	if not plan_name or not names or not key:
		frappe.throw(frappe._("Plan, selected Demands and idempotency key are required."), title="PLN_FORMATION_REQUIRED")
	if not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(frappe._("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")
	replayed = _replay(plan_name, key)
	if replayed:
		return replayed
	if not cstr(expected_version_token).strip():
		frappe.throw(frappe._("The expected Plan Version token is required."), title="PLN_VERSION_TOKEN_REQUIRED")
	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(procuring_entity=plan_doc.procuring_entity, user=actor, require_write=False)
	focus = cstr(plan_doc.open_draft_version or plan_doc.current_approved_version)
	if not focus:
		frappe.throw(frappe._("The Plan has no editable or approved Version."), title="PLN_NO_PLAN_VERSION")
	mode = cstr(formation_mode).strip()
	if len(names) == 1:
		if mode:
			frappe.throw(frappe._("A formation choice is not accepted for one Demand."), title="PLN_FORMATION_MODE_UNEXPECTED")
		mode = FORMATION_SEPARATE
	elif mode not in (FORMATION_SEPARATE, FORMATION_COMBINED):
		frappe.throw(frappe._("Choose separate or combined Plan Item formation."), title="PLN_FORMATION_MODE_REQUIRED")
	reason = cstr(formation_reason).strip()
	if mode == FORMATION_COMBINED and not reason:
		frappe.throw(frappe._("A reason for combining is required."), title="PLN_FORMATION_REASON_REQUIRED")

	# Lock the Plan, the token-bearing Version, every selected source item and any
	# existing hold before eligibility is re-evaluated.  The unique active-hold
	# key remains the final database race guard.
	frappe.db.sql("select name from `tabProcurement Plan` where name=%s for update", plan_name)
	plan_doc.reload()
	focus = cstr(plan_doc.open_draft_version or plan_doc.current_approved_version)
	frappe.db.sql("select name from `tabProcurement Plan Version` where name=%s for update", focus)
	assert_version_concurrency(focus, expected_version_token)
	frappe.db.sql("select name from `tabDemand` where name in %(names)s for update", {"names": names})
	frappe.db.sql("select name from `tabDemand Item` where demand in %(names)s for update", {"names": names})
	frappe.db.sql(
		"select name from `tabPlan Demand Allocation` where demand in %(names)s and status in ('Draft', 'Effective') for update",
		{"names": names},
	)
	all_rows = list_eligible_demands(plan=plan_name, user=actor)["demands"]
	available = {row["demand"]: row for row in all_rows}
	missing = [name for name in names if name not in available]
	if missing:
		exclusion = list_eligible_demands(plan=plan_name, requested_demand=missing[0], user=actor).get("requested_exclusion") or {}
		frappe.throw(
			frappe._(exclusion.get("reason") or "A selected Demand is no longer eligible or has no available Need Items."),
			title=exclusion.get("code") or "PLN_DEMAND_CHANGED",
		)
	selected = [available[name] for name in names]
	for source in selected:
		assert_planning_scope(procuring_entity=plan_doc.procuring_entity, org_unit=source["organisation_unit"], user=actor, require_write=True)
	ous = {row["organisation_unit"] for row in selected}
	if mode == FORMATION_COMBINED and len(ous) > 1:
		# Mixed-OU combination is PE-owned and therefore requires entity-wide mutation authority.
		assert_planning_scope(procuring_entity=plan_doc.procuring_entity, user=actor, require_write=True)

	if not plan_doc.open_draft_version:
		from kentender_procurement.procurement_planning.services.open_or_create_plan_revision import open_or_create_plan_revision
		created_version = open_or_create_plan_revision(plan=plan_name, version_reason="Opened to add approved Demands", user=actor)
		plan_doc.reload()
	version = frappe.get_doc("Procurement Plan Version", plan_doc.open_draft_version)
	if version.name != focus:
		frappe.db.sql("select name from `tabProcurement Plan Version` where name=%s for update", version.name)
	# Enrich immutable funding lineage in one bounded query.
	funding_rows = frappe.get_all("Demand Funding Allocation", filters={"demand": ["in", names]}, fields=["name", "demand", "funding_reservation"])
	funding = {r.demand: {"allocation": r.name, "reservation_reference": r.funding_reservation} for r in funding_rows}
	for source in selected:
		source["funding"] = funding.get(source["demand"], {})

	created: list[dict[str, Any]] = []
	if mode == FORMATION_COMBINED:
		created.append(_create_item(plan_doc=plan_doc, version=version, sources=selected, owner_ou=next(iter(ous)) if len(ous) == 1 else None, key=key, index=1, combined=True, reason=reason))
	else:
		for index, source in enumerate(selected, start=1):
			created.append(_create_item(plan_doc=plan_doc, version=version, sources=[source], owner_ou=source["organisation_unit"], key=key, index=index, combined=False, reason=""))
	new_token = new_concurrency_token()
	frappe.db.set_value("Procurement Plan Version", version.name, {"concurrency_token": new_token, "validation_projection": VALIDATION_NOT_RUN}, update_modified=True)
	items = [row["plan_item"] for row in created]
	allocations = [name for row in created for name in row["allocations"]]
	return {
		"ok": True, "replayed": False, "formation_mode": mode, "plan": plan_name,
		"version": version.name, "concurrency_token": new_token,
		"plan_item": items[0], "plan_item_code": created[0]["plan_item_code"], "plan_items": items,
		"item_version": created[0]["item_version"] if len(created) == 1 else None,
		"allocations": allocations,
		# Singular aliases retain the established one-Demand consumer contract.
		"allocation": allocations[0] if len(allocations) == 1 else None,
		"allocation_status": ALLOC_DRAFT,
		"allocated_amount": sum(row["allocated_amount"] for row in created),
		"editor_route": f"/app/procurement-plan-item-editor/{items[0]}" if len(items) == 1 else None,
		"builder_route": (
			f"/app/procurement-plan-builder?plan={plan_name}"
			if plan_doc.current_approved_version
			else f"/app/procurement-plan-builder?plan={plan_name}"
		),
		"actor": actor,
	}
