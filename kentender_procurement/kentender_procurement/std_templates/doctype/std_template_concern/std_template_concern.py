# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-IMP-001 v1.0 §4.3 — a bounded concern against one installed
release. Created only by `CreateSTDTemplateConcern` and resolved only by the
release owner's `ResolveSTDTemplateConcern`; it never edits, blocks,
approves, supersedes or withdraws the release."""

from __future__ import annotations

import frappe
from frappe.model.document import Document

RESOLUTION_FIELDS = frozenset({"status", "resolved_by", "resolved_at", "resolution_note", "successor_release_id"})
_SYSTEM_FIELDS = frozenset({"modified", "modified_by", "creation", "owner", "idx", "docstatus", "_user_tags", "_comments", "_assign", "_liked_by"})


class STDTemplateConcern(Document):
	def before_insert(self) -> None:
		if not self.flags.get("kt_std_concern"):
			frappe.throw("A concern is recorded only through Report concern (STD-TPL-IMP-001 §6).")

	def after_insert(self) -> None:
		if not self.concern_id:
			self.db_set("concern_id", self.name, update_modified=False)

	def validate(self) -> None:
		if self.is_new():
			return
		if not self.flags.get("kt_std_concern_resolve"):
			frappe.throw("A concern is changed only by the release owner's resolution.")
		before = self.get_doc_before_save()
		for field in self.meta.get_valid_columns():
			if field in _SYSTEM_FIELDS or field in RESOLUTION_FIELDS or field == "concern_id":
				continue
			if before and (before.get(field) or None) != (self.get(field) or None):
				frappe.throw(f"Concern field {field} is immutable.")

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("Concerns are never deleted.")
