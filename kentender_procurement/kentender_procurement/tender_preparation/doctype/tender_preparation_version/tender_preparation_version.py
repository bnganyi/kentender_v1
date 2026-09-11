# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §7.2/§10.5 — one Tender Version. Plan D13: a Version
that has left Draft is written only by the lifecycle commands (status,
decision and audit columns, under ``flags.kt_lifecycle``); the inherited
snapshot is never written again after insert; nothing here is deleted
outside a fixture wipe.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

# Columns the lifecycle may still write on a non-Draft Version (status,
# decision evidence, readiness/render digests recorded at approval).
_LIFECYCLE_COLUMNS = frozenset(
	{
		"version_status", "record_version", "readiness_findings", "readiness_digest", "readiness_run_at",
		"blocking_count", "warning_count", "content_digest", "render_context_digest", "invitation_html_digest",
		"issued_tender_html_digest", "submitted_by", "submitted_at", "decided_by", "decided_at", "modified", "modified_by",
	}
)


class TenderPreparationVersion(Document):
	def validate(self) -> None:
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if before is None:
			return
		if before.snapshot_json and before.snapshot_json != self.snapshot_json:
			frappe.throw("The inherited requirement snapshot is immutable (TPR-CHG-001 v0.6 §7.3).")
		if before.version_status == "Draft" or self.flags.get("kt_lifecycle"):
			return
		changed = {
			f.fieldname
			for f in self.meta.fields
			if f.fieldtype not in ("Section Break", "Column Break", "Table")
			and (before.get(f.fieldname) or None) != (self.get(f.fieldname) or None)
		}
		if changed - _LIFECYCLE_COLUMNS:
			frappe.throw(
				"A submitted, returned, approved or reopened Tender Version is immutable; "
				f"changed: {', '.join(sorted(changed - _LIFECYCLE_COLUMNS))} (TPR-CHG-001 v0.6 §10.5)."
			)

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("Tender Versions are never deleted outside a fixture wipe (TPR-CHG-001 v0.6 §15).")
