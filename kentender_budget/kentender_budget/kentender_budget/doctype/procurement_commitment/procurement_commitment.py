# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document
from frappe.utils import flt


class ProcurementCommitment(Document):
	def validate(self):
		self.outstanding_amount = max(
			0.0, flt(self.current_amount) - flt(self.actual_expenditure)
		)
