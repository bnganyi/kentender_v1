"""Backfill the governed Procuring Entity reporting currency."""

from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.has_column("Procuring Entity", "reporting_currency"):
		return
	if frappe.db.exists("DocType", "Currency") and not frappe.db.exists("Currency", "KES"):
		frappe.get_doc(
			{"doctype": "Currency", "currency_name": "Kenyan Shilling", "enabled": 1}
		).insert(ignore_permissions=True)
	frappe.db.sql(
		"""
		update `tabProcuring Entity`
		set reporting_currency = 'KES'
		where coalesce(reporting_currency, '') = ''
		"""
	)
