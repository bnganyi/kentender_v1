# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

SECTION_EDITABILITY = ("Locked", "Parameter Only", "Structured Editable", "Generated", "Generated Structured")


class STDSectionDefinition(Document):
	def validate(self):
		if self.editability not in SECTION_EDITABILITY:
			frappe.throw(_("Invalid section editability."), title=_("Invalid editability"))
		if not frappe.db.exists("STD Template Version", self.version_code):
			frappe.throw(_("Version Code is not valid."), title=_("Invalid version link"))
		if not frappe.db.exists("STD Part Definition", self.part_code):
			frappe.throw(_("Part Code is not valid."), title=_("Invalid part link"))
		if not frappe.db.exists("Source Document Registry", self.source_document_code):
			frappe.throw(_("Source Document Code is not valid."), title=_("Invalid source link"))

