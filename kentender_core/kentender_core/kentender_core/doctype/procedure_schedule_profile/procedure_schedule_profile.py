# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.1 / §17.2 (CFG owner work) — one versioned,
effective-dated procedure schedule profile: the applicable milestones in
order, their counting rule, statutory minimum/maximum periods (or the fact
that verification is still required) and separately labelled internal
planning assumptions. Immutable once inserted; a newer overlapping Version
supersedes, the earlier one is retained.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

_MUTABLE_AFTER_INSERT = frozenset({"status", "modified", "modified_by", "docstatus", "idx"})


class ProcedureScheduleProfile(Document):
	def validate(self):
		if not self.effective_from:
			frappe.throw("Enter the date this profile version takes effect.", title="CFG_PROFILE_INVALID")
		if self.effective_until and str(self.effective_until) < str(self.effective_from):
			frappe.throw("The profile cannot end before it takes effect.", title="CFG_PROFILE_INVALID")
		seen = set()
		for row in self.get("milestones") or []:
			if row.milestone in seen:
				frappe.throw(f"Milestone {row.milestone} appears twice.", title="CFG_PROFILE_INVALID")
			seen.add(row.milestone)
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if before is None or getattr(self.flags, "kt_supersede", False):
			return
		for field in self.meta.get_valid_columns():
			if field in _MUTABLE_AFTER_INSERT or field.startswith("_"):
				continue
			if (self.get(field) or None) != (before.get(field) or None):
				frappe.throw(
					"A schedule profile version is never edited in place. Register a new version instead.",
					title="CFG_PROFILE_IMMUTABLE",
				)
		if len(self.get("milestones") or []) != len(before.get("milestones") or []):
			frappe.throw(
				"A schedule profile version is never edited in place. Register a new version instead.",
				title="CFG_PROFILE_IMMUTABLE",
			)

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw("Schedule profile versions are retained for audit and cannot be deleted.", title="CFG_PROFILE_IMMUTABLE")
