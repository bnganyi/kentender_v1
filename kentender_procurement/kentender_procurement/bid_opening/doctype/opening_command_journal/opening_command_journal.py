# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class OpeningCommandJournal(Document):
	def validate(self) -> None:
		# BOP-CHG-001 v0.10 plan D2 — written only by the Bid Opening commands
		# (`flags.kt_bop_command`), never by a Desk save or script.
		if not self.flags.get("kt_bop_command"):
			frappe.throw("%s records change only through Bid Opening commands." % self.doctype)

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("%s records are never deleted outside a fixture wipe." % self.doctype)
