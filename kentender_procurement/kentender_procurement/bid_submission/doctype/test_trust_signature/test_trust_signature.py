# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class TestTrustSignature(Document):
	def validate(self) -> None:
		# BDS-CHG-001 v0.8 owner decision OD-C — simulation state, written only by
		# the test services on a test environment (`flags.kt_bds_test_service`).
		if not self.flags.get("kt_bds_test_service"):
			frappe.throw("%s is written only by the Bid Submission test services." % self.doctype)

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("%s records are never deleted outside a fixture wipe." % self.doctype)
