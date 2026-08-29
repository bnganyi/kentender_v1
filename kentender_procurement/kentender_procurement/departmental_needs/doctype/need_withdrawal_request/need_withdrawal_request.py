# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §4.6 — the minimal request to stop using an accepted Need.

There is at most one open withdrawal request for an accepted Need. The Need
remains `Accepted for planning` until approval succeeds (§4.6, §5.3).
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.constants import (
	OPEN_WITHDRAWAL_STATUSES,
	REASON_MAX,
	REASON_MIN,
)
from kentender_procurement.departmental_needs.errors import fail


class NeedWithdrawalRequest(Document):
	def validate(self):
		self._validate_reason()
		self._require_single_open_request()

	def _validate_reason(self):
		reason = (self.reason or "").strip()
		self.reason = reason
		if not (REASON_MIN <= len(reason) <= REASON_MAX):
			fail("NDS_FIELD_REQUIRED", f"Reason must be {REASON_MIN}-{REASON_MAX} characters.")

	def _require_single_open_request(self):
		if self.status not in OPEN_WITHDRAWAL_STATUSES:
			return
		duplicate = frappe.db.exists(
			"Need Withdrawal Request",
			{
				"departmental_need": self.departmental_need,
				"status": ("in", list(OPEN_WITHDRAWAL_STATUSES)),
				"name": ("!=", self.name),
			},
		)
		if duplicate:
			fail(
				"NDS_WITHDRAWAL_ALREADY_OPEN",
				f"An open withdrawal request already exists for {self.departmental_need}.",
			)

	def on_trash(self):
		fail("NDS_STATE_CONFLICT", "Need Withdrawal Requests are retained permanently.")
