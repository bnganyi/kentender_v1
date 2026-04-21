# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""B5.1: Map legacy Archived status to Approved before Select options drop Archived."""

import frappe


def execute():
	# Archived budgets are treated as finalized (read-only path aligns with Approved).
	frappe.db.sql(
		"""
		UPDATE `tabBudget`
		SET `status` = 'Approved', `modified` = `modified`
		WHERE `status` = 'Archived'
		"""
	)
