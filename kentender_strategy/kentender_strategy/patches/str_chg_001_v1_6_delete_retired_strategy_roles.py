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

Did NOT delete "Strategy Manager" at the time, because kentender_procurement's
Procurement Lifecycle G0-011 role matrix and DocPerm rows on Procurement
Journey / Procurement Handoff Card / Procuring Department / Procuring Entity
still granted read through it.

Superseded: those grants were removed and the Role deleted in
`str_chg_001_v1_7_delete_strategy_manager_role.py`. Sparing it here left a
Role whose name promised Strategy authority it had not carried since the
rebuild — holders saw "STRATEGY MANAGER" in the Desk header and were then
refused AUTH_ROLE_REQUIRED by every Strategy action.
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
