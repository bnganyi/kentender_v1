# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PackageReviewDecision(Document):
	def validate(self):
		if self.decision_type in ("Returned for Correction", "Cancelled") and not (
			self.decision_reason or ""
		).strip():
			frappe.throw(frappe._("Decision reason is required for return or cancellation."))
		if self.decision_type == "Returned for Correction" and not (
			self.required_correction or ""
		).strip():
			frappe.throw(frappe._("Required correction is required when returning a package."))
