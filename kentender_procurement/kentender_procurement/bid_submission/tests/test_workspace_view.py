# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.7 BDS-DES-06 (plan Phase 11, slice 11.6): the bid
workspace read gives the header line and the one permitted header action,
the deadline with the time remaining from trusted time (or the trusted time
once closed), the availability notice when submission cannot happen, the
current notices (answers by delivery, addenda by acknowledgement), each
task's last change and action, and who saved the Draft last. The client
derives none of it. Reads create nothing."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import reads, simulation
from kentender_procurement.bid_submission.tests.support import DAVID, MARY, BidCase, fill_everything
from kentender_procurement.bid_submission.tests.test_addendum_refresh import AddendumCase
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase

DESCRIPTION = "Complete the five tasks below before an Authorised Signatory submits the bid."
REMAINING = r"^Closes in (\d+ days? )?(\d+ hours? )?\d+ minutes?$"


class TestReadyWorkspace(SubmissionCase):
	def view(self, user=DAVID):
		return reads.get_bid_workspace(bid_reference=self.bid, user=user)

	def test_the_header_deadline_tasks_and_saved_line(self):
		view = self.view()
		header = view["header"]
		draft = frappe.db.get_value("Bid Workspace", self.bid, "current_draft_version")
		self.assertEqual((header["title_line"], header["refs_line"], header["description"]), (view["tender"]["title"], f"{self.reference} · {self.bid} · Draft Version {draft}", DESCRIPTION))
		self.assertEqual(header["action"], {"label": "Review bid", "href": f"/tenders/{self.reference}/bid/review", "tone": "primary"})
		self.assertEqual(view["deadline"]["rows"][0], {"label": "Submissions close", "value": view["tender"]["deadline_label"]})
		self.assertEqual(view["deadline"]["rows"][1]["label"], "Time remaining")
		self.assertRegex(view["deadline"]["rows"][1]["value"], REMAINING)
		self.assertIsNone(view["availability_notice"])
		self.assertEqual([t["action"]["label"] for t in view["tasks"]], ["View", "View", "View", "View", "Review bid"])
		self.assertEqual(view["tasks"][1]["action"]["href"], f"/tenders/{self.reference}/bid/company")
		self.assertTrue(all(t["updated_label"] for t in view["tasks"][1:4]), view["tasks"])
		self.assertRegex(view["saved_text"], r"^Saved \d{1,2} \w{3} 2027, \d{2}:\d{2} EAT by David Ouma\.$")
		self.assertEqual(self.view(user=MARY)["header"]["action"]["label"], "Review bid")

	def test_a_closed_gate_names_itself_above_the_tasks_and_keeps_the_saved_bid(self):
		frappe.conf["production_bid_submission_enabled"] = 0  # restored by submission_on's cleanup
		notice = self.view(user=MARY)["availability_notice"]
		deadline = self.view()["tender"]["deadline_label"]
		self.assertEqual((notice["tone"], notice["title"]), ("critical", "Electronic bid submission is not available yet"))
		self.assertEqual(notice["text"], f"Your bid remains saved and has not been submitted. Submissions close {deadline}.")
		self.assertEqual([link["label"] for link in notice["links"]], ["Supplier support"])

	def test_an_outage_offers_the_status_and_support(self):
		simulation.set_controls(custody_service_down=1)
		notice = self.view(user=MARY)["availability_notice"]
		self.assertEqual((notice["tone"], notice["title"]), ("critical", "Electronic submission is temporarily unavailable"))
		self.assertTrue(notice["text"].startswith("Your bid remains saved and no receipt exists. Submissions close "))
		self.assertEqual([link["label"] for link in notice["links"]], ["View status", "Supplier support"])

	def test_after_the_deadline_the_draft_is_read_only_with_the_trusted_time(self):
		self.at(str(frappe.utils.add_to_date(self.deadline(), seconds=1)))
		view = self.view()
		self.assertEqual([r["label"] for r in view["deadline"]["rows"]], ["Submission deadline", "Trusted server time"])
		self.assertRegex(view["deadline"]["rows"][1]["value"], r":\d{2} EAT$")
		self.assertEqual(view["header"]["action"], {"label": "Back to My bids", "href": "/my-bids", "tone": "secondary"})
		self.assertTrue(all(t["action"]["label"] == "View" for t in view["tasks"]))


class TestDraftWorkspace(BidCase):
	def test_an_unfinished_bid_continues_at_its_first_open_task(self):
		from kentender_procurement.bid_submission.services import start_bid
		from kentender_procurement.bid_submission.tests.support import AFYA, key

		bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		view = reads.get_bid_workspace(bid_reference=bid, user=DAVID)
		self.assertEqual(view["header"]["action"], {"label": "Continue bid", "href": f"/tenders/{self.reference}/bid/company", "tone": "primary"})
		self.assertEqual(view["tasks"][1]["action"]["label"], "Continue")
		self.assertEqual(view["tasks"][4]["updated_label"], "—")
		events = frappe.db.count("Bid Submission Event")
		reads.get_bid_workspace(bid_reference=bid, user=DAVID)
		self.assertEqual(frappe.db.count("Bid Submission Event"), events)


class TestNoticesAndAddendum(AddendumCase):
	def test_an_effective_addendum_is_listed_unacknowledged_until_the_bid_moves(self):
		name = self.issue_addendum()
		reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		self.at("2027-06-01 12:05:00")
		view = reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)
		row = next(n for n in view["notices"] if n["key"] == reference)
		self.assertEqual((row["status"], row["tone"], row["action"]["label"]), ("Not acknowledged", "attention", "Review addendum"))
		self.assertEqual(row["action"]["href"], f"/tenders/{self.reference}/bid/documents")
		self.assertTrue(row["label"].startswith(f"{reference} · "))
		self.assertEqual(view["header"]["action"]["label"], "Review addendum")
		self.assertEqual(view["notices_note"], "Delivery describes the notice sent to your Tender notice email. The published answer and addendum are available here whether or not a notice was delivered.")


class TestWorkspaceAddress(SubmissionCase):
	def test_the_bid_address_needs_a_signed_in_person_and_shows_only_their_organisations_bid(self):
		from kentender_procurement.bid_submission import portal
		from kentender_procurement.bid_submission.tests.support import PETER

		path = f"/tenders/{self.reference}/bid"
		self.assertEqual(portal.resolve(path=path, query={}, user="Guest")["verdict"], "SIGN_IN")
		mine = portal.resolve(path=path, query={}, user=DAVID)
		self.assertEqual((mine["verdict"], mine["title"], mine["payload"]["screen"], mine["payload"]["data"]["bid"]["reference"]), ("OK", "Your bid", "workspace", self.bid))
		masked = portal.resolve(path=path, query={}, user=PETER)
		self.assertEqual((masked["verdict"], masked["payload"]["screen"]), ("NOT_FOUND", "not-found"))
		self.assertNotIn(self.bid, str(masked))
