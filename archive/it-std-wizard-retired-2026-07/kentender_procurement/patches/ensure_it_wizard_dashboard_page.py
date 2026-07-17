# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure IT Tender Configurations (Screen 01) Desk page exists."""

from __future__ import annotations

import frappe

PAGE_NAME = "it-tender-configuration-dashboard"
PAGE_TITLE = "IT Tender Configurations"

_ROLES = (
	"Administrator",
	"System Manager",
	"IT Tender Drafter",
	"Procurement Officer",
	"Procurement Planner",
	"Planning Authority",
)


def execute() -> None:
	if frappe.db.exists("Page", PAGE_NAME):
		frappe.db.set_value("Page", PAGE_NAME, "title", PAGE_TITLE)
		return
	doc = frappe.get_doc(
		{
			"doctype": "Page",
			"name": PAGE_NAME,
			"page_name": PAGE_NAME,
			"title": PAGE_TITLE,
			"module": "Kentender Procurement",
			"standard": "Yes",
		}
	)
	for role in _ROLES:
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
