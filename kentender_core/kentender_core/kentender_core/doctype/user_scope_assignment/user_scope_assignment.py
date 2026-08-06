# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class UserScopeAssignment(Document):
	def validate(self):
		if self.organisation_unit:
			ou_pe = frappe.db.get_value(
				"Organisation Unit", self.organisation_unit, "procuring_entity"
			)
			if ou_pe and ou_pe != self.procuring_entity:
				frappe.throw(
					"Organisation Unit must belong to the assigned Procuring Entity.",
					title="Invalid user scope",
				)
