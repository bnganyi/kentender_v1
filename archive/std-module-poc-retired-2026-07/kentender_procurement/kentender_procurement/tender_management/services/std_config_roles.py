# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG — shared role gates for configurator, technical JSON, and advanced catalogue."""

from __future__ import annotations

import frappe

STD_TECHNICAL_VIEW_ROLES: frozenset[str] = frozenset(
	{
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Reviewer",
		"STD Template Auditor",
		"STD Technical Inspector",
	}
)

STD_ADVANCED_CATALOGUE_ROLES: frozenset[str] = frozenset(
	{
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Importer",
		"STD Template Reviewer",
		"STD Template Approver",
		"STD Template Activator",
		"STD Template Auditor",
		"STD Technical Inspector",
	}
)

STD_CONFIGURATOR_WRITE_ROLES: frozenset[str] = frozenset(
	{
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Importer",
	}
)


def has_any_role(roles: frozenset[str]) -> bool:
	if frappe.session.user == "Administrator":
		return True
	return bool(roles.intersection(frappe.get_roles()))


def can_use_std_advanced_catalogue() -> bool:
	return has_any_role(STD_ADVANCED_CATALOGUE_ROLES)


def can_view_technical_json() -> bool:
	return has_any_role(STD_TECHNICAL_VIEW_ROLES)


def can_edit_technical_json_config() -> bool:
	"""Write-capable technical JSON (lifecycle checked separately per template)."""
	return has_any_role(STD_CONFIGURATOR_WRITE_ROLES)
