# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure Desk/login browser title uses KenTender, not Frappe/ERPNext."""

from __future__ import annotations

import frappe


def execute() -> None:
	for doctype in ("Website Settings", "System Settings"):
		if not frappe.db.exists("DocType", doctype):
			continue
		current = frappe.db.get_single_value(doctype, "app_name")
		if current != "KenTender":
			frappe.db.set_single_value(doctype, "app_name", "KenTender")
	frappe.clear_cache()
