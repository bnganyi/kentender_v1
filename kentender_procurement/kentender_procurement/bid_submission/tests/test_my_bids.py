# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.6 BDS-DES-05 and §10.20 BDS-DES-17 (plan Phase 11,
slice 11.5): My bids gives the active organisation's bids with the status,
version, deadline, last update and the actions this person may take — Review
bid, View receipt, View acknowledgement and, for the signatory before the
deadline, Start replacement; Receipts is a read-only register of submission
receipts and withdrawal acknowledgements, readable by a suspended Account and
masked for anyone else. Reads create nothing."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import reads
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, KISIWA, MARY, PETER
from kentender_procurement.bid_submission.tests.test_changes_and_close import ChangeCase


class TestMyBids(ChangeCase):
	def row(self, user=DAVID, **filters):
		rows = reads.get_my_bids(user=user, **filters)["rows"]
		return rows[0] if rows else None

	def test_each_state_carries_its_version_update_and_actions(self):
		ready = self.row()
		self.assertEqual((ready["status_label"], ready["status_tone"], ready["version_label"]), ("Ready to submit", "live", f"Draft Version {frappe.db.get_value('Bid Workspace', self.bid, 'current_draft_version')}"))
		self.assertEqual(ready["actions"], [{"label": "Review bid", "href": f"/tenders/{self.reference}/bid/review"}])
		self.assertRegex(ready["updated_label"], r"^\d{1,2} \w{3} 2027, \d{2}:\d{2} EAT$")
		self.assertRegex(ready["deadline_label"], r"^\d{1,2} \w{3} 2027, \d{2}:\d{2} EAT$")
		self.assertEqual(reads.get_my_bids(user=DAVID)["count_text"], "1 bid")

		receipt = self.submitted()
		submitted = self.row()
		self.assertEqual((submitted["status_label"], submitted["version_label"], submitted["updated_label"]), ("Submitted", "Submitted bid Version 1", "30 May 2027, 14:30 EAT"))
		self.assertEqual(submitted["actions"], [{"label": "View receipt", "href": f"/tenders/{self.reference}/bid/receipt/{receipt}"}])

		self.at("2027-05-30 15:00:00")
		ack = self.withdraw(receipt=receipt)["acknowledgement_reference"]
		withdrawn = self.row(user=MARY)
		self.assertEqual((withdrawn["status_label"], withdrawn["status_tone"], withdrawn["version_label"], withdrawn["updated_label"]), ("Withdrawn", "critical", "", "30 May 2027, 15:00 EAT"))
		view, start = withdrawn["actions"]
		self.assertEqual(view, {"label": "View acknowledgement", "href": f"/tenders/{self.reference}/bid/receipt/{ack}"})
		self.assertEqual((start["label"], start["command"], start["href"], start["record_version"]), ("Start replacement", "prepare_replacement", f"/tenders/{self.reference}/bid", self.version()))
		# the representative cannot start a replacement; after the deadline nobody can
		self.assertEqual([a["label"] for a in self.row(user=DAVID)["actions"]], ["View acknowledgement"])
		self.at(str(self.deadline()))
		self.assertEqual([a["label"] for a in self.row(user=MARY)["actions"]], ["View acknowledgement"])

	def test_filters_search_the_tender_and_the_bid_and_name_the_statuses(self):
		read = reads.get_my_bids(user=DAVID)
		self.assertEqual([o["label"] for o in read["options"]["status"]][:2], ["All statuses", "Draft"])
		title = read["rows"][0]["tender_title"]
		for search in (self.bid.lower(), self.reference, title.split()[-1].upper()):
			self.assertEqual(len(reads.get_my_bids(user=DAVID, search=search)["rows"]), 1, search)
		self.assertEqual(reads.get_my_bids(user=DAVID, search="no such bid")["rows"], [])
		self.assertEqual(reads.get_my_bids(user=DAVID, status="Submitted")["rows"], [])
		self.assertEqual(len(reads.get_my_bids(user=DAVID, status="Ready to submit")["rows"]), 1)

	def test_another_organisation_and_an_empty_list(self):
		empty = reads.get_my_bids(user=PETER, organisation=KISIWA)
		self.assertEqual((empty["rows"], empty["empty_text"]), ([], "No bids yet. Find a Tender to start your first bid."))


class TestReceiptHistory(ChangeCase):
	def test_receipts_and_acknowledgements_in_order_with_their_own_links(self):
		empty = reads.get_receipt_history(user=DAVID)
		self.assertEqual((empty["rows"], empty["empty_text"], empty["suspended"]), ([], "No submission or withdrawal receipts for this organisation.", False))
		receipt = self.submitted()
		self.at("2027-05-30 15:00:00")
		ack = self.withdraw(receipt=receipt)["acknowledgement_reference"]
		read = reads.get_receipt_history(user=DAVID)
		self.assertEqual(
			[(r["document"], r["event"], r["event_tone"], r["at_label"], r["href"]) for r in read["rows"]],
			[
				(receipt, "Submitted", "live", "30 May 2027, 14:30:00", f"/tenders/{self.reference}/bid/receipt/{receipt}"),
				(ack, "Withdrawn", "critical", "30 May 2027, 15:00:00", f"/tenders/{self.reference}/bid/receipt/{ack}"),
			],
		)
		self.assertEqual(read["count_text"], "2 records")
		self.assertEqual({r["tender_reference"] for r in read["rows"]}, {self.reference})
		text = frappe.as_json(read)
		for leak in ("package_digest", "KES", "price", "signature"):
			self.assertNotIn(leak, text)

	def test_a_suspended_account_still_reads_its_receipts(self):
		self.submitted()
		self.accounts.orgs[AFYA]["account_status"] = "Suspended"
		read = reads.get_receipt_history(user=DAVID)
		self.assertEqual((read["suspended"], len(read["rows"])), (True, 1))
		self.assertEqual(read["suspended_text"], "This supplier account is suspended. You can read and download existing receipts; no bid can be prepared, submitted, replaced or withdrawn.")

	def test_another_organisation_is_not_found_and_reads_create_nothing(self):
		self.submitted()
		with self.assertRaises(frappe.DoesNotExistError):
			reads.get_receipt_history(user=PETER, organisation=AFYA)
		self.assertEqual(reads.get_receipt_history(user=PETER, organisation=KISIWA)["rows"], [])
		events = frappe.db.count("Bid Submission Event")
		reads.get_receipt_history(user=MARY)
		reads.get_my_bids(user=MARY)
		self.assertEqual(frappe.db.count("Bid Submission Event"), events)


class TestPortalAddresses(ChangeCase):
	def test_my_bids_and_receipts_need_a_signed_in_person_and_carry_their_reads(self):
		from kentender_procurement.bid_submission import portal

		for path in ("/my-bids", "/account/receipts"):
			self.assertEqual(portal.resolve(path=path, query={}, user="Guest")["verdict"], "SIGN_IN", path)
		bids = portal.resolve(path="/my-bids", query={"status": "Ready to submit"}, user=DAVID)
		self.assertEqual((bids["verdict"], bids["title"], bids["payload"]["screen"]), ("OK", "My bids", "my-bids"))
		self.assertEqual([r["bid_reference"] for r in bids["payload"]["data"]["rows"]], [self.bid])
		receipts = portal.resolve(path="/account/receipts", query={}, user=DAVID)
		self.assertEqual((receipts["title"], receipts["payload"]["screen"]), ("Receipts", "receipts"))
		masked = portal.resolve(path="/account/receipts", query={"organisation": AFYA}, user=PETER)
		self.assertEqual((masked["verdict"], masked["payload"]["screen"]), ("NOT_FOUND", "not-found"))
		self.assertEqual(portal.resolve(path="/my-bids/anything", query={}, user=DAVID)["verdict"], "NOT_FOUND")
