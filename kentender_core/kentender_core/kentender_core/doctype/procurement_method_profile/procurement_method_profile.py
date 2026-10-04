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
`configuration_versions` so every versioned setting, its service and a raw
Desk edit all answer it the same way.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_core.services.configuration_versions import guard_in_place_edit

_MUTABLE_AFTER_INSERT = frozenset({"status", "modified", "modified_by", "docstatus", "idx"})


class ProcurementMethodProfile(Document):
	def validate(self):
		if not self.effective_from:
			frappe.throw("Enter the date this profile version takes effect.", title="CFG_PROFILE_INVALID")
		if self.effective_until and str(self.effective_until) < str(self.effective_from):
			frappe.throw("The profile cannot end before it takes effect.", title="CFG_PROFILE_INVALID")
		guard_in_place_edit(self, mutable_fields=_MUTABLE_AFTER_INSERT, child_tables=("conditions",))

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw("Method profile versions are retained for audit and cannot be deleted.", title="CFG_PROFILE_IMMUTABLE")
