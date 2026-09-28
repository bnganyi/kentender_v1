# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §12 (BDS01-AC-081; found by the 28 Sep 2026 acceptance
audit): change tracking copied bid answers, files and prior/new values into
Frappe's Version log. Tracking is now off on those records; this removes the
Version rows it already wrote, so no Desk reader finds a bid's content there."""

import frappe

CONTENT_DOCTYPES = ("Bid Section Response", "Bid Evidence", "Bid Draft Change", "Bid Command Journal", "Bid Receipt", "Bid Submission Change")


def execute():
	frappe.db.delete("Version", {"ref_doctype": ("in", CONTENT_DOCTYPES)})
