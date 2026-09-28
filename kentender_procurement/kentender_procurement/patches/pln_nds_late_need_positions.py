# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tell Departmental Needs where every accepted Need stands against its
department's plan (owner decision 26 Sep 2026).

A Need accepted after its department's plan was accepted is in no plan until
the department creates an update. Planning now projects that position back to
the Need after every change to the department's plan; Needs accepted before
this reached the site have no position yet, so their page still says nothing.
One reconciliation per department and year that has a plan, exactly as the
next plan change would run it.

Idempotent: an unchanged position is ignored by the consumer.
"""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning.services import needs_intake


def execute() -> None:
	if not frappe.db.table_exists("Need Planning Intake Projection"):
		return
	sent = 0
	for root in frappe.get_all("Departmental Plan", fields=["name", "organisation_unit", "fiscal_year"], order_by="name asc"):
		sent += needs_intake.publish_need_positions(root.organisation_unit, root.fiscal_year, source=f"BACKFILL-POSITIONS-{root.name}")
	if sent:
		print(f"Recorded the departmental-plan position of {sent} accepted Need(s).")
