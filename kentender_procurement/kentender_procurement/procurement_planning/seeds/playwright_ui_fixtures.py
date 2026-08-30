# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright fixtures for the Procurement Planning browser specs (decision D8:
fixture endpoints live here, never in api.py; invoked via `bench execute`).

Isolation is by Procuring Entity — **PE-PWPL** — never the §14 demo world and
never the Python tests' PE-PLNT (tracker rule 8: each spec file owns its
fixture entity). Fixture instants are pinned except the submission window,
which must span the real test clock. Every reset clears the actors' server-side
context preferences (CTX-CHG-001): they outlive spec files otherwise.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils.password import update_password

PE = "PE-PWPL"
OU = "OU-PWPL-DHI"
FY = "FY-2098-2099"
CTX = "CTX-PWPL-2098-2099"

AUTHOR = "pwpl.author@example.test"
HOD = "pwpl.hod@example.test"
PLANNER = "pwpl.planner@example.test"
AUDITOR = "pwpl.auditor@example.test"
OUTSIDER = "pwpl.outsider@example.test"

PASSWORD = "Test@123"

CONTEXT_PREFERENCE_KEYS = (
	"kt_working_procuring_entity",
	"kt_planning_financial_year",
	"kt_planning_org_unit",
)


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"Procurement Planning Playwright fixtures are test data. Enable "
		"developer_mode or allow_tests on this site before building them."
	)


def _actor(email: str, full_name: str, roles: tuple[str, ...], *, unit: bool) -> None:
	if not frappe.db.exists("User", email):
		parts = full_name.split()
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": parts[0],
				"last_name": " ".join(parts[1:]),
				"enabled": 1,
				"user_type": "System User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	held = {row.role for row in user.roles}
	missing = [role for role in ("Desk User", *roles) if role not in held]
	if missing:
		user.add_roles(*missing)
	update_password(email, PASSWORD)
	scope = [("Procuring Entity", PE)]
	if unit:
		scope.append(("Organisation Unit", OU))
	for allow, value in scope:
		if not frappe.db.exists(
			"User Permission", {"user": email, "allow": allow, "for_value": value}
		):
			frappe.get_doc(
				{"doctype": "User Permission", "user": email, "allow": allow, "for_value": value}
			).insert(ignore_permissions=True)


def _clear_context_preferences() -> None:
	for user in (AUTHOR, HOD, PLANNER, AUDITOR, OUTSIDER):
		for key in CONTEXT_PREFERENCE_KEYS:
			frappe.defaults.clear_user_default(key, user)


def ensure_world(*, commit: bool = True) -> dict[str, Any]:
	"""The PE-PWPL world: entity, department, active FY context, open window
	and the five §6 personas the workspace spec logs in as."""
	_guard()
	from kentender_procurement.procurement_planning.services.planning_roles import (
		ensure_planning_roles,
	)

	ensure_planning_roles()
	if not frappe.db.exists("Procuring Entity", PE):
		frappe.get_doc(
			{
				"doctype": "Procuring Entity",
				"entity_code": PE,
				"legal_name": "Playwright Planning Entity",
				"entity_name": "Playwright Planning Entity",
				"reporting_currency": "KES",
				"status": "Active",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Organisation Unit", OU):
		ou_type = frappe.get_all("Organisation Unit Type", limit=1, pluck="name")[0]
		frappe.get_doc(
			{
				"doctype": "Organisation Unit",
				"unit_code": OU,
				"unit_name": "Digital Health",
				"unit_type": ou_type,
				"procuring_entity": PE,
				"status": "Active",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Financial Year", FY):
		frappe.get_doc(
			{
				"doctype": "Financial Year",
				"start_year": 2098,
				"label": "FY 2098/99",
				"start_date": "2098-07-01",
				"end_date": "2099-06-30",
				"timezone": "Africa/Nairobi",
				"record_status": "Available",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("PE Fiscal Year Context", CTX):
		frappe.get_doc(
			{
				"doctype": "PE Fiscal Year Context",
				"procuring_entity": PE,
				"financial_year": FY,
				"context_status": "Active",
				"active_from": "2020-01-01 00:00:00",
				"active_to": "2105-01-01 00:00:00",
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Departmental Plan Submission Window", {"pe_fy_context": CTX}):
		frappe.get_doc(
			{
				"doctype": "Departmental Plan Submission Window",
				"pe_fy_context": CTX,
				"opens_at": "2020-01-01 00:00:00",
				"closes_at": "2099-01-01 00:00:00",
				"fixture_namespace": "KENTENDER_PLAYWRIGHT",
			}
		).insert(ignore_permissions=True)

	_actor(AUTHOR, "Playwright Planning Author", ("Departmental Author",), unit=True)
	_actor(
		HOD, "Playwright Planning HoD",
		("Departmental Author", "Head of User Department"), unit=True,
	)
	_actor(PLANNER, "Playwright Procurement Planner", ("Procurement Planner",), unit=False)
	_actor(AUDITOR, "Playwright Planning Auditor", ("Planning Auditor",), unit=False)
	# The outsider holds a Planning role but no PE-PWPL permission at all.
	if not frappe.db.exists("User", OUTSIDER):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": OUTSIDER,
				"first_name": "Playwright",
				"last_name": "Outsider",
				"enabled": 1,
				"user_type": "System User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	outsider = frappe.get_doc("User", OUTSIDER)
	if "Departmental Author" not in {row.role for row in outsider.roles}:
		outsider.add_roles("Desk User", "Departmental Author")
	update_password(OUTSIDER, PASSWORD)
	_clear_context_preferences()
	if commit:
		frappe.db.commit()
	return {"pe": PE, "ou": OU, "fy": FY}


def reset_workspace_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""Empty PE-PWPL Planning world with the window open: the workspace spec's
	documented starting state."""
	world = ensure_world(commit=False)
	_wipe(commit=False)
	_clear_context_preferences()
	if commit:
		frappe.db.commit()
	return world


def _wipe(*, commit: bool = False) -> None:
	roots = frappe.get_all("Departmental Plan", filters={"procuring_entity": PE}, pluck="name")
	versions = frappe.get_all(
		"Departmental Plan Version",
		filters={"departmental_plan": ("in", roots or ("",))},
		pluck="name",
	)
	tasks = frappe.get_all(
		"Departmental Plan Validation Task", filters={"procuring_entity": PE}, pluck="name"
	)
	frappe.db.delete(
		"Departmental Plan Validation Decision", {"task": ("in", tasks or ("",))}
	)
	frappe.db.delete("Departmental Plan Validation Task", {"procuring_entity": PE})
	frappe.db.delete(
		"Departmental Plan Submission", {"dpp_version": ("in", versions or ("",))}
	)
	frappe.db.delete("Departmental Plan Entry", {"dpp_version": ("in", versions or ("",))})
	frappe.db.delete("Departmental Plan Version", {"name": ("in", versions or ("",))})
	frappe.db.delete("Departmental Plan", {"name": ("in", roots or ("",))})
	plans = frappe.get_all("Annual Plan", filters={"procuring_entity": PE}, pluck="name")
	plan_versions = frappe.get_all(
		"Annual Plan Version", filters={"annual_plan": ("in", plans or ("",))}, pluck="name"
	)
	frappe.db.delete("Plan Source Allocation", {"plan_version": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan Item", {"plan_version": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan Version", {"name": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan", {"name": ("in", plans or ("",))})
	if commit:
		frappe.db.commit()


def reset_all(*, commit: bool = True) -> dict[str, Any]:
	"""Remove every PE-PWPL Planning row (the purge entry point)."""
	_guard()
	_wipe(commit=commit)
	return {"ok": True}
