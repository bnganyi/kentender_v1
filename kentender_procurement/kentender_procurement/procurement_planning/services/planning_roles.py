# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §6 — the native Frappe role set for Procurement Planning.

This module is the single vocabulary for Planning role names. There is no
capability store, scope-assignment record or second permission layer (§6,
decision D4): authorisation is native Role + User Permission, and every
service check names these constants.
"""

from __future__ import annotations

import frappe

ROLE_DEPARTMENTAL_AUTHOR = "Departmental Author"
ROLE_HEAD_OF_USER_DEPARTMENT = "Head of User Department"
ROLE_PROCUREMENT_PLANNER = "Procurement Planner"
ROLE_BUDGET_OFFICER = "Budget Officer"
ROLE_ACCOUNTING_OFFICER = "Accounting Officer"
ROLE_PLAN_STATUTORY_APPROVER = "Plan Statutory Approver"
ROLE_PLANNING_AUDITOR = "Planning Auditor"

ALL_PLANNING_ROLES = (
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	ROLE_BUDGET_OFFICER,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PLANNING_AUDITOR,
)


def ensure_planning_roles() -> None:
	"""Idempotently create the §6 role set (also run by the v1.2 patch)."""
	for role in ALL_PLANNING_ROLES:
		if frappe.db.exists("Role", role):
			continue
		frappe.get_doc(
			{"doctype": "Role", "role_name": role, "desk_access": 1}
		).insert(ignore_permissions=True)
