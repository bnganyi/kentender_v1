# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §6 — the business responsibilities Tenders names,
exactly as registered in `kentender_core.services.business_role_registry`.

Authority is a role-bound `User Responsibility Assignment` resolved by the
shared AUTH-ADR-001 v1.8 resolver (`services/tender_authorization.py`); a
Frappe Role is only the framework projection of an assignment. No new
registry entry is needed for v0.8 (plan D11): Procurement Officer, Head of
Procurement Function, Accounting Officer and Auditor are Site-wide;
Departmental Author and Head of User Department read the neutral projection
for Tenders whose source Requisition their Organisation Unit contributed to.
"Authorised technical operator" has no MVP action and no entry (§6).
"""

from __future__ import annotations

ROLE_PROCUREMENT_OFFICER = "Procurement Officer"
ROLE_HEAD_OF_PROCUREMENT_FUNCTION = "Head of Procurement Function"
ROLE_ACCOUNTING_OFFICER = "Accounting Officer"
ROLE_AUDITOR = "Auditor"
ROLE_DEPARTMENTAL_AUTHOR = "Departmental Author"
ROLE_HEAD_OF_USER_DEPARTMENT = "Head of User Department"

# §6 — Site-wide business responsibilities that act on a Tender.
ACTOR_ROLES = (ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_ACCOUNTING_OFFICER)
# §6 — Site-wide readers (every actor role plus the Auditor).
SITE_WIDE_ROLES = ACTOR_ROLES + (ROLE_AUDITOR,)
# §6 — Organisation-Unit-scoped neutral readers.
DEPARTMENTAL_ROLES = (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT)
ALL_TENDER_ROLES = SITE_WIDE_ROLES + DEPARTMENTAL_ROLES

# §10.15 Forbidden copy names them in this order.
FORBIDDEN_RESPONSIBILITIES = (
	"Procurement Officer, Head of Procurement Function, Accounting Officer, Departmental Author, "
	"Head of User Department, Auditor or Authorised technical operator"
)

# §7.4 `ReceiveAddendumInquiry` — the inbound producer is a service identity,
# never a business responsibility (plan D8). Registered as a Frappe Role so a
# service user can carry it; it grants no Desk read of anything.
INQUIRY_PRODUCER_ROLE = "Tender Inquiry Producer"


def ensure_tender_roles() -> None:
	"""The Frappe Role projections are owned by the registry (AUTH §5.7)."""
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()
