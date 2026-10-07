# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class AuthorizationDelegation(CommandWriteGuardMixin, Document):
	"""Retired AUTH-G04 authority store (AUD-XC-026, AUTH-ADR-001 §11.3 step 9):
	no service opens `command_write("Legacy Authorization")`, so the record
	cannot be created, changed or deleted through the Desk, REST or any
	service. Rows that exist are kept for the migration evidence only."""

	command_write_family = "Legacy Authorization"
