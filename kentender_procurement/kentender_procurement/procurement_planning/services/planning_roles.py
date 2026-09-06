# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §6 — the business responsibilities Procurement Planning
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

# §6 — Organisation Unit scoped responsibilities.
DEPARTMENTAL_ROLES = (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT)
# §6 — Site-wide responsibilities.
SITE_WIDE_ROLES = (
	ROLE_PROCUREMENT_PLANNER,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_AUDITOR,
)
ALL_PLANNING_ROLES = DEPARTMENTAL_ROLES + SITE_WIDE_ROLES

# PLN-DES-16 Forbidden copy names them in this order.
FORBIDDEN_RESPONSIBILITIES = (
	"Procurement Planner, Finance Confirmation Officer, Accounting Officer, the entity's "
	"statutory approver, Head of User Department, Departmental Author or Auditor"
)


def ensure_planning_roles() -> None:
	"""The Frappe Role projections are owned by the registry (AUTH §5.7)."""
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()
