# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.1B / §10.11 C04 — the one operational Planning
setting Configuration & Governance maintains: the approaching-milestone
reminder threshold (initial default 7 calendar days, expressly not a
statutory period).

CFG-CHG-002 v0.11 §10.10 supersedes the original 1–60 bound with 0–365: 0 is
a legitimate setting ("Use 0 to begin reminders on the milestone date;
overdue reminders still apply"), which the old lower bound refused outright.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class ProcurementSettings(Document):
	def validate(self):
		days = int(self.approaching_milestone_threshold_days or 0)
		if not (0 <= days <= 365):
			frappe.throw("Enter a whole number from 0 to 365.", title="CFG_PROFILE_INVALID")
