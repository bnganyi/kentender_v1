# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.6 — hard-delete the Strategy-owned legacy Role master
records left in place by the v1.5 role/lifecycle simplification patch
(`str_chg_001_v1_5_role_and_lifecycle_simplification.py`), which only
stripped the `Has Role` grants and deliberately left the Role docs
themselves (documentation-only retirement at the time).

Deletes, provided no live code/DocPerm anywhere in the repo still
references them by name (re-verified by grep before writing this patch):

- Strategy Officer
- Strategy Reviewer
- Strategy Approval Authority (renamed to Strategy Approver in v1.5)

Does NOT delete "Strategy Manager" — that Role is still live outside
Strategy's own workflow: kentender_procurement's Procurement Lifecycle
G0-011 role matrix (`procurement_lifecycle/api/permission_guard.py`'s
`JOURNEY_READ_ROLES`) and DocPerm rows on kentender_procurement's
`Procurement Journey`/`Procurement Handoff Card` and kentender_core's
`Procuring Department`/`Procuring Entity` doctypes all still grant read
access to "Strategy Manager" holders. Deleting that Role would silently
break those cross-app read grants, so it is intentionally left alone here.
"""

from __future__ import annotations

import frappe

ROLES_TO_DELETE = (
	"Strategy Officer",
	"Strategy Reviewer",
	"Strategy Approval Authority",
)


def execute() -> None:
	for role in ROLES_TO_DELETE:
		# Defensive: strip any stray Has Role grant first (v1.5 already
		# stripped Reviewer/Approval Authority grants; Strategy Officer
		# grants were never explicitly stripped by an earlier patch).
		frappe.db.delete("Has Role", {"parenttype": "User", "role": role})
		if frappe.db.exists("Role", role):
			frappe.delete_doc("Role", role, force=True, ignore_permissions=True)

	frappe.db.commit()
