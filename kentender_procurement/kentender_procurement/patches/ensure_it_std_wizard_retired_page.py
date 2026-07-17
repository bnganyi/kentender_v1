# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Ensure IT STD Wizard retirement notice Desk page exists."""

from __future__ import annotations

import frappe

PAGE_NAME = "it-std-wizard-retired"
PAGE_TITLE = "IT Tender Configuration Wizard — Retired"

_ROLES = (
	"Administrator",
	"System Manager",
	"Procurement Officer",
	"Procurement Planner",
	"Planning Authority",
	"Requisitioner",
	"Auditor",
)


def _ensure_page(page_name: str, title: str) -> None:
	if frappe.db.exists("Page", page_name):
		frappe.db.set_value("Page", page_name, "title", title)
		return
	doc = frappe.new_doc("Page")
	doc.update(
		{
			"name": page_name,
			"page_name": page_name,
			"title": title,
			"module": "Kentender Procurement",
			"standard": "Yes",
		}
	)
	doc.name = page_name
	for role in _ROLES:
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	doc.insert(ignore_permissions=True)


def execute() -> None:
	_ensure_page(PAGE_NAME, PAGE_TITLE)
	frappe.db.commit()
