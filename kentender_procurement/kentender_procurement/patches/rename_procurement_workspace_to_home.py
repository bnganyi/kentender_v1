# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Rename legacy Workspace ``Procurement`` to ``Procurement Home`` (IA v1.0)."""

import frappe


def execute() -> None:
	if not frappe.db.exists("DocType", "Workspace"):
		return
	if frappe.db.exists("Workspace", "Procurement") and not frappe.db.exists("Workspace", "Procurement Home"):
		frappe.rename_doc("Workspace", "Procurement", "Procurement Home", force=True)
