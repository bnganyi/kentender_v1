"""AUTH-ADR-001 — the reference-data seed used to grant BOTH central Roles
(Central Reference Data Steward, Central Configuration Approver) to every
known governance actor as a coarse Page-visibility gate. Now that Role
membership is itself real authority under the native engine, that over-grant
silently over-authorizes every actor to every central action. Strip the
Role each actor does not actually hold real authority for — the seed itself
only ever adds Roles via `add_roles()`, so this one-time correction is
needed to remove what a prior run of that seed already granted.
"""

from __future__ import annotations

import frappe

STEWARD_ROLE = "Central Reference Data Steward"
APPROVER_ROLE = "Central Configuration Approver"

# email -> the one central role this actor should NOT hold.
_STRIP = {
	"lydia.mwangi@kentender.example.test": APPROVER_ROLE,
	"daniel.kariuki@kentender.example.test": STEWARD_ROLE,
	"mercy.kilonzo@moh.example.test": (STEWARD_ROLE, APPROVER_ROLE),
	"samuel.otieno@moh.example.test": (STEWARD_ROLE, APPROVER_ROLE),
	"amina.hassan@moh.example.test": (STEWARD_ROLE, APPROVER_ROLE),
}


def execute() -> None:
	for email, roles in _STRIP.items():
		if not frappe.db.exists("User", email):
			continue
		to_strip = (roles,) if isinstance(roles, str) else roles
		for role in to_strip:
			frappe.db.delete("Has Role", {"parent": email, "parenttype": "User", "role": role})
