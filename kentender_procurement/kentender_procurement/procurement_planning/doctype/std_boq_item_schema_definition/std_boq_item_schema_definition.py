# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

OWNERS = ("Procuring Entity", "Tenderer", "System")


class STDBOQItemSchemaDefinition(Document):
	def validate(self):
		if not frappe.db.exists("STD BOQ Definition", self.boq_definition_code):
			frappe.throw(_("BOQ Definition Code is not valid."), title=_("Invalid BOQ definition link"))
		if self.item_owner not in OWNERS:
			frappe.throw(_("Invalid owner."), title=_("Invalid schema owner"))
		if self.field_key == "quantity" and (
			self.item_owner != "Procuring Entity" or int(self.supplier_editable or 0)
		):
			frappe.throw(
				_("Quantity field must be Procuring Entity owned and not supplier editable."),
				title=_("Invalid quantity ownership"),
			)

