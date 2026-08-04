# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class BudgetLine(Document):
	def validate(self):
		if flt(self.approved_amount) <= 0:
			frappe.throw("Approved amount must be positive.")
		available = (
			flt(self.approved_amount) - flt(self.amount_reserved) - flt(self.amount_committed)
		)
		if available < 0:
			frappe.throw("Budget Line Available cannot be negative.")
