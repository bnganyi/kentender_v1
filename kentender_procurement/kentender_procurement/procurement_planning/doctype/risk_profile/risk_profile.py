# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import parse_json

VALID_RISK_LEVELS = frozenset(("Low", "Medium", "High"))


class RiskProfile(Document):
	def validate(self):
		self._validate_risk_level()
		self._validate_risks_json()
		self._validate_profile_code_unique()

	def _validate_risk_level(self):
		if self.risk_level not in VALID_RISK_LEVELS:
			frappe.throw(
				_("Risk Level must be one of: Low, Medium, High."),
				title=_("Invalid risk level"),
			)

	def _validate_risks_json(self):
		raw = self.risks
		if raw in (None, ""):
			frappe.throw(_("Risks JSON is required."), title=_("Invalid risks"))
		parsed = parse_json(raw) if isinstance(raw, str) else raw
		if not isinstance(parsed, list):
			frappe.throw(_("Risks must be a JSON list."), title=_("Invalid risks"))
		for idx, row in enumerate(parsed):
			if not isinstance(row, dict):
				frappe.throw(
					_("Risks entry {0} must be a JSON object.").format(idx + 1),
					title=_("Invalid risks"),
				)
			for key in ("risk", "mitigation"):
				if key in row and row[key] is not None and not isinstance(row[key], str):
					frappe.throw(
						_("Risks entry {0}: {1} must be a string when set.").format(idx + 1, key),
						title=_("Invalid risks"),
					)

	def _validate_profile_code_unique(self):
		if not self.profile_code:
			return
		filters = {"profile_code": self.profile_code}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		if frappe.db.exists("Risk Profile", filters):
			frappe.throw(_("Profile Code must be unique."), title=_("Duplicate profile code"))
