# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.1 / §17.2 (CFG owner work) — one versioned,
effective-dated procedure schedule profile: the applicable milestones in
order, their counting rule, statutory minimum/maximum periods (or the fact
that verification is still required) and separately labelled internal
planning assumptions. A newer overlapping Version supersedes, the earlier one
is retained.

It freezes as soon as it could matter to anyone — a plan pins it, or it takes
effect. Until then it is unfinished configuration and may be corrected in
place; the rule is `configuration_versions.version_editable`.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_core.services.configuration_versions import guard_in_place_edit

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
		guard_in_place_edit(self, mutable_fields=_MUTABLE_AFTER_INSERT, child_tables=("milestones",))

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw("Schedule profile versions are retained for audit and cannot be deleted.", title="CFG_PROFILE_IMMUTABLE")
