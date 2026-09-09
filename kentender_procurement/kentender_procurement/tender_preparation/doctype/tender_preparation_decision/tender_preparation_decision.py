# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §7.6 — an immutable decision record."""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class TenderPreparationDecision(Document):
	def validate(self) -> None:
		if not self.is_new():
			frappe.throw("A Tender decision is immutable once recorded (TPR-CHG-001 v0.6 §15).")

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("Tender decisions are never deleted outside a fixture wipe.")
