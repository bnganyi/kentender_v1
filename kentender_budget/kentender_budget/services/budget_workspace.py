# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Single source of truth for the Budget Management Workspace identity.

Workspace autoname is ``field:label`` (frappe/desk/doctype/workspace/workspace.json).
Inserting a doc with ``label="Budget & Funding"`` and no ``set_name`` therefore names
the record "Budget & Funding", not the canonical "Budget Management" every Link
(Procurement sidebar) and lookup expects. ``insert(set_name=...)`` is the correction.
"""

from __future__ import annotations

import frappe

CANONICAL_NAME = "Budget Management"
LEGACY_NAME = "Budget & Funding"

_DISPLAY_LABEL = "Budget & Funding"
_MODULE = "Kentender Budget"
_APP = "kentender_budget"
_ICON = "money-bill-wave"


def ensure_budget_workspace() -> str:
	"""Create, rename, or normalize the Budget Management Workspace. Idempotent."""
	if not frappe.db.exists("Workspace", CANONICAL_NAME):
		if frappe.db.exists("Workspace", LEGACY_NAME):
			frappe.rename_doc(
				"Workspace",
				LEGACY_NAME,
				CANONICAL_NAME,
				force=True,
			)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Workspace",
					"label": _DISPLAY_LABEL,
					"title": CANONICAL_NAME,
					"module": _MODULE,
					"app": _APP,
					"type": "Workspace",
					"content": "[]",
					"icon": _ICON,
					# validate() requires Workspace Manager to set public on save; db.set_value below bypasses it.
					"public": 0,
					"is_hidden": 0,
				}
			)
			doc.insert(ignore_permissions=True, set_name=CANONICAL_NAME)

	# Unconditional: normalizes a Workspace another creation site (e.g. a cross-app
	# fixture) already created under the canonical name with a mismatched label/module.
	frappe.db.set_value(
		"Workspace",
		CANONICAL_NAME,
		{
			"label": _DISPLAY_LABEL,
			"title": CANONICAL_NAME,
			"module": _MODULE,
			"app": _APP,
			"public": 1,
			"is_hidden": 0,
		},
		update_modified=False,
	)

	return CANONICAL_NAME
