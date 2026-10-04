"""PLN-CHG-001 v1.18 §17.2 — every existing Regulatory Reference version
predates the verification-status field; none was verified against primary
law, so each is stamped `Production verification pending` (never `Verified`)."""

import frappe


def execute():
	if not frappe.db.has_column("Regulatory Reference", "verification_status"):
		return
	frappe.db.sql(
		"""update `tabRegulatory Reference`
		set verification_status = 'Production verification pending'
		where ifnull(verification_status, '') = ''"""
	)
