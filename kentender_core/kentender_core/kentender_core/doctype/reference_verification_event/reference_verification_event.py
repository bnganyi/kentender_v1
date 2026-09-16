# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.11 §4.6 — append-only source-check evidence against an
exact `Regulatory Reference` or `Business Day Calendar` version. Recording
an event never mutates the target's legal payload; it only appends here and
updates the target's `verification_status` projection field.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

_MUTABLE_AFTER_INSERT = frozenset({"modified", "modified_by", "docstatus", "idx"})


class ReferenceVerificationEvent(Document):
	def validate(self):
		if not self.reviewer:
			self.reviewer = frappe.session.user
		if self.outcome != "Verified" and not (self.unresolved_points or "").strip():
			frappe.throw(
				"Record the missing or contradictory point for this outcome.",
				title="CFG_VERIFICATION_EVIDENCE_REQUIRED",
			)
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if before is None:
			return
		for field in self.meta.get_valid_columns():
			if field in _MUTABLE_AFTER_INSERT or field.startswith("_"):
				continue
			if (self.get(field) or None) != (before.get(field) or None):
				frappe.throw(
					"A verification event is never edited in place.",
					title="CFG_REFERENCE_IMMUTABLE",
				)

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw("Verification events are retained for audit and cannot be deleted.", title="CFG_REFERENCE_IMMUTABLE")
