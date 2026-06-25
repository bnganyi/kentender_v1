# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""UI test user helpers for PP3 Playwright specs."""

from __future__ import annotations

import frappe


def ensure_p7_010_supplier_user(
	email: str = "supplier.p7-010@moh.test",
	password: str = "test",
) -> dict[str, str]:
	"""Create/update supplier login user for P7-010 UI negative test."""
	email = (email or "").strip()
	if not email:
		raise ValueError("email is required")
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P7010",
				"last_name": "Supplier",
				"send_welcome_email": 0,
			}
		)
		user.insert(ignore_permissions=True)
	if "Supplier" not in {r.role for r in user.roles}:
		user.add_roles("Supplier")
	from frappe.utils.password import update_password

	update_password(user=email, pwd=password)
	frappe.db.commit()
	return {"email": email, "password": password}
