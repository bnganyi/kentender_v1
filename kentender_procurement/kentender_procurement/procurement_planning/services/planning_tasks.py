"""Stable, assignment-backed identities for protected Planning tasks."""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_core.services.authorization_policy import evaluate_capability
from kentender_core.services.workflow_routing import RoutingContext
from kentender_core.services.workflow_tasks import (
	TaskSpec,
	create_routed_task,
	get_authorized_task,
	invalidate_task,
	transition_task,
)
from kentender_procurement.procurement_planning.services._invariants import new_concurrency_token


def task_owner(task) -> str:
	return cstr(task.claimed_by or task.assigned_user_id or task.queue_id)


def create_governed_planning_task(
	*,
	prefix: str,
	record: object,
	id_field: str,
	iteration_field: str,
	task_type: str,
	subject_type: str,
	subject_id: str,
	procuring_entity: str,
	financial_year: str,
	organisation_unit: str = "",
	predecessor_task_id: str = "",
	idempotency_key: str,
	actor: str,
):
	task_id, iteration, _token = next_task_identity(
		prefix=prefix,
		record=record,
		id_field=id_field,
		iteration_field=iteration_field,
	)
	task = create_routed_task(
		TaskSpec(
			routing=RoutingContext(
				module_name="Procurement Planning",
				task_type=task_type,
				procuring_entity_id=procuring_entity,
				financial_year_id=financial_year,
				organisation_unit_id=organisation_unit,
			),
			subject_type=subject_type,
			subject_id=subject_id,
			idempotency_key=idempotency_key,
			task_iteration=iteration,
			predecessor_task_id=predecessor_task_id,
			task_id=task_id,
		),
		actor=actor,
	)
	return task, iteration


def authorize_planning_task(
	*, task_id: str, actor: str, capability: str | None, subject_type: str, subject_id: str = ""
):
	task = get_authorized_task(task_id, actor=actor, capability=capability)
	if task.subject_type != subject_type or (subject_id and task.subject_id != subject_id):
		frappe.throw(frappe._("Task not found."), frappe.PermissionError, title="PLN_TASK_NOT_FOUND")
	return task


def planning_task_action_allowed(*, task_id: str, actor: str, capability: str) -> bool:
	if not task_id or not frappe.db.exists("Workflow Task", task_id):
		return False
	task = frappe.get_doc("Workflow Task", task_id)
	if task.state != "Open":
		return False
	resource = {
		"resource_type": task.subject_type,
		"resource_id": task.subject_id,
		"procuring_entity_id": task.procuring_entity_id,
		"financial_year_id": task.financial_year_id,
		"organisation_unit_id": task.organisation_unit_id,
	}
	return evaluate_capability(actor, capability, resource, task_id=task.name).allowed


def transition_planning_task(
	*, task_id: str, actor: str, capability: str, target_state: str, expected_token: str, prior_actions=None
):
	return transition_task(
		task_id,
		actor=actor,
		capability=capability,
		target_state=target_state,
		expected_token=expected_token,
		prior_actions=prior_actions,
	)


def invalidate_planning_task(*, task_id: str, subject_type: str, subject_id: str, actor: str, reason: str):
	return invalidate_task(
		task_id,
		subject_type=subject_type,
		subject_id=subject_id,
		actor=actor,
		reason=reason,
	)


def resolve_single_assignee(*, role: str, procuring_entity: str, organisation_unit: str | None = None) -> str:
	rows = frappe.get_all(
		"User Scope Assignment",
		filters={"role": role, "procuring_entity": procuring_entity},
		fields=["user", "organisation_unit", "include_descendants"],
	)
	active = [row for row in rows if row.user and frappe.db.get_value("User", row.user, "enabled")]
	unit = cstr(organisation_unit).strip()
	precise = []
	if unit:
		from kentender_core.services.org_scope_access import descendant_org_units

		exact = [row for row in active if cstr(row.organisation_unit).strip() == unit and not int(row.include_descendants or 0)]
		exact_tree = [row for row in active if cstr(row.organisation_unit).strip() == unit and int(row.include_descendants or 0)]
		ancestor = [
			row for row in active
			if row.organisation_unit
			and cstr(row.organisation_unit).strip() != unit
			and int(row.include_descendants or 0)
			and unit in descendant_org_units(row.organisation_unit)
		]
		precise = exact or exact_tree or ancestor
		pe_wide = [row for row in active if not row.organisation_unit]
		# Eliminate assignments outside the item's scope before persona preference.
		# A PE-wide dedicated task persona remains an authorised route; a dedicated
		# assignment for a different OU does not.
		active = precise + pe_wide
	# Prefer a user configured solely for this task role at the PE. This excludes
	# multi-role operational personas and Budget Authority support assignments.
	dedicated = []
	for row in active:
		roles = set(frappe.get_all(
			"User Scope Assignment",
			filters={"user": row.user, "procuring_entity": procuring_entity},
			pluck="role",
		))
		if roles == {role}:
			dedicated.append(row)
	if dedicated:
		active = dedicated
	if active:
		base_roles = {"All", "Desk User", "Guest", "Website User", "System Manager"}
		non_authority = [
			row for row in active
			if not any("Authority" in candidate for candidate in frappe.get_roles(row.user))
		]
		if non_authority:
			active = non_authority
		role_counts = {
			cstr(row.user): len(set(frappe.get_roles(row.user)) - base_roles)
			for row in active
		}
		minimum = min(role_counts.values())
		active = [row for row in active if role_counts.get(cstr(row.user)) == minimum]
	users = sorted({cstr(row.user).strip() for row in active if row.user and row.user != "Guest"})
	if len(users) != 1:
		frappe.throw(
			frappe._("Exactly one enabled {0} must be configured for this Procuring Entity; found {1}.").format(role, len(users)),
			title="PLN_TASK_ASSIGNEE_AMBIGUOUS" if users else "PLN_TASK_ASSIGNEE_MISSING",
		)
	return users[0]


def next_task_identity(*, prefix: str, record: object, id_field: str, iteration_field: str) -> tuple[str, int, str]:
	iteration = int(getattr(record, iteration_field, 0) or 0) + 1
	code = cstr(getattr(record, "item_version_code", None) or getattr(record, "version_code", None) or getattr(record, "name", ""))
	task_id = f"{prefix}-{code}-{iteration:02d}"
	return task_id, iteration, new_concurrency_token()


def assert_task_assignment(*, record: object, task: str, id_field: str, assignee_field: str, state_field: str, actor: str) -> None:
	if cstr(getattr(record, id_field, "")) != cstr(task).strip():
		frappe.throw(frappe._("Task not found."), frappe.PermissionError, title="PLN_TASK_NOT_FOUND")
	if cstr(getattr(record, assignee_field, "")) != actor:
		frappe.throw(frappe._("This task is assigned to another user."), frappe.PermissionError, title="PLN_TASK_NOT_ASSIGNED")
	if cstr(getattr(record, state_field, "")) != "Open":
		frappe.throw(frappe._("This task is no longer open."), title="PLN_TASK_CLOSED")


def assert_task_token(*, actual: str | None, expected: str | None) -> None:
	if not expected or cstr(actual) != cstr(expected):
		frappe.throw(frappe._("The task changed while you were working. Reload and try again."), title="PLN_TASK_STALE")


def idempotent_decision(
	key: str | None, *, actor: str = "", task_id: str = "", capability: str = ""
) -> dict | None:
	key = cstr(key).strip()
	if not key:
		frappe.throw(frappe._("An idempotency key is required."), title="PLN_IDEMPOTENCY_REQUIRED")
	decision = frappe.db.get_value(
		"Plan Decision",
		{"command_idempotency_key": key},
		["name", "actor", "task_id"],
		as_dict=True,
	)
	if not decision:
		return None
	if actor and cstr(decision.actor) != cstr(actor):
		frappe.throw(frappe._("Not permitted for this action."), frappe.PermissionError)
	if task_id and cstr(decision.task_id) != cstr(task_id):
		frappe.throw(frappe._("Task not found."), frappe.PermissionError, title="PLN_TASK_NOT_FOUND")
	if capability:
		task = frappe.get_doc("Workflow Task", cstr(decision.task_id))
		if cstr(task.claimed_by or task.assigned_user_id) != cstr(actor):
			frappe.throw(frappe._("Not permitted for this action."), frappe.PermissionError)
		resource = {
			"resource_type": task.subject_type,
			"resource_id": task.subject_id,
			"procuring_entity_id": task.procuring_entity_id,
			"financial_year_id": task.financial_year_id,
			"organisation_unit_id": task.organisation_unit_id,
		}
		if not evaluate_capability(actor, capability, resource).allowed:
			frappe.throw(frappe._("Not permitted for this action."), frappe.PermissionError)
	return {"ok": True, "idempotent": True, "decision": decision.name}
