# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUDGET-MVP1-REQ roles for Budget & Funding."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_core.services.authorization_policy import ResourceContext, evaluate_capability

ROLE_VIEWER = "Budget Viewer"
ROLE_OFFICER = "Budget Officer"
ROLE_REVIEWER = "Budget Reviewer"
ROLE_AUTHORITY = "Budget Authority"
ROLE_AUDITOR = "Auditor"

ALL_BUDGET_ROLES = (
	ROLE_VIEWER,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_AUTHORITY,
	ROLE_AUDITOR,
)

# Viewer may not see in-progress registration states (BUD-FR roles matrix).
_VIEWER_STATUSES = ("Active", "Submitted", "Closed", "Cancelled")


def ensure_budget_roles() -> None:
	for role in ALL_BUDGET_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def user_roles(user: str | None = None) -> set[str]:
	user = user or frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return set(ALL_BUDGET_ROLES) | {"System Manager"}
	return set(frappe.get_roles(user))


def require_any_role(*roles: str) -> None:
	have = user_roles()
	if "System Manager" in have:
		return
	if not have.intersection(roles):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def visible_statuses_for_roles(roles: set[str]) -> list[str] | None:
	"""Return status allow-list, or None when all statuses are visible."""
	if "System Manager" in roles:
		return None
	elevated = {ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_AUDITOR}
	if roles.intersection(elevated):
		return None
	if ROLE_VIEWER in roles:
		return list(_VIEWER_STATUSES)
	return None


def visible_statuses_for_user(user: str | None = None) -> list[str] | None:
	return visible_statuses_for_roles(user_roles(user))


def can_register_budget_for_roles(roles: set[str]) -> bool:
	"""BUD-FR create Draft — Budget Officer (and System Manager), not Authority alone."""
	if "System Manager" in roles:
		return True
	return ROLE_OFFICER in roles


def can_register_budget() -> bool:
	return can_register_budget_for_roles(user_roles())


def can_review_budget() -> bool:
	return bool(user_roles().intersection({ROLE_REVIEWER, ROLE_AUTHORITY, "System Manager"}))


def can_export_funding_performance(user: str | None = None, pe: str | None = None) -> bool:
	"""Export is an assignment-scoped capability, never a presentation-role grant.

	`pe` should be the procuring entity already resolved for the current
	request (e.g. via `resolve_scoped_entity`) — an explicitly-requested PE
	must be honoured here too, not silently re-derived from the actor's own
	implicit scope (which is blank for an unrestricted Administrator).
	"""
	actor = user or frappe.session.user
	pe = pe or entity_for_user(actor) or ""
	if not pe:
		return False
	return evaluate_capability(
		actor,
		"budget.export",
		ResourceContext(
			resource_type="Budget Funding Performance",
			resource_id=pe,
			procuring_entity_id=pe,
		),
	).allowed


def entity_for_user(user: str | None = None) -> str | None:
	"""Best-effort procuring entity from User Scope Assignment / User Permission.

	Returns None when no single procuring entity can be determined — including
	for an unrestricted (Administrator / System Manager) user, who is not
	implicitly scoped to any one entity. Callers decide whether a blank scope
	is acceptable (e.g. an admin-level cross-entity read) or must fail closed.
	"""
	user = user or frappe.session.user
	if user == "Guest":
		return None
	from kentender_core.services.org_scope_access import permitted_procuring_entities

	pes = permitted_procuring_entities(user)
	if pes is None:
		return None
	if len(pes) == 1:
		return next(iter(pes))
	if pes:
		# Prefer default User Permission among permitted PEs.
		default = frappe.db.get_value(
			"User Permission",
			{"user": user, "allow": "Procuring Entity", "is_default": 1},
			"for_value",
		)
		if default in pes:
			return default
		return sorted(pes)[0]
	pe = frappe.db.get_value(
		"User Permission",
		{"user": user, "allow": "Procuring Entity", "is_default": 1},
		"for_value",
	)
	if pe:
		return pe
	return frappe.db.get_value(
		"User Permission",
		{"user": user, "allow": "Procuring Entity"},
		"for_value",
	)


def assert_org_unit_in_scope(
	procuring_entity: str | None,
	owner_org_unit: str | None,
	user: str | None = None,
	*,
	require_write: bool = False,
) -> None:
	from kentender_core.services.org_scope_access import assert_can_access_owned_record

	assert_can_access_owned_record(
		procuring_entity=procuring_entity,
		owner_org_unit=owner_org_unit,
		user=user,
		require_write=require_write,
	)


def ownership_path_for_unit(owner_org_unit: str | None) -> str:
	from kentender_core.services.org_scope_access import ownership_path_label

	return ownership_path_label(owner_org_unit)


def can_access_budget_line(
	line,
	user: str | None = None,
	*,
	require_write: bool = False,
) -> bool:
	"""Line-level PE + owner_org_unit check."""
	from kentender_core.services.org_scope_access import can_access_owned_record

	pe = getattr(line, "procuring_entity", None)
	if not pe and getattr(line, "budget", None):
		pe = frappe.db.get_value("Budget", line.budget, "procuring_entity")
	return can_access_owned_record(
		procuring_entity=pe,
		owner_org_unit=getattr(line, "owner_org_unit", None),
		user=user,
		require_write=require_write,
	)
