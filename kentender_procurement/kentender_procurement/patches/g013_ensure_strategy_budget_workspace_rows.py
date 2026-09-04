# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G0-012 — ensure the **Strategy Management** Workspace row exists.

The Procurement ``Workspace Sidebar`` links to this target. If the ``Workspace``
document was never shipped (no fixtures in-tree) or never imported, boot rebuild
(``setup/workspace_permissions.py``) drops **Strategy Alignment** from the rail
because workspace links require the target ``Workspace`` to exist.

Creates a minimal public workspace shell when missing, then matches
``g012_cross_app_workspaces_public`` visibility (``public=1``, ``is_hidden=0``).

Idempotent; safe to re-run.

FOLLOW_UPS.md FU-01 (closed): this patch originally also ensured a **Budget
Management** Workspace row, via ``kentender_budget.services.budget_workspace.
ensure_budget_workspace`` — a module BUD-CHG-001 v1.2's service-layer rewrite
(``ab785c6d``) deleted outright. On a site that had never run this patch,
``execute()`` raised ``ModuleNotFoundError`` and failed the whole-site
``bench migrate``, not just ``kentender_budget``'s. The rebuilt Budget &
Funding UI (BUD-CHG-001 v1.3) has no Workspace of its own at all — Procurement's
own rail row now points directly at the ``budget-funding`` Page
(``label: "Budget & Funding", link_to: "budget-funding", link_type: "Page"``),
so a **Budget Management** Workspace shell is no longer wanted. The Budget half
of this patch is removed outright (not left as dead, unreachable code) rather
than working around the missing import — patches may have their own body
corrected after having already run on some sites (the Patch Log only records
that the *name* ran once, not a hash of its contents), so this is safe for a
site that already executed the old two-Workspace version. The Strategy half
below is untouched and still real, still wanted.
"""

from __future__ import annotations

import frappe

_WORKSPACES: tuple[tuple[str, str, str, str], ...] = (
	("Strategy Management", "Kentender Strategy", "kentender_strategy", "project"),
)


def execute() -> None:
	frappe.set_user("Administrator")

	for label, module, app, icon in _WORKSPACES:
		if frappe.db.exists("Workspace", label):
			frappe.db.set_value(
				"Workspace",
				label,
				{"public": 1, "is_hidden": 0},
				update_modified=False,
			)
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Workspace",
				"label": label,
				"title": label,
				"module": module,
				"app": app,
				"type": "Workspace",
				"content": "[]",
				"icon": icon,
				# validate() requires Workspace Manager to set public on save; patch flip below.
				"public": 0,
				"is_hidden": 0,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.set_value(
			"Workspace",
			label,
			{"public": 1, "is_hidden": 0},
			update_modified=False,
		)

	frappe.db.commit()
