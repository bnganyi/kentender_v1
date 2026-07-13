# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Wire Tender Configuration Dashboard into Procurement sidebar (Tender Management cluster)."""

from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.exists("Workspace Sidebar", "Procurement"):
		return

	doc = frappe.get_doc("Workspace Sidebar", "Procurement")
	if any(
		row.type == "Link"
		and row.label == "Tender Configuration Dashboard"
		and row.link_to == "it-tender-configuration-dashboard"
		for row in doc.items
	):
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
			"label": "Tender Configuration Dashboard",
			"link_type": "Page",
			"link_to": "it-tender-configuration-dashboard",
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
