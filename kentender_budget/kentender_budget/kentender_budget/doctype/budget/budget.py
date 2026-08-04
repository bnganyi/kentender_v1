# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class Budget(Document):
	def validate(self):
		if not (self.registration_source or "").strip():
			self.registration_source = "Direct capture"
		if self.start_date and self.end_date and self.start_date > self.end_date:
			frappe.throw("Budget end date must be on or after start date.")
