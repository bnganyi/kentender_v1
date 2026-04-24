# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Normalize PP reference document names to business codes (hide internal hash IDs in Link UI)."""

from __future__ import annotations

import frappe


def _rename_to_code(doctype: str, code_field: str) -> None:
	if not frappe.db.exists("DocType", doctype):
		return
	rows = frappe.get_all(doctype, fields=["name", code_field], limit_page_length=0)
	for row in rows:
		old = (row.get("name") or "").strip()
		code = (row.get(code_field) or "").strip()
		if not old or not code or old == code:
			continue
		if frappe.db.exists(doctype, code):
			# Keep existing canonical code-named row.
			continue
		try:
			frappe.rename_doc(doctype, old, code, force=True, show_alert=False)
		except Exception:
			# Non-blocking migration; continue best-effort.
			continue


def execute() -> None:
	_rename_to_code("Procurement Plan", "plan_code")
	_rename_to_code("Procurement Template", "template_code")
	_rename_to_code("Risk Profile", "profile_code")
	_rename_to_code("KPI Profile", "profile_code")
	_rename_to_code("Decision Criteria Profile", "profile_code")
	_rename_to_code("Vendor Management Profile", "profile_code")
