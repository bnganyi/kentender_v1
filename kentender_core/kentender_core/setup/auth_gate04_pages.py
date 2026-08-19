"""Generate AUTH-G04 standard Desk Pages through Frappe's Page lifecycle."""

from __future__ import annotations

import frappe


PAGES = (
	("user-operational-access", "User operational access", "Kentender Core"),
	("workflow-routing-rule", "Workflow routing rule", "Kentender Core"),
	("access-diagnostic", "Access diagnostic", "Kentender Core"),
	("support-plan-view", "Support read-only Plan", "Kentender Procurement"),
)


def generate() -> list[str]:
	frappe.flags.allow_doctype_export = True
	created = []
	for page_name, title, module in PAGES:
		if frappe.db.exists("Page", page_name):
			created.append(page_name)
			continue
		frappe.get_doc(
			{
				"doctype": "Page",
				"page_name": page_name,
				"title": title,
				"module": module,
				"standard": "Yes",
				"system_page": 0,
			}
		).insert(ignore_permissions=True)
		created.append(page_name)
	return created
