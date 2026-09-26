# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class TenderBidDefinition(Document):
	pass

	def validate(self) -> None:
		# TPR-CHG-001 v0.12 §5.8/§12.3 / plan D14 — a row is written only by the
		# module's own lifecycle commands (`envelope.bump()` under
		# `flags.kt_lifecycle`), never by a Desk save or an ad-hoc script.
		if not self.is_new() and not self.flags.get("kt_lifecycle"):
			frappe.throw("%s rows are immutable outside the Tenders lifecycle commands (TPR-CHG-001 v0.12 §12.3)." % self.doctype)

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("%s rows are never deleted outside a fixture wipe (TPR-CHG-001 v0.12 §12.3)." % self.doctype)
