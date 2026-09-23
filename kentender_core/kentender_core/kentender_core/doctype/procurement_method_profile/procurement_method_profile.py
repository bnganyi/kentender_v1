# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.3.3 / §17.2 (CFG owner work) — one versioned,
effective-dated method eligibility profile: applicable categories, value and
cumulative limits, required circumstances, evidence and any specific
authorisation. A newer Version whose window overlaps supersedes the earlier
one, which is retained so a Plan that referenced it stays reproducible.
Configuration & Governance owns the rows; Planning decides what blocks.

A Version freezes as soon as it could matter to anyone — the moment a plan
pins it, or the moment it takes effect, whichever comes first. Until then it
is unfinished configuration and may be corrected in place (owner decision, 23
Sep 2026); afterwards a correction is a new Version. The rule itself lives in
`procurement_settings.method_profile_editable` so the service and a raw Desk
edit cannot answer it differently.
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
		# The service has already checked, and is mid-correction: re-running the
		# test here would read the values being written, not the stored ones.
		if getattr(self.flags, "kt_correct_unused", False):
			return
		from kentender_core.services.procurement_settings import method_profile_editable

		# Judged on the stored row, never on what is being written: moving the
		# effective date into the future must not unfreeze a rule already in force.
		editable, reason = method_profile_editable(before)
		if editable:
			return
		for field in self.meta.get_valid_columns():
			if field in _MUTABLE_AFTER_INSERT or field.startswith("_"):
				continue
			if (self.get(field) or None) != (before.get(field) or None):
				frappe.throw(reason, title="CFG_PROFILE_IMMUTABLE")
		if len(self.get("conditions") or []) != len(before.get("conditions") or []):
			frappe.throw(reason, title="CFG_PROFILE_IMMUTABLE")

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw("Method profile versions are retained for audit and cannot be deleted.", title="CFG_PROFILE_IMMUTABLE")
