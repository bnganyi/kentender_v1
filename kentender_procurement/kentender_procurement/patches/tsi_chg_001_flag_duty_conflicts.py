# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Project Owner, 10 October 2026: tender-security intake and opening or
evaluation duties exclude each other on the same Tender. Flag, for explicit
resolution by the Accounting Officer, every existing Tender where someone who
recorded an intake, or holds the duty, also sits on its opening or evaluation.
Nothing is deleted, reassigned or re-attributed: the original intake records
keep their recorder and times."""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Tender Security Duty Conflict"):
		return
	from kentender_procurement.bid_submission.services import security_duty

	flagged = security_duty.detect_conflicts()
	if flagged:
		frappe.logger().info(f"Tender-security duty conflicts flagged for resolution: {len(flagged)}")
