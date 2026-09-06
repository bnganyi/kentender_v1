# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.9 §4.4A — one effective-dated version of the regulator
reference register (threshold matrix, preference and reservation categories and
targets, exclusive-preference thresholds, market price index, schedule-buffer
defaults) for one Fiscal Year.

CFG-BR-015: every version carries the Fiscal Year it applies to; superseded
versions are retained and never edited in place. Registering a newer version
for the same Fiscal Year marks the earlier one `Superseded`; nothing is ever
deleted. Configuration & Governance owns the records; consuming modules
interpret them (what blocks, what advises) and never write here.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

_MUTABLE_AFTER_INSERT = frozenset({"status", "modified", "modified_by", "docstatus", "idx"})


class RegulatoryReference(Document):
	def validate(self):
		if not self.effective_from:
			frappe.throw("Enter the date this reference version takes effect.", title="CFG_REFERENCE_INVALID")
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if before is None:
			return
		if getattr(self.flags, "kt_supersede", False):
			return
		for field in self.meta.get_valid_columns():
			if field in _MUTABLE_AFTER_INSERT or field.startswith("_"):
				continue
			if (self.get(field) or None) != (before.get(field) or None):
				frappe.throw(
					"A regulator reference version is never edited in place. Register a new version instead.",
					title="CFG_REFERENCE_IMMUTABLE",
				)
		for table in ("threshold_bands", "reservation_categories", "market_prices", "schedule_buffers"):
			if len(self.get(table) or []) != len(before.get(table) or []):
				frappe.throw(
					"A regulator reference version is never edited in place. Register a new version instead.",
					title="CFG_REFERENCE_IMMUTABLE",
				)

	def after_insert(self):
		# Registering a newer version supersedes the earlier Active one for
		# the same Fiscal Year (retained, never deleted).
		for name in frappe.get_all(
			"Regulatory Reference",
			filters={"fiscal_year": self.fiscal_year, "status": "Active", "name": ("!=", self.name)},
			pluck="name",
		):
			older = frappe.get_doc("Regulatory Reference", name)
			older.flags.kt_supersede = True
			older.status = "Superseded"
			older.save(ignore_permissions=True)

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw(
				"Regulator reference versions are retained for audit and cannot be deleted.",
				title="CFG_REFERENCE_IMMUTABLE",
			)
