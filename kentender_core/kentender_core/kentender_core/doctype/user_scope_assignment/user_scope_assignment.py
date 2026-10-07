# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class UserScopeAssignment(CommandWriteGuardMixin, Document):
	"""A retired scope projection (AUTH-ADR-001 §19: no User Scope Assignment beside the User
	Responsibility Assignment). Nothing creates or edits it any more; legacy rows are removed only
	by the seed clean-ups, inside the maintenance window of this family (RG-32)."""

	command_write_family = "Legacy Authorization"

	def validate(self):
		super().validate()
		if self.organisation_unit:
			ou_pe = frappe.db.get_value(
				"Organisation Unit", self.organisation_unit, "procuring_entity"
			)
			if ou_pe and ou_pe != self.procuring_entity:
				frappe.throw(
					"Organisation Unit must belong to the assigned Procuring Entity.",
					title="Invalid user scope",
				)
