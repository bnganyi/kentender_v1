# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §4.5 — an immutable record created only by a successful command.

Reasons exist only for Return for correction, Do not take forward, Request
withdrawal and Decline withdrawal (§4.5). There is no generic reason, comment or
evidence field on the Need. Decision rows are never rewritten or deleted (§13).
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.constants import (
	REASON_MAX,
	REASON_MIN,
	REASON_REQUIRED_ACTIONS,
)
from kentender_procurement.departmental_needs.errors import fail


class DepartmentalNeedDecision(Document):
	def validate(self):
		if not self.is_new():
			fail("NDS_STATE_CONFLICT", "A Departmental Need Decision is immutable once recorded.")
		self._validate_reason()

	def _validate_reason(self):
		reason = (self.reason or "").strip()
		self.reason = reason
		if self.action in REASON_REQUIRED_ACTIONS:
			if not (REASON_MIN <= len(reason) <= REASON_MAX):
				fail(
					"NDS_FIELD_REQUIRED",
					f"{self.action} requires a reason of {REASON_MIN}-{REASON_MAX} characters.",
				)
		elif reason:
			fail("NDS_FIELD_REQUIRED", f"{self.action} does not collect a reason.")

	def on_trash(self):
		frappe.throw(
			"Departmental Need Decisions are retained permanently.",
			title="NDS_DELETE_FORBIDDEN",
		)
