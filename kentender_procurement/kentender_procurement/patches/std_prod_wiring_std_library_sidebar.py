# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD prod Phase 1 — wire Official STD Library sidebar to std-library Desk page."""

from __future__ import annotations

import frappe


def execute() -> None:
	if not frappe.db.exists("Workspace Sidebar", "Procurement"):
		return

	doc = frappe.get_doc("Workspace Sidebar", "Procurement")
	changed = False
	for row in doc.items:
		if row.type != "Link":
			continue
		if (row.link_type or "").lower() != "page":
			continue
		if row.label != "Official STD Library":
			continue
		if row.link_to == "std-library":
			continue
		row.link_to = "std-library"
		changed = True

	if changed:
		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)
		frappe.db.commit()
