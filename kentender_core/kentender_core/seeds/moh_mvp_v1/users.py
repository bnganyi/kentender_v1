# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""§4.4 canonical access profiles for MOH_MVP_V1."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils.password import update_password

from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_core.seeds import constants as CoreC
from kentender_core.seeds._common import ensure_user_permission
from kentender_core.seeds.moh_mvp_v1 import constants as C
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles

# (email, full_name, roles, pe_code, state_dept_code|None, directorate_code|None)
_USER_SPECS: tuple[tuple[Any, ...], ...] = (
	(
		C.USER_MEDICAL,
		"MOH Medical Services Officer",
		("Strategy Officer", "Budget Officer"),
		C.PE_MOH,
		C.SD_MEDICAL,
		C.DIR_DHP,
	),
	(
		C.USER_PUBLIC,
		"MOH Public Health Officer",
		("Strategy Officer", "Budget Officer"),
		C.PE_MOH,
		C.SD_PUBLIC,
		C.DIR_HRMD,
	),
	(
		C.USER_STR_REVIEWER,
		"MOH Strategy Reviewer",
		("Strategy Reviewer",),
		C.PE_MOH,
		None,
		None,
	),
	(
		C.USER_BUD_REVIEWER,
		"MOH Budget Reviewer",
		("Budget Reviewer",),
		C.PE_MOH,
		None,
		None,
	),
	(
		C.USER_BUD_AUTHORITY,
		"MOH Budget Authority",
		("Budget Authority",),
		C.PE_MOH,
		None,
		None,
	),
	(
		C.USER_VIEWER,
		"MOH Management Viewer",
		("Strategy Viewer", "Budget Viewer"),
		C.PE_MOH,
		None,
		None,
	),
	(
		C.USER_OTHER_ENTITY,
		"Other Entity Officer",
		("Strategy Officer", "Budget Officer"),
		C.PE_MOE,
		None,
		None,
	),
	# Thin dual-role persona for BUD-SUP-002 AC-018 (SoD) — not a §4.4 demo login.
	(
		"moh.budget.officer.authority@example.test",
		"MOH Budget Officer+Authority",
		("Budget Officer", "Budget Authority"),
		C.PE_MOH,
		None,
		None,
	),
)


def _dept_name(code: str | None) -> str | None:
	if not code:
		return None
	return frappe.db.get_value("Procuring Department", {"department_code": code}, "name")


def _upsert_user(
	email: str,
	full_name: str,
	roles: tuple[str, ...],
	pe_code: str,
	state_dept_code: str | None,
	directorate_code: str | None,
) -> str:
	parts = (full_name or "").split()
	first = parts[0] if parts else email.split("@")[0]
	last = " ".join(parts[1:]) if len(parts) > 1 else "User"
	if not frappe.db.exists("User", email):
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first,
				"last_name": last,
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		doc.insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.enabled = 1
	user.first_name = first
	user.last_name = last
	user.save(ignore_permissions=True)
	have = set(frappe.get_roles(email))
	# Strip prior strategy/budget matrix roles not in target set
	for role in (
		"Strategy Viewer",
		"Strategy Officer",
		"Strategy Manager",
		"Strategy Reviewer",
		"Budget Viewer",
		"Budget Officer",
		"Budget Reviewer",
		"Budget Authority",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles("Desk User", *roles)
	update_password(email, CoreC.TEST_PASSWORD)
	ensure_user_permission(email, pe_code)
	frappe.defaults.set_user_default("Procuring Entity", pe_code, user=email)
	sd = _dept_name(state_dept_code)
	dr = _dept_name(directorate_code)
	if sd and frappe.db.has_column("User", "kt_primary_department"):
		frappe.db.set_value("User", email, "kt_primary_department", sd, update_modified=False)
	# Store ownership codes as DefaultValue for seed-aware services/tests
	frappe.defaults.set_user_default("kt_owner_state_department", state_dept_code or "", user=email)
	frappe.defaults.set_user_default("kt_owner_directorate", directorate_code or "", user=email)
	if sd:
		from kentender_core.seeds._common import ensure_department_permission

		ensure_department_permission(email, sd)
	if dr:
		from kentender_core.seeds._common import ensure_department_permission

		ensure_department_permission(email, dr)
	return email


def upsert_canonical_users() -> dict[str, Any]:
	ensure_strategy_roles()
	ensure_budget_roles()
	created = []
	for email, full_name, roles, pe, sd, dr in _USER_SPECS:
		created.append(_upsert_user(email, full_name, roles, pe, sd, dr))
	# Disable retired demo matrix users when present
	disabled = []
	for email in C.RETIRED_DEMO_USERS:
		if frappe.db.exists("User", email):
			frappe.db.set_value("User", email, "enabled", 0, update_modified=False)
			disabled.append(email)
	return {"ok": True, "users": created, "disabled_retired": disabled, "password": CoreC.TEST_PASSWORD}
