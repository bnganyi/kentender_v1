# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class OrganisationUnit(Document):
	def validate(self):
		if not (self.org_unit_reference or "").strip():
			self.org_unit_reference = make_autoname("OU-.########")
		if not self.status:
			self.status = "Active"
		if self.parent_org_unit:
			parent_pe = frappe.db.get_value(
				"Organisation Unit", self.parent_org_unit, "procuring_entity"
			)
			if parent_pe and parent_pe != self.procuring_entity:
				frappe.throw(
					"Parent Organisation Unit must belong to the same Procuring Entity.",
					title="Invalid organisation hierarchy",
				)
			if self.parent_org_unit == self.name:
				frappe.throw("Organisation Unit cannot be its own parent.")
