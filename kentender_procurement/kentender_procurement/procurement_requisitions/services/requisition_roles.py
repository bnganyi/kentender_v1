# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §8 — the business responsibilities Procurement
Requisitions names, exactly as registered in
`kentender_core.services.business_role_registry`.

Authority is a role-bound `User Responsibility Assignment` resolved by the
shared AUTH-ADR-001 v1.6 resolver (services/requisition_authorization.py); a
Frappe Role is only the framework projection of an assignment. This module is
the single vocabulary for the role labels Requisitions commands require.
"""

from __future__ import annotations

ROLE_DEPARTMENTAL_AUTHOR = "Departmental Author"
ROLE_HEAD_OF_USER_DEPARTMENT = "Head of User Department"
ROLE_HEAD_OF_PROCUREMENT_FUNCTION = "Head of Procurement Function"
ROLE_PROCUREMENT_PLANNER = "Procurement Planner"
ROLE_AUDITOR = "Auditor"
ROLE_PROCUREMENT_OFFICER = "Procurement Officer"

# §8 — Organisation Unit scoped responsibilities.
DEPARTMENTAL_ROLES = (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT)
# §8 — Site-wide responsibilities (neutral read; decisions stay with HOPF).
SITE_WIDE_ROLES = (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_PLANNER, ROLE_PROCUREMENT_OFFICER, ROLE_AUDITOR)
ALL_REQUISITION_ROLES = DEPARTMENTAL_ROLES + SITE_WIDE_ROLES

# The Tender Preparation responsibilities that consume this module's handoff
# (command purpose), and those that may only list it (read purpose).
TENDER_CALLER_ROLES = (ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
TENDER_SEAM_READER_ROLES = TENDER_CALLER_ROLES + (ROLE_AUDITOR,)

# §13.13 Workspace forbidden — exact copy.
FORBIDDEN_MESSAGE = (
	"You do not have access to Procurement Requisitions. This area needs Departmental Author, Head of User Department, "
	"Head of Procurement Function, Procurement Planner, Procurement Officer, Auditor, Administrator or System Manager access. "
	"Ask your KenTender administrator to assign the appropriate responsibility in System setup."
)


def ensure_requisition_roles() -> None:
	"""The Frappe Role projections are owned by the registry (AUTH §5.7)."""
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()
