# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Post-sync: map legacy Procurement Package status values to governance v1 labels."""

import frappe


def execute():
	frappe.db.sql(
		"""
		UPDATE `tabProcurement Package`
		SET status = 'Completed'
		WHERE IFNULL(status, '') = 'Structured'
		"""
	)
	frappe.db.sql(
		"""
		UPDATE `tabProcurement Package`
		SET status = 'Ready for Tender'
		WHERE IFNULL(status, '') = 'Ready'
		"""
	)
