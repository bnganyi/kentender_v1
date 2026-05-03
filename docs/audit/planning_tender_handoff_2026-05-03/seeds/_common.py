# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

import frappe
from kentender_core.seeds import constants as C


def ensure_roles():
	for role in C.BUSINESS_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role}).insert()


def ensure_currency_kes():
	if frappe.db.exists("Currency", "KES"):
		return
	frappe.get_doc(
		{
			"doctype": "Currency",
			"currency_name": "Kenya Shilling",
			"symbol": "KES",
			"enabled": 1,
			"fraction": "Cent",
			"fraction_units": 100,
			"smallest_currency_fraction_value": 1,
		}
	).insert(ignore_permissions=True)


def ensure_procuring_entity(entity_code: str, entity_name: str) -> str:
	"""Return Procuring Entity name (document name = entity_code with autoname field:entity_code)."""
	if frappe.db.exists("Procuring Entity", entity_code):
		doc = frappe.get_doc("Procuring Entity", entity_code)
		if doc.entity_name != entity_name:
			doc.entity_name = entity_name
			doc.save(ignore_permissions=True)
		return doc.name
	doc = frappe.get_doc(
		{
			"doctype": "Procuring Entity",
			"entity_code": entity_code,
			"entity_name": entity_name,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def find_department(name: str, entity: str) -> str | None:
	row = frappe.db.get_value(
		"Procuring Department",
		{"department_name": name, "procuring_entity": entity},
		"name",
	)
	return row


def ensure_department(department_name: str, entity_name: str) -> str:
	existing = find_department(department_name, entity_name)
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Procuring Department",
			"department_name": department_name,
			"procuring_entity": entity_name,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def add_user_entity_permission(user: str, entity: str):
	frappe.get_doc(
		{
			"doctype": "User Permission",
			"user": user,
			"allow": "Procuring Entity",
			"for_value": entity,
			"apply_to_all_doctypes": 1,
		}
	).insert(ignore_permissions=True)


def ensure_user_permission(user: str, entity: str):
	"""Idempotent User Permission on Procuring Entity."""
	exists = frappe.db.exists(
		"User Permission",
		{"user": user, "allow": "Procuring Entity", "for_value": entity},
	)
	if exists:
		return
	add_user_entity_permission(user, entity)


def upsert_seed_user(
	email: str,
	full_name: str,
	business_role: str,
	*,
	entity_name: str,
	department_docname: str | None,
	password: str = C.TEST_PASSWORD,
):
	"""Create or update test user with Desk User + business role and scope fields."""
	ensure_roles()
	is_new = not frappe.db.exists("User", email)
	if is_new:
		parts = (full_name or "").split()
		doc = frappe.get_doc(
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
		doc.insert(ignore_permissions=True)
	else:
		frappe.db.set_value("User", email, {"enabled": 1, "full_name": full_name})

	user = frappe.get_doc("User", email)
	user.add_roles("Desk User", business_role)

	if frappe.db.has_column("User", "kt_procuring_entity"):
		frappe.db.set_value(
			"User",
			email,
			{
				"kt_procuring_entity": entity_name,
				"kt_primary_department": department_docname,
			},
		)
	ensure_user_permission(email, entity_name)

	from frappe.utils.password import update_password

	update_password(email, password)


def get_moh_entity_name() -> str:
	return C.ENTITY_MOH
