# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-SUP-002 — deterministic Budget role users for UI/API matrix evidence."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils.password import update_password

from kentender_budget.services.budget_permissions import (
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_VIEWER,
	ensure_budget_roles,
)

try:
	from kentender_core.seeds.constants import TEST_PASSWORD
except Exception:  # pragma: no cover
	TEST_PASSWORD = "Test@123"

PE_MOH_CODE = "PE-MOH"
PE_MOE_CODE = "PE-MOE"

# (email, full_name, roles..., entity_code)
BUDGET_ROLE_USERS: tuple[tuple[Any, ...], ...] = (
	("budget.viewer@moh.test", "Budget Viewer MOH", (ROLE_VIEWER,), PE_MOH_CODE),
	("budget.officer@moh.test", "Budget Officer MOH", (ROLE_OFFICER,), PE_MOH_CODE),
	("budget.reviewer@moh.test", "Budget Reviewer MOH", (ROLE_REVIEWER,), PE_MOH_CODE),
	("budget.authority@moh.test", "Budget Authority MOH", (ROLE_AUTHORITY,), PE_MOH_CODE),
	(
		"budget.officer.authority@moh.test",
		"Budget Officer Authority MOH",
		(ROLE_OFFICER, ROLE_AUTHORITY),
		PE_MOH_CODE,
	),
	("budget.officer@moe.test", "Budget Officer MOE", (ROLE_OFFICER,), PE_MOE_CODE),
)


def _ensure_pe(entity_code: str, entity_name: str) -> str:
	name = frappe.db.get_value("Procuring Entity", {"entity_code": entity_code}, "name")
	if name:
		return name
	# Fallback: name == code on some sites
	if frappe.db.exists("Procuring Entity", entity_code):
		return entity_code
	doc = frappe.get_doc(
		{
			"doctype": "Procuring Entity",
			"entity_code": entity_code,
			"entity_name": entity_name,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_user_permission(user: str, pe_name: str) -> None:
	if frappe.db.exists(
		"User Permission",
		{"user": user, "allow": "Procuring Entity", "for_value": pe_name},
	):
		frappe.db.set_value(
			"User Permission",
			{"user": user, "allow": "Procuring Entity", "for_value": pe_name},
			{"is_default": 1},
			update_modified=False,
		)
		return
	frappe.get_doc(
		{
			"doctype": "User Permission",
			"user": user,
			"allow": "Procuring Entity",
			"for_value": pe_name,
			"is_default": 1,
			"apply_to_all_doctypes": 1,
		}
	).insert(ignore_permissions=True)


def _upsert_user(email: str, full_name: str, roles: tuple[str, ...], pe_name: str) -> str:
	parts = (full_name or "").split()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": parts[0] if parts else email,
				"last_name": " ".join(parts[1:]) if len(parts) > 1 else "",
				"full_name": full_name,
				"send_welcome_email": 0,
				"enabled": 1,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	else:
		frappe.db.set_value(
			"User",
			email,
			{"enabled": 1, "full_name": full_name},
			update_modified=False,
		)
		user = frappe.get_doc("User", email)

	user.add_roles("Desk User", *roles)
	update_password(email, TEST_PASSWORD)
	_ensure_user_permission(email, pe_name)
	if frappe.db.has_column("User", "kt_procuring_entity"):
		frappe.db.set_value(
			"User",
			email,
			{"kt_procuring_entity": pe_name},
			update_modified=False,
		)
	return email


def upsert_budget_role_users() -> dict[str, Any]:
	"""Idempotent seed for BUD-SUP-002 role matrix users."""
	ensure_budget_roles()
	pe_moh = _ensure_pe(PE_MOH_CODE, "Ministry of Health")
	pe_moe = _ensure_pe(PE_MOE_CODE, "Ministry of Education")
	pe_by_code = {PE_MOH_CODE: pe_moh, PE_MOE_CODE: pe_moe}

	created: list[str] = []
	for email, full_name, roles, entity_code in BUDGET_ROLE_USERS:
		_upsert_user(email, full_name, roles, pe_by_code[entity_code])
		created.append(email)

	frappe.db.commit()
	return {
		"ok": True,
		"users": created,
		"password": TEST_PASSWORD,
		"pe_moh": pe_moh,
		"pe_moe": pe_moe,
	}
