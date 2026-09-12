# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.1B / §10.11 C04 — the one operational Planning
setting Configuration & Governance maintains: the approaching-milestone
reminder threshold (initial default 7 calendar days, expressly not a
statutory period)."""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class ProcurementSettings(Document):
	def validate(self):
		days = int(self.approaching_milestone_threshold_days or 0)
		if not (1 <= days <= 60):
			frappe.throw("Enter a reminder threshold between 1 and 60 calendar days.", title="CFG_PROFILE_INVALID")
