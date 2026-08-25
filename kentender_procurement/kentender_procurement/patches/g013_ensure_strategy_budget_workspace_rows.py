# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G0-012 — ensure **Strategy Management** and **Budget Management** Workspace rows exist.

The Procurement ``Workspace Sidebar`` links to these targets. If the ``Workspace``
documents were never shipped (no fixtures in-tree) or never imported, boot rebuild
(``setup/workspace_permissions.py``) drops **Strategy Alignment** / **Budget & Funding**
from the rail because workspace links require the target ``Workspace`` to exist.

Creates minimal public workspace shells when missing, then matches
``g012_cross_app_workspaces_public`` visibility (``public=1``, ``is_hidden=0``).

Idempotent; safe to re-run.
"""

from __future__ import annotations

import frappe

_WORKSPACES: tuple[tuple[str, str, str, str], ...] = (
	("Strategy Management", "Kentender Strategy", "kentender_strategy", "project"),
)


def execute() -> None:
	frappe.set_user("Administrator")

	# Budget Management has one canonical creation/repair implementation, owned by
	# kentender_budget, to prevent this row drifting to a different label/icon.
	from kentender_budget.services.budget_workspace import ensure_budget_workspace

	ensure_budget_workspace()

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
