# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.constants import STATE_ACCEPTED


class PlanNeedAllocation(Document):
	def validate(self):
		if float(self.allocated_quantity or 0) <= 0:
			frappe.throw("Allocated quantity must be greater than zero.", title="NDS_ALLOCATION_QUANTITY_INVALID")
		item = frappe.db.get_value("Departmental Need Item", self.departmental_need_item, ["departmental_need", "indicative_quantity"], as_dict=True)
		if not item or item.departmental_need != self.departmental_need:
			frappe.throw("The source Need line does not belong to the selected Departmental Need.", title="NDS_ALLOCATION_LINE_MISMATCH")
		if frappe.db.get_value("Departmental Need", self.departmental_need, "status") != STATE_ACCEPTED:
			frappe.throw("Only Accepted for planning Needs may be allocated.", title="NDS_NEED_NOT_ELIGIBLE")
		if float(self.allocated_quantity) > float(item.indicative_quantity):
			frappe.throw("Allocated quantity exceeds the source Need line.", title="NDS_ALLOCATION_EXCEEDS_LINE")
