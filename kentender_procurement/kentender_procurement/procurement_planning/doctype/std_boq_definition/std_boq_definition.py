# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

SUPPLIER_INPUT_MODE = ("Rate Only", "Amount Only", "None", "Mixed")


class STDBOQDefinition(Document):
	def validate(self):
		if not frappe.db.exists("STD Template Version", self.version_code):
			frappe.throw(_("Version Code is not valid."), title=_("Invalid version link"))
		if not frappe.db.exists("STD Section Definition", self.section_code):
			frappe.throw(_("Section Code is not valid."), title=_("Invalid section link"))
		if self.quantity_owner != "Procuring Entity":
			frappe.throw(
				_("Quantity owner must be Procuring Entity for Works BOQ definitions."),
				title=_("Invalid quantity owner"),
			)
		if self.supplier_input_mode not in SUPPLIER_INPUT_MODE:
			frappe.throw(_("Invalid supplier input mode."), title=_("Invalid supplier input mode"))
		if self.arithmetic_correction_stage != "Evaluation":
			frappe.throw(
				_("Arithmetic correction stage must be Evaluation."),
				title=_("Invalid arithmetic correction stage"),
			)

