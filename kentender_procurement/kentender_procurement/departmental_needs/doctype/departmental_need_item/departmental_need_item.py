# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.constants import STATE_DRAFT, STATE_RETURNED


class DepartmentalNeedItem(Document):
	def validate(self):
		if float(self.indicative_quantity or 0) <= 0:
			frappe.throw("Indicative quantity must be greater than zero.", title="NDS_ITEM_QUANTITY_INVALID")
		state = frappe.db.get_value("Departmental Need", self.departmental_need, "status")
		if state and state not in {STATE_DRAFT, STATE_RETURNED}:
			frappe.throw("Accepted or submitted Departmental Need items are immutable.", frappe.PermissionError, title="NDS_CONTENT_LOCKED")

	def on_trash(self):
		state = frappe.db.get_value("Departmental Need", self.departmental_need, "status")
		if state not in {STATE_DRAFT, STATE_RETURNED}:
			frappe.throw("Accepted or submitted Departmental Need items are immutable.", frappe.PermissionError, title="NDS_CONTENT_LOCKED")
