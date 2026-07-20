# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import cstr


class ElectronicBidSubmission(Document):
	def validate(self):
		prior = None
		if not self.is_new():
			prior = frappe.db.get_value("Electronic Bid Submission", self.name, "status")
		if cstr(prior) == "Sealed" and cstr(self.status) == "Sealed":
			# Block mutation of sealed bids (except no-op reloads)
			db_hash = frappe.db.get_value("Electronic Bid Submission", self.name, "seal_hash")
			db_resp = frappe.db.get_value("Electronic Bid Submission", self.name, "responses")
			if cstr(self.seal_hash) != cstr(db_hash) or cstr(self.responses) != cstr(db_resp or ""):
				frappe.throw(
					frappe._("Sealed electronic bids are immutable."),
					title="BID_IMMUTABLE",
				)
