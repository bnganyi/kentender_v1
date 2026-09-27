# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class BidHandoff(Document):
	def validate(self) -> None:
		# BDS-CHG-001 v0.8 plan D12 — written only by the Bid Submission commands
		# (`flags.kt_bid_command`), never by a Desk save or script.
		if not self.flags.get("kt_bid_command"):
			frappe.throw("%s records change only through Bid Submission commands." % self.doctype)

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("%s records are never deleted outside a fixture wipe." % self.doctype)
