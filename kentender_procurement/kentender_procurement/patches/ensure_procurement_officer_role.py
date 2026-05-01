# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure ``Procurement Officer`` desk role exists (Officer Tender Configuration POC)."""

from __future__ import annotations

import frappe


def execute():
	if frappe.db.exists("Role", "Procurement Officer"):
		return
	frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": "Procurement Officer",
			"desk_access": 1,
		}
	).insert(ignore_permissions=True)
