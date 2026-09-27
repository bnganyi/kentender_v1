# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-STD-001 v1.6 §3A.6 and BDS-CHG-001 v0.8 §5.9 item 7 (owner decision 27
Sep 2026): a technical reader reads a bid's metadata only — identities,
states, instants, custody and correlation references — with no business
action and no bid content; a supplier or business user gets Not found."""

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

	def test_metadata_only_for_a_technical_reader_and_nothing_for_anyone_else(self):
		receipt = self.submitted()
		summary = self.as_user("Administrator", api.get_bid_technical_summary, bid_reference=self.bid)
		self.assertEqual((summary["outcome"], summary["bid"]["status"], summary["next_step"]["kind"]), ("OK", "Submitted", "not_involved"))
		self.assertEqual([(v["version_number"], v["status"], v["receipt_reference"]) for v in summary["submission_versions"]], [(1, "Submitted", receipt)])
		text = json.dumps(summary)
		for content in ("Afya Digital Supplies Limited", "Mary Wanjiku", "ApexBook", ".pdf", "KES "):
			self.assertNotIn(content, text)
		for user in (DAVID, MARY, tender_fx.HOPF):
			self.assertEqual(self.as_user(user, api.get_bid_technical_summary, bid_reference=self.bid)["outcome"], "NOT_FOUND")
		status = self.as_user("Administrator", api.get_submission_service_status)
		self.assertEqual((status["outcome"], status["availability"]["available"]), ("OK", True))
		self.assertEqual(self.as_user(DAVID, api.get_submission_service_status)["outcome"], "NOT_FOUND")

	def test_the_search_resolvers_route_to_the_desk_record(self):
		resolvers = {r["doctype"]: r for r in technical_read.reference_resolvers()}
		self.assertEqual(resolvers["Bid Workspace"]["route"](self.bid), ["Form", "Bid Workspace", self.bid])
		for doctype, resolver in resolvers.items():
			with self.subTest(doctype=doctype):
				meta = frappe.get_meta(doctype)
				for key in ("reference_field", "title_field", "status_field"):
					self.assertTrue(meta.has_field(resolver[key]), (doctype, resolver[key]))
