# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §5.2/§6.1/§8.2 — Annual Plan governance (Slice F).

`SubmitConsolidatedPlan`/`SubmitCorrectedPlan` freeze the exact immutable
Plan Version (all sources allocated, every item complete and Finance
current) and create the Accounting Officer task; `AdoptAndSubmitPlan`
records adoption and creates exactly one statutory-approval task resolved
from `Procuring Entity.entity_type` (§4.12: "resolved from governed PE
data" — MVP-1 has no dedicated jurisdiction-routing table, so this reads the
one governed field that already carries it); `ApproveAnnualPlan` moves the
Version to publication pending; `ReturnPlanVersion` (used at both stages)
preserves the submitted Version and creates the next numbered Draft
correction containing exactly its sources — including their finance state,
per §5.2: a correction proceeds without creating replacement reservations
when every retained reservation stays current.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import (
	authority,
	envelope,
	plan_finance,
	plan_read,
	references,
)
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PROCUREMENT_PLANNER,
)

STAGE_AO = "Accounting Officer adoption"
STAGE_STATUTORY = "Statutory approval"

_BOARD_ENTITY_TYPES = {"State Corporation", "Public University"}
_COUNTY_ENTITY_TYPES = {"County Government"}


def _capacity_for_pe(procuring_entity: str) -> str:
	"""§4.12/§6 — the one statutory route applicable to the PE, resolved from
	its governed `entity_type` (Ministry/Judiciary/Commission/Other route to
	the Cabinet Secretary; County Government to the County Executive
	Committee Member; a corporate/university PE to its governing body)."""
	entity_type = cstr(frappe.db.get_value("Procuring Entity", procuring_entity, "entity_type"))
	if entity_type in _COUNTY_ENTITY_TYPES:
		return "County Executive Committee Member"
	if entity_type in _BOARD_ENTITY_TYPES:
		return "Board of Directors or similar governing body"
	return "Responsible Cabinet Secretary"


def _is_board_capacity(capacity: str) -> bool:
	return capacity == "Board of Directors or similar governing body"


def _authorise_planner(actor: str, procuring_entity: str) -> None:
	authority.require_scope(actor, roles=(ROLE_PROCUREMENT_PLANNER,), procuring_entity=procuring_entity)


def _open_task(task_name: str, *, stage: str | None = None):
	if not task_name or not frappe.db.exists("Plan Governance Task", task_name):
		authority.not_found()
	task = frappe.get_doc("Plan Governance Task", task_name)
	if stage and task.stage != stage:
		authority.not_found()
	if task.status != "Open":
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")
	return task


def _stage_role(stage: str) -> str:
	return ROLE_ACCOUNTING_OFFICER if stage == STAGE_AO else ROLE_PLAN_STATUTORY_APPROVER


def _authorise_stage(actor: str, task) -> None:
	authority.require_scope(actor, roles=(_stage_role(task.stage),), procuring_entity=task.procuring_entity)


def _ao_decision_actor(version_name: str) -> str:
	"""The actor who adopted this Version as Accounting Officer, if any —
	§6.1's segregation chain for the statutory stage."""
	ao_task = frappe.db.get_value(
		"Plan Governance Task", {"plan_version": version_name, "stage": STAGE_AO}, "decision"
	)
	if not ao_task:
		return ""
	return cstr(frappe.db.get_value("Plan Governance Decision", ao_task, "actor"))


def _maker_checker(actor: str, version) -> None:
	conflicts = {cstr(version.submitted_by_user), _ao_decision_actor(version.name)}
	conflicts.discard("")
	if actor in conflicts:
		fail(
			"PLN_SEGREGATION_CONFLICT",
			"You cannot make this decision because you performed an incompatible earlier action.",
		)


def _next_plan_version_number(annual_plan: str) -> int:
	rows = frappe.get_all("Annual Plan Version", filters={"annual_plan": annual_plan}, pluck="version_number")
	return max([int(n or 0) for n in rows] or [0]) + 1


def _build_snapshot(version_name: str, procuring_entity: str) -> list[dict[str, Any]]:
	"""The exact immutable rows DES-11/12's Plan table renders, frozen once
	at submission — governance tasks read this JSON, never the live tables."""
	from kentender_procurement.procurement_planning.services import strategy_gateway

	eligible = {
		row["id"]: row for row in strategy_gateway.list_eligible_strategic_objectives(
			procuring_entity=procuring_entity,
		)
	}
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")},
		fields=[
			"name", "plan_item_id", "title", "requirement_type", "procurement_method",
			"strategic_objective", "finance_state", "delivery_completion_date",
		],
		order_by="creation asc",
	)
	rows = []
	for item in items:
		allocations = frappe.get_all(
			"Plan Source Allocation",
			filters={"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
			fields=["organisation_unit", "source_origin", "quantity", "unit", "indicative_amount"],
		)
		departments = sorted({
			cstr(frappe.db.get_value("Organisation Unit", a.organisation_unit, "unit_name") or a.organisation_unit)
			for a in allocations
		})
		origins = {a.source_origin for a in allocations}
		units = {a.unit for a in allocations}
		total_qty = sum(flt(a.quantity) for a in allocations)
		unit_label = cstr(frappe.db.get_value("Unit Of Measure", allocations[0].unit, "unit_label")) if allocations else ""
		value = sum(flt(a.indicative_amount) for a in allocations)
		objective = eligible.get(cstr(item.strategic_objective), {})
		rows.append(
			{
				"plan_item_id": item.plan_item_id,
				"title": item.title,
				"department": " / ".join(departments),
				"source_origin": next(iter(origins)) if len(origins) == 1 else "Multiple",
				"quantity_display": f"{total_qty:g} {unit_label.lower()}".strip() if units else "",
				"strategic_objective_label": objective.get("title", ""),
				"procurement_method": cstr(item.procurement_method),
				"value": value,
				"value_display": plan_read._money(value),
				"delivery_completion_display": plan_read._date(item.delivery_completion_date),
				"finance_state": item.finance_state,
			}
		)
	return rows


def _validate_ready_to_submit(version, plan) -> list:
	"""§8.2 `SubmitConsolidatedPlan`/`SubmitCorrectedPlan`: every accepted
	source allocated, every item complete and Finance current."""
	unallocated = [
		row for row in plan_read._accepted_entry_rows(plan.pe_fy_context)
		if row["dpp_entry"] not in plan_read._allocated_dpp_entries(version.name)
	]
	if unallocated:
		fail(
			"PLN_ENTRY_INCOMPLETE",
			"Every accepted departmental entry must be allocated to a Plan Item before submission.",
		)
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version.name, "item_state": ("!=", "Dissolved")},
		pluck="name",
	)
	if not items:
		fail("PLN_ENTRY_INCOMPLETE", "Form at least one Plan Item before submission.")
	item_docs = []
	for name in items:
		item = frappe.get_doc("Annual Plan Item", name)
		allocations = plan_finance._allocations(item.name)
		plan_finance.validate_item_complete(item, allocations, plan)
		if item.finance_state != "Confirmed":
			fail(
				"PLN_ENTRY_INCOMPLETE",
				f"Every Plan Item must have Confirmed funding before submission: {item.plan_item_id}.",
			)
		item_docs.append(item)
	return item_docs


def submit_consolidated_plan(
	*, plan_version: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {"plan_version": plan_version}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise_planner(actor, plan.procuring_entity)
	if version.version_status != "Draft":
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")
	envelope.check_record_version(version, expected_record_version)

	_validate_ready_to_submit(version, plan)
	snapshot = _build_snapshot(version.name, plan.procuring_entity)
	snapshot_json = json.dumps(snapshot, sort_keys=True)
	envelope.bump(
		version,
		version_status="Awaiting Accounting Officer",
		submitted_snapshot=snapshot_json,
		snapshot_hash=hashlib.sha256(snapshot_json.encode()).hexdigest(),
		submitted_by_user=actor,
		submitted_at=now_datetime(),
	)
	task = frappe.get_doc(
		{
			"doctype": "Plan Governance Task",
			"task_reference": references.governance_task_reference(STAGE_AO, version.name),
			"annual_plan": plan.name,
			"plan_version": version.name,
			"stage": STAGE_AO,
			"capacity": "Accounting Officer",
			"procuring_entity": plan.procuring_entity,
			"status": "Open",
			"task_token": envelope.token(),
			"record_version": 0,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	result = {"ok": True, "idempotent": False, "action": "submitted", "task": task.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="SubmitConsolidatedPlan", payload=payload,
		result=result, document_type="Plan Governance Task", document_name=task.name,
		actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


def adopt_and_submit_plan(
	*, task: str, task_token: str, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {"task": task}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	task_doc = _open_task(task, stage=STAGE_AO)
	_authorise_stage(actor, task_doc)
	envelope.assert_task_token(task_doc, task_token)
	version = envelope.locked("Annual Plan Version", task_doc.plan_version)
	_maker_checker(actor, version)
	if version.version_status != "Awaiting Accounting Officer":
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")

	decision = frappe.get_doc(
		{
			"doctype": "Plan Governance Decision",
			"decision_reference": references.governance_decision_reference(STAGE_AO, version.name),
			"task": task_doc.name,
			"plan_version": version.name,
			"stage": STAGE_AO,
			"decision": "Adopt and submit",
			"capacity": "Accounting Officer",
			"actor": actor,
			"authority_snapshot": authority.authority_snapshot(
				actor, role=ROLE_ACCOUNTING_OFFICER, values=(task_doc.procuring_entity,)
			),
			"decided_at": now_datetime(),
			"command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(task_doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(version, version_status="Awaiting statutory approval")

	capacity = _capacity_for_pe(task_doc.procuring_entity)
	statutory_task = frappe.get_doc(
		{
			"doctype": "Plan Governance Task",
			"task_reference": references.governance_task_reference(STAGE_STATUTORY, version.name),
			"annual_plan": task_doc.annual_plan,
			"plan_version": version.name,
			"stage": STAGE_STATUTORY,
			"capacity": capacity,
			"procuring_entity": task_doc.procuring_entity,
			"status": "Open",
			"task_token": envelope.token(),
			"record_version": 0,
			"fixture_namespace": cstr(task_doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	result = {
		"ok": True, "idempotent": False, "action": "adopted", "statutory_task": statutory_task.name,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="AdoptAndSubmitPlan", payload=payload,
		result=result, document_type="Plan Governance Decision", document_name=decision.name,
		actor=actor, fixture_namespace=cstr(task_doc.fixture_namespace),
	)
	return result


def approve_annual_plan(
	*, task: str, task_token: str, resolution_reference: str = "", idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	resolution_reference = cstr(resolution_reference).strip()
	payload = {"task": task, "resolution_reference": resolution_reference}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	task_doc = _open_task(task, stage=STAGE_STATUTORY)
	_authorise_stage(actor, task_doc)
	envelope.assert_task_token(task_doc, task_token)
	version = envelope.locked("Annual Plan Version", task_doc.plan_version)
	_maker_checker(actor, version)
	if version.version_status != "Awaiting statutory approval":
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")
	if _is_board_capacity(task_doc.capacity) and not resolution_reference:
		fail(
			"PLN_ENTRY_INCOMPLETE",
			"A Board or similar governing body's approval requires a resolution reference.",
		)

	decision = frappe.get_doc(
		{
			"doctype": "Plan Governance Decision",
			"decision_reference": references.governance_decision_reference(STAGE_STATUTORY, version.name),
			"task": task_doc.name,
			"plan_version": version.name,
			"stage": STAGE_STATUTORY,
			"decision": "Approve Annual Procurement Plan",
			"capacity": task_doc.capacity,
			"resolution_reference": resolution_reference or None,
			"actor": actor,
			"authority_snapshot": authority.authority_snapshot(
				actor, role=ROLE_PLAN_STATUTORY_APPROVER, values=(task_doc.procuring_entity,)
			),
			"decided_at": now_datetime(),
			"command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(task_doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(version, version_status="Approved — publication pending")
	result = {"ok": True, "idempotent": False, "action": "approved", "plan_version": version.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ApproveAnnualPlan", payload=payload,
		result=result, document_type="Plan Governance Decision", document_name=decision.name,
		actor=actor, fixture_namespace=cstr(task_doc.fixture_namespace),
	)
	return result


def _copy_version_content(source_version: str, target_version, fixture_namespace: str) -> None:
	"""§4.8/§5.2 — a correction contains exactly the returned Version's
	sources, including their current finance state; no replacement
	reservation is created here (§7.3 — Confirmed items stay Confirmed
	until Budget's own revalidation says otherwise)."""
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": source_version, "item_state": ("!=", "Dissolved")},
		fields=[
			"name", "plan_item_id", "title", "description", "strategic_objective",
			"strategy_plan", "strategy_plan_version", "objective_path", "requirement_type",
			"procurement_method", "aggregation_reason", "invitation_date", "bid_opening_date",
			"evaluation_completion_date", "award_approval_date", "award_notification_date",
			"contract_signing_date", "delivery_completion_date", "finance_state",
		],
	)
	for source_item in items:
		new_item = frappe.get_doc(
			{
				"doctype": "Annual Plan Item",
				"plan_item_id": source_item.plan_item_id,
				"plan_version": target_version.name,
				"title": source_item.title,
				"description": source_item.description,
				"strategic_objective": source_item.strategic_objective,
				"strategy_plan": source_item.strategy_plan,
				"strategy_plan_version": source_item.strategy_plan_version,
				"objective_path": source_item.objective_path,
				"requirement_type": source_item.requirement_type,
				"procurement_method": source_item.procurement_method,
				"aggregation_reason": source_item.aggregation_reason,
				"invitation_date": source_item.invitation_date,
				"bid_opening_date": source_item.bid_opening_date,
				"evaluation_completion_date": source_item.evaluation_completion_date,
				"award_approval_date": source_item.award_approval_date,
				"award_notification_date": source_item.award_notification_date,
				"contract_signing_date": source_item.contract_signing_date,
				"delivery_completion_date": source_item.delivery_completion_date,
				"item_state": "Draft",
				"finance_state": source_item.finance_state,
				"record_version": 0,
				"fixture_namespace": fixture_namespace,
			}
		).insert(ignore_permissions=True)
		allocations = frappe.get_all(
			"Plan Source Allocation",
			filters={"plan_item": source_item.name, "allocation_state": ("in", ("Draft", "Active"))},
			fields=[
				"name", "allocation_id", "dpp_entry", "source_origin", "need", "need_version",
				"organisation_unit", "quantity", "unit", "required_by_date", "budget_line",
				"indicative_amount",
			],
		)
		for allocation in allocations:
			new_allocation = frappe.get_doc(
				{
					"doctype": "Plan Source Allocation",
					"allocation_id": allocation.allocation_id,
					"plan_item": new_item.name,
					"plan_item_id": new_item.plan_item_id,
					"plan_version": target_version.name,
					"dpp_entry": allocation.dpp_entry,
					"source_origin": allocation.source_origin,
					"need": allocation.need,
					"need_version": allocation.need_version,
					"organisation_unit": allocation.organisation_unit,
					"quantity": allocation.quantity,
					"unit": allocation.unit,
					"required_by_date": allocation.required_by_date,
					"budget_line": allocation.budget_line,
					"indicative_amount": allocation.indicative_amount,
					"allocation_state": "Draft",
					"fixture_namespace": fixture_namespace,
				}
			).insert(ignore_permissions=True)
			# carry forward the reservation reference under the new allocation/
			# item, so a later dissolve/revalidate still finds it (finding: a
			# correction retains Confirmed items' reservations unless Budget's
			# own revalidation says otherwise — §5.2/§7.3).
			old_refs = frappe.get_all(
				"Plan Reservation Reference",
				filters={"allocation": allocation.name},
				fields=["finance_decision", "reservation", "budget_line", "amount"],
			)
			for ref in old_refs:
				frappe.get_doc(
					{
						"doctype": "Plan Reservation Reference",
						"finance_decision": ref.finance_decision,
						"plan_item": new_item.name,
						"plan_item_id": new_item.plan_item_id,
						"allocation": new_allocation.name,
						"reservation": ref.reservation,
						"budget_line": ref.budget_line,
						"amount": ref.amount,
						"fixture_namespace": fixture_namespace,
					}
				).insert(ignore_permissions=True)


def return_plan_version(
	*, task: str, reason: str, task_token: str, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	reason = cstr(reason).strip()
	payload = {"task": task, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not (10 <= len(reason) <= 500):
		fail("PLN_ENTRY_INCOMPLETE", "State one actionable correction reason.")

	task_doc = _open_task(task)
	_authorise_stage(actor, task_doc)
	envelope.assert_task_token(task_doc, task_token)
	version = envelope.locked("Annual Plan Version", task_doc.plan_version)
	_maker_checker(actor, version)
	expected_status = "Awaiting Accounting Officer" if task_doc.stage == STAGE_AO else "Awaiting statutory approval"
	if version.version_status != expected_status:
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")

	decision = frappe.get_doc(
		{
			"doctype": "Plan Governance Decision",
			"decision_reference": references.governance_decision_reference(task_doc.stage, version.name),
			"task": task_doc.name,
			"plan_version": version.name,
			"stage": task_doc.stage,
			"decision": "Return for correction",
			"capacity": task_doc.capacity,
			"return_reason": reason,
			"actor": actor,
			"authority_snapshot": authority.authority_snapshot(
				actor, role=_stage_role(task_doc.stage), values=(task_doc.procuring_entity,)
			),
			"decided_at": now_datetime(),
			"command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(task_doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(version, version_status="Returned")

	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	correction = frappe.get_doc(
		{
			"doctype": "Annual Plan Version",
			"version_reference": f"{plan.plan_reference}-V{_next_plan_version_number(plan.name)}",
			"annual_plan": plan.name,
			"version_number": _next_plan_version_number(plan.name),
			"based_on_version": version.based_on_version or None,
			"correction_of_plan_version": version.name,
			"version_status": "Draft",
			"record_version": 0,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	_copy_version_content(version.name, correction, cstr(plan.fixture_namespace))
	frappe.db.set_value(
		"Annual Plan", plan.name, "open_successor_version", correction.name, update_modified=False,
	)
	result = {
		"ok": True, "idempotent": False, "action": "returned", "correction_version": correction.name,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ReturnPlanVersion", payload=payload,
		result=result, document_type="Plan Governance Decision", document_name=decision.name,
		actor=actor, fixture_namespace=cstr(task_doc.fixture_namespace),
	)
	return result


def submit_corrected_plan(
	*, plan_version: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	"""§5.3 invariant 23: a corrected Plan always restarts at Accounting
	Officer adoption. §5.2: revalidates every retained reservation first;
	an item whose reservation is no longer current flips Stale and blocks
	submission until Finance is requested again."""
	actor = cstr(user or frappe.session.user)
	payload = {"plan_version": plan_version}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise_planner(actor, plan.procuring_entity)
	if version.version_status != "Draft" or not version.correction_of_plan_version:
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")
	envelope.check_record_version(version, expected_record_version)

	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version.name, "item_state": ("!=", "Dissolved"), "finance_state": "Confirmed"},
		fields=["name"],
	)
	# revalidate every retained reservation once, across all confirmed items
	all_reservations = frappe.get_all(
		"Plan Reservation Reference",
		filters={"plan_item": ("in", [i.name for i in items] or ("",))},
		fields=["plan_item", "reservation"],
	)
	if all_reservations:
		from kentender_procurement.procurement_planning.services import budget_gateway

		outcome = budget_gateway.revalidate_planning_reservations(
			reservations=[r.reservation for r in all_reservations],
			correlation_id=idempotency_key, event_type="SubmitCorrectedPlan",
		)
		status_by_reservation = {row["reservation_id"]: row["status"] for row in outcome.get("reservations", [])}
		stale_items = {
			r.plan_item for r in all_reservations
			if status_by_reservation.get(r.reservation) not in ("Active", "Partially Converted")
		}
		if stale_items:
			frappe.db.set_value(
				"Annual Plan Item", {"name": ("in", list(stale_items))}, "finance_state", "Stale",
				update_modified=False,
			)
			fail(
				"PLN_FINANCE_STALE",
				"Funding confirmation is no longer current for one or more Plan Items. Request confirmation again.",
			)

	_validate_ready_to_submit(version, plan)
	snapshot = _build_snapshot(version.name, plan.procuring_entity)
	snapshot_json = json.dumps(snapshot, sort_keys=True)
	envelope.bump(
		version,
		version_status="Awaiting Accounting Officer",
		submitted_snapshot=snapshot_json,
		snapshot_hash=hashlib.sha256(snapshot_json.encode()).hexdigest(),
		submitted_by_user=actor,
		submitted_at=now_datetime(),
	)
	task = frappe.get_doc(
		{
			"doctype": "Plan Governance Task",
			"task_reference": references.governance_task_reference(STAGE_AO, version.name),
			"annual_plan": plan.name,
			"plan_version": version.name,
			"stage": STAGE_AO,
			"capacity": "Accounting Officer",
			"procuring_entity": plan.procuring_entity,
			"status": "Open",
			"task_token": envelope.token(),
			"record_version": 0,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	result = {"ok": True, "idempotent": False, "action": "submitted", "task": task.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="SubmitCorrectedPlan", payload=payload,
		result=result, document_type="Plan Governance Task", document_name=task.name,
		actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result
