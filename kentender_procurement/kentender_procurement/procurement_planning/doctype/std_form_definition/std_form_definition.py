# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

COMPLETED_BY = (
	"Procuring Entity",
	"Tenderer",
	"Successful Tenderer",
	"Bank",
	"Insurer",
	"Surety",
	"System",
	"Mixed",
)


class STDFormDefinition(Document):
	def validate(self):
		if self.completed_by not in COMPLETED_BY:
			frappe.throw(_("Invalid completed_by value."), title=_("Invalid form ownership"))
		if not frappe.db.exists("STD Template Version", self.version_code):
			frappe.throw(_("Version Code is not valid."), title=_("Invalid version link"))
		if not frappe.db.exists("STD Section Definition", self.section_code):
			frappe.throw(_("Section Code is not valid."), title=_("Invalid section link"))
		if not frappe.db.exists("Source Document Registry", self.source_document_code):
			frappe.throw(_("Source Document Code is not valid."), title=_("Invalid source link"))

