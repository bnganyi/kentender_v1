# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §10.9 BDS-DES-08 (plan Phase 11, slice 11.8): the company
task read gives the bidding organisation as copied to the bid (and the two
choices once the Account has changed), the bid's Tender contact, one row per
form of the task in the definition's order with its state and who confirmed
it, the tender security with the physical original as this bid knows it, and
the Authorised Signatory with their certificate. A read saves nothing."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import reads, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, BidCase, key
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase


def company(bid, user=DAVID):
	return reads.get_bid_task(bid_reference=bid, task="company", user=user)


class TestCompleteCompanyTask(SubmissionCase):
	def test_the_complete_task_as_the_board_draws_it(self):
		view = company(self.bid)
		self.assertEqual((view["page"]["title"], view["badge"]), ("Company, declarations and tender security", {"label": "Complete", "tone": "live"}))
		org = view["organisation"]
		self.assertEqual([f["label"] for f in org["facts"]], ["Legal name", "Registration number", "KRA PIN", "Address", "Arrangement"])
		self.assertEqual((org["kind"], org["update"], org["current_text"]), ("single", None, "This bid is using your current Account details."))
		self.assertTrue(org["snapshot_text"].startswith("From your Account · copied to this bid on "))
		self.assertEqual((view["contact"]["phone"], view["contact"]["note"]), ("+254 709 555 015", "These values apply only to this bid."))
		rows = view["declarations"]
		self.assertTrue(rows and all(r["status"] in ("Complete", "Confirmed") for r in rows), [(r["label"], r["status"]) for r in rows])
		confirmed = [r for r in rows if r["status"] == "Confirmed"]
		self.assertTrue(confirmed and all(r["confirmed_text"] == "Confirmed by David Ouma" for r in confirmed))
		self.assertTrue(all(r["fields"] for r in rows))
		# each form by its own name (the product profile's names for the definition's form ids)
		labels = [r["label"] for r in rows]
		for name in ("Tenderer information", "Form of Tender", "Independent tender determination", "Self-declaration — not debarred", "Self-declaration — no corrupt or fraudulent practice", "Code of ethics commitment"):
			self.assertIn(name, labels)
		self.assertNotIn("Declaration", labels)
		self.assertEqual(view["contact"]["assigned"], "David Ouma")
		notice = view["contact"]["notice"]
		self.assertIn(notice["current"], [o["contact_id"] for o in notice["options"]])  # verified Account emails only
		security = view["tender_security"]
		self.assertEqual((security["entered"], security["physical"]["tone"], security["physical"]["title"]), (True, "warning", "Physical original not yet recorded"))
		self.assertIn("You may submit electronically, but failure to deliver the original before closing may disqualify the bid.", security["physical"]["text"])
		self.assertEqual(view["signatory"]["name"], "Mary Wanjiku")
		self.assertEqual(view["signatory"]["certificate"]["status"], "Ready")
		# every other task is done and David cannot submit, so his part is finished: the button says so
		self.assertEqual(view["footer"], {"save_label": "Save and finish", "next_href": f"/tenders/{self.reference}/bid"})
		# and the panel says who can change the signatory, and that David cannot
		self.assertIn("Ask Mary Wanjiku.", view["signatory"]["change_note"])
		self.assertEqual(view["signatory"]["change_href"], "")
		self.assertEqual(view["signatory"]["certificate_note"], "")  # her certificate is ready

	def test_a_changed_account_offers_its_two_choices_and_changes_nothing(self):
		self.accounts.orgs[AFYA]["registered_address"] = "Riverside Drive, Nairobi"
		events = frappe.db.count("Bid Submission Event")
		org = company(self.bid)["organisation"]
		self.assertEqual([r["label"] for r in org["update"]["rows"]], ["This bid", "Current Account"])
		self.assertEqual(org["update"]["rows"][1]["value"], "Riverside Drive, Nairobi")
		self.assertEqual((org["update"]["fact"], org["current_text"]), ("Address", ""))
		self.assertEqual(frappe.db.count("Bid Submission Event"), events)

	def test_every_changed_fact_is_listed_including_the_business_profile(self):
		# release 1.4: the standing facts are copied into the bid; one that changes on the Account shows too
		self.accounts.orgs[AFYA]["registered_address"] = "Riverside Drive, Nairobi"
		self.accounts.set_profile(AFYA, {**self.accounts.profiles[AFYA], "business_structure": "Sole proprietor", "directors": []})
		update = company(self.bid)["organisation"]["update"]
		self.assertEqual(update["fact"], "Address")  # the first change keeps the board's own table
		by_fact = {c["fact"]: c for c in update["changes"]}
		structure = by_fact["Afya Digital Supplies Limited — Business structure"]
		self.assertEqual((structure["this_bid"], structure["current"]), ("Registered company", "Sole proprietor"))
		directors = by_fact["Afya Digital Supplies Limited — Directors"]
		self.assertEqual((directors["this_bid"], directors["current"]), ("Mary Wanjiku · Kenyan · Kenyan · 100.00", ""))


class TestFormOfTenderPrice(SubmissionCase):
	def test_the_form_of_tender_states_the_calculated_bid_total(self):
		# BDS01-AC-040 (found by the 28 Sep 2026 acceptance audit): the Form of
		# Tender's price line is the Price task's total, never entered again.
		from kentender_procurement.bid_submission.services import price
		from kentender_procurement.bid_submission.services.bid_context import load

		view = company(self.bid)
		form = next(r for r in view["declarations"] if r["label"] == "Form of Tender")
		calc = price.calculate(load(self.bid, actor=DAVID, organisation="", at=frappe.utils.now_datetime()))
		self.assertIn(f"is: KES {calc['total']:,.2f} (", form["statement"])
		self.assertNotIn("_____ (in words and figures, indicating the currency)", form["statement"])


class TestNewCompanyTask(BidCase):
	def test_an_unpriced_bid_leaves_the_form_of_tender_price_line_blank(self):
		bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		form = next(r for r in company(bid)["declarations"] if r["label"] == "Form of Tender")
		self.assertIn("(in words and figures, indicating the currency)", form["statement"])

	def test_a_new_bid_lists_every_form_not_started_and_no_security_yet(self):
		bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		view = company(bid)
		self.assertNotEqual(view["badge"]["label"], "Complete")
		# nothing is the bidder's to answer in a business profile copied from the Account, so it is complete at once
		self.assertTrue(all(r["status"] in ("Not started", "In progress") for r in view["declarations"] if not r["label"].startswith("Business profile")), [(r["label"], r["status"]) for r in view["declarations"]])
		self.assertEqual([r["status"] for r in view["declarations"] if r["label"].startswith("Business profile")], ["Complete"])
		self.assertFalse(view["tender_security"]["entered"])
		self.assertEqual(view["contact"]["notice_email"] != "", True)


class TestTenderContactPerson(BidCase):
	"""BDS-CHG-001 v0.8 §4.3 and §10.9: the bid's Tender contact may be any
	active person of the bidding organisation (FU-V08-54); another
	organisation's person never."""

	def test_the_contact_can_become_another_person_of_the_organisation(self):
		from kentender_procurement.bid_submission.services import tender_contact
		from kentender_procurement.bid_submission.tests.support import KISIWA, MARY, PETER

		bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]
		contact = company(bid)["contact"]
		people = {p["name"]: p["assignment_id"] for p in contact["people"]}
		self.assertEqual(set(people), {"David Ouma", "Mary Wanjiku"})
		self.assertEqual(contact["person"], people["David Ouma"])
		arrangement = frappe.db.get_value("Bid Workspace", bid, "bidder_arrangement")

		def update(assignment_id, email=MARY):
			return tender_contact.update_tender_contact(
				bid_reference=bid, assignment_id=assignment_id, email=email, phone="+254 709 555 016",
				expected_record_version=frappe.db.get_value("Bidder Arrangement", arrangement, "record_version"), idempotency_key=key(), user=DAVID,
			)

		outsider = self.accounts.assign(PETER, KISIWA, "Supplier Representative")
		refused = update(outsider)
		self.assertEqual((refused["ok"], refused["errors"]), (False, {"assignment_id": "Choose a person of this organisation."}))
		self.assertTrue(update(people["Mary Wanjiku"])["ok"])
		row = frappe.db.get_value("Bidder Arrangement", arrangement, ["tender_contact_user", "tender_contact_name", "tender_contact_email", "tender_contact_phone"], as_dict=True)
		self.assertEqual((row.tender_contact_user, row.tender_contact_name, row.tender_contact_email, row.tender_contact_phone), (MARY, "Mary Wanjiku", MARY, "+254 709 555 016"))
		after = company(bid)["contact"]
		self.assertEqual((after["assigned"], after["person"]), ("Mary Wanjiku", people["Mary Wanjiku"]))
