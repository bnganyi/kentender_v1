# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import parse_json


class KPIProfile(Document):
	def validate(self):
		self._validate_metrics_json()
		self._validate_profile_code_unique()

	def _validate_metrics_json(self):
		raw = self.metrics
		if raw in (None, ""):
			frappe.throw(_("Metrics JSON is required."), title=_("Invalid metrics"))
		parsed = parse_json(raw) if isinstance(raw, str) else raw
		if not isinstance(parsed, list):
			frappe.throw(_("Metrics must be a JSON list."), title=_("Invalid metrics"))
		for idx, row in enumerate(parsed):
			if isinstance(row, str):
				continue
			if isinstance(row, dict) and row:
				continue
			frappe.throw(
				_("Metrics entry {0} must be a non-empty string or object.").format(idx + 1),
				title=_("Invalid metrics"),
			)

	def _validate_profile_code_unique(self):
		if not self.profile_code:
			return
		filters = {"profile_code": self.profile_code}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		if frappe.db.exists("KPI Profile", filters):
			frappe.throw(_("Profile Code must be unique."), title=_("Duplicate profile code"))
