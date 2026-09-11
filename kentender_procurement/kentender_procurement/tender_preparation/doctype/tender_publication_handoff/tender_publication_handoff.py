# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §7.6 — the immutable ``TenderPublicationHandoff v1.1``.
Only the consumption columns may change after insert (§9.5 / §11.2)."""

from __future__ import annotations

import frappe
from frappe.model.document import Document

_CONSUMPTION_COLUMNS = frozenset({"status", "consumed_at", "consumption_correlation_id", "published_on", "modified", "modified_by"})


class TenderPublicationHandoff(Document):
	def validate(self) -> None:
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if before is None:
			return
		changed = {
			f.fieldname for f in self.meta.fields
			if f.fieldtype not in ("Section Break", "Column Break") and (before.get(f.fieldname) or None) != (self.get(f.fieldname) or None)
		}
		if changed - _CONSUMPTION_COLUMNS:
			frappe.throw(f"A publication handoff is immutable except for its consumption status; changed: {', '.join(sorted(changed - _CONSUMPTION_COLUMNS))}.")

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("Publication handoffs are never deleted outside a fixture wipe.")
