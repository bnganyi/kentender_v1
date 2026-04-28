# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

FIELD_TYPES = ("String", "Text", "Int", "Float", "Date", "Datetime", "Select", "Boolean", "JSON")


class STDFormFieldDefinition(Document):
	def validate(self):
		if self.data_type not in FIELD_TYPES:
			frappe.throw(_("Invalid form field data type."), title=_("Invalid data type"))
		if not frappe.db.exists("STD Form Definition", self.form_code):
			frappe.throw(_("Form Code is not valid."), title=_("Invalid form link"))
		if not self.field_key or not str(self.field_key).strip():
			frappe.throw(_("Field Key is required."), title=_("Missing field key"))

