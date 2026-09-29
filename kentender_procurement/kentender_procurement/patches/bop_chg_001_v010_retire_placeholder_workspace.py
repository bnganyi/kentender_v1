# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.10 §9 and plan D12 — retire the "Bid Opening" placeholder
Workspace ("This lifecycle step is not implemented yet").

Every Bid Opening view is reached from the Tender record under
`/app/tenders/{tender}`; there is no Bid Opening menu or landing page. The
workspace file is removed from the app, and this deletes its record, which a
removed file alone never does. Existence-guarded; fresh installs skip."""

from __future__ import annotations

import frappe


def execute() -> None:
	if frappe.db.exists("Workspace", "Bid Opening"):
		frappe.delete_doc("Workspace", "Bid Opening", force=True, ignore_permissions=True, delete_permanently=True)
	frappe.db.commit()
