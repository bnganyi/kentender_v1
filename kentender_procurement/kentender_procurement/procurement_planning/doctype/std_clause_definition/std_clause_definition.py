# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

CLAUSE_EDITABILITY = ("Locked", "Parameter Only", "Structured Editable", "Generated", "Generated Structured")


class STDClauseDefinition(Document):
	def validate(self):
		if self.editability not in CLAUSE_EDITABILITY:
			frappe.throw(_("Invalid clause editability."), title=_("Invalid editability"))
		if not frappe.db.exists("STD Section Definition", self.section_code):
			frappe.throw(_("Section Code is not valid."), title=_("Invalid section link"))
		if not frappe.db.exists("STD Template Version", self.version_code):
			frappe.throw(_("Version Code is not valid."), title=_("Invalid version link"))
		if not frappe.db.exists("Source Document Registry", self.source_document_code):
			frappe.throw(_("Source Document Code is not valid."), title=_("Invalid source link"))
		if self.editability == "Locked" and int(self.instance_edit_allowed or 0):
			frappe.throw(
				_("Locked clauses cannot be marked as instance-editable."),
				title=_("Invalid locked clause setting"),
			)
		has_page_trace = self.source_page_start or self.source_page_end
		has_hash_trace = bool(self.source_text_hash)
		if not has_page_trace and not has_hash_trace:
			frappe.throw(
				_("Clause source trace is required (page range or source text hash)."),
				title=_("Missing source trace"),
			)

