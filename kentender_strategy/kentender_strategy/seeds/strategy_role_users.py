# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STR-SUP-005 — deterministic Strategy role users for thin UI role evidence."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils.password import update_password

from kentender_strategy.services.strategy_permissions import (
	ROLE_MANAGER,
	ROLE_OFFICER,
	ROLE_VIEWER,
	ensure_strategy_roles,
)

try:
	from kentender_core.seeds.constants import TEST_PASSWORD
except Exception:  # pragma: no cover
	TEST_PASSWORD = "Test@123"

PE_MOH_CODE = "PE-MOH"
PE_MOE_CODE = "PE-MOE"

STRATEGY_ROLE_USERS: tuple[tuple[Any, ...], ...] = (
	("strategy.viewer@moh.test", "Strategy Viewer MOH", (ROLE_VIEWER,), PE_MOH_CODE),
	("strategy.officer@moh.test", "Strategy Officer MOH", (ROLE_OFFICER,), PE_MOH_CODE),
	("strategy.manager@moh.test", "Strategy Manager MOH", (ROLE_MANAGER,), PE_MOH_CODE),
	("strategy.viewer@moe.test", "Strategy Viewer MOE", (ROLE_VIEWER,), PE_MOE_CODE),
)


def _ensure_pe(entity_code: str, entity_name: str) -> str:
	name = frappe.db.get_value("Procuring Entity", {"entity_code": entity_code}, "name")
	if name:
		return name
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
	frappe.defaults.set_user_default("Procuring Entity", pe_name, user=email)
	return email


def upsert_strategy_role_users() -> dict[str, Any]:
	"""Idempotent seed for STR-SUP-005 role matrix users (MOH + OTHER-PE Viewer)."""
	ensure_strategy_roles()
	pe_by_code = {
		PE_MOH_CODE: _ensure_pe(PE_MOH_CODE, "Ministry of Health"),
		PE_MOE_CODE: _ensure_pe(PE_MOE_CODE, "Ministry of Education"),
	}
	created: list[str] = []
	for email, full_name, roles, entity_code in STRATEGY_ROLE_USERS:
		pe_name = pe_by_code[entity_code]
		_upsert_user(email, full_name, roles, pe_name)
		created.append(email)
	frappe.db.commit()
	return {
		"ok": True,
		"users": created,
		"password": TEST_PASSWORD,
		"pe_moh": pe_by_code[PE_MOH_CODE],
		"pe_moe": pe_by_code[PE_MOE_CODE],
	}
