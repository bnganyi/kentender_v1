# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Owner decision 2 Oct 2026 (TPR-CHG-001 v0.16) — the Open Tender `bid_opening`
period carries a verified legal minimum of 7 days (PPADA s.97(1); PPADR 2020
reg. 86, the Project Owner's research), separate from the 21-day default. Sites
seeded before the decision recorded only the default, so Tenders treated 21 as
a floor. Only a row with no minimum is filled; an administrator's own minimum
is never overwritten, and the profile's verification status is untouched."""

from __future__ import annotations

import frappe

MINIMUM_DAYS = 7
REFERENCE = "PPADA s.97(1); PPADR 2020 reg. 86"


def execute():
	if not frappe.db.has_table("Procedure Schedule Profile"):
		return
	profiles = frappe.get_all("Procedure Schedule Profile", filters={"procurement_method": "Open Tender"}, pluck="name")
	for row in frappe.get_all(
		"Schedule Profile Milestone", filters={"parent": ("in", profiles or [""]), "milestone": "bid_opening"}, fields=["name", "minimum_days"], limit_page_length=0,
	):
		if int(row.minimum_days or 0):
			continue
		frappe.db.set_value("Schedule Profile Milestone", row.name, {"minimum_days": MINIMUM_DAYS, "statutory_reference": REFERENCE}, update_modified=False)
