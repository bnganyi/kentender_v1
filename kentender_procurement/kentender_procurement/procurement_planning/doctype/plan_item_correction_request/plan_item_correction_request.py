# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §7.4A / PLN-CHG-001 v1.18 §5.4.5 — the inbound half of a
Requisition's upstream correction route. Immutable once received, except the
status/resolution columns the Procurement Planner's own
`start_plan_item_correction`, `resolve_plan_item_correction_request` and
`close_plan_item_correction_without_change` commands set as the request
moves Open -> In progress -> Resolved / Closed without change.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class PlanItemCorrectionRequest(Document):
	def validate(self) -> None:
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if not before:
			return
		mutable_fields = {"status", "resolved_by", "resolved_at", "resolution_note", "record_version"}
		# Only this doctype's own declared fields — never Frappe's standard
		# bookkeeping columns (`modified`, `modified_by`, `idx`, `docstatus`, …),
		# which legitimately change on every save.
		for field in [f.fieldname for f in self.meta.fields]:
			if field in mutable_fields:
				continue
			if self.get(field) != before.get(field):
				frappe.throw(f"Plan Item Correction Request is immutable except its resolution ({field} changed).")
