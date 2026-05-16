# Copyright (c) 2026, KenTender and contributors
"""Rename Desk Page slug to avoid collision with Procurement Journey DocType route."""

import frappe


def execute() -> None:
	if not frappe.db.exists("DocType", "Page"):
		return
	if frappe.db.exists("Page", "procurement-journey") and not frappe.db.exists(
		"Page", "plc-procurement-journey"
	):
		frappe.rename_doc(
			"Page", "procurement-journey", "plc-procurement-journey", force=True
		)
