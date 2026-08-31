# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §5.2/§7.3/§8.2 — Finance confirmation (Slice E).

`RequestFinanceConfirmation` is the Planner's own completion gate: unlike
`SavePlanItem` (partial, no validation), this fully validates the item
before creating or reusing one current `Plan Finance Task`. `ConfirmFunding`
consumes the short-lived `check_funding` token `GetFinanceTask` mints
(services/plan_read.py) and calls `reserve_funding` under Budget's own row
lock — all-or-none, never a partial reservation. `ReturnFromFinance` records
the required reason and creates no reservation. Both Budget decision
commands run as a system principal against Budget's own two contracts
(`budget_gateway._system_principal`): Budget's internal capability role
(`Finance Confirmation Officer`) is not Planning's `Budget Officer` role —
Planning authorises its own actor against its own role first, exactly the
same boundary `list_eligible_budget_lines` already crosses (found live the
first time this gateway path was actually exercised end-to-end).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, getdate, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import (
	authority,
	budget_gateway,
	envelope,
	plan_read,
	references,
)
from kentender_procurement.procurement_planning.services.plan_workbench import (
	SCHEDULE_FIELDS,
	_item_doc_name,
)
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_BUDGET_OFFICER,
	ROLE_PROCUREMENT_PLANNER,
)


def _authorise_planner(actor: str, procuring_entity: str) -> None:
	authority.require_scope(
		actor, roles=(ROLE_PROCUREMENT_PLANNER,), procuring_entity=procuring_entity,
	)


def _authorise_budget_officer(actor: str, procuring_entity: str) -> None:
	authority.require_scope(
		actor, roles=(ROLE_BUDGET_OFFICER,), procuring_entity=procuring_entity,
	)


def _open_task(task_name: str):
	if not task_name or not frappe.db.exists("Plan Finance Task", task_name):
		authority.not_found()
	task = frappe.get_doc("Plan Finance Task", task_name)
	if task.status != "Open":
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")
	return task


def _requesting_planner(task_name: str) -> str:
	"""§6.1 maker-checker: the Planner who requested this Finance task, via
	the command journal (Plan Finance Task carries no such field — §2.2
	forbids adding an undocumented one)."""
	return cstr(
		frappe.db.get_value(
			"Planning Command Journal",
			{
				"document_type": "Plan Finance Task", "document_name": task_name,
				"command": "RequestFinanceConfirmation",
			},
			"actor", order_by="occurred_at desc",
		)
	)


def _source_set_hash(allocations: list) -> str:
	material = sorted(
		(a.name, cstr(a.budget_line), f"{flt(a.indicative_amount):.2f}") for a in allocations
	)
	return hashlib.sha256(json.dumps(material).encode()).hexdigest()[:32]


def _allocations(item_name: str) -> list:
	return frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item_name, "allocation_state": ("in", ("Draft", "Active"))},
		fields=["name", "budget_line", "indicative_amount", "dpp_entry", "required_by_date"],
		order_by="creation asc",
	)


def request_finance_confirmation(
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
	_authorise_planner(actor, plan.procuring_entity)
	if item.item_state != "Draft" or version.version_status != "Draft":
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")
	envelope.check_record_version(item, expected_record_version)

	allocations = _allocations(item.name)
	if any(plan_read.source_correction_required(a.dpp_entry) for a in allocations):
		fail(
			"PLN_SOURCE_CORRECTION_REQUIRED",
			"A departmental source changed. Dissolve and re-form the affected Draft item before continuing.",
		)

	# §12.8 "fully validates in one transaction" — the completeness gate
	# Save draft deliberately skips.
	if not cstr(item.strategic_objective).strip():
		fail("PLN_OBJECTIVE_INELIGIBLE", "Select an Active Strategic Objective valid for this Plan.")
	from kentender_procurement.procurement_planning.services import strategy_gateway

	eligible = {
		row["id"] for row in strategy_gateway.list_eligible_strategic_objectives(
			procuring_entity=plan.procuring_entity,
		)
	}
	if cstr(item.strategic_objective) not in eligible:
		fail("PLN_OBJECTIVE_INELIGIBLE", "Select an Active Strategic Objective valid for this Plan.")
	if len(allocations) > 1 and not (20 <= len(cstr(item.aggregation_reason).strip()) <= 500):
		fail(
			"PLN_ENTRY_INCOMPLETE",
			"Aggregation reason must be 20-500 characters before Finance confirmation.",
		)
	dates = {}
	for field in SCHEDULE_FIELDS:
		raw = item.get(field)
		if not cstr(raw).strip():
			fail(
				"PLN_SCHEDULE_INVALID",
				"Correct the highlighted dates so the schedule is chronological and meets the required-by date.",
			)
		dates[field] = getdate(raw)
	ordered = [dates[f] for f in SCHEDULE_FIELDS]
	earliest_required_by = min(
		(getdate(a.required_by_date) for a in allocations if a.required_by_date), default=None,
	)
	if ordered != sorted(ordered) or (
		earliest_required_by and dates["delivery_completion_date"] > earliest_required_by
	):
		fail(
			"PLN_SCHEDULE_INVALID",
			"Correct the highlighted dates so the schedule is chronological and meets the required-by date.",
		)

	source_set_hash = _source_set_hash(allocations)
	required_amount = sum(flt(a.indicative_amount) for a in allocations)
	existing_name = frappe.db.get_value(
		"Plan Finance Task", {"plan_item": item.name, "status": "Open"}, "name"
	)
	if existing_name:
		task = frappe.get_doc("Plan Finance Task", existing_name)
		if task.source_set_hash != source_set_hash or flt(task.required_amount) != required_amount:
			envelope.bump(task, source_set_hash=source_set_hash, required_amount=required_amount)
		action = "reused"
	else:
		task = frappe.get_doc(
			{
				"doctype": "Plan Finance Task",
				"task_reference": references.finance_task_reference(item.plan_item_id),
				"plan_item": item.name,
				"plan_item_id": item.plan_item_id,
				"plan_version": version.name,
				"procuring_entity": plan.procuring_entity,
				"source_set_hash": source_set_hash,
				"required_amount": required_amount,
				"status": "Open",
				"task_token": envelope.token(),
				"record_version": 0,
				"fixture_namespace": cstr(item.fixture_namespace),
			}
		).insert(ignore_permissions=True)
		action = "requested"

	envelope.bump(item, finance_state="Awaiting Finance")
	result = {
		"ok": True, "idempotent": False, "action": action,
		"task": task.name, "task_reference": task.task_reference,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RequestFinanceConfirmation", payload=payload,
		result=result, document_type="Plan Finance Task", document_name=task.name,
		actor=actor, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def _decide(task, *, decision: str, actor: str, return_reason: str = "", idempotency_key: str = ""):
	decision_doc = frappe.get_doc(
		{
			"doctype": "Plan Finance Decision",
			"decision_reference": references.finance_decision_reference(task.task_reference),
			"task": task.name,
			"decision": decision,
			"return_reason": return_reason or None,
			"actor": actor,
			"authority_snapshot": authority.authority_snapshot(
				actor, role=ROLE_BUDGET_OFFICER, values=(task.procuring_entity,)
			),
			"decided_at": now_datetime(),
			"command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(task.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	return decision_doc


def confirm_funding(
	*, task: str, task_token: str, check_token: str, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {"task": task}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	task_doc = _open_task(task)
	_authorise_budget_officer(actor, task_doc.procuring_entity)
	envelope.assert_task_token(task_doc, task_token)
	if _requesting_planner(task_doc.name) == actor:
		fail(
			"PLN_SEGREGATION_CONFLICT",
			"You cannot make this decision because you performed an incompatible earlier action.",
		)
	item = envelope.locked("Annual Plan Item", task_doc.plan_item)
	allocations = _allocations(item.name)
	if _source_set_hash(allocations) != task_doc.source_set_hash:
		fail("PLN_FINANCE_STALE", "Funding confirmation is no longer current. Request confirmation again.")

	try:
		reserved = budget_gateway.reserve_funding(
			check_token=check_token, finance_task=task_doc.name,
			source_set_hash=task_doc.source_set_hash, idempotency_key=idempotency_key,
		)
	except frappe.ValidationError as exc:
		# `frappe.throw(msg, exc, title=...)` never attaches `title` to the
		# raised instance (frappe/utils/messages.py — it only labels the
		# client dialog); Budget's contract gives Python callers no
		# structured error code, only this message text to match on.
		if "Insufficient funding" in str(exc):
			fail(
				"PLN_FINANCE_SHORTFALL",
				"Funding is insufficient for one or more source allocations. No reservation was created.",
			)
		fail("PLN_FINANCE_STALE", "Funding confirmation is no longer current. Request confirmation again.")

	decision = _decide(task_doc, decision="Confirm funding", actor=actor, idempotency_key=idempotency_key)
	allocations_by_line = {a.budget_line: a for a in allocations}
	for row in reserved.get("reservations", []):
		allocation = allocations_by_line.get(row["budget_line"])
		frappe.get_doc(
			{
				"doctype": "Plan Reservation Reference",
				"finance_decision": decision.name,
				"plan_item": item.name,
				"plan_item_id": item.plan_item_id,
				"allocation": allocation.name if allocation else None,
				"reservation": row["reservation_id"],
				"budget_line": row["budget_line"],
				"amount": flt(row["original_amount"]),
				"fixture_namespace": cstr(item.fixture_namespace),
			}
		).insert(ignore_permissions=True)

	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(item, finance_state="Confirmed")
	result = {"ok": True, "idempotent": False, "action": "confirmed", "task": task_doc.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ConfirmFunding", payload=payload,
		result=result, document_type="Plan Finance Decision", document_name=decision.name,
		actor=actor, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def return_from_finance(
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
	_authorise_budget_officer(actor, task_doc.procuring_entity)
	envelope.assert_task_token(task_doc, task_token)
	if _requesting_planner(task_doc.name) == actor:
		fail(
			"PLN_SEGREGATION_CONFLICT",
			"You cannot make this decision because you performed an incompatible earlier action.",
		)
	item = envelope.locked("Annual Plan Item", task_doc.plan_item)

	decision = _decide(
		task_doc, decision="Return to planner", actor=actor,
		return_reason=reason, idempotency_key=idempotency_key,
	)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(item, finance_state="Returned")
	result = {"ok": True, "idempotent": False, "action": "returned", "task": task_doc.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ReturnFromFinance", payload=payload,
		result=result, document_type="Plan Finance Decision", document_name=decision.name,
		actor=actor, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def revalidate_item_reservations(plan_item: str, *, event_type: str, correlation_id: str) -> dict[str, Any]:
	"""§7.3/§4.11 `RevalidatePlanningReservations` for one item's confirmed
	reservations. Built and tested here; no caller is wired in Phase 7 —
	the trigger points (SubmitCorrectedPlan, Requisition eligibility) land
	in Phase 8/10."""
	item_name = _item_doc_name(plan_item)
	reservations = frappe.get_all(
		"Plan Reservation Reference",
		filters={"plan_item": item_name},
		pluck="reservation",
	)
	if not reservations:
		return {"ok": True, "reservations": []}
	return budget_gateway.revalidate_planning_reservations(
		reservations=reservations, correlation_id=correlation_id, event_type=event_type,
	)
