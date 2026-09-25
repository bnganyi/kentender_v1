# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.27 §7.7 — retire the legacy public "My Work" Workspace.

It shared the /app/my-work route with the My Work Desk Page, and Frappe's
router resolves a visible Workspace first: every reader holding one of its
roles (Procurement Planner, Auditor, Requisitioner, ...) was shown a Stitch-era
shortcut page to "Demands" and "Procurement Plans" instead of their assigned
and waiting work — so the Planner never saw the hand-off register's waiting
items (found in the browser 25 Sep 2026). The same collision the v1.2 cycle
resolved for /app/procurement-planning. Existence-guarded; fresh installs
simply skip."""

from __future__ import annotations

import frappe


def execute() -> None:
	if frappe.db.exists("Workspace", "My Work"):
		frappe.delete_doc("Workspace", "My Work", force=True, ignore_permissions=True, delete_permanently=True)
	frappe.db.commit()
