# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PackageMethodDecision(Document):
	def validate(self):
		if self.override_flag and not (self.override_reason or "").strip():
			frappe.throw(frappe._("Override reason is required when method is overridden."))
