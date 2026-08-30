# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §6 — ensure the native Planning roles exist before the
Planning doctype permissions sync (pre_model_sync)."""

from __future__ import annotations

import frappe

ROLES = (
	"Departmental Author",
	"Head of User Department",
	"Procurement Planner",
	"Budget Officer",
	"Accounting Officer",
	"Plan Statutory Approver",
	"Planning Auditor",
)


def execute() -> None:
	for role in ROLES:
		if frappe.db.exists("Role", role):
			continue
		frappe.get_doc(
			{"doctype": "Role", "role_name": role, "desk_access": 1}
		).insert(ignore_permissions=True)
