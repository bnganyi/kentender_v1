# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Rename existing Procurement Package names to package_code where safe."""

from __future__ import annotations

import frappe


def execute() -> None:
	doctype = "Procurement Package"
	if not frappe.db.exists("DocType", doctype):
		return

	rows = frappe.get_all(doctype, fields=["name", "package_code"], limit_page_length=0)
	for row in rows:
		old = (row.get("name") or "").strip()
		code = (row.get("package_code") or "").strip()
		if not old or not code or old == code:
			continue
		if frappe.db.exists(doctype, code):
			# Keep existing canonical code-named row; skip collision.
			continue
		try:
			frappe.rename_doc(doctype, old, code, force=True, show_alert=False)
		except Exception:
			# Keep migration non-blocking; continue best-effort.
			continue

