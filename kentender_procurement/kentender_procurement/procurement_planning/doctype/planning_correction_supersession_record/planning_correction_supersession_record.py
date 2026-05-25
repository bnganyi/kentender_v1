# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import parse_json


class PlanningCorrectionSupersessionRecord(Document):
	def validate(self):
		if not (self.reason or "").strip():
			frappe.throw(_("Reason is required."), title=_("Missing reason"))
		raw = self.affected_fields_json
		if raw in (None, "", "[]", "{}"):
			frappe.throw(
				_("Affected fields must describe at least one impacted field."),
				title=_("Missing affected fields"),
			)
		parsed = parse_json(raw) if isinstance(raw, str) else raw
		if isinstance(parsed, dict):
			if not parsed:
				frappe.throw(
					_("Affected fields must describe at least one impacted field."),
					title=_("Missing affected fields"),
				)
		elif isinstance(parsed, list):
			if not parsed:
				frappe.throw(
					_("Affected fields must describe at least one impacted field."),
					title=_("Missing affected fields"),
				)
		else:
			try:
				json.loads(raw if isinstance(raw, str) else str(raw))
			except (TypeError, json.JSONDecodeError):
				frappe.throw(
					_("Affected fields must be valid JSON."),
					title=_("Invalid affected fields"),
				)
