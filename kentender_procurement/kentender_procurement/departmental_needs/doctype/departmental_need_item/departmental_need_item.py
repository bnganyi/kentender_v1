# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.constants import STATE_DRAFT, STATE_RETURNED


class DepartmentalNeedItem(Document):
	def validate(self):
		# Draft/Returned items may be genuinely incomplete (NDS-FR-023) — only reject
		# values that are actively nonsensical, never merely absent. Completeness for
		# submission is enforced exclusively by lifecycle.submit_need's §5 check.
		if float(self.indicative_quantity or 0) < 0:
			frappe.throw("Indicative quantity cannot be negative.", title="NDS_ITEM_QUANTITY_INVALID")
		if self.other_unit and self.unit_code != "Other":
			frappe.throw("Other Unit may only be set when Unit is Other.", title="NDS_ITEM_OTHER_UNIT_INVALID")
		state = frappe.db.get_value("Departmental Need", self.departmental_need, "status")
		if state and state not in {STATE_DRAFT, STATE_RETURNED}:
			frappe.throw("Accepted or submitted Departmental Need items are immutable.", frappe.PermissionError, title="NDS_CONTENT_LOCKED")

	def on_trash(self):
		state = frappe.db.get_value("Departmental Need", self.departmental_need, "status")
		if state not in {STATE_DRAFT, STATE_RETURNED}:
			frappe.throw("Accepted or submitted Departmental Need items are immutable.", frappe.PermissionError, title="NDS_CONTENT_LOCKED")
