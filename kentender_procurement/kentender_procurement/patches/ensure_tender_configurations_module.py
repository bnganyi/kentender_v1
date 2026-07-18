# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure Tender Configurations Module Def exists (modules.txt sync edge case)."""

from __future__ import annotations

import frappe


def execute() -> None:
	if frappe.db.exists("Module Def", "Tender Configurations"):
		return
	frappe.get_doc(
		{
			"doctype": "Module Def",
			"module_name": "Tender Configurations",
			"app_name": "kentender_procurement",
		}
	).insert(ignore_permissions=True)
