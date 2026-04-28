# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class STDWorksRequirementComponentDefinition(Document):
	def validate(self):
		if not frappe.db.exists("STD Template Version", self.version_code):
			frappe.throw(_("Version Code is not valid."), title=_("Invalid version link"))
		if not frappe.db.exists("STD Section Definition", self.section_code):
			frappe.throw(_("Section Code is not valid."), title=_("Invalid section link"))

