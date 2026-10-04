# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.10 plan D12, completed: retiring the "Bid Opening"
placeholder Workspace (bop_chg_001_v010_retire_placeholder_workspace) left
the Workspace Sidebar and the hidden Desktop Icon Frappe had made for it; the
sidebar's only link pointed at the deleted Workspace. Both go. Bid Opening is
reached from its Tender record (the Tender's "Bid opening" button) and from
My Work. Existence-guarded; fresh installs skip."""

from __future__ import annotations

import frappe


def execute() -> None:
	for doctype in ("Workspace Sidebar", "Desktop Icon"):
		if frappe.db.exists("DocType", doctype) and frappe.db.exists(doctype, "Bid Opening"):
			frappe.delete_doc(doctype, "Bid Opening", force=True, ignore_permissions=True)
	frappe.db.commit()
