# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.23 §4.4 — stamp the governed procurement category onto the
existing Requirement Type catalogue.

The Planner selects only the requirement type; the server derives the category
from this catalogue entry. Before this patch the mapping lived as a module
constant inside a Planning consumer, which is not a governed catalogue. Every seeded catalogue title is stamped from the
mapping below; a title outside it keeps whatever it already has, so an owner's
own addition is never overwritten.
"""

import frappe

CATEGORY_BY_TITLE = {
	"Non-consulting services": "Services",
	"Consulting services": "Services",
	"Goods": "Goods",
	"Works": "Works",
}


def execute() -> None:
	if not frappe.db.table_exists("Requirement Type"):
		return
	frappe.reload_doc("kentender_core", "doctype", "requirement_type")
	for row in frappe.get_all("Requirement Type", fields=["name", "title", "procurement_category"]):
		governed = CATEGORY_BY_TITLE.get((row.title or row.name).strip())
		if not governed:
			# An owner-added type: leave its own category alone.
			continue
		if (row.procurement_category or "").strip() == governed:
			continue
		frappe.db.set_value("Requirement Type", row.name, "procurement_category", governed, update_modified=False)
