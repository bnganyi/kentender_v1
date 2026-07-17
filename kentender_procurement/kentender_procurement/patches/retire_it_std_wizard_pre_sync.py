# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Remove IT Tender Wizard Module Def before schema sync (code already archived)."""

from __future__ import annotations

import frappe


def execute() -> None:
	if frappe.db.exists("Module Def", "IT Tender Wizard"):
		frappe.delete_doc("Module Def", "IT Tender Wizard", force=True, ignore_permissions=True)
		frappe.db.commit()
