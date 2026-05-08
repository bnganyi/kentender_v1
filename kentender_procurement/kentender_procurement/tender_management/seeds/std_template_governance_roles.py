# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Template Governance — role bootstrap (STD-GOV-001).

Doc 7 §6: create Role documents with exact names; idempotent; no DocPerms here.
`QA / Test User` and `System Manager` are excluded per pack.
"""

from __future__ import annotations

import frappe

# Exact strings from STD Template Governance implementation pack §6.
STD_TEMPLATE_GOVERNANCE_ROLES: tuple[str, ...] = (
	"STD Template Importer",
	"STD Template Administrator",
	"STD Template Reviewer",
	"STD Template Approver",
	"STD Template Activator",
	"STD Template Auditor",
	"STD Technical Inspector",
	"Procurement Officer",
	"Procurement Planning Officer",
)


def ensure_std_template_governance_roles() -> None:
	"""Insert missing governance roles. Safe to call on every migrate."""
	for role_name in STD_TEMPLATE_GOVERNANCE_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(
			ignore_permissions=True
		)


def run_after_migrate() -> None:
	"""Hook: ``after_migrate`` entrypoint."""
	ensure_std_template_governance_roles()
