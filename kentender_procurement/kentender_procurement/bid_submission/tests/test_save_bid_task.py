# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.4.5, §4.5, §4.6, §5.3, §7.1 and §7.2 `SaveBidTask`
(plan Phase 6, BDS8-602): a save carries values by opaque field handle for
one task; the server re-resolves the bound definition and rejects anything
unknown, hidden, supplied or out of range; the Draft version advances and
every change is kept; reads change nothing and mask other organisations."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import errors, reads, save, start_bid, tender_contact
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, KISIWA, MARY, PETER, BidCase, key


class SaveCase(BidCase):
	def setUp(self):
		super().setUp()
		self.bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]

	def task(self, name="company", user=DAVID):
		return reads.get_bid_task(bid_reference=self.bid, task=name, user=user)

	def field(self, view, label):
		return next(f for g in view["groups"] for f in g["fields"] if f["label"] == label)

	def version(self):
		return frappe.db.get_value("Bid Workspace", self.bid, "record_version")

	def save(self, values, task="company", version=None, request=None, user=DAVID):
		return save.save_bid_task(bid_reference=self.bid, task=task, values=values, expected_record_version=self.version() if version is None else version, idempotency_key=request or key(), user=user)


class TestSaveBidTask(SaveCase):
	def test_david_saves_a_company_answer_and_the_draft_version_advances(self):
		view = self.task()
		year = self.field(view, "Year of registration")
		self.assertEqual((year["kind"], year["editable"], year["value"], year["required"]), ("integer", True, None, True))
		saved = self.save({year["handle"]: "2011"})
		self.assertEqual((saved["ok"], saved["draft_version"]), (True, 2))
		self.assertEqual(self.field(self.task(), "Year of registration")["value"], 2011)
		change = frappe.get_all("Bid Draft Change", filters={"bid_workspace": self.bid}, fields=["draft_version", "change_kind", "prior_value", "new_value", "actor"])
		self.assertEqual([(c.draft_version, c.change_kind, c.prior_value, c.new_value, c.actor) for c in change], [(2, "Saved", "null", "2011", DAVID)])
		self.assertEqual(frappe.db.get_value("Bid Section Response", {"bid_workspace": self.bid, "section_key": "company"}, "status"), "In progress")

	def test_supplied_facts_are_shown_from_the_account_and_arrangement_and_never_accepted(self):
		view = self.task()
		legal = self.field(view, "Tenderer's legal name")
		self.assertEqual((legal["value"], legal["editable"], legal["supplied_from"]), ("Afya Digital Supplies Limited", False, "arrangement"))
		self.assertEqual(self.field(view, "Address in the country of registration")["value"], "Afya Digital Supplies Limited, Nairobi")
		other_task = next(f for g in self.task("requirements")["groups"] for f in g["fields"] if f["editable"])
		for handle in (legal["handle"], "f" + "0" * 20, other_task["handle"]):
			with self.subTest(handle=handle), self.assertRaises(errors.BidSubmissionError) as ctx:
				self.save({handle: "Something else"})
			self.assertEqual(ctx.exception.code, "BDS_UNKNOWN_RESPONSE")
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, "current_draft_version"), 1)

	def test_a_value_the_published_rule_refuses_is_a_field_error_and_nothing_is_saved(self):
		view = self.task()
		amount = self.field(view, "Amount of the instrument")
		year = self.field(view, "Year of registration")
		refused = self.save({amount["handle"]: "600000", year["handle"]: "twenty"})
		self.assertEqual((refused["ok"], refused["code"]), (False, "BDS_FIELD_INVALID"))
		self.assertEqual(refused["errors"], {amount["handle"]: "Enter exactly KES 500,000.00.", year["handle"]: "Enter a whole number."})
		self.assertEqual((frappe.db.get_value("Bid Workspace", self.bid, "current_draft_version"), frappe.db.count("Bid Draft Change", {"bid_workspace": self.bid})), (1, 0))

	def test_a_conditional_field_follows_its_controlling_answer(self):
		view = self.task()
		form, bank = self.field(view, "Form of Tender Security"), next(f for g in view["groups"] for f in g["fields"] if f["label"] == "Guarantee valid until" and f["shown_when"]["values"] == ["Demand Bank Guarantee"])
		self.assertFalse(bank["visible"])
		with self.assertRaises(errors.BidSubmissionError) as hidden:
			self.save({bank["handle"]: "2027-11-15"})
		self.assertEqual(hidden.exception.code, "BDS_UNKNOWN_RESPONSE")
		self.save({form["handle"]: "Demand Bank Guarantee", bank["handle"]: "2027-11-15"})
		self.assertEqual(self.field(self.task(), "Form of Tender Security")["value"], "Demand Bank Guarantee")
		shown = next(f for g in self.task()["groups"] for f in g["fields"] if f["handle"] == bank["handle"])
		self.assertEqual((shown["visible"], shown["value"]), (True, "2027-11-15"))
		self.save({form["handle"]: "Insurance Guarantee"})
		hidden_now = next(f for g in self.task()["groups"] for f in g["fields"] if f["handle"] == bank["handle"])
		self.assertEqual((hidden_now["visible"], hidden_now.get("issue")), (False, None))

	def test_a_stale_or_replayed_save(self):
		view = self.task()
		year = self.field(view, "Year of registration")
		request, version = key(), self.version()
		first = self.save({year["handle"]: "2011"}, version=version, request=request)
		self.assertEqual(self.save({year["handle"]: "2011"}, version=version, request=request), first)
		with self.assertRaises(errors.BidSubmissionError) as stale:
			self.save({year["handle"]: "2012"}, version=version)
		self.assertEqual(stale.exception.code, "BDS_STALE_VERSION")

	def test_after_the_deadline_nothing_saves(self):
		year = self.field(self.task(), "Year of registration")
		self.at("2027-07-01 09:00:00")
		with self.assertRaises(errors.BidSubmissionError) as ctx:
			self.save({year["handle"]: "2011"})
		self.assertEqual(ctx.exception.code, "BDS_TENDER_NOT_OPEN")


class TestReads(SaveCase):
	def test_reads_change_nothing(self):
		before = frappe.db.get_value("Bid Workspace", self.bid, ["record_version", "current_draft_version", "last_saved_at", "status"], as_dict=True)
		events = frappe.db.count("Bid Submission Event")
		reads.get_bid_workspace(bid_reference=self.bid, user=MARY)
		for name in ("documents", "company", "requirements", "price", "review"):
			self.task(name, user=MARY)
		reads.get_my_bids(user=DAVID)
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, ["record_version", "current_draft_version", "last_saved_at", "status"], as_dict=True), before)
		self.assertEqual(frappe.db.count("Bid Submission Event"), events)

	def test_the_workspace_lists_five_tasks_with_the_next_one_to_do(self):
		view = reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)
		self.assertEqual([t["key"] for t in view["tasks"]], ["documents", "company", "requirements", "price", "review"])
		self.assertEqual(view["tasks"][0]["status"], "Complete")  # nothing to acknowledge without an addendum
		self.assertEqual((view["bid"]["status"], view["bid"]["draft_version"], view["next"]["task"]), ("Draft", 1, "company"))

	def test_another_organisation_sees_nothing(self):
		for call in (lambda: reads.get_bid_workspace(bid_reference=self.bid, user=PETER), lambda: self.task(user=PETER)):
			with self.assertRaises(frappe.DoesNotExistError):
				call()
		self.assertEqual(reads.get_my_bids(user=PETER, organisation=KISIWA)["rows"], [])

	def test_my_bids_shows_the_organisation_bid_with_one_next_action(self):
		rows = reads.get_my_bids(user=MARY)["rows"]
		self.assertEqual([(r["bid_reference"], r["tender_reference"], r["status"]) for r in rows], [(self.bid, self.reference, "Draft")])
		self.assertEqual(rows[0]["next_action"]["label"], "Continue bid")

	def test_no_internal_identity_reaches_the_portal(self):
		import json
		import re

		leak = re.compile(r"\bRSP-|\bCOMP-|\bCTL-|\bRR-|\bEVG-|\bVAL-|\bRQ-|\bVS-|\bSV-|\bAP-|\bTASK-|\bPBD-|\bTDA-|\bTND[RV]-|[0-9a-f]{64}")
		payloads = [reads.get_bid_workspace(bid_reference=self.bid, user=DAVID), reads.get_my_bids(user=DAVID)] + [self.task(name) for name in ("documents", "company", "requirements", "price", "review")]
		for payload in payloads:
			self.assertIsNone(leak.search(json.dumps(payload, default=str)), leak.search(json.dumps(payload, default=str)))


class TestTenderContact(SaveCase):
	def test_the_tender_contact_phone_completes_the_supplied_contact(self):
		phone = self.field(self.task(), "Authorised representative's telephone")
		self.assertEqual((phone["value"], phone["issue"]["severity"]), (None, "Must fix"))
		arrangement = frappe.db.get_value("Bid Workspace", self.bid, "bidder_arrangement")
		version = frappe.db.get_value("Bidder Arrangement", arrangement, "record_version")
		bad = tender_contact.update_tender_contact(bid_reference=self.bid, email="david.ouma@afyadigital.example", phone="not a phone", expected_record_version=version, idempotency_key=key(), user=DAVID)
		self.assertEqual((bad["ok"], list(bad["errors"])), (False, ["phone"]))
		done = tender_contact.update_tender_contact(bid_reference=self.bid, email="david.ouma@afyadigital.example", phone="+254 709 555 015", expected_record_version=version, idempotency_key=key(), user=DAVID)
		self.assertTrue(done["ok"])
		shown = self.field(self.task(), "Authorised representative's telephone")
		self.assertEqual((shown["value"], shown.get("issue")), ("+254 709 555 015", None))
