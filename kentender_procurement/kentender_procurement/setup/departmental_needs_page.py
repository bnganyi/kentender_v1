"""Generate the canonical Departmental Needs Desk page through Frappe."""

from __future__ import annotations

import frappe


def generate() -> list[str]:
	frappe.flags.allow_doctype_export = True
	if frappe.db.exists("Page", "departmental-needs"):
		return []
	page = frappe.get_doc({
		"doctype": "Page",
		"page_name": "departmental-needs",
		"title": "Departmental Needs",
		"module": "Departmental Needs",
		"standard": "Yes",
		"system_page": 0,
		"roles": [
			{"role": role}
			for role in (
				"Administrator",
				"System Manager",
				"Departmental Need Requester",
				"Head of User Department",
				"Departmental Review Delegate",
				"Procurement Planner",
				"Budget Officer",
				"Accounting Officer",
			)
		],
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	return [page.name]
