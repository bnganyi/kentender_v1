# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G0-012 / Procurement rail — keep cross-app workspaces visible in boot sidebar filter.

``workspace_permissions._build_sidebar_dict`` builds ``allowed_workspaces`` from
``public=1 AND is_hidden=0``. **Strategy Management** (kentender_strategy) and
**Budget Management** (kentender_budget) must stay in that set so **Strategy
Alignment** and **Budget & Funding** remain in the Procurement left rail above DIA.

Idempotent; safe to re-run.
"""

from __future__ import annotations

import frappe

_WORKSPACES: tuple[str, ...] = (
	"Strategy Management",
	"Budget Management",
)


def execute() -> None:
	for name in _WORKSPACES:
		if not frappe.db.exists("Workspace", name):
			continue
		frappe.db.set_value(
			"Workspace",
			name,
			{"public": 1, "is_hidden": 0},
			update_modified=False,
		)
	frappe.db.commit()
