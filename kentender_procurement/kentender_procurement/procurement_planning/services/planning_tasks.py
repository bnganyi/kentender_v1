"""Stable, assignment-backed identities for protected Planning tasks."""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_planning.services._invariants import new_concurrency_token
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


def idempotent_decision(key: str | None) -> dict | None:
	key = cstr(key).strip()
	if not key:
		frappe.throw(frappe._("An idempotency key is required."), title="PLN_IDEMPOTENCY_REQUIRED")
	name = frappe.db.get_value("Plan Decision", {"command_idempotency_key": key}, "name")
	return {"ok": True, "idempotent": True, "decision": name} if name else None
