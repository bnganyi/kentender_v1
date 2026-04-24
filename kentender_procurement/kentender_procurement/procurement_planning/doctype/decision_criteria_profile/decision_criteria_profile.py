# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from frappe.utils.data import parse_json


class DecisionCriteriaProfile(Document):
	def validate(self):
		self._validate_criteria_json()
		self._validate_profile_code_unique()

	def _validate_criteria_json(self):
		raw = self.criteria
		if raw in (None, ""):
			frappe.throw(_("Criteria JSON is required."), title=_("Invalid criteria"))
		parsed = parse_json(raw) if isinstance(raw, str) else raw
		if not isinstance(parsed, list):
			frappe.throw(_("Criteria must be a JSON list."), title=_("Invalid criteria"))
		for idx, row in enumerate(parsed):
			if not isinstance(row, dict):
				frappe.throw(
					_("Criteria entry {0} must be a JSON object.").format(idx + 1),
					title=_("Invalid criteria"),
				)
			criterion = row.get("criterion")
			if not criterion or not isinstance(criterion, str) or not criterion.strip():
				frappe.throw(
					_("Criteria entry {0} must include a non-empty \"criterion\" string.").format(idx + 1),
					title=_("Invalid criteria"),
				)
			if "weight" in row and row["weight"] is not None:
				w = flt(row["weight"])
				if w < 0 or w > 100:
					frappe.throw(
						_("Criteria entry {0}: weight must be between 0 and 100 when set.").format(idx + 1),
						title=_("Invalid criteria"),
					)

	def _validate_profile_code_unique(self):
		if not self.profile_code:
			return
		filters = {"profile_code": self.profile_code}
		if not self.is_new():
			filters["name"] = ("!=", self.name)
		if frappe.db.exists("Decision Criteria Profile", filters):
			frappe.throw(_("Profile Code must be unique."), title=_("Duplicate profile code"))
