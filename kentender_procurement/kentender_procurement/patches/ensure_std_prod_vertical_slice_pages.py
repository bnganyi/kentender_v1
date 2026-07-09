# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-09 — ensure vertical-slice Desk pages exist (source, sections, clause, validation, audit)."""

from __future__ import annotations

import frappe

_PAGES = (
	("std-source-doc", "Source Document & Traceability"),
	("std-section-clauses", "Section and Clause Map"),
	("std-clause-detail", "Clause Detail"),
	("std-validation-report", "Validation Report"),
	("std-audit-log", "Audit Log"),
)

_ROLES = (
	"Administrator",
	"System Manager",
	"Procurement Officer",
	"Procurement Planner",
	"Planning Authority",
	"STD Template Administrator",
	"STD Template Importer",
	"STD Template Reviewer",
	"STD Template Approver",
	"STD Template Activator",
	"STD Template Auditor",
	"STD Technical Inspector",
	"Auditor",
	"Department Approver",
	"Finance Reviewer",
	"Requisitioner",
)


def execute() -> None:
	for page_name, title in _PAGES:
		if frappe.db.exists("Page", page_name):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Page",
				"name": page_name,
				"page_name": page_name,
				"title": title,
				"module": "Kentender Procurement",
			}
		)
		for role in _ROLES:
			if frappe.db.exists("Role", role):
				doc.append("roles", {"role": role})
		doc.insert(ignore_permissions=True)
	frappe.db.commit()
