# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §4.1 — the only Departmental Needs configuration record.

`Scheduled`, `Open` and `Closed` are derived from the configured clock and are
never stored (§4.1). There is at most one window per PE/FY.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.errors import fail


class NeedsIntakeWindow(Document):
	def validate(self):
		if not self.opens_at or not self.closes_at:
			fail("NDS_FIELD_REQUIRED", "Opens at and Closes at are both required.")
		if str(self.closes_at) <= str(self.opens_at):
			fail("NDS_FIELD_REQUIRED", "Closes at must be later than Opens at.")
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
			fail(
				"NDS_STATE_CONFLICT",
				f"A Needs Intake Window already exists for {self.procuring_entity} / {self.financial_year}.",
			)
