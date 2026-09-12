# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §6 — the business responsibilities Procurement Planning
names, exactly as registered in `kentender_core.services.business_role_registry`.

Authority is a role-bound `User Responsibility Assignment` resolved by the
shared AUTH-ADR-001 v1.6 resolver (services/planning_authorization.py); a
Frappe Role is only the framework projection of an assignment. This module is
the single vocabulary for the role labels Planning commands require.
"""

from __future__ import annotations

ROLE_DEPARTMENTAL_AUTHOR = "Departmental Author"
ROLE_HEAD_OF_USER_DEPARTMENT = "Head of User Department"
ROLE_PROCUREMENT_PLANNER = "Procurement Planner"
ROLE_FINANCE_CONFIRMATION_OFFICER = "Finance Confirmation Officer"
ROLE_ACCOUNTING_OFFICER = "Accounting Officer"
ROLE_PLAN_STATUTORY_APPROVER = "Plan Statutory Approver"
ROLE_AUDITOR = "Auditor"
# PLN-CHG-001 v1.18 §6.2 (plan D6) — the Head of Procurement Function is a
# Plan actor in its own right: the exact read and **Sign and submit Annual
# Plan** capability (sod tag `plan_preparation_signature` in the registry),
# never an implicit Procurement Planner assignment.
ROLE_HEAD_OF_PROCUREMENT_FUNCTION = "Head of Procurement Function"

# §6 — Organisation Unit scoped responsibilities.
DEPARTMENTAL_ROLES = (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT)
# §6 — Site-wide responsibilities.
SITE_WIDE_ROLES = (
	ROLE_PROCUREMENT_PLANNER,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_AUDITOR,
)
ALL_PLANNING_ROLES = DEPARTMENTAL_ROLES + SITE_WIDE_ROLES

# REQ-CHG-001 v1.6 §5A/§9.1 — every role the requisition-eligibility
# projection and its two drawdown commands may see a caller from. Site-wide
# roles read unconditionally; the two Organisation-Unit-scoped roles only
# for a Plan Item whose contributing departments they hold (§7.4).
REQUISITION_CALLER_SITE_WIDE_ROLES = (ROLE_PROCUREMENT_PLANNER, ROLE_AUDITOR, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
REQUISITION_CALLER_ROLES = DEPARTMENTAL_ROLES + REQUISITION_CALLER_SITE_WIDE_ROLES

# PLN-DES-16 Forbidden copy names them in this order.
FORBIDDEN_RESPONSIBILITIES = (
	"Procurement Planner, Head of Procurement Function, Finance Confirmation Officer, Accounting Officer, "
	"the entity's statutory approver, Head of User Department, Departmental Author or Auditor"
)


def ensure_planning_roles() -> None:
	"""The Frappe Role projections are owned by the registry (AUTH §5.7)."""
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()
