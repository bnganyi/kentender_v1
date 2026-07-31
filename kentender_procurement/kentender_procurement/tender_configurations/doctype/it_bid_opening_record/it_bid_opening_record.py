# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import cstr


class ITBidOpeningRecord(Document):
	def before_insert(self):
		if not cstr(self.opening_ref or "").strip():
			self.opening_ref = cstr(make_autoname("OPEN-.YYYY.-.#####"))

	def validate(self):
		if self.is_new() or getattr(self.flags, "ignore_opening_immutability", False):
			return
		prior = frappe.db.get_value(self.doctype, self.name, "status")
		if cstr(prior) != "Completed":
			return
		locked = (
			"publication",
			"configuration",
			"active_submission_ids",
			"active_bid_count",
			"opened_at",
			"opened_by",
			"register_completed_at",
			"opening_ref",
			"status",
		)
		for field in locked:
			db_val = frappe.db.get_value(self.doctype, self.name, field)
			if cstr(self.get(field) or "") != cstr(db_val or ""):
				frappe.throw(
					frappe._("Completed bid opening records are immutable."),
					title="BID_OPENING_IMMUTABLE",
				)
