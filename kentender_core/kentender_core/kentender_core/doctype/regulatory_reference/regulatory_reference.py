# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.11 §4.6 — one immutable, effective-dated version of a
`Regulatory Reference Set`. Same proven pattern as `Procedure Schedule
Profile` and `Business Day Calendar`: a newer overlapping version
supersedes the earlier one (triggered by the service, not this hook), never
edited in place, never deleted outside a fixture purge.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

_MUTABLE_AFTER_INSERT = frozenset({"status", "modified", "modified_by", "docstatus", "idx", "verification_status"})


class RegulatoryReference(Document):
	def validate(self):
		if not self.effective_from:
			frappe.throw("Enter the date this reference version takes effect.", title="CFG_REFERENCE_INVALID")
		if self.effective_until and str(self.effective_until) < str(self.effective_from):
			frappe.throw("The reference version cannot end before it takes effect.", title="CFG_REFERENCE_INVALID")
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if before is None or getattr(self.flags, "kt_supersede", False) or getattr(self.flags, "kt_verify", False):
			return
		for field in self.meta.get_valid_columns():
			if field in _MUTABLE_AFTER_INSERT or field.startswith("_"):
				continue
			if (self.get(field) or None) != (before.get(field) or None):
				frappe.throw(
					"A reference version is never edited in place. Create a new version instead.",
					title="CFG_REFERENCE_IMMUTABLE",
				)

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw(
				"Regulator reference versions are retained for audit and cannot be deleted.",
				title="CFG_REFERENCE_IMMUTABLE",
			)
