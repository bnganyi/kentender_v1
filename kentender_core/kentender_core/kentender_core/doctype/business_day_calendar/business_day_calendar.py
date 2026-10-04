# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.11 §4.8 — one versioned, effective-dated business-day
calendar: weekend exclusions and exceptional holiday dates with source
evidence. Same pattern as `Procedure Schedule Profile`: a newer overlapping
Version supersedes, the earlier one retained, and it freezes once a schedule
counts days by it, once a source check is recorded against it, or once it
takes effect (`configuration_versions.version_editable`).
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_core.services.configuration_versions import guard_in_place_edit

_MUTABLE_AFTER_INSERT = frozenset({"status", "modified", "modified_by", "docstatus", "idx"})

WEEKDAYS: frozenset[str] = frozenset(
	{"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
)


class BusinessDayCalendar(Document):
	def validate(self):
		if not self.effective_from:
			frappe.throw("Enter the date this calendar version takes effect.", title="CFG_CALENDAR_INVALID")
		if self.effective_until and str(self.effective_until) < str(self.effective_from):
			frappe.throw("The calendar cannot end before it takes effect.", title="CFG_CALENDAR_INVALID")
		days = [d.strip() for d in (self.weekend_days or "").split(",") if d.strip()]
		if not days or any(d not in WEEKDAYS for d in days):
			frappe.throw("Select the weekend days from the seven weekday names.", title="CFG_CALENDAR_INVALID")
		self.weekend_days = ",".join(days)
		seen = set()
		for row in self.get("holidays") or []:
			if not row.holiday_date or not row.holiday_name:
				frappe.throw("Each holiday needs a date and a name.", title="CFG_CALENDAR_INVALID")
			if row.holiday_date in seen:
				frappe.throw(f"Holiday date {row.holiday_date} appears twice.", title="CFG_CALENDAR_INVALID")
			seen.add(row.holiday_date)
		guard_in_place_edit(self, mutable_fields=_MUTABLE_AFTER_INSERT, child_tables=("holidays",))

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw("Calendar versions are retained for audit and cannot be deleted.", title="CFG_CALENDAR_IMMUTABLE")
