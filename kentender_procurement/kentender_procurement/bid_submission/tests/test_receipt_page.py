# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.14 BDS-DES-13 and §10.15 BDS-DES-14-REPLACED (plan
Phase 11, slice 11.13): the receipt page states the accepted Version to the
second with nothing technical; Prepare replacement and Withdraw bid are the
Authorised Signatory's on the current receipt before the deadline only;
after the deadline submission changes are closed; a replacement receipt
names the Version it superseded. Another organisation, or another Tender's
address, is Not found."""

from __future__ import annotations

import re

import frappe

from kentender_procurement.bid_submission import portal
from kentender_procurement.bid_submission.services import receipt_view
from kentender_procurement.bid_submission.tests.support import DAVID, MARY, PETER
from kentender_procurement.bid_submission.tests.test_changes_and_close import ChangeCase


def labels(rows):
	return [r["label"] for r in rows]


class ReceiptCase(ChangeCase):
	def page(self, receipt, user=MARY):
		return receipt_view.get_receipt_page(tender_reference=self.reference, receipt_reference=receipt, user=user)


class TestReceiptPage(ReceiptCase):
	def test_the_signatory_reads_the_receipt_with_both_changes_offered(self):
		receipt = self.submitted()
		view = self.page(receipt)
		self.assertEqual((view["page"]["title"], view["page"]["description"], view["page"]["badge"]), ("Bid submitted", "Your bid was accepted into the electronic tender box.", {"label": "Submitted", "tone": "live"}))
		self.assertEqual([a["key"] for a in view["actions"]], ["prepare_replacement", "withdraw_bid", "print"])
		self.assertEqual(view["actions"][0]["href"], f"/tenders/{self.reference}/bid/replace")
		self.assertEqual(labels(view["receipt"]), ["Receipt reference", "Tender", "Bidder", "Bid", "Submitted bid Version", "Submitted by", "Received by tender-box service", "Accepted into tender box", "Status"])
		facts = {r["label"]: r["value"] for r in view["receipt"]}
		self.assertEqual((facts["Receipt reference"], facts["Submitted bid Version"], facts["Submitted by"]), (receipt, "1", "Mary Wanjiku"))
		self.assertRegex(facts["Accepted into tender box"], r"^\d{1,2} \w{3} \d{4}, \d{2}:\d{2}:\d{2} EAT$")
		self.assertEqual(labels(view["summary"]), ["Bid total", "Offered item", "Quantity", "Delivery date", "Current deadline"])
		self.assertEqual(view["notice"], "This receipt confirms submission only. It is not an opening, evaluation or award result.")
		self.assertEqual(view["sentence"], "The current submitted bid remains valid until a replacement is accepted or a withdrawal is acknowledged.")
		self.assertEqual(view["withdrawal"]["receipt_reference"], receipt)
		self.assertFalse({"prepare_replacement", "withdraw_bid"} & {f.get("fix_id") for f in view["next_step"]["fixes"]})
		self.assertEqual(view["footer"]["back_href"], "/my-bids")
		self.assertIn(f"receipt_reference={receipt}", view["footer"]["download_href"])
		# nothing technical reaches the page
		text = frappe.as_json(view)
		self.assertIsNone(re.search(r"[0-9a-f]{64}|TCERT-|TSR-|COR-BDS-|private/", text))

	def test_the_submitter_is_named_from_the_user_record_not_a_process_cache(self):
		# a fixture or worker process may have cached a login as its own "name"
		# before the person existed (Frappe's get_fullname cache)
		frappe.local.fullnames = {MARY: MARY}
		self.addCleanup(lambda: setattr(frappe.local, "fullnames", {}))
		receipt = self.submitted()
		facts = {r["label"]: r["value"] for r in self.page(receipt)["receipt"]}
		self.assertEqual(facts["Submitted by"], "Mary Wanjiku")

	def test_the_representative_may_only_read_print_and_download(self):
		receipt = self.submitted()
		view = self.page(receipt, user=DAVID)
		self.assertEqual([a["key"] for a in view["actions"]], ["print"])
		self.assertIsNone(view["withdrawal"])
		self.assertEqual(view["sentence"], "")
		self.assertEqual((view["next_step"]["kind"], view["next_step"]["headline"][:30]), ("done", "Bid Version 1 was accepted on "))

	def test_after_the_deadline_submission_changes_are_closed(self):
		receipt = self.submitted()
		self.at(frappe.utils.add_to_date(self.deadline(), seconds=1))
		view = self.page(receipt)
		self.assertEqual([a["key"] for a in view["actions"]], ["print"])
		self.assertTrue(view["sentence"].startswith("Submission changes closed on "), view["sentence"])
		self.assertTrue(view["next_step"]["headline"].startswith("Bid Version 1 remains submitted; submission changes closed at "), view["next_step"])

	def test_the_route_masks_another_organisation_and_another_tender(self):
		receipt = self.submitted()
		ok = portal.resolve(path=f"/tenders/{self.reference}/bid/receipt/{receipt}", query={}, user=MARY)
		self.assertEqual((ok["verdict"], ok["payload"]["screen"]), ("OK", "receipt"))
		for path, user in ((f"/tenders/{self.reference}/bid/receipt/{receipt}", PETER), (f"/tenders/TND-OTHER-0000-001/bid/receipt/{receipt}", MARY), (f"/tenders/{self.reference}/bid/receipt/RCPT-NONE", MARY)):
			with self.subTest(path=path, user=user):
				self.assertEqual(portal.resolve(path=path, query={}, user=user)["verdict"], "NOT_FOUND")


class TestReplacementReceipt(ReceiptCase):
	def test_a_replacement_receipt_names_the_version_it_superseded(self):
		first = self.submitted()
		self.at("2027-05-31 08:30:00")
		self.assertTrue(self.replace()["ok"])
		self.at("2027-05-31 09:15:00")
		second = self.submitted(replaces=first)
		view = self.page(second)
		self.assertEqual((view["page"]["title"], view["page"]["description"]), ("Replacement bid submitted", "Your replacement bid was accepted into the electronic tender box."))
		self.assertEqual(view["lineage"]["status"], {"label": "Version 1 superseded", "tone": "pending"})
		self.assertEqual(view["lineage"]["link"], {"label": f"View Version 1 receipt · {first}", "href": f"/tenders/{self.reference}/bid/receipt/{first}"})
		earlier = self.page(first)
		self.assertEqual((earlier["page"]["badge"], [a["key"] for a in earlier["actions"]]), ({"label": "Superseded", "tone": "draft"}, ["print"]))
		self.assertEqual(earlier["sentence"], "")


class TestReplacementPage(ReceiptCase):
	def test_the_signatory_may_create_a_replacement_and_the_receipt_stays_current(self):
		from kentender_procurement.bid_submission.services import changes_view

		receipt = self.submitted()
		base = f"/tenders/{self.reference}/bid"
		view = changes_view.get_replacement_page(tender_reference=self.reference, user=MARY)
		self.assertEqual((view["page"]["title"], view["page"]["badge"]), ("Prepare replacement bid", {"label": "Version 1 submitted", "tone": "live"}))
		self.assertEqual(view["notice"]["text"], f"Receipt {receipt} remains current until the replacement is accepted.")
		self.assertEqual(labels(view["facts"]), ["Current submitted bid Version", "Submitted", "Deadline", "Current definition includes"])
		self.assertEqual(view["decision"], {"cancel_href": f"{base}/receipt/{receipt}", "create_label": "Create replacement Draft", "next_href": base})
		self.assertIsNone(changes_view.get_replacement_page(tender_reference=self.reference, user=DAVID)["decision"])
		# the bid page's guidance leads to this page and to the receipt's withdrawal dialog
		from kentender_procurement.bid_submission.services import reads

		targets = {f["fix_id"]: f["target"] for f in reads.get_bid_workspace(bid_reference=self.bid, user=MARY)["next_step"]["fixes"]}
		self.assertEqual(targets, {"prepare_replacement": f"{base}/replace", "withdraw_bid": f"{base}/receipt/{receipt}?action=withdraw"})
		# once the replacement Draft is open the page leads to it
		self.at("2027-05-31 08:30:00")
		self.assertTrue(self.replace()["ok"])
		self.assertEqual(reads.get_submit_page(tender_reference=self.reference, user=MARY)["replaces"], receipt)  # the Submit page names the current receipt
		opened = changes_view.get_replacement_page(tender_reference=self.reference, user=MARY)
		self.assertEqual((opened["decision"], opened["continue"]["href"]), (None, base))
		self.assertTrue(opened["text"].startswith("Your replacement Draft is open."))
		self.assertEqual(portal.resolve(path=f"{base}/replace", query={}, user=MARY)["payload"]["screen"], "replace")
		self.assertEqual(portal.resolve(path=f"{base}/replace", query={}, user=PETER)["verdict"], "NOT_FOUND")


class TestAcknowledgementPage(ReceiptCase):
	def test_the_acknowledgement_reads_the_withdrawal_and_offers_start_replacement(self):
		from kentender_procurement.bid_submission.services import changes_view, reads

		self.submitted()
		done = self.withdraw()
		self.assertTrue(done["ok"], done)
		reference = done["acknowledgement_reference"]
		view = changes_view.get_acknowledgement_page(tender_reference=self.reference, acknowledgement_reference=reference, user=MARY)
		self.assertEqual((view["kind"], view["page"]["title"], view["page"]["badge"]), ("acknowledgement", "Bid withdrawn", {"label": "Withdrawn", "tone": "critical"}))
		self.assertEqual(labels(view["acknowledgement"]), ["Acknowledgement reference", "Tender", "Bidder", "Bid", "Withdrawn by", "Withdrawn at", "Status"])
		self.assertEqual(view["footer"]["start"], {"label": "Start replacement", "next_href": f"/tenders/{self.reference}/bid"})
		self.assertIn(f"acknowledgement_reference={reference}", view["footer"]["download_href"])
		self.assertEqual(view["next_step"]["fixes"], [])
		self.assertIsNone(changes_view.get_acknowledgement_page(tender_reference=self.reference, acknowledgement_reference=reference, user=DAVID)["footer"]["start"])
		# the bid page's Start replacement leads here
		fix = reads.get_bid_workspace(bid_reference=self.bid, user=MARY)["next_step"]["fixes"][0]
		self.assertEqual((fix["fix_id"], fix["target"]), ("start_replacement", f"/tenders/{self.reference}/bid/receipt/{reference}"))
		routed = portal.resolve(path=f"/tenders/{self.reference}/bid/receipt/{reference}", query={}, user=MARY)
		self.assertEqual((routed["verdict"], routed["payload"]["data"]["kind"]), ("OK", "acknowledgement"))
		for path, user in ((f"/tenders/{self.reference}/bid/receipt/{reference}", PETER), (f"/tenders/TND-OTHER-0000-001/bid/receipt/{reference}", MARY)):
			with self.subTest(path=path, user=user):
				self.assertEqual(portal.resolve(path=path, query={}, user=user)["verdict"], "NOT_FOUND")
