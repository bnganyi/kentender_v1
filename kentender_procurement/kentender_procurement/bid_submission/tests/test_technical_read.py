# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-STD-001 v1.6 §3A.6, BDS-CHG-001 §5.9 item 7 and the Project Owner's decision
of 10 October 2026: a technical reader (Administrator or System Manager) sees
the submission service's status and nothing about any bid — not its existence, a
count, an identity or a receipt, before or after the opening. A supplier or
business user gets Not found."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.bid_submission import api
from kentender_procurement.bid_submission.services import technical_read
from kentender_procurement.bid_submission.tests.support import DAVID, MARY
from kentender_procurement.bid_submission.tests.test_changes_and_close import ChangeCase
from kentender_procurement.tenders.tests import fixtures as tender_fx


class TestBidTechnicalRead(ChangeCase):
	def as_user(self, user, fn, **kwargs):
		frappe.set_user(user)
		try:
			return fn(**kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_a_technical_reader_reads_the_service_status_and_no_bid(self):
		receipt = self.submitted()
		self.assertFalse(hasattr(api, "get_bid_technical_summary"))  # the per-bid technical read is gone
		self.assertFalse(hasattr(technical_read, "get_bid_technical_summary"))
		status = self.as_user("Administrator", api.get_submission_service_status)
		self.assertEqual((status["outcome"], status["availability"]["available"]), ("OK", True))
		text = json.dumps(status)
		for content in (self.bid, receipt, "Afya Digital Supplies Limited", "affected_bids"):
			self.assertNotIn(content, text)
		self.assertEqual(self.as_user(DAVID, api.get_submission_service_status)["outcome"], "NOT_FOUND")
		# the read by a technical account is audited; the refused read by a supplier writes nothing
		audited = frappe.db.count("Audit Event", {"event_type": "submission_service_status_read", "performed_by": "Administrator"})
		self.as_user("Administrator", api.get_submission_service_status)
		self.assertEqual(frappe.db.count("Audit Event", {"event_type": "submission_service_status_read", "performed_by": "Administrator"}), audited + 1)
		self.assertEqual(frappe.db.count("Audit Event", {"event_type": "submission_service_status_read", "performed_by": DAVID}), 0)

	def test_no_bid_record_is_findable_through_the_technical_record_search(self):
		self.assertEqual(technical_read.reference_resolvers(), [])
		from kentender_core.services import technical_search

		for reference in (self.bid, self.reference):
			text = json.dumps(technical_search.search(query=reference, user="Administrator"))
			for doctype in ("Bid Workspace", "Bidder Arrangement", "Bid Receipt", "Bid Submission Attempt", "Tender Security Intake", "Bid Opening Handoff"):
				self.assertNotIn(doctype, text)
