# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.4.6, §5.4 items 2–5 and plan D10 (plan Phase 6,
BDS8-601): an effective addendum puts a Draft in Needs attention without a
read changing it; the first change moves it to the current definition by
Tenders' stored identity map only, asks for the named acknowledgement, and
each affected task needs attention until the bidder saves it."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import addendum, errors, reads, save, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, BidCase, key
from kentender_procurement.tenders.services import addenda, bid_definition
from kentender_procurement.tenders.tests import fixtures as tender_fx
from kentender_procurement.tenders.tests.test_open_period import CHANNELS


class AddendumCase(BidCase):
	def setUp(self):
		super().setUp()
		self._flag("kt_tenders_notice_sync", True)
		self._flag("kt_tenders_notice_transport", lambda notice: {"result": "Delivered", "provider_reference": f"test:{notice.name}", "failure_reason": ""})
		self.bid = start_bid.start_bid(tender_reference=self.reference, organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)["bid_reference"]

	def version(self):
		return frappe.db.get_value("Bid Workspace", self.bid, "record_version")

	def field(self, task, label, *, view=None):
		view = view or reads.get_bid_task(bid_reference=self.bid, task=task, user=DAVID)
		return next(f for g in view["groups"] for f in g["fields"] if f["label"] == label)

	def save(self, task, values):
		return save.save_bid_task(bid_reference=self.bid, task=task, values=values, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)

	def issue_addendum(self) -> str:
		frappe.flags.kt_tenders_clock = "2027-05-31 08:30:00"
		name = self._addendum(values={**self.FIXTURE_ADDENDUM, "revised_submission_deadline": "2027-06-12 11:00:00"})
		root = self._root()
		addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=tender_fx.key(), user=tender_fx.OFFICER)
		root.reload()
		frappe.flags.kt_tenders_clock = "2027-05-31 09:00:00"
		addenda.issue_addendum(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=tender_fx.key(), user=tender_fx.HOPF)
		for channel in CHANNELS:
			self._confirm("addendum", channel, addendum=name, available_at="2027-05-31 09:00:00")
		self.assertEqual(bid_definition.current(self.name)["definition_version"], 2)
		return name


class TestRefreshForAddendum(AddendumCase):
	def test_a_draft_moves_to_the_current_definition_only_by_the_stored_map(self):
		year = self.field("company", "Authorised representative's address")
		model = self.field("requirements", "Offered make and model")
		self.save("company", {year["handle"]: "11 Riverside Drive, Nairobi"})
		self.save("requirements", {model["handle"]: "ApexBook Pro 14"})
		name = self.issue_addendum()
		reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		self.at("2027-06-01 12:05:00")

		# a read says Needs attention and changes nothing
		before = frappe.db.get_value("Bid Workspace", self.bid, ["record_version", "current_draft_version", "definition_version"])
		view = reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)
		self.assertEqual((view["bid"]["status"], view["next"]["task"], bool(view["addendum_notice"])), ("Needs attention", "documents", True))
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, ["record_version", "current_draft_version", "definition_version"]), before)

		# the first change refreshes the Draft and asks for review first
		self.at("2027-06-01 12:10:00")
		refreshed = self.save("company", {year["handle"]: "12 Riverside Drive, Nairobi"})
		self.assertEqual((refreshed["ok"], refreshed["code"], refreshed["refreshed"]), (False, "BDS_ADDENDUM_REVIEW_REQUIRED", True))
		self.assertIn("documents", refreshed["tasks"])
		ws = frappe.db.get_value("Bid Workspace", self.bid, ["definition_version", "current_draft_version", "status"], as_dict=True)
		self.assertEqual((ws.definition_version, ws.current_draft_version, ws.status), (2, before[1] + 1, "Needs attention"))

		# answers move only as Tenders' identity map says
		steps = bid_definition.map_bid_definition_addendum(tender=self.name, from_version=1, to_version=2)["steps"]
		by_key = {c["stable_key"]: c for c in steps[0]["classifications"]}
		year_now = self.field("company", "Authorised representative's address")
		model_now = self.field("requirements", "Offered make and model")
		year_row = next(c for k, c in by_key.items() if k.endswith(":RR-SUPPLIER-DETAILS:representative_address"))
		model_row = next(c for k, c in by_key.items() if k.endswith(":RR-GOODS-OFFER:offered_make_model"))
		self.assertEqual(year_now["value"], "11 Riverside Drive, Nairobi" if year_row["copy_prior_answer"] else None)
		self.assertEqual(model_now["value"], "ApexBook Pro 14" if model_row["copy_prior_answer"] else None)
		if not model_row["copy_prior_answer"]:
			# kept in history: "removed" when the Goods line's identity changed (its destination is part of it), else "fresh"
			self.assertTrue(frappe.db.exists("Bid Draft Change", {"bid_workspace": self.bid, "change_kind": ("in", ["Fresh response required", "Removed"]), "prior_value": '"ApexBook Pro 14"'}))

		# the named acknowledgement completes the documents task
		documents = reads.get_bid_task(bid_reference=self.bid, task="documents", user=DAVID)
		acknowledge = next(f for g in documents["groups"] for f in g["fields"] if f["kind"] == "confirmation")
		self.assertEqual(acknowledge["label"], f"I have reviewed {reference} and understand how it changes this Tender.")
		self.assertEqual((documents["task"]["status"], acknowledge["issue"]["severity"]), ("Needs attention", "Must fix"))
		self.assertTrue(self.save("documents", {acknowledge["handle"]: True})["ok"])
		tasks = {t["key"]: t["status"] for t in reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)["tasks"]}
		self.assertEqual(tasks["documents"], "Complete")
		for key in refreshed["tasks"]:
			if key != "documents":
				self.assertEqual(tasks[key], "Needs attention", key)

	def test_an_old_handle_after_the_refresh_is_unknown(self):
		year = self.field("company", "Authorised representative's address")
		self.issue_addendum()
		self.at("2027-06-01 12:10:00")
		self.save("company", {year["handle"]: "11 Riverside Drive, Nairobi"})  # refreshes
		self.assertIsNone(addendum.pending(type("Ctx", (), {"workspace": frappe.get_doc("Bid Workspace", self.bid)})()))
		with self.assertRaises(errors.BidSubmissionError) as ctx:
			self.save("company", {year["handle"]: "11 Riverside Drive, Nairobi"})
		self.assertEqual(ctx.exception.code, "BDS_UNKNOWN_RESPONSE")
