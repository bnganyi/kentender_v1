# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.2 / §7.1 / §7.2 — activation, successor and Active
Plan management.

`_activate_version`/`_publish_usage_events` are the shared controlled
activation `publication_pipeline.activate_plan_version` calls once its
predicates pass: supersede the predecessor, seed every Plan Item's baseline
into its forecast (invariant 12e), publish `NeedPlanningUsageChanged.v1` for
every Need-origin source that starts or stops being represented (§7.1).
Planning holds no reservation, so nothing is released here. The remaining
commands here (`BeginPlanUpdate`, `RemovePlanItemInSuccessor`,
`CancelPlanUpdate`) manage the Draft successor/correction chain against the
current Active baseline; the async publication pipeline itself lives in
`publication_pipeline.py`.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope, schedule
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.plan_governance import _copy_version_content, _next_plan_version_number
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER

def _publish_usage_events(version, plan, *, event_suffix: str) -> None:
	"""§7.1 `NeedPlanningUsageChanged.v1` — "Fully included" for every
	Need-origin source in the now-Active version, "Not included" for every
	Need-origin source a Removed-in-successor item drops."""
	from kentender_procurement.departmental_needs.services import usage as needs_usage

	active_items = frappe.get_all("Annual Plan Item", filters={"plan_version": version.name, "item_state": "Active"}, fields=["name", "plan_item_id"])
	items_by_name = {i.name: i.plan_item_id for i in active_items}
	included = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": ("in", list(items_by_name) or ("",)), "source_origin": "Accepted Departmental Need", "allocation_state": "Active"},
		fields=["plan_item", "need", "need_revision"],
	)
	for row in included:
		needs_usage.project_planning_usage(
			departmental_need=row.need, accepted_revision=row.need_revision, usage="Fully included",
			source_event_id=f"{event_suffix}:{row.need_revision}:included", source_event_time=now_datetime(),
			active_plan=plan.plan_reference, active_plan_item=items_by_name.get(row.plan_item, ""), user="Administrator",
		)
	removed_items = frappe.get_all("Annual Plan Item", filters={"plan_version": version.name, "item_state": "Removed in successor"}, pluck="name")
	dropped = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": ("in", removed_items or ("",)), "source_origin": "Accepted Departmental Need"},
		fields=["need", "need_revision"],
	)
	for row in dropped:
		needs_usage.project_planning_usage(
			departmental_need=row.need, accepted_revision=row.need_revision, usage="Not included",
			source_event_id=f"{event_suffix}:{row.need_revision}:removed", source_event_time=now_datetime(), user="Administrator",
		)


def _activate_version(version, plan) -> None:
	"""Invariants 16–18 and 12e — the controlled activation: supersede the
	predecessor, mark this Version's items Active, seed forecasts from
	baseline, update the one Active pointer."""
	predecessor = cstr(plan.active_version)
	if predecessor and predecessor != version.name:
		removed_ids = frappe.get_all("Annual Plan Item", filters={"plan_version": version.name, "item_state": "Removed in successor"}, pluck="plan_item_id")
		if removed_ids:
			frappe.db.set_value("Annual Plan Item", {"plan_version": predecessor, "plan_item_id": ("in", removed_ids)}, "item_state", "Superseded", update_modified=False)
			removed_item_names = frappe.get_all("Annual Plan Item", filters={"plan_version": version.name, "item_state": "Removed in successor"}, pluck="name")
			frappe.db.set_value("Plan Source Allocation", {"plan_item": ("in", removed_item_names)}, "allocation_state", "Removed in successor", update_modified=False)
		frappe.db.set_value("Annual Plan Version", predecessor, "version_status", "Superseded", update_modified=False)

	activating = frappe.get_all("Annual Plan Item", filters={"plan_version": version.name, "item_state": "Draft"}, pluck="name")
	frappe.db.set_value("Annual Plan Item", {"plan_version": version.name, "item_state": "Draft"}, "item_state", "Active", update_modified=False)
	for name in activating:
		schedule.seed_forecast_from_baseline(name)
	frappe.db.set_value("Plan Source Allocation", {"plan_version": version.name, "allocation_state": "Draft"}, "allocation_state", "Active", update_modified=False)
	envelope.bump(version, version_status="Active", activated_at=now_datetime())
	frappe.db.set_value("Annual Plan", plan.name, {"active_version": version.name, "open_successor_version": ""}, update_modified=False)
	_publish_usage_events(version, plan, event_suffix=f"activate:{version.name}")


def begin_plan_update(*, plan_reference: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§8.2/§5.2 — create/reuse the sole Draft successor from the Active
	Version, copying its exact items (invariant 22)."""
	actor = authz.actor(user)
	payload = {"plan_reference": plan_reference}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	name = frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference})
	if not name:
		authz.not_found()
	plan = envelope.locked("Annual Plan", name)
	authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	if not plan.active_version:
		fail("PLN_STALE_WRITE")
	if plan.open_successor_version:
		existing_status = frappe.db.get_value("Annual Plan Version", plan.open_successor_version, "version_status")
		if existing_status not in ("Active", "Superseded", "Cancelled"):
			result = {"ok": True, "idempotent": True, "action": "reused", "successor_version": plan.open_successor_version}
			envelope.record_command(
				idempotency_key=idempotency_key, command="BeginPlanUpdate", payload=payload, result=result,
				document_type="Annual Plan Version", document_name=plan.open_successor_version, actor=actor,
				fixture_namespace=cstr(plan.fixture_namespace),
			)
			return result
	active_version = frappe.get_doc("Annual Plan Version", plan.active_version)
	number = _next_plan_version_number(plan.name)
	successor = frappe.get_doc(
		{
			"doctype": "Annual Plan Version",
			"version_reference": f"{plan.plan_reference}-V{number}",
			"annual_plan": plan.name,
			"version_number": number,
			"based_on_version": active_version.name,
			"version_status": "Draft",
			"funding_state": "Not requested",
			"record_version": 0,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	_copy_version_content(active_version.name, successor, cstr(plan.fixture_namespace))
	frappe.db.set_value("Annual Plan", plan.name, "open_successor_version", successor.name, update_modified=False)
	result = {"ok": True, "idempotent": False, "action": "created", "successor_version": successor.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="BeginPlanUpdate", payload=payload, result=result,
		document_type="Annual Plan Version", document_name=successor.name, actor=actor,
		fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


def _no_downstream_use(item) -> bool:
	"""§12.12 — fresh downstream check (drawdown, Tender handoff, commitment,
	contract). The drawdown ledger is the one downstream source in this repo."""
	return not frappe.db.exists("Plan Drawdown Reference", {"plan_item_id": item.plan_item_id, "drawdown_state": "Active"})


def remove_plan_item_in_successor(*, plan_item: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"plan_item": plan_item}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	from kentender_procurement.procurement_planning.services import plan_read

	item = envelope.locked("Annual Plan Item", plan_read.resolve_item_doc_name(plan_item))
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	if version.version_status != "Draft" or not version.based_on_version:
		fail("PLN_STALE_WRITE")
	envelope.check_record_version(item, expected_record_version)
	if item.item_state != "Draft":
		fail("PLN_STALE_WRITE")
	if not _no_downstream_use(item):
		fail("PLN_REMOVAL_BLOCKED")
	envelope.bump(item, item_state="Removed in successor")
	result = {"ok": True, "idempotent": False, "action": "removed", "plan_item": item.plan_item_id}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RemovePlanItemInSuccessor", payload=payload, result=result,
		document_type="Annual Plan Item", document_name=item.name, actor=actor,
		fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def cancel_plan_update(*, plan_reference: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§8.2 / invariant 21 — cancel the successor; the Active Version and
	every Budget balance are unchanged."""
	actor = authz.actor(user)
	payload = {"plan_reference": plan_reference}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	name = frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference})
	if not name:
		authz.not_found()
	plan = envelope.locked("Annual Plan", name)
	authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	successor_name = cstr(plan.open_successor_version)
	if not successor_name:
		fail("PLN_STALE_WRITE")
	successor = frappe.get_doc("Annual Plan Version", successor_name)
	if successor.version_status != "Draft" or not successor.based_on_version:
		fail("PLN_STALE_WRITE")
	envelope.check_record_version(successor, expected_record_version)
	for task in frappe.get_all("Plan Finance Task", filters={"plan_version": successor.name, "status": "Open"}, pluck="name"):
		frappe.db.set_value("Plan Finance Task", task, "status", "Cancelled", update_modified=False)
	envelope.bump(successor, version_status="Cancelled")
	frappe.db.set_value("Annual Plan", plan.name, "open_successor_version", "", update_modified=False)
	result = {"ok": True, "idempotent": False, "action": "cancelled", "successor_version": successor.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="CancelPlanUpdate", payload=payload, result=result,
		document_type="Annual Plan Version", document_name=successor.name, actor=actor,
		fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result
