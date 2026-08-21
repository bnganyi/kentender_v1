# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared fixtures for Gate 02 Planning permission / scope tests."""

from __future__ import annotations

import frappe

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ROLE_AUTHORITY,
	ROLE_DESIGNATED_APPROVER,
	ROLE_PLANNER,
	ensure_planning_roles,
)

PE_MOH = "PE-MOH"
PE_CGK = "PE-CGKIS"
OU_MOH = "MOH-DIR-DHP"
OU_CGK = "CGK-DEPT-HEALTH"
FY = "2027/28"


def _ensure_ou(code: str, name: str, pe: str) -> None:
	if frappe.db.exists("Organisation Unit", code):
		return
	ou_type = frappe.db.get_value("Organisation Unit Type", {}, "name")
	if not ou_type:
		ot = frappe.get_doc(
			{
				"doctype": "Organisation Unit Type",
				"type_reference": "DIR",
				"display_label": "Directorate",
				"status": "Active",
			}
		)
		ot.insert(ignore_permissions=True)
		ou_type = ot.name
	frappe.get_doc(
		{
			"doctype": "Organisation Unit",
			"unit_code": code,
			"unit_name": name,
			"unit_type": ou_type,
			"procuring_entity": pe,
			"status": "Active",
		}
	).insert(ignore_permissions=True)


def ensure_org() -> dict[str, str]:
	ensure_currency_kes()
	ensure_procuring_entity(PE_MOH, "Ministry of Health")
	ensure_procuring_entity(PE_CGK, "County Government of Kisumu")
	_ensure_ou(OU_MOH, "Directorate of Digital Health and Policy", PE_MOH)
	_ensure_ou(OU_CGK, "Medical Services, Public Health and Sanitation", PE_CGK)
	ensure_planning_roles()
	return {"pe_moh": PE_MOH, "pe_cgk": PE_CGK, "ou_moh": OU_MOH, "ou_cgk": OU_CGK, "fy": FY}


def _clear_usa(user: str) -> None:
	if not frappe.db.exists("DocType", "User Scope Assignment"):
		return
	for name in frappe.get_all("User Scope Assignment", filters={"user": user}, pluck="name"):
		frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)


def ensure_user_with_roles(
	email: str,
	*,
	roles: tuple[str, ...],
	pe: str | None = None,
	org_unit: str | None = None,
	include_descendants: int = 1,
	clear_scope: bool = True,
) -> str:
	ensure_planning_roles()
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0].split(".")[0].title(),
				"last_name": "Planning",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.enabled = 1
	user.save(ignore_permissions=True)
	user.add_roles("Desk User", *roles)
	if clear_scope:
		_clear_usa(email)
	if pe:
		for role in roles:
			frappe.get_doc(
				{
					"doctype": "User Scope Assignment",
					"user": email,
					"role": role,
					"procuring_entity": pe,
					"organisation_unit": org_unit or "",
					"include_descendants": include_descendants,
				}
			).insert(ignore_permissions=True)
	return email


def ensure_moh_planner() -> str:
	ensure_org()
	return ensure_user_with_roles(
		"pln.gate02.planner@test.local",
		roles=(ROLE_PLANNER,),
		pe=PE_MOH,
		org_unit=OU_MOH,
	)


def ensure_moh_approver() -> str:
	ensure_org()
	return ensure_user_with_roles(
		"pln.gate02.approver@test.local",
		roles=(ROLE_DESIGNATED_APPROVER,),
		pe=PE_MOH,
		org_unit=None,
		include_descendants=0,
	)


def ensure_moh_authority() -> str:
	ensure_org()
	return ensure_user_with_roles(
		"pln.gate02.authority@test.local",
		roles=(ROLE_AUTHORITY,),
		pe=PE_MOH,
		org_unit=None,
		include_descendants=0,
	)


def ensure_county_planner() -> str:
	ensure_org()
	return ensure_user_with_roles(
		"pln.gate02.county.planner@test.local",
		roles=(ROLE_PLANNER,),
		pe=PE_CGK,
		org_unit=OU_CGK,
	)


def ensure_admin_only() -> str:
	ensure_org()
	email = "pln.gate02.sysadmin@test.local"
	ensure_user_with_roles(email, roles=(), pe=None, clear_scope=True)
	user = frappe.get_doc("User", email)
	user.add_roles("System Manager")
	# Strip any Planning roles
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ALL_PLANNING_ROLES,
	)

	have = {r.role for r in user.roles}
	for role in ALL_PLANNING_ROLES:
		if role in have:
			user.remove_roles(role)
	_clear_usa(email)
	return email
