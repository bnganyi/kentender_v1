# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""H3: centralized policy for privileged supplier governance actions."""


import frappe


def can_blacklist() -> bool:
	from kentender_suppliers.services import registry_access

	return registry_access.has_capability("blacklist")
