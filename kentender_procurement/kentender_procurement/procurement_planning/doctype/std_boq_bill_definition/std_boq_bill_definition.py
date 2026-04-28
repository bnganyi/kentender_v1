# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class STDBOQBillDefinition(Document):
	def validate(self):
		if not frappe.db.exists("STD BOQ Definition", self.boq_definition_code):
			frappe.throw(_("BOQ Definition Code is not valid."), title=_("Invalid BOQ definition link"))

