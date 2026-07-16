# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure IT Tender Configuration Implementation Schedule Desk page exists."""

from __future__ import annotations

import frappe

PAGE_NAME = "it-tender-configuration-implementation-schedule"
PAGE_TITLE = "Implementation Schedule"

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
		return
	doc = frappe.get_doc(
		{
			"doctype": "Page",
			"page_name": PAGE_NAME,
			"title": PAGE_TITLE,
			"module": "Kentender Procurement",
			"standard": "Yes",
		}
	)
	for role in _ROLES:
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	doc.insert(ignore_permissions=True, set_name=PAGE_NAME)
	frappe.db.commit()
