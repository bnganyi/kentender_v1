# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import parse_json

DATA_TYPES = ("Boolean", "Select", "String", "Int", "Float", "Date", "Datetime", "JSON")
VALUE_RESOLUTION_STAGES = ("Template Configuration", "Tender Configuration", "Contract Creation")


class STDParameterDefinition(Document):
	def validate(self):
		if self.data_type not in DATA_TYPES:
			frappe.throw(_("Invalid parameter data type."), title=_("Invalid data type"))
		if self.value_resolution_stage and self.value_resolution_stage not in VALUE_RESOLUTION_STAGES:
			frappe.throw(
				_("Invalid value resolution stage."),
				title=_("Invalid value resolution stage"),
			)
		if not frappe.db.exists("STD Template Version", self.version_code):
			frappe.throw(_("Version Code is not valid."), title=_("Invalid version link"))
		if not frappe.db.exists("STD Section Definition", self.section_code):
			frappe.throw(_("Section Code is not valid."), title=_("Invalid section link"))
		if self.source_document_code and not frappe.db.exists("Source Document Registry", self.source_document_code):
			frappe.throw(_("Source Document Code is not valid."), title=_("Invalid source link"))
		if self.allowed_values:
			parsed = parse_json(self.allowed_values) if isinstance(self.allowed_values, str) else self.allowed_values
			if not isinstance(parsed, (list, dict)):
				frappe.throw(
					_("Allowed Values must be JSON list/object."),
					title=_("Invalid allowed values"),
				)

