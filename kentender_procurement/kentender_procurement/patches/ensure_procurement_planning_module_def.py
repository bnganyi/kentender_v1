# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure ``Procurement Planning`` exists in ``tabModule Def`` before model sync."""

import frappe


def execute():
	if frappe.db.exists("Module Def", "Procurement Planning"):
		return
	doc = frappe.new_doc("Module Def")
	doc.app_name = "kentender_procurement"
	doc.module_name = "Procurement Planning"
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
