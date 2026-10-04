# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.11 BDS-DES-10 (plan Phase 11, slice 11.10): the price
task read gives each published line with the bid's unit price and tax inputs
and the calculated line amount, then the subtotal, tax and bid total —
calculated, never entered; an unpriced line leaves the totals empty."""

from __future__ import annotations

from kentender_procurement.bid_submission.services import reads, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, BidCase, key
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase


def price(bid):
	return reads.get_bid_task(bid_reference=bid, task="price", user=DAVID)


class TestPricedBid(SubmissionCase):
	def test_the_schedule_calculates_the_bid_total(self):
		view = price(self.bid)
		self.assertEqual((view["page"]["title"], view["badge"]["label"]), ("Price", "Complete"))
		self.assertTrue(view["terms"].startswith("Currency KES"))
		line = view["lines"][0]
		self.assertEqual((line["unit_price"]["kind"], line["tax"]["kind"]), ("money", "money"))
		self.assertTrue(line["amount_before_tax"].startswith("KES "))
		self.assertTrue(view["totals"]["complete"])
		self.assertTrue(all(view["totals"][k].startswith("KES ") for k in ("subtotal", "tax", "total")))
		self.assertEqual(view["note"], "The Form of Tender uses this Bid total. You do not enter the total again.")
		self.assertEqual(view["footer"]["next_href"], f"/tenders/{self.reference}/bid")  # the preparer is done: back to the bid page, which says who signs


class TestUnpricedBid(BidCase):
	def test_an_unpriced_line_leaves_the_totals_empty(self):
		bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		view = price(bid)
		self.assertEqual((view["lines"][0]["amount_before_tax"], view["totals"]["total"], view["totals"]["complete"]), ("—", "—", False))
		self.assertIsNone(view["lines"][0]["unit_price"]["value"])
