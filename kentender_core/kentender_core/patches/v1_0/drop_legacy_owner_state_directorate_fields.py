# Copyright (c) 2026, KenTender and contributors

"""Drop disposable MVP State Department / Directorate ownership columns."""

from __future__ import annotations

import frappe


_DOCTYPES = (
	"Strategic Plan",
	"Strategy Programme",
	"Strategy Sub Programme",
	"Strategic Outcome",
	"Performance Indicator",
	"Performance Target",
	"Performance Measurement",
	"Strategy Corrective Action",
	"Plan Value Commitment",
	"Procurement Budget Line",
)


def execute():
	for doctype in _DOCTYPES:
		if not frappe.db.table_exists(doctype):
			continue
		for col in ("owner_state_department", "owner_directorate"):
			if frappe.db.has_column(doctype, col):
				frappe.db.sql_ddl(f"alter table `tab{doctype}` drop column `{col}`")
