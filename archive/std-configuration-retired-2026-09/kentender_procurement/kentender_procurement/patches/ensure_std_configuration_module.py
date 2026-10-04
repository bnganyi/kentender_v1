# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure STD Configuration Module Def exists (modules.txt sync edge case)."""

from __future__ import annotations

import frappe


def execute() -> None:
	if frappe.db.exists("Module Def", "STD Configuration"):
		return
	frappe.get_doc(
		{
			"doctype": "Module Def",
			"module_name": "STD Configuration",
			"app_name": "kentender_procurement",
		}
	).insert(ignore_permissions=True)
