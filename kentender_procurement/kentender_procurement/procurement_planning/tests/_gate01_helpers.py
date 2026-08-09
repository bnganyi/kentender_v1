# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared fixtures for Gate 01 Planning tests (Gate 02 scope-aware)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ROLE_DESIGNATED_APPROVER,
	ROLE_PLANNER,
	ensure_planning_roles,
)

PE = "PE-MOH"
OU = "MOH-DIR-DHP"
FY = "2027/28"
PLANNER_ROLE = ROLE_PLANNER
PLANNER_USER = "pln.gate01.planner@test.local"
APPROVER_USER = "pln.gate01.approver@test.local"


def _ensure_usa(user: str, role: str, pe: str, org_unit: str | None) -> None:
	if not frappe.db.exists("DocType", "User Scope Assignment"):
		return
	filters = {"user": user, "role": role, "procuring_entity": pe}
	if org_unit:
		filters["organisation_unit"] = org_unit
	if frappe.db.exists("User Scope Assignment", filters):
		return
	frappe.get_doc(
		{
			"doctype": "User Scope Assignment",
			"user": user,
			"role": role,
			"procuring_entity": pe,
			"organisation_unit": org_unit or "",
			"include_descendants": 1 if org_unit else 0,
		}
	).insert(ignore_permissions=True)


def ensure_planner_user() -> str:
	ensure_planning_roles()
	if not frappe.db.exists("Role", PLANNER_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": PLANNER_ROLE}).insert(ignore_permissions=True)
	if not frappe.db.exists("User", PLANNER_USER):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": PLANNER_USER,
				"first_name": "Gate01",
				"last_name": "Planner",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	roles = {r.role for r in frappe.get_doc("User", PLANNER_USER).roles}
	if PLANNER_ROLE not in roles:
		frappe.get_doc("User", PLANNER_USER).add_roles(PLANNER_ROLE)
	_ensure_usa(PLANNER_USER, PLANNER_ROLE, PE, OU)
	return PLANNER_USER


def ensure_approver_user() -> str:
	ensure_planning_roles()
	if not frappe.db.exists("User", APPROVER_USER):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": APPROVER_USER,
				"first_name": "Gate01",
				"last_name": "Approver",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	roles = {r.role for r in frappe.get_doc("User", APPROVER_USER).roles}
	if ROLE_DESIGNATED_APPROVER not in roles:
		frappe.get_doc("User", APPROVER_USER).add_roles(ROLE_DESIGNATED_APPROVER)
	_ensure_usa(APPROVER_USER, ROLE_DESIGNATED_APPROVER, PE, None)
	return APPROVER_USER


def ensure_scope() -> dict[str, str]:
	ensure_currency_kes()
	ensure_procuring_entity(PE, "Ministry of Health")
	if not frappe.db.exists("Organisation Unit", OU):
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
				"unit_code": OU,
				"unit_name": "Department of Health Planning",
				"unit_type": ou_type,
				"procuring_entity": PE,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
	ensure_planner_user()
	ensure_approver_user()
	return {"pe": PE, "ou": OU, "fy": FY}


def make_approved_demand(
	*,
	pe: str = PE,
	ou: str = OU,
	title: str = "Gate01 Demand",
) -> dict[str, str]:
	ensure_scope()
	planner = ensure_planner_user()
	code = f"DEM-G01-{frappe.generate_hash(length=6).upper()}"
	demand = frappe.get_doc(
		{
			"doctype": "Demand",
			"demand_code": code,
			"title": title,
			"procuring_entity": pe,
			"owner_org_unit": ou,
			"requester": planner,
			"demand_route": "Standard",
			"status": "Approved",
			"current_stage": "Complete",
			"planning_ready": 1,
			"planning_usage": "Not taken up",
			"currency": "KES",
			"confirmed_estimate": 1_000_000,
			"requester_estimate": 1_000_000,
		}
	)
	demand.insert(ignore_permissions=True)
	item_code = f"DI-{code}"
	item = frappe.get_doc(
		{
			"doctype": "Demand Item",
			"demand": demand.name,
			"item_code": item_code,
			"description": title,
			"confirmed_estimate": 1_000_000,
			"requester_estimate": 1_000_000,
			"currency": "KES",
			"quantity": 1,
			"confirmed_quantity": 1,
		}
	)
	item.insert(ignore_permissions=True)
	return {"demand": demand.name, "demand_item": item.name, "demand_code": code}


def create_plan_as_planner(**overrides: Any) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services.create_procurement_plan import (
		create_procurement_plan,
	)

	scope = ensure_scope()
	planner = ensure_planner_user()
	seq = int(frappe.db.count("Procurement Plan") or 0) + 1
	fy = overrides.pop("financial_year", None) or f"{2100 + seq}/{str(2101 + seq)[-2:]}"
	kwargs = {
		"procuring_entity": scope["pe"],
		"financial_year": fy,
		"title": "Gate01 Annual Plan",
		"currency": "KES",
		"coordinating_org_unit": scope["ou"],
		"user": planner,
	}
	kwargs.update(overrides)
	return create_procurement_plan(**kwargs)
