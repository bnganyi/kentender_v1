# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

# B3 — keep in sync with Demand.STATUSES_FULLY_EDITABLE (avoid circular import).
_PARENT_EDITABLE_STATUSES = frozenset(("Draft", "Rejected"))


class DemandItem(Document):
	def validate(self):
		# B3 — defense-in-depth if child rows are saved without parent.
		if self.parenttype == "Demand" and self.parent:
			if not getattr(frappe.flags, "demand_lifecycle_action", None):
				st = frappe.db.get_value("Demand", self.parent, "status")
				if st and st not in _PARENT_EDITABLE_STATUSES:
					frappe.throw(
						_("Line items cannot be edited in the current workflow state."),
						title=_("Record locked"),
					)
		# A3 — line_total is derived; always overwrite (field is read-only in schema).
		qty = flt(self.quantity)
		unit = flt(self.estimated_unit_cost)
		self.line_total = flt(qty * unit)
