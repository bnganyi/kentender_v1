# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.11 §4.6 — the stable header a `Regulatory Reference`
version family hangs off: a generated ID, a user-defined `reference_key`
distinct from that ID, and an immutable `reference_kind`. Exists with zero
versions to support §7.3's "Rule created; version not saved" recovery state.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class RegulatoryReferenceSet(Document):
	def validate(self):
		key = " ".join((self.reference_key or "").split())
		if not key:
			frappe.throw("Enter a reference key.", title="CFG_REFERENCE_INVALID")
		self.reference_key = key
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if before is None:
			return
		has_versions = frappe.db.exists("Regulatory Reference", {"reference_set": self.name})
		if has_versions and (self.reference_key != before.reference_key or self.reference_kind != before.reference_kind):
			frappe.throw(
				"The reference key and kind cannot change once a version exists.",
				title="CFG_REFERENCE_IMMUTABLE",
			)

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw("Reference sets are retained for audit and cannot be deleted.", title="CFG_REFERENCE_IMMUTABLE")
