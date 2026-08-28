"""CFG-CHG-002 v0.4 / AUTH-ADR-001 v1.1 §12.2 — Reference Data maintenance
collapses from a five-role, two-approval-chain model onto one global
Reference Data Manager Role. This one-time patch performs the explicit
user-by-user reconciliation the ADR requires: it strips the four retired
Roles from every current holder (they carry no other live authority — none
of the other three apps reference these Role names) and grants Reference
Data Manager only to the confirmed positive fixture, Lydia Mwangi (ADR §12.4
— Amina Hassan and the other holders of retired roles do NOT receive
Reference Data Manager automatically; that would just re-create the same
over-authorization defect this migration corrects).

Role master records and historical Audit Event/Capability Profile rows are
left in place (documentation-only retirement, not a hard delete) — only the
live `Has Role` grants that would otherwise silently confer no-longer-real
authority are removed.
"""

from __future__ import annotations

import frappe

_RETIRED_ROLES = (
	"Central Reference Data Steward",
	"Central Configuration Approver",
	"PE Configuration Steward",
	"Professional Configuration Reviewer / HoPF",
)

_RECONCILED_MANAGER_EMAIL = "lydia.mwangi@kentender.example.test"


def execute() -> None:
	for role in _RETIRED_ROLES:
		frappe.db.delete("Has Role", {"parenttype": "User", "role": role})

	if not frappe.db.exists("Role", "Reference Data Manager"):
		frappe.get_doc({"doctype": "Role", "role_name": "Reference Data Manager", "desk_access": 1}).insert(
			ignore_permissions=True
		)
	if frappe.db.exists("User", _RECONCILED_MANAGER_EMAIL):
		frappe.get_doc("User", _RECONCILED_MANAGER_EMAIL).add_roles("Reference Data Manager")
