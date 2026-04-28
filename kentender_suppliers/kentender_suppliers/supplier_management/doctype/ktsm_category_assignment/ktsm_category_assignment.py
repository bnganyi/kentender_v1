# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class KTSMCategoryAssignment(Document):
	def validate(self):
		# B3: inactive category
		if self.category and not frappe.db.get_value("KTSM Supplier Category", self.category, "is_active"):
			frappe.throw(_("This category is not active for new assignment."))
		existing = frappe.db.exists(
			"KTSM Category Assignment",
			{
				"supplier_profile": self.supplier_profile,
				"category": self.category,
				"name": ("!=", self.name),
			},
		)
		if existing:
			frappe.throw(_("This category is already assigned to this supplier profile."))
		if self.qualification_status == "Rejected" and not (self.review_notes or "").strip():
			frappe.throw(_("Review notes are required when category qualification is Rejected."))
