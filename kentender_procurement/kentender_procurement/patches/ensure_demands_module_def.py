# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure ``Demands`` exists in ``tabModule Def`` before model sync."""

from __future__ import annotations

import frappe


def execute() -> None:
	if frappe.db.exists("Module Def", "Demands"):
		return
	doc = frappe.new_doc("Module Def")
	doc.app_name = "kentender_procurement"
	doc.module_name = "Demands"
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
