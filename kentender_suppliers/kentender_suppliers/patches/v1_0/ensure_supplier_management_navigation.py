# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""G/H: expose Supplier Management in Procurement navigation (idempotent)."""

from __future__ import annotations

import frappe


def _ensure_procurement_sidebar_link() -> None:
	if not frappe.db.exists("Workspace Sidebar", "Procurement"):
		return
	if not frappe.db.exists("Workspace", "KTSM Supplier Registry"):
		return

	sidebar = frappe.get_doc("Workspace Sidebar", "Procurement")
	for row in sidebar.items:
		if (row.type or "") == "Link" and (row.link_type or "") == "Workspace" and (row.link_to or "") == "KTSM Supplier Registry":
			return

	insert_at = len(sidebar.items)
	for idx, row in enumerate(sidebar.items):
		if (row.type or "") == "Section Break" and (row.label or "") == "Settings":
			insert_at = idx
			break

	new_row = {
		"type": "Link",
		"label": "Supplier Management",
		"link_type": "Workspace",
		"link_to": "KTSM Supplier Registry",
		"icon": "organization",
		"child": 0,
		"collapsible": 0,
		"indent": 0,
		"keep_closed": 0,
		"show_arrow": 0,
	}
	sidebar.append("items", new_row)
	if insert_at < len(sidebar.items) - 1:
		items = list(sidebar.items)
		items.insert(insert_at, items.pop())
		for idx, row in enumerate(items, start=1):
			row.idx = idx
		sidebar.set("items", items)

	sidebar.flags.ignore_permissions = True
	sidebar.save()


def execute() -> None:
	_ensure_procurement_sidebar_link()
