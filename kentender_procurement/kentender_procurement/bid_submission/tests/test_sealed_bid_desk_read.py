# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-ACCESS-REV-001 AR-01 — a technical reader never reads a bid's identity or
payload before governed opening through a raw Desk / REST read.

BDS-CHG-001 v0.11 §6: Administrator / System Manager see "configuration/health
metadata only for sealed bids; no business authority and no content access
before governed opening". The service layer already answers that; the DocPerm
rows must not hand the same records out by another door. (Administrator bypasses
Frappe's permission hooks — the recorded production-gate residual.)
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.tests import v16_fixtures as fx

SEALED = (
	"Bidder Arrangement",
	"Bid Organisation Snapshot",
	"Bid Workspace",
	"Bid Submission Attempt",
	"Bid Submission Version",
	"Bid Submission Event",
	"Tender Box Envelope",
	"Bid Opening Handoff",
)


class TestSealedBidDeskRead(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.manager = fx.user("sealed.sysmgr", "Sealed Test System Manager", roles=("System Manager",))

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_each_record_carries_both_denial_hooks(self):
		"""The list query is closed (`1=0`) and a single record is refused."""
		access = frappe.get_hooks("has_permission")
		query = frappe.get_hooks("permission_query_conditions")
		for doctype in SEALED:
			with self.subTest(doctype=doctype):
				self.assertIn("deny_desk_access", " ".join(access.get(doctype) or []))
				self.assertIn("deny_desk_query", " ".join(query.get(doctype) or []))

	def test_a_system_manager_cannot_read_a_single_record_of_them(self):
		# Frappe consults a has_permission hook for a concrete document, so the
		# check is made against one (an unsaved shell is enough for the hook).
		for doctype in SEALED:
			with self.subTest(doctype=doctype):
				doc = frappe.new_doc(doctype)
				doc.name = "sealed-probe"
				self.assertFalse(frappe.has_permission(doctype, "read", doc=doc, user=self.manager), doctype)
