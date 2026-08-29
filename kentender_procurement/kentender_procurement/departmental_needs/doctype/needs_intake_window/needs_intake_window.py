# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §4.1 — the only Departmental Needs configuration record.

`Scheduled`, `Open` and `Closed` are derived from the configured clock and are
never stored (§4.1). There is at most one window per PE/FY.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class NeedsIntakeWindow(Document):
	def validate(self):
		if not self.opens_at or not self.closes_at:
			frappe.throw("Opens at and Closes at are both required.", title="NDS_FIELD_REQUIRED")
		if str(self.closes_at) <= str(self.opens_at):
			frappe.throw(
				"Closes at must be later than Opens at.",
				title="NDS_FIELD_REQUIRED",
			)
		self._require_single_window_per_pe_fy()

	def _require_single_window_per_pe_fy(self):
		duplicate = frappe.db.exists(
			"Needs Intake Window",
			{
				"procuring_entity": self.procuring_entity,
				"financial_year": self.financial_year,
				"name": ("!=", self.name),
			},
		)
		if duplicate:
			frappe.throw(
				f"A Needs Intake Window already exists for {self.procuring_entity} / {self.financial_year}.",
				title="NDS_STATE_CONFLICT",
			)
