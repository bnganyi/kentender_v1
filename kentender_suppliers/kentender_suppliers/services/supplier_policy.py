# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""H3: centralized policy for privileged supplier governance actions."""


import frappe


def can_blacklist() -> bool:
	roles = frappe.get_roles()
	return "System Manager" in roles or "KenTender Supplier Blacklist Authority" in roles
