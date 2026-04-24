# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import parse_json


class VendorManagementProfile(Document):
	def validate(self):
		self._validate_rules_objects()
		self._validate_profile_code_unique()

	def _validate_rules_objects(self):
		for field, label in (
			("monitoring_rules", _("Monitoring Rules")),
			("escalation_rules", _("Escalation Rules")),
		):
			raw = self.get(field)
			if raw in (None, ""):
				frappe.throw(_("{0} JSON is required.").format(label), title=_("Invalid rules"))
			parsed = parse_json(raw) if isinstance(raw, str) else raw
			if not isinstance(parsed, dict):
				frappe.throw(_("{0} must be a JSON object.").format(label), title=_("Invalid rules"))
			self.set(field, parsed)

	def _validate_profile_code_unique(self):
		if not self.profile_code:
			return
		filters = {"profile_code": self.profile_code}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		if frappe.db.exists("Vendor Management Profile", filters):
			frappe.throw(_("Profile Code must be unique."), title=_("Duplicate profile code"))
