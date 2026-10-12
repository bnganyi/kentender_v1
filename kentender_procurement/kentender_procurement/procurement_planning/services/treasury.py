# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.31 §5.5.2.3 / §7.2 — the withdrawal-for-correction recovery
route.

The Treasury submission evidence that the Accounting Officer recorded here under
v1.29 and v1.30 is retired: the Planner's publication confirmation
(`publication_confirmation.py`) replaces it, and the old rows stay as read-only
history. What remains is the Accounting Officer's request and the statutory
authority's decision to withdraw an approved plan that has no Current
confirmation. It travels through the same statutory-capacity governance task
machinery §6/§7.2 already uses, so it inherits capacity resolution, segregation
and the decision journal rather than inventing a parallel approval shape."""

from __future__ import annotations

from typing import Any

import json

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope, plan_governance, publication_pipeline, references
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_ACCOUNTING_OFFICER, ROLE_PLAN_STATUTORY_APPROVER
from kentender_procurement.procurement_planning.write_family import planning_command


def _confirmed_unpublished(version) -> bool:
	"""§5.5.2.3 (v1.31) — no Current publication confirmation exists. A saved
	Draft is not evidence and does not count. (v1.30 read: no matched
	acknowledgement and no pending or indeterminate attempt.)"""
	return not frappe.db.exists("Plan Publication Confirmation", {"plan_version": version.name, "confirmation_state": "Current"})


@planning_command
def request_plan_withdrawal(*, plan_version: str, reason: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `RequestPlanWithdrawal` — the Accounting Officer's request to the
	configured statutory authority; requires confirmed-unpublished content
	and no outstanding transmission. Content stays locked throughout."""
	actor = authz.actor(user)
	reason = " ".join(cstr(reason).split())
	payload = {"plan_version": plan_version, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not (10 <= len(reason) <= 500):
		fail("PLN_ENTRY_INCOMPLETE", "State the reason for the withdrawal request (10–500 characters).", {"field": "reason"})
	version = envelope.locked("Annual Plan Version", plan_version)
	assignment = authz.require_site_role(ROLE_ACCOUNTING_OFFICER, actor)
	if version.version_status not in ("Approved — publication pending", "Publication failed"):
		fail("PLN_WITHDRAWAL_NOT_PERMITTED")
	if not _confirmed_unpublished(version):
		fail("PLN_WITHDRAWAL_NOT_PERMITTED")
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	hold = publication_pipeline.hold_plan_publication(
		plan_version=version.name, reason=reason, hold_kind="Withdrawal request", idempotency_key=f"{idempotency_key}:hold", user=actor,
	)["hold"]
	capacity = plan_governance.capacity_for_site()
	task = frappe.get_doc(
		{
			"doctype": "Plan Governance Task", "task_reference": f"SAT-WD-{version.name}",
			"annual_plan": plan.name, "plan_version": version.name, "stage": "Statutory approval", "capacity": capacity,
			"status": "Open", "task_token": envelope.token(), "record_version": 0, "fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	result = {"ok": True, "idempotent": False, "action": "withdrawal_requested", "hold": hold, "task": task.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RequestPlanWithdrawal", payload=payload, result=result,
		document_type="Plan Governance Task", document_name=task.name, actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


@planning_command
def withdraw_approved_plan_for_correction(*, task: str, task_token: str, collective_resolution_reference: str = "", idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `WithdrawApprovedPlanForCorrection` — the configured statutory
	authority confirms the content is still unpublished with no outstanding
	transmission, then preserves the approved evidence as **Withdrawn for
	correction** and creates one copied Draft correction."""
	actor = authz.actor(user)
	payload = {"task": task, "collective_resolution_reference": cstr(collective_resolution_reference).strip()}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not task or not frappe.db.exists("Plan Governance Task", task):
		authz.not_found()
	task_doc = frappe.get_doc("Plan Governance Task", task)
	if task_doc.stage != "Statutory approval" or task_doc.status != "Open":
		fail("PLN_REVIEW_STALE")
	assignment = authz.require_site_role(ROLE_PLAN_STATUTORY_APPROVER, actor)
	envelope.assert_task_token(task_doc, task_token)
	resolution_reference = cstr(collective_resolution_reference).strip()
	if plan_governance.is_collective_capacity(task_doc.capacity) and not resolution_reference:
		fail("PLN_COLLECTIVE_RESOLUTION_REQUIRED", detail={"field": "collective_resolution_reference"})
	version = envelope.locked("Annual Plan Version", task_doc.plan_version)
	if version.version_status not in ("Approved — publication pending", "Publication failed"):
		fail("PLN_WITHDRAWAL_NOT_PERMITTED")
	hold_name = publication_pipeline._active_hold(version.name)
	if not hold_name or frappe.db.get_value("Plan Publication Hold", hold_name, "hold_kind") != "Withdrawal request":
		fail("PLN_WITHDRAWAL_NOT_PERMITTED", "No valid Accounting Officer withdrawal request is open for this Plan Version.")
	if not _confirmed_unpublished(version):
		fail("PLN_WITHDRAWAL_NOT_PERMITTED")
	plan = envelope.locked("Annual Plan", version.annual_plan)

	decision = frappe.get_doc(
		{
			"doctype": "Plan Governance Decision", "decision_reference": f"APP-WD-{version.name}",
			"task": task_doc.name, "plan_version": version.name, "stage": task_doc.stage, "decision": "Withdraw for correction",
			"capacity": task_doc.capacity, "collective_resolution_reference": resolution_reference or None, "actor": actor,
			"authority_snapshot": authz.authority_snapshot(assignment), "decided_at": now_datetime(), "command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(task_doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(version, version_status="Withdrawn for correction")
	frappe.db.set_value("Plan Publication Hold", hold_name, {"hold_state": "Released", "released_at": now_datetime(), "withdrawal_decision": decision.name, "reconciliation_outcome": "Confirmed unpublished"}, update_modified=False)

	number = plan_governance._next_plan_version_number(plan.name)
	correction = frappe.get_doc(
		{
			"doctype": "Annual Plan Version", "version_reference": f"{plan.plan_reference}-V{number}", "annual_plan": plan.name,
			"version_number": number, "based_on_version": version.based_on_version or None, "correction_of_plan_version": version.name,
			"version_status": "Draft", "funding_state": "Confirmed" if version.funding_state == "Confirmed" else "Not requested",
			"funding_line_totals_hash": version.funding_line_totals_hash if version.funding_state == "Confirmed" else None,
			"source_cohort": version.source_cohort or json.dumps(plan_governance.source_cohort(version.name)),
			"project_name": version.project_name, "record_version": 0, "fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	plan_governance._copy_version_content(version.name, correction, cstr(plan.fixture_namespace))
	frappe.db.set_value("Annual Plan", plan.name, "open_successor_version", correction.name, update_modified=False)

	result = {"ok": True, "idempotent": False, "action": "withdrawn_for_correction", "correction_version": correction.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="WithdrawApprovedPlanForCorrection", payload=payload, result=result,
		document_type="Plan Governance Decision", document_name=decision.name, actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result
