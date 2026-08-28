# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.4 / AUTH-ADR-001 v1.1 — Reference Data authorization.

One global Frappe Role, Reference Data Manager, is the entire authorization
decision for every Procuring Entity, Financial Year and PE/FY Context
maintenance action. PE, FY and PE/FY Context are reference records, not
transactional approvals — they carry no `reference_data.*` capability
string, no PE/FY-specific scope, and no maker-checker/segregation chain
(CFG-CHG-002 v0.4 §1/§7/§18; AUTH-ADR-001 v1.1 §5.2/§12.2, AUTH-AC-003A/019).
"""

from __future__ import annotations

import frappe
from frappe import _

REFERENCE_DATA_MANAGER_ROLE = "Reference Data Manager"


def has_reference_data_manager_role(user: str) -> bool:
	"""Administrator is deliberately excluded: `frappe.get_roles("Administrator")`
	returns every Role registered in the system regardless of actual assignment,
	which would otherwise let the Administrator account silently perform a
	business decision without ever being granted the named Role (AUTH-AC-012)."""
	if not user or user in ("Guest", "Administrator"):
		return False
	return REFERENCE_DATA_MANAGER_ROLE in frappe.get_roles(user)


def require_reference_data_manager(user: str) -> None:
	if not has_reference_data_manager_role(user):
		frappe.throw(
			_("You do not have the required role for this action."),
			frappe.PermissionError,
			title="AUTH_ROLE_REQUIRED",
		)


def has_reference_data_read_access(user: str) -> bool:
	"""Maintenance access and read access to the Reference Data workspace are
	the same gate here (CFG-CHG-002 v0.4 §13.1: "Maintenance access requires
	the Reference Data Manager Frappe Role") — System Manager/Administrator
	retain their ordinary administrative visibility on top of that."""
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return True
	return has_reference_data_manager_role(user)
