# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class BOPTestEnvironmentControls(Document):
	def validate(self) -> None:
		# BOP-CHG-001 v0.10 owner decision OD-C — simulation state, written only by
		# the Bid Opening test services on a test environment (`flags.kt_bop_test_service`).
		if not self.flags.get("kt_bop_test_service"):
			frappe.throw("%s is written only by the Bid Opening test services." % self.doctype)
