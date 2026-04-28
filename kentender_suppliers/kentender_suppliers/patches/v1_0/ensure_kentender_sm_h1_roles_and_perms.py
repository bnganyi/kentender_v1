# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""H1: KenTender Supplier roles + custom DocPerms (idempotent)."""

import frappe


def execute():
	roles = (
		"KenTender External Supplier",
		"KenTender Supplier Registry Officer",
		"KenTender Compliance Officer",
		"KenTender Approving Authority",
		"KenTender Supplier Auditor",
		"KenTender Supplier Blacklist Authority",
	)
	for rn in roles:
		if not frappe.db.exists("Role", rn):
			rr = frappe.get_doc(
				{
					"doctype": "Role",
					"role_name": rn,
					"desk_access": 1,
				}
			)
			rr.insert(ignore_permissions=True)

	# (doctype, role, read, write, create, select, read_if_owner, write_if_owner, ...)
	rules: list[
		tuple[str, str, dict]
	] = [
		(
			"KTSM Supplier Profile",
			"KenTender Supplier Registry Officer",
			{
				"read": 1,
				"write": 1,
				"create": 1,
				"print": 1,
				"export": 1,
			},
		),
		(
			"KTSM Supplier Document",
			"KenTender Supplier Registry Officer",
			{
				"read": 1,
				"write": 1,
				"create": 1,
				"print": 1,
				"export": 1,
			},
		),
		(
			"KTSM Category Assignment",
			"KenTender Supplier Registry Officer",
			{
				"read": 1,
				"write": 1,
				"create": 1,
				"print": 1,
				"export": 1,
			},
		),
		(
			"KTSM Document Type",
			"KenTender Supplier Registry Officer",
			{
				"read": 1,
				"print": 1,
				"export": 1,
			},
		),
		(
			"KTSM Supplier Category",
			"KenTender Supplier Registry Officer",
			{
				"read": 1,
				"print": 1,
				"export": 1,
			},
		),
		(
			"KTSM Supplier Document",
			"KenTender Compliance Officer",
			{
				"read": 1,
				"write": 1,
				"print": 1,
				"export": 1,
			},
		),
		(
			"KTSM Supplier Profile",
			"KenTender Approving Authority",
			{
				"read": 1,
				"write": 1,
				"print": 1,
				"export": 1,
			},
		),
		(
			"KTSM Supplier Profile",
			"KenTender Supplier Auditor",
			{
				"read": 1,
				"print": 1,
				"export": 1,
			},
		),
		(
			"KTSM Supplier Document",
			"KenTender Supplier Auditor",
			{
				"read": 1,
				"print": 1,
				"export": 1,
			},
		),
	]

	for doctype, role, perms in rules:
		# Match `frappe.permissions.add_permission` uniqueness (no parenttype in filter)
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
		if existing is not None:
			continue
		p = frappe.get_doc(
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
		p.insert(ignore_permissions=True)
