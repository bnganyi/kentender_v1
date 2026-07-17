# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Wire IT Tender Configurations (Screen 01) into Procurement sidebar."""

from __future__ import annotations

import frappe

PAGE_ROUTE = "it-tender-configuration-dashboard"
PAGE_LABEL = "IT Tender Configurations"
LEGACY_LABEL = "Tender Configuration Dashboard"


def execute() -> None:
	if not frappe.db.exists("Workspace Sidebar", "Procurement"):
		return

	doc = frappe.get_doc("Workspace Sidebar", "Procurement")
	for row in doc.items:
		if row.type == "Link" and row.link_to == PAGE_ROUTE:
			if row.label != PAGE_LABEL:
				row.label = PAGE_LABEL
				doc.flags.ignore_links = True
				doc.save(ignore_permissions=True)
				frappe.db.commit()
			return

	insert_at = None
	for idx, row in enumerate(doc.items):
		if row.label == "Tender Management" and row.link_to == "tender-management-v2":
			insert_at = idx + 1
			break
	if insert_at is None:
		insert_at = len(doc.items)

	doc.append(
		"items",
		{
			"type": "Link",
			"label": PAGE_LABEL,
			"link_type": "Page",
			"link_to": PAGE_ROUTE,
			"icon": "table",
			"child": 0,
			"collapsible": 0,
			"indent": 0,
			"keep_closed": 0,
			"show_arrow": 0,
		},
	)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
