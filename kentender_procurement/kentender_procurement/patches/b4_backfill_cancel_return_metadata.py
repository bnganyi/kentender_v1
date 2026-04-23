# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B4 — backfill actor/time for Cancelled and returned Draft rows created before B4."""

import frappe


def execute():
	if not frappe.db.table_exists("Demand"):
		return

	# Cancelled with reason but missing cancelled_by/at (pre-B4)
	frappe.db.sql(
		"""
		UPDATE `tabDemand`
		SET `cancelled_by` = COALESCE(`owner`, 'Administrator'),
			`cancelled_at` = COALESCE(`modified`, `creation`)
		WHERE `status` = 'Cancelled'
			AND IFNULL(`cancellation_reason`, '') != ''
			AND (`cancelled_by` IS NULL OR `cancelled_by` = '')
		"""
	)
	# Rejected with reason but missing rejected_by/at (edge / pre-B4)
	frappe.db.sql(
		"""
		UPDATE `tabDemand`
		SET `rejected_by` = COALESCE(`owner`, 'Administrator'),
			`rejected_at` = COALESCE(`modified`, `creation`)
		WHERE `status` = 'Rejected'
			AND IFNULL(`rejection_reason`, '') != ''
			AND (`rejected_by` IS NULL OR `rejected_by` = '')
		"""
	)
	# Draft with return_reason but missing returned_by/at (pre-B4)
	frappe.db.sql(
		"""
		UPDATE `tabDemand`
		SET `returned_by` = COALESCE(`owner`, 'Administrator'),
			`returned_at` = COALESCE(`modified`, `creation`)
		WHERE `status` = 'Draft'
			AND IFNULL(`return_reason`, '') != ''
			AND (`returned_by` IS NULL OR `returned_by` = '')
		"""
	)
