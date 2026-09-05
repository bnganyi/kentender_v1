# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §4.11/§5.2/§7.3/§8.2 — one plan-level funding confirmation.

`RequestPlanFundingConfirmation` validates Plan readiness (exact blockers,
never a score), computes the affordability statement through Budget's
non-mutating `check_plan_affordability` and creates or reuses the one
current Finance task for the Version. `ConfirmPlanFunding` re-checks
affordability under lock and records the decision with the statement as it
stood; it creates no reservation, no ledger event and no Budget record.
`ReturnFromFinance` records the required reason. Within-approved blocks;
within-currently-available is advisory (§7.3).

Funding evidence becomes Stale when the plan's per-line totals change or a
line's approved amount changes through a Budget successor (§4.11) —
recomputed at read and at submission from the confirmed statement.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import budget_gateway, envelope, readiness, references
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_PROCUREMENT_PLANNER,
)


def _open_task(task_name: str):
	if not task_name or not frappe.db.exists("Plan Finance Task", task_name):
		authz.not_found()
	task = frappe.get_doc("Plan Finance Task", task_name)
	if task.status != "Open":
		fail("PLN_REVIEW_STALE")
	return task


def affordability_statement(plan, version) -> dict[str, Any]:
	totals = readiness.line_totals(version.name)
	statement = budget_gateway.check_plan_affordability(fiscal_year=plan.fiscal_year, planned_totals=totals)
	statement["line_totals_hash"] = readiness.line_totals_hash(totals)
	statement["plan_value"] = sum(totals.values())
	return statement


def validate_plan_ready(version, plan) -> dict[str, Any]:
	"""§8.2 — the exact blocker list; raises the first blocking code."""
	from kentender_procurement.procurement_planning.services import plan_read

	report = plan_read.plan_readiness(version, plan)
	if report["blockers"]:
		first = report["blockers"][0]
		fail(first["code"], first.get("message") or "", {k: v for k, v in first.items() if k != "code"})
	return report


def funding_is_current(version, statement: dict[str, Any] | None = None) -> bool:
	"""§4.11 — Confirmed, and neither the per-line totals nor any line's
	approved amount has changed since the confirmation."""
	if version.funding_state != "Confirmed":
		return False
	totals = readiness.line_totals(version.name)
	if readiness.line_totals_hash(totals) != cstr(version.funding_line_totals_hash):
		return False
	decision = _confirmed_decision(version.name)
	if not decision:
		return False
	confirmed = json.loads(decision.affordability_statement or "{}")
	current = statement or budget_gateway.check_plan_affordability(fiscal_year=frappe.db.get_value("Annual Plan", version.annual_plan, "fiscal_year"), planned_totals=totals)
	approved_then = {row["budget_line"]: flt(row["approved"]) for row in confirmed.get("lines", [])}
	for row in current.get("lines", []):
		if row["budget_line"] in totals and approved_then.get(row["budget_line"]) != flt(row["approved"]):
			return False
	return True


def _confirmed_decision(version_name: str):
	# §5.2 — a correction carries the returned Version's confirmation forward,
	# so the decision may sit on an earlier Version of the same evidence chain.
	chain = authz.evidence_chain(version_name) or [version_name]
	tasks = frappe.get_all("Plan Finance Task", filters={"plan_version": ("in", chain)}, pluck="name")
	if not tasks:
		return None
	name = frappe.db.get_value(
		"Plan Finance Decision", {"task": ("in", tasks), "decision": "Confirm plan funding"}, "name", order_by="decided_at desc"
	)
	return frappe.get_doc("Plan Finance Decision", name) if name else None


def request_plan_funding_confirmation(*, plan_version: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"plan_version": plan_version}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	if version.version_status != "Draft":
		fail("PLN_STALE_WRITE")
	envelope.check_record_version(version, expected_record_version)

	validate_plan_ready(version, plan)
	statement = affordability_statement(plan, version)
	if not statement.get("within_approved"):
		fail("PLN_PLAN_NOT_AFFORDABLE", detail={"failing_lines": statement.get("failing_lines", [])})

	existing = frappe.db.get_value("Plan Finance Task", {"plan_version": version.name, "status": "Open"}, "name")
	if existing:
		task = frappe.get_doc("Plan Finance Task", existing)
		envelope.bump(task, line_totals_hash=statement["line_totals_hash"], plan_value=statement["plan_value"], affordability_statement=json.dumps(statement, default=str))
		action = "reused"
	else:
		task = frappe.get_doc(
			{
				"doctype": "Plan Finance Task",
				"task_reference": references.finance_task_reference(plan.plan_reference),
				"plan_version": version.name,
				"plan_value": statement["plan_value"],
				"line_totals_hash": statement["line_totals_hash"],
				"affordability_statement": json.dumps(statement, default=str),
				"status": "Open",
				"task_token": envelope.token(),
				"record_version": 0,
				"fixture_namespace": cstr(plan.fixture_namespace),
			}
		).insert(ignore_permissions=True)
		action = "requested"
	envelope.bump(version, funding_state="Awaiting Finance")
	result = {"ok": True, "idempotent": False, "action": action, "task": task.name, "task_reference": task.task_reference}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RequestPlanFundingConfirmation", payload=payload, result=result,
		document_type="Plan Finance Task", document_name=task.name, actor=actor,
		fixture_namespace=cstr(plan.fixture_namespace),
	)
	_notify_finance_officers(task, plan)
	return result


def _notify_finance_officers(task, plan) -> None:
	from kentender_core.services.authorization import resolve_assignments
	from kentender_procurement.procurement_planning.services import notifications

	users = frappe.get_all(
		"User Responsibility Assignment", filters={"business_role": ROLE_FINANCE_CONFIRMATION_OFFICER, "status": "Enabled"}, pluck="user", distinct=True,
	)
	for user in sorted(set(users)):
		if not resolve_assignments(user, ROLE_FINANCE_CONFIRMATION_OFFICER):
			continue
		notifications.notify_task(
			for_user=user, subject=f"Confirm plan funding — {plan.title}",
			message="The consolidated plan is ready for funding confirmation against the approved budget.",
			document_type="Plan Finance Task", document_name=task.name, event_type="planning.finance_requested",
			route=f"/app/procurement-planning/finance/{task.name}", correlation_key=f"pln:finance:{task.name}:{user}",
		)


def _decide(task, *, decision: str, actor: str, assignment, statement: dict[str, Any], return_reason: str = "", idempotency_key: str = ""):
	version_number = frappe.db.get_value("Annual Plan Version", task.plan_version, "version_number")
	return frappe.get_doc(
		{
			"doctype": "Plan Finance Decision",
			"decision_reference": references.finance_decision_reference(task.task_reference, version_number),
			"task": task.name,
			"decision": decision,
			"return_reason": return_reason or None,
			"affordability_statement": json.dumps(statement, default=str),
			"actor": actor,
			"authority_snapshot": authz.authority_snapshot(assignment),
			"decided_at": now_datetime(),
			"command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(task.fixture_namespace),
		}
	).insert(ignore_permissions=True)


def confirm_plan_funding(*, task: str, task_token: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"task": task}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	task_doc = _open_task(task)
	assignment = authz.require_site_role(ROLE_FINANCE_CONFIRMATION_OFFICER, actor)
	envelope.assert_task_token(task_doc, task_token)
	authz.require_not_segregated(actor, authz.ACTION_FINANCE_DECIDE, plan_version=task_doc.plan_version)
	version = envelope.locked("Annual Plan Version", task_doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	if version.version_status != "Draft" or version.funding_state != "Awaiting Finance":
		fail("PLN_REVIEW_STALE")

	statement = affordability_statement(plan, version)
	if statement["line_totals_hash"] != cstr(task_doc.line_totals_hash):
		fail("PLN_FINANCE_STALE")
	if not statement.get("within_approved"):
		fail("PLN_PLAN_NOT_AFFORDABLE", detail={"failing_lines": statement.get("failing_lines", [])})

	decision = _decide(task_doc, decision="Confirm plan funding", actor=actor, assignment=assignment, statement=statement, idempotency_key=idempotency_key)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(version, funding_state="Confirmed", funding_line_totals_hash=statement["line_totals_hash"])
	result = {"ok": True, "idempotent": False, "action": "confirmed", "task": task_doc.name, "decision": decision.decision_reference}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ConfirmPlanFunding", payload=payload, result=result,
		document_type="Plan Finance Decision", document_name=decision.name, actor=actor,
		fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


def return_from_finance(*, task: str, reason: str, task_token: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	reason = cstr(reason).strip()
	payload = {"task": task, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not (10 <= len(reason) <= 500):
		fail("PLN_ENTRY_INCOMPLETE", "State one actionable correction reason.", {"field": "reason"})
	task_doc = _open_task(task)
	assignment = authz.require_site_role(ROLE_FINANCE_CONFIRMATION_OFFICER, actor)
	envelope.assert_task_token(task_doc, task_token)
	authz.require_not_segregated(actor, authz.ACTION_FINANCE_DECIDE, plan_version=task_doc.plan_version)
	version = envelope.locked("Annual Plan Version", task_doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	if version.funding_state != "Awaiting Finance":
		fail("PLN_REVIEW_STALE")
	statement = json.loads(task_doc.affordability_statement or "{}")
	decision = _decide(task_doc, decision="Return to planner", actor=actor, assignment=assignment, statement=statement, return_reason=reason, idempotency_key=idempotency_key)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(version, funding_state="Returned")
	result = {"ok": True, "idempotent": False, "action": "returned", "task": task_doc.name, "decision": decision.decision_reference}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ReturnFromFinance", payload=payload, result=result,
		document_type="Plan Finance Decision", document_name=decision.name, actor=actor,
		fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result
