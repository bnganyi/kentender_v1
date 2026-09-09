# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §15 — the append-only command journal."""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class TenderPreparationCommandJournal(Document):
	def validate(self) -> None:
		if not self.is_new():
			frappe.throw("The command journal is append-only.")
