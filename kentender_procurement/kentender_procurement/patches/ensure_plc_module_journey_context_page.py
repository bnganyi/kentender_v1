# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R5-001 — Ensure Desk ``Page`` ``plc-module-journey-context`` exists (module journey context smoke host).

Idempotent: skips if the Page is already present.
"""

from __future__ import annotations

import frappe

PAGE_NAME = "plc-module-journey-context"

_ROLES = [
	"Administrator",
	"System Manager",
	"Procurement Officer",
	"Procurement Planner",
	"Requisitioner",
	"Planning Authority",
	"Auditor",
]


def execute() -> None:
	if frappe.db.exists("Page", PAGE_NAME):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Page",
			"name": PAGE_NAME,
			"page_name": PAGE_NAME,
			"title": "Module journey context",
			"module": "Kentender Procurement",
		}
	)
	for role in _ROLES:
		if frappe.db.exists("Role", role):
			doc.append("roles", {"role": role})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
