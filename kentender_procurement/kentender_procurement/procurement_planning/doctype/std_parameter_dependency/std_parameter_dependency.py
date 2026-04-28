# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import parse_json

EFFECTS = ("Required", "Visible", "Hidden", "Default", "Validation")


class STDParameterDependency(Document):
	def validate(self):
		if self.effect not in EFFECTS:
			frappe.throw(_("Invalid dependency effect."), title=_("Invalid dependency effect"))
		if not frappe.db.exists("STD Template Version", self.version_code):
			frappe.throw(_("Version Code is not valid."), title=_("Invalid version link"))
		if not frappe.db.exists("STD Parameter Definition", self.trigger_parameter_code):
			frappe.throw(_("Trigger Parameter Code is not valid."), title=_("Invalid trigger parameter"))
		if not frappe.db.exists("STD Parameter Definition", self.dependent_parameter_code):
			frappe.throw(_("Dependent Parameter Code is not valid."), title=_("Invalid dependent parameter"))
		parsed = parse_json(self.trigger_value) if isinstance(self.trigger_value, str) else self.trigger_value
		if parsed is None:
			frappe.throw(_("Trigger Value must be valid JSON."), title=_("Invalid trigger value"))
		if not self.condition_expression:
			frappe.throw(
				_("Condition expression is required."),
				title=_("Missing dependency condition"),
			)

