# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Child table: section-bound attachment metadata (doc 5 §9, WH-003)."""

import frappe
from frappe.exceptions import ValidationError
from frappe.model.document import Document
from frappe.utils import cint


class TenderSectionAttachment(Document):
	def validate(self) -> None:
		if cint(self.supplier_facing) and cint(self.internal_only):
			frappe.throw(
				frappe._("Supplier Facing and Internal Only cannot both be set (doc 5 §9)."),
				title=frappe._("Conflicting attachment flags"),
				exc=ValidationError,
			)
