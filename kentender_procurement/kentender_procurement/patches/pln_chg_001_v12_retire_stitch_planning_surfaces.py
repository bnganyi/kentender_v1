# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 Phase 3 (decisions D3/D10) — retire the Stitch-era
Planning surfaces from the site: the public Workspace that owned
/app/procurement-planning (its route now belongs to the v1.2 Desk Page), the
six Stitch pages and the System-Administrator support page (§1.1: removed
concept). Existence-guarded; fresh installs simply skip."""

from __future__ import annotations

import frappe

RETIRED_PAGES = (
	"planning-workspace",
	"procurement-plan-register",
	"procurement-plan-builder",
	"procurement-plan-item-editor",
	"procurement-plan-review",
	"procurement-plan-approved",
	"support-plan-view",
)


def execute() -> None:
	if frappe.db.exists("Workspace", "Procurement Planning"):
		frappe.delete_doc(
			"Workspace", "Procurement Planning",
			force=True, ignore_permissions=True, delete_permanently=True,
		)
	for page in RETIRED_PAGES:
		if frappe.db.exists("Page", page):
			frappe.delete_doc(
				"Page", page,
				force=True, ignore_permissions=True, delete_permanently=True,
			)
	frappe.db.commit()
