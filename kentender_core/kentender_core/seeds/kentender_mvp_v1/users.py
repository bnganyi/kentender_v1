# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract v2 §4.6 access profiles + User Scope Assignments."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils.password import update_password

from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_core.seeds import constants as CoreC
from kentender_core.seeds._common import ensure_user_permission
from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.services.demand_permissions import (
	ROLE_BUSINESS,
	ROLE_REQUESTER,
	ensure_demand_roles,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_DESIGNATED_APPROVER,
	ROLE_PLANNER,
	ROLE_REVIEWER,
	ROLE_TENDER_INITIATOR,
	ROLE_VIEWER,
	ensure_planning_roles,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles

# (email, full_name, roles, pe, org_unit|None, include_descendants)
# Miriam also carries Demand Requester for Contract v2.2 §7.5 single-scope create.
_USER_SPECS: tuple[tuple[Any, ...], ...] = (
	(
		C.USER_MEDICAL,
		"Dr Miriam Njeri",
		("Strategy Officer", "Budget Officer", ROLE_REQUESTER, ROLE_BUSINESS),
		C.PE_MOH,
		C.OU_DIR_DHP,
		1,
	),
	(
		C.USER_PUBLIC,
		"Anne Achieng",
		("Strategy Officer", "Budget Officer", ROLE_REQUESTER, ROLE_BUSINESS),
		C.PE_MOH,
		C.OU_DIR_HRMD,
		1,
	),
	(
		C.USER_STR_REVIEWER,
		"MOH Strategy Reviewer",
		("Strategy Reviewer",),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_BUD_REVIEWER,
		"MOH Budget Reviewer",
		("Budget Reviewer",),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_BUD_AUTHORITY,
		"MOH Budget Authority",
		("Budget Authority",),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_VIEWER,
		"MOH Management Viewer",
		("Strategy Viewer", "Budget Viewer", ROLE_VIEWER),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_KISUMU_OFFICER,
		"Kisumu Health Officer",
		("Strategy Officer", "Budget Officer", ROLE_REQUESTER),
		C.PE_CGKIS,
		C.OU_CGK_HEALTH,
		1,
	),
	(
		C.USER_KISUMU_VIEWER,
		"Kisumu Management Viewer",
		("Strategy Viewer", "Budget Viewer", ROLE_VIEWER),
		C.PE_CGKIS,
		None,
		0,
	),
	(
		C.USER_BUD_DUAL,
		"MOH Budget Officer+Authority",
		("Budget Officer", "Budget Authority"),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_PLANNING_OFFICER,
		"Mercy Kilonzo",
		(ROLE_PLANNER,),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_PLANNING_REVIEWER,
		"David Kiptoo",
		(ROLE_REVIEWER,),
		C.PE_MOH,
		None,
		0,
	),
	(
		# Extra SoD persona — not Demo v2.7 §4.6 (Anne / James / Grace / Peter).
		C.USER_ACCOUNTING_OFFICER,
		"Josephine Mburu",
		(ROLE_ACCOUNTING_OFFICER,),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_TENDER_INITIATOR,
		"MOH Tender Initiator",
		(ROLE_TENDER_INITIATOR,),
		C.PE_MOH,
		C.OU_DIR_DHP,
		1,
	),
	(
		C.USER_COUNTY_PLANNER,
		"Kisumu Planning Officer",
		(ROLE_PLANNER,),
		C.PE_CGKIS,
		C.OU_CGK_HEALTH,
		1,
	),
	(
		C.USER_BUSINESS_APPROVER,
		"James Mwangi",
		(ROLE_BUSINESS,),
		C.PE_MOH,
		C.OU_DIR_HRMD,
		1,
	),
	(
		C.USER_HOP,
		"Grace Wanjiku",
		(ROLE_DESIGNATED_APPROVER,),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_BUD_OFFICER,
		"Peter Otieno",
		("Budget Officer", ROLE_VIEWER),
		C.PE_MOH,
		None,
		0,
	),
)


def _clear_fixture_assignments(user: str) -> None:
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": user, "fixture_namespace": C.FIXTURE_NS},
		pluck="name",
	):
		frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)


def _upsert_scope(
	*,
	user: str,
	role: str,
	pe: str,
	org_unit: str | None,
	include_descendants: int,
) -> None:
	frappe.get_doc(
		{
			"doctype": "User Scope Assignment",
			"user": user,
			"role": role,
			"procuring_entity": pe,
			"organisation_unit": org_unit or "",
			"include_descendants": include_descendants,
			"fixture_namespace": C.FIXTURE_NS,
		}
	).insert(ignore_permissions=True)


def _save_user_identity_if_changed(user, *, first_name: str, last_name: str) -> None:
	changes = {
		"enabled": 1,
		"first_name": first_name,
		"last_name": last_name,
	}
	if all(user.get(field) == value for field, value in changes.items()):
		return
	user.update(changes)
	user.save(ignore_permissions=True)


def _add_missing_roles(user, *roles: str) -> None:
	current = {row.role for row in user.get("roles")}
	missing = [role for role in roles if role not in current]
	if missing:
		user.add_roles(*missing)


def _upsert_user(
	email: str,
	full_name: str,
	roles: tuple[str, ...],
	pe_code: str,
	org_unit: str | None,
	include_descendants: int,
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
	_save_user_identity_if_changed(user, first_name=first, last_name=last)
	_add_missing_roles(user, "Desk User", *roles)
	update_password(email, CoreC.TEST_PASSWORD)
	ensure_user_permission(email, pe_code)
	frappe.defaults.set_user_default("Procuring Entity", pe_code, user=email)
	_clear_fixture_assignments(email)
	for role in roles:
		_upsert_scope(
			user=email,
			role=role,
			pe=pe_code,
			org_unit=org_unit,
			include_descendants=include_descendants,
		)
	return email


def _upsert_multiscope_admin() -> str:
	"""Contract §4.6 — System Manager + two explicit Demand Requester pairs; no silent default."""
	ensure_demand_roles()
	email = C.USER_MULTISCOPE
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Multi",
				"last_name": "Scope Admin",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	_save_user_identity_if_changed(user, first_name="Multi", last_name="Scope Admin")
	_add_missing_roles(user, "Desk User", "System Manager", ROLE_REQUESTER)
	update_password(email, CoreC.TEST_PASSWORD)
	ensure_user_permission(email, C.PE_MOH)
	ensure_user_permission(email, C.PE_CGKIS)
	_clear_fixture_assignments(email)
	_upsert_scope(
		user=email,
		role=ROLE_REQUESTER,
		pe=C.PE_MOH,
		org_unit=C.OU_DIR_DHP,
		include_descendants=1,
	)
	_upsert_scope(
		user=email,
		role=ROLE_REQUESTER,
		pe=C.PE_CGKIS,
		org_unit=C.OU_CGK_HEALTH,
		include_descendants=1,
	)
	return email


def ensure_administrator_planning_support_viewer() -> str:
	"""Desk Administrator: cross-entity Planning Viewer (read-only support).

	Grants no create/edit/approve/tender authority — Viewer USA only for MOH + Kisumu.
	Strips accidental operational Planning roles from Administrator (support ≠ owner).
	"""
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		ALL_PLANNING_ROLES,
	)

	ensure_planning_roles()
	email = "Administrator"
	if not frappe.db.exists("User", email):
		return email
	user = frappe.get_doc("User", email)
	# Remove operational Planning roles; keep support Viewer only.
	have = {r.role for r in (user.roles or [])}
	to_remove = [r for r in ALL_PLANNING_ROLES if r != ROLE_VIEWER and r in have]
	if to_remove:
		user.remove_roles(*to_remove)
	_add_missing_roles(user, ROLE_VIEWER)
	# Drop operational Planning USA rows for Administrator (keep fixture Viewer only).
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": email},
		pluck="name",
	):
		role = frappe.db.get_value("User Scope Assignment", name, "role")
		ns = frappe.db.get_value("User Scope Assignment", name, "fixture_namespace")
		if role == ROLE_VIEWER and ns == C.FIXTURE_NS:
			frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)
		elif role in ALL_PLANNING_ROLES and role != ROLE_VIEWER:
			frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)
	for pe, ou in (
		(C.PE_MOH, C.OU_DIR_DHP),
		(C.PE_CGKIS, C.OU_CGK_HEALTH),
	):
		_upsert_scope(
			user=email,
			role=ROLE_VIEWER,
			pe=pe,
			org_unit=ou,
			include_descendants=1,
		)
	return email


def _upsert_system_admin_no_requester() -> str:
	"""Contract §4.6 — System Manager only; proves admin alone cannot create Demands."""
	email = C.USER_SYSTEM_ADMIN
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "System",
				"last_name": "Admin",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	_save_user_identity_if_changed(user, first_name="System", last_name="Admin")
	_add_missing_roles(user, "Desk User", "System Manager")
	# Strip accidental Requester role from prior seeds.
	have = {r.role for r in user.roles}
	if ROLE_REQUESTER in have:
		user.roles = [r for r in user.roles if r.role != ROLE_REQUESTER]
		user.save(ignore_permissions=True)
	update_password(email, CoreC.TEST_PASSWORD)
	_clear_fixture_assignments(email)
	# Remove any non-fixture Requester USA that would defeat the blocked demo.
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": email, "role": ROLE_REQUESTER},
		pluck="name",
	):
		frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)
	return email


def upsert_canonical_users(*, commit: bool = True) -> dict[str, Any]:
	ensure_strategy_roles()
	ensure_budget_roles()
	ensure_demand_roles()
	ensure_planning_roles()
	# Skip User→Contact sync (avoids RetryBackgroundJobError under tests / reseed).
	prev_import = frappe.flags.in_import
	frappe.flags.in_import = True
	created: list[str] = []
	try:
		for spec in _USER_SPECS:
			created.append(_upsert_user(*spec))
		created.append(_upsert_multiscope_admin())
		created.append(_upsert_system_admin_no_requester())
		created.append(ensure_administrator_planning_support_viewer())
		disabled: list[str] = []
		for email in C.RETIRED_DEMO_USERS:
			if frappe.db.exists("User", email):
				frappe.db.set_value("User", email, "enabled", 0, update_modified=False)
				disabled.append(email)
		if commit:
			frappe.db.commit()
	finally:
		frappe.flags.in_import = prev_import
	return {
		"ok": True,
		"users": created,
		"disabled_retired": disabled,
		"password": CoreC.TEST_PASSWORD,
	}
