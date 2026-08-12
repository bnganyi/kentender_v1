# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-GATE-C02 — delete Departmental Submission DocType and rows."""

from __future__ import annotations

import frappe


def execute() -> None:
	dt = "Departmental Submission"
	if not frappe.db.exists("DocType", dt):
		return
	try:
		frappe.db.sql(f"DELETE FROM `tab{dt}`")
	except Exception:
		pass
	frappe.delete_doc("DocType", dt, force=1, ignore_permissions=True)
	frappe.db.commit()
