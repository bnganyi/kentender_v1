# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.3.3 / §17.2 (CFG owner work) — one versioned,
effective-dated method eligibility profile: applicable categories, value and
cumulative limits, required circumstances, evidence and any specific
authorisation. Immutable once inserted (a change is a new Version); a newer
Version whose window overlaps supersedes the earlier one, which is retained
so a Plan that referenced it stays reproducible. Configuration & Governance
owns the rows; Planning decides what blocks.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

_MUTABLE_AFTER_INSERT = frozenset({"status", "modified", "modified_by", "docstatus", "idx"})


class ProcurementMethodProfile(Document):
	def validate(self):
		if not self.effective_from:
			frappe.throw("Enter the date this profile version takes effect.", title="CFG_PROFILE_INVALID")
		if self.effective_until and str(self.effective_until) < str(self.effective_from):
			frappe.throw("The profile cannot end before it takes effect.", title="CFG_PROFILE_INVALID")
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
					"A method profile version is never edited in place. Register a new version instead.",
					title="CFG_PROFILE_IMMUTABLE",
				)
		if len(self.get("conditions") or []) != len(before.get("conditions") or []):
			frappe.throw(
				"A method profile version is never edited in place. Register a new version instead.",
				title="CFG_PROFILE_IMMUTABLE",
			)

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw("Method profile versions are retained for audit and cannot be deleted.", title="CFG_PROFILE_IMMUTABLE")
