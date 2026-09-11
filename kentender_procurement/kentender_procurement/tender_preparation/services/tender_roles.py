# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §5 — the business responsibilities Tender Preparation
names, exactly as registered in
`kentender_core.services.business_role_registry`.

All three are Site-wide (§5): the site is one Procuring Entity and Fiscal
Year is inherited display data, never an authorization dimension. Authority
is a role-bound `User Responsibility Assignment` resolved by the shared
AUTH-ADR-001 v1.6 resolver (services/tender_authorization.py); a Frappe Role
is only the framework projection of an assignment.
"""

from __future__ import annotations

ROLE_PROCUREMENT_OFFICER = "Procurement Officer"
ROLE_HEAD_OF_PROCUREMENT_FUNCTION = "Head of Procurement Function"
ROLE_AUDITOR = "Auditor"

# §5 — every Tender Preparation reader; all Site-wide.
SITE_WIDE_ROLES = (ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_AUDITOR)
# §5 — the two responsibilities that may run a command.
COMMAND_ROLES = (ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)

# §13.9 Forbidden copy names them in this order.
FORBIDDEN_RESPONSIBILITIES = "Procurement Officer, Head of Procurement Function or Auditor"
FORBIDDEN_HEADING = "You do not have access to Tender Preparation."
FORBIDDEN_TEXT = (
	f"This area needs one of these responsibilities: {FORBIDDEN_RESPONSIBILITIES}. "
	"Ask your KenTender administrator to assign one in System setup."
)


def ensure_tender_roles() -> None:
	"""The Frappe Role projections are owned by the registry (AUTH §5.7)."""
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()
