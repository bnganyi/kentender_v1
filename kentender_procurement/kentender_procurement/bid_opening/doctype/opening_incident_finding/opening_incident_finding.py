# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Opening Incident Finding: one support finding on an Opening incident (BOP-CHG-001 v0.16 §5.2). Append-only — a changed technical finding is a new
row and the earlier failed attempt stays — written only by the Bid Opening commands, carrying no sealed content, and a sealed record no Desk, list,
search or export reaches."""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_procurement.bid_submission.services.sealed import SealedRecordMixin


class OpeningIncidentFinding(SealedRecordMixin, Document):
	def validate(self) -> None:
		if not self.flags.get("kt_bop_command"):
			frappe.throw("%s records change only through Bid Opening commands." % self.doctype)
		if not self.is_new():
			frappe.throw("A finding is never changed.")

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("%s records are never deleted outside a fixture wipe." % self.doctype)
