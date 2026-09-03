# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 §7 roles for Budget & Funding — two-role Officer/Approver model."""

from __future__ import annotations

import frappe
from frappe import _

ROLE_VIEWER = "Budget Viewer"
ROLE_OFFICER = "Budget Officer"
ROLE_APPROVER = "Budget Approver"
ROLE_AUDITOR = "Auditor"

ALL_BUDGET_ROLES = (
	ROLE_VIEWER,
	ROLE_OFFICER,
	ROLE_APPROVER,
	ROLE_AUDITOR,
)


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
