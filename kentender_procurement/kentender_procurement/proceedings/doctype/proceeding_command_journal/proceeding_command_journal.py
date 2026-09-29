# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class ProceedingCommandJournal(Document):
	def validate(self) -> None:
		# PRC-CHG-001 v0.9 §7 and BOP-CHG-001 v0.10 plan D2 — written only by the Proceedings commands
		# (`flags.kt_prc_command`), never by a Desk save or script.
		if not self.flags.get("kt_prc_command"):
			frappe.throw("%s records change only through Proceedings commands." % self.doctype)

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("%s records are never deleted outside a fixture wipe." % self.doctype)
