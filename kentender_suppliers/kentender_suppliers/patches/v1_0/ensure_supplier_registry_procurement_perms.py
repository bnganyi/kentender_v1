"""Grant supplier registry DocPerms to core procurement roles (idempotent)."""

from __future__ import annotations

import frappe


def _upsert_custom_perm(doctype: str, role: str, perms: dict) -> None:
	existing = frappe.db.get_value(
		"Custom DocPerm",
		{
			"parent": doctype,
			"role": role,
			"permlevel": 0,
			"if_owner": 0,
		},
		"name",
	)
	if existing:
		return

	doc = frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			"__islocal": 1,
			"parent": doctype,
			"parenttype": "DocType",
			"parentfield": "permissions",
			"role": role,
			"if_owner": 0,
			"permlevel": 0,
			**perms,
		}
	)
	doc.insert(ignore_permissions=True)


def execute():
	full_roles = ("Procurement Officer", "Procurement Planner")
	review_roles = ("Planning Authority",)

	for role in (*full_roles, *review_roles):
		if not frappe.db.exists("Role", role):
			continue

		base_perms = {"read": 1, "print": 1, "export": 1}
		if role in full_roles:
			base_perms.update({"write": 1, "create": 1})
		if role in review_roles:
			base_perms.update({"write": 1})

		_upsert_custom_perm("KTSM Supplier Profile", role, base_perms)

		doc_perms = {"read": 1, "print": 1, "export": 1}
		cat_perms = {"read": 1, "print": 1, "export": 1}
		if role in full_roles:
			doc_perms.update({"write": 1, "create": 1})
			cat_perms.update({"write": 1, "create": 1})
		if role in review_roles:
			doc_perms.update({"write": 1})
			cat_perms.update({"write": 1})

		_upsert_custom_perm("KTSM Supplier Document", role, doc_perms)
		_upsert_custom_perm("KTSM Category Assignment", role, cat_perms)
		_upsert_custom_perm("KTSM Document Type", role, {"read": 1, "print": 1, "export": 1})
		_upsert_custom_perm(
			"KTSM Supplier Category", role, {"read": 1, "print": 1, "export": 1}
		)

