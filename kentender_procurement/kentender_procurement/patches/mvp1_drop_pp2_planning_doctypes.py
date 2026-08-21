# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RET-004 — Drop PP2 Planning DocTypes from the site (Package / Inclusion / Release path)."""

from __future__ import annotations

import frappe


_PP2_DOCTYPES = (
	"Planning Release Consumption",
	"Planning Correction Supersession",
	"Package Review Decision",
	"Package Readiness Result",
	"Package Method Decision",
	"Procurement Package Line",
	"Procurement Package",
	"Planning Audit Event",
	"Planning Inclusion",
	"Planning Release",
	"Package Template",
	"Package Profile",
)


def execute() -> None:
	for dt in _PP2_DOCTYPES:
		if not frappe.db.exists("DocType", dt):
			continue
		try:
			frappe.delete_doc("DocType", dt, force=1, ignore_permissions=True)
		except Exception:
			frappe.db.delete("DocType", {"name": dt})
			frappe.db.sql(f"DROP TABLE IF EXISTS `tab{dt}`")
	frappe.clear_cache()
