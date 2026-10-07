# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — the Bid Evaluation feed to Home (`bid_evaluation/services/home_provider.py`).

Uses the module's shared evaluation world (the published Tender, the bid and the completed opening are built once; every test starts
from a clean evaluation, as the other Bid Evaluation tests do) and moves the case on with the owner's own commands. The provider only
reads. The world and every row it adds are removed at the end and counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.bid_evaluation.tests.test_home_provider
"""

from __future__ import annotations

import json
import re
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import frappe
from kentender_core.services.command_write_guard import purge_doc
from frappe.utils import get_datetime

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import home_workspace as hw
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.bid_evaluation.services import (
	appointment, clarification, correction, declaration, findings, my_work_provider, oversight, people, preparation, reads, report, roster, secretary, signing,
	stage_summary, timers,
)
from kentender_procurement.bid_evaluation.services import home_provider
from kentender_procurement.bid_evaluation.services.home_provider import entries
from kentender_procurement.bid_evaluation.tests.support import (
	AO, AUDITOR, CHAIR, HOP, MEMBER, MEMBER_2, NS, OUTSIDER, ROSTER, SECRETARY, SUPPORT, EvaluationCase,
)
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx
from kentender_procurement.tenders.services import stage_summary as ss
from kentender_procurement.tenders.tests import fixtures as tender_fx

BIDDER = "Afya Digital Supplies Limited"
HOD = req_fx.HOD  # Head of User Department in the contributing unit
HOD_OTHER = req_fx.HOD_BETA  # a Head of User Department whose unit never contributed
NOBODY = tender_fx.NOBODY
EXTRA = "evlt.home.extra@example.test"  # a second Accounting Officer, granted and revoked inside one test
EXTRA_NS = "KT_TEST_EVLHOME"
MEMBERS = (CHAIR, MEMBER, MEMBER_2)
EVALUATION_ROWS = ("Evaluation Case", "Evaluation Appointment", "Evaluation Secretary Appointment", "Evaluation Report Version", "Evaluation Report Delivery",
	"Evaluation Command Journal", "Evaluation Clarification")
QUESTION = "Please identify the page and section of your submitted Kenya service-centre details that gives the Nairobi service address."
SCOPE = "Explain the submitted evidence. Do not change your offer or add a new service arrangement."


def _remove_extra() -> None:
	frappe.set_user("Administrator")
	for name in frappe.get_all("User Responsibility Assignment", filters={"user": EXTRA}, pluck="name"):
		purge_doc("User Responsibility Assignment", name)
	for name in frappe.get_all("Contact Email", filters={"email_id": EXTRA}, pluck="parent"):
		frappe.delete_doc("Contact", name, force=1, ignore_permissions=1)
	frappe.db.delete("Notification Log", {"for_user": EXTRA})
	if frappe.db.exists("User", EXTRA):
		frappe.delete_doc("User", EXTRA, force=1, ignore_permissions=1)
	frappe.db.commit()


def _assert_nothing_left() -> None:
	"""Runs last (registered first): the world and its rows are gone."""
	left = {doctype: frappe.db.count(doctype, {"fixture_namespace": NS}) for doctype in EVALUATION_ROWS if frappe.get_meta(doctype).has_field("fixture_namespace")}
	left["Tender"] = frappe.db.count("Tender", {"fixture_namespace": tender_fx.NS})
	left["extra user"] = int(bool(frappe.db.exists("User", EXTRA)))
	if any(left.values()):
		raise AssertionError(f"Bid Evaluation Home test rows left behind: {left}")


class TestEvaluationHomeProvider(EvaluationCase):
	@classmethod
	def setUpClass(cls):
		unittest.addModuleCleanup(_assert_nothing_left)
		super().setUpClass()
		cls.addClassCleanup(_remove_extra)
		tender_fx._user(EXTRA, "EVLT Extra Accounting Officer")

	def setUp(self):
		super().setUp()
		home_support.reset()

	# ----- the evaluation, step by step (the owner's own commands) -----

	def prep(self) -> str:
		self.case = preparation.ensure_preparation(tender=self.name)["evaluation"]
		return self.case

	def evl_version(self) -> int:
		return int(frappe.db.get_value("Evaluation Case", self.case, "record_version"))

	def h_appoint(self):
		appointment.appoint_committee(tender=self.name, members=ROSTER, appointment_reference="MOH/EVAL/TEST/2101", expected_version=self.evl_version(),
			idempotency_key=key(), user=AO)

	def assign_secretary(self):
		secretary.assign_secretary(tender=self.name, secretary=SECRETARY, appointment_reference="MOH/EVAL/SEC/TEST", expected_version=self.evl_version(),
			idempotency_key=key(), user=HOP)

	def declare(self, *users):
		for user in users:
			declaration.declare_interest(tender=self.name, choice="No conflict to declare", confidentiality_accepted=True, idempotency_key=key(), user=user)

	def review(self) -> str:
		self.case = self.reviewing()
		return self.case

	def h_freeze(self):
		self.resolve_all(self.case)
		draft = report.draft(self.evl_doc())
		return signing.send_for_signing(tender=self.name, expected_version=draft.record_version, idempotency_key=key(), user=SECRETARY)

	def h_sign(self, *users):
		version = signing.signing_version(self.evl_doc()).name
		for user in users:
			signing.sign(tender=self.name, report_version=version, idempotency_key=key(), user=user)

	def deliver(self):
		self.h_freeze()
		self.h_sign(*MEMBERS)
		self.assertEqual(self.evl_doc().state, "Report sent")

	def evl_doc(self):
		return frappe.get_doc("Evaluation Case", self.case)

	def authorise_clarification(self) -> str:
		service = self.requirement(self.case, "Service location")
		findings.record_evidence_finding(tender=self.name, bid=service["bid"], requirement_key=service["requirement_key"], result="Needs review",
			reason="The submitted evidence does not clearly identify the service address.", idempotency_key=key(), user=MEMBER)
		self.session()
		deadline = get_datetime(frappe.flags.kt_evl_clock) + timedelta(days=1)
		out = clarification.authorise(tender=self.name, bid=service["bid"], requirement_key=service["requirement_key"], question=QUESTION, reply_scope=SCOPE,
			reply_deadline=str(deadline), idempotency_key=key(), user=CHAIR)
		self.end_session()
		return out["clarification"]

	# ----- helpers -----

	def region(self, user: str, region: str):
		home_support.reset()
		return entries(user=user, region=region)

	def mine(self, rows):
		"""The rows about this world's case (the test site also holds the canonical evaluation)."""
		return [row for row in rows or [] if row["root"] == self.case]

	def one(self, user: str, region: str, action_id: str) -> dict:
		rows = [row for row in self.region(user, region) or [] if row["action_id"] == f"{self.case}:{action_id}"]
		self.assertEqual(len(rows), 1, f"{user} {region} {action_id}: {rows}")
		return rows[0]

	def done(self, user: str, name: str) -> dict:
		"""The user's completed action for the owner's own record (its action id is the record's name)."""
		rows = [row for row in self.region(user, he.COMPLETED) or [] if row["action_id"] == name]
		self.assertEqual(len(rows), 1, f"{user} completed {name}: {rows}")
		return rows[0]

	def ids(self, user: str, region: str) -> list[str]:
		return [row["action_id"].split(":", 1)[1] for row in self.mine(self.region(user, region))]

	def name_of(self, user: str) -> str:
		return frappe.db.get_value("User", user, "full_name")

	def home(self, user: str, at: datetime):
		return hw.get_workspace(user, providers=[entries], at=at)

	def all_rows(self, user: str, at: datetime, region: str) -> list[dict]:
		rows, cursor = [], None
		while True:
			page = hw.get_workspace(user, regions=[region], cursors={region: cursor} if cursor else None, providers=[entries], at=at)["regions"][region]
			rows += page["entries"]
			cursor = page["next_cursor"]
			if not cursor:
				return rows

	def row(self, user: str, at: datetime, region: str, action_id: str) -> dict:
		rows = [row for row in self.all_rows(user, at, region) if row["key"].endswith(f"|{self.case}:{action_id}")]
		self.assertEqual(len(rows), 1, f"{region} {action_id}: {rows}")
		return rows[0]

	def holders(self, text: str, prefix: str, suffix: str, role: str, phrase: str) -> None:
		"""`text` is prefix + the people who hold `role` (either order) when there are two or fewer, otherwise `phrase` + suffix."""
		self.assertTrue(text.startswith(prefix) and text.endswith(suffix), text)
		who = text[len(prefix) : len(text) - len(suffix)]
		holders = people.holders(role)
		if len(holders) <= 2:
			self.assertEqual(set(who.split(" or ")), {people.full_name(user) for user in holders}, text)
		else:
			self.assertEqual(who, phrase, text)

	# ----- My work -----

	def test_the_accounting_officers_appointment_row_uses_the_specs_wording_and_the_head_assigns_the_secretary(self):
		self.prep()
		doc = self.evl_doc()
		row = self.one(AO, he.MY_WORK, "appoint")
		self.assertEqual((row["title"], row["action"], row["reference"]), (doc.tender_title, "Appoint the evaluation committee", doc.tender_reference))
		self.assertNotEqual(row["title"], row["reference"])
		self.assertEqual((row["owner"], row["region"], row["root"], row["blocked"], row["reason"], row["due"]), ("evaluation", he.MY_WORK, doc.name, False, "", None))
		self.assertEqual((row["entered_at"], type(row["entered_at"]), row["entered_verb"]), (doc.prepared_at or doc.creation, datetime, "Received"))
		self.assertEqual(row["destination"], {"route": ["tenders", doc.tender_reference, "evaluation", "appoint"], "route_options": {}})
		secretary_row = self.one(HOP, he.MY_WORK, "secretary")
		self.assertEqual((secretary_row["action"], secretary_row["destination"]["route"]), ("Assign evaluation secretary", ["tenders", doc.tender_reference, "evaluation", "secretary"]))
		self.assertNotIn("secretary", self.ids(AO, he.MY_WORK))

	def test_an_unset_preparation_instant_falls_back_to_the_cases_creation(self):
		self.prep()
		frappe.db.set_value("Evaluation Case", self.case, "prepared_at", None, update_modified=False)
		doc = self.evl_doc()
		self.assertIsNone(doc.prepared_at)
		self.assertEqual(self.one(AO, he.MY_WORK, "appoint")["entered_at"], doc.creation)
		self.assertEqual(self.one(HOP, he.WAITING, "appoint:waiting")["since"], doc.creation)

	def test_once_appointed_each_member_declares_from_the_appointment_instant(self):
		self.prep()
		self.h_appoint()
		appointed = roster.current_appointment(self.case)
		for user in MEMBERS:
			row = self.one(user, he.MY_WORK, f"declare:{appointed.name}:{user}")
			self.assertEqual((row["action"], row["entered_at"], row["title"]), ("Declare interests", appointed.appointed_at, self.evl_doc().tender_title))
			self.assertEqual(row["destination"]["route"], ["tenders", self.reference, "evaluation", "declaration"])
		self.assertNotIn("appoint", self.ids(AO, he.MY_WORK))

	def test_review_bids_has_no_owner_instant_so_it_enters_when_the_opening_package_was_received(self):
		self.review()
		doc = self.evl_doc()
		received = frappe.db.get_value("Evaluation Source Intake", doc.source_intake, "received_at")
		self.assertTrue(received)
		for user in MEMBERS:
			row = self.one(user, he.MY_WORK, f"review:{doc.source_intake}:{user}")
			self.assertEqual((row["action"], row["entered_at"], row["destination"]["route"]), ("Review bids", received, ["tenders", self.reference, "evaluation"]))
		self.assertEqual([r for r in self.ids(SECRETARY, he.MY_WORK) if r.startswith("review")], [])

	def test_the_owners_action_table_matches_the_owners_own_row_titles(self):
		source = (Path(my_work_provider.__file__)).read_text()
		matches = re.findall(r'key=f?"([a-z-]+(?::[^"]*)?)"', source)
		kinds = {match.split(":")[0] for match in matches if ":waiting" not in match}
		self.assertEqual(kinds, set(home_provider.ACTIONS))  # every row kind the owner can raise has its wording
		self.review()
		request = self.authorise_clarification()
		self.assertTrue(request)
		seen = set()
		for user in (AO, HOP, SECRETARY, *MEMBERS):
			for row in my_work_provider.my_work_rows(user)["assigned"]:
				if row["reference"] != self.reference:
					continue
				kind = row["task_type"].removeprefix("bid_evaluation.")
				seen.add(kind)
				self.assertEqual(home_provider.ACTIONS[kind], row["title"].split(" for ")[0], row["title"])
				self.assertNotIn(self.reference, home_provider.ACTIONS[kind])
		self.assertTrue({"review", "send"} <= seen, seen)
		self.assertEqual(home_provider.ACTIONS["appoint"], "Appoint the evaluation committee")  # the spec's own wording

	def test_no_row_is_blocked_because_the_owner_never_answers_your_turn_blocked(self):
		self.review()
		self.authorise_clarification()
		for user in (AO, HOP, SECRETARY, *MEMBERS):
			for row in self.mine(self.region(user, he.MY_WORK)):
				self.assertEqual((row["blocked"], row["reason"]), (False, ""), (user, row["action"]))

	def test_the_report_to_sign_enters_with_the_frozen_instant_and_the_secretary_waits_for_the_signatures(self):
		self.review()
		self.h_freeze()
		version = signing.signing_version(self.evl_doc())
		for user in MEMBERS:
			row = self.one(user, he.MY_WORK, f"sign:{version.name}:{user}")
			self.assertEqual((row["action"], row["entered_at"], row["destination"]["route"]), ("Review and sign report", version.frozen_at, ["tenders", self.reference, "evaluation", "report"]))
		waiting = self.one(SECRETARY, he.WAITING, f"sign:waiting:{version.name}")
		self.assertEqual((waiting["action"], waiting["holder"], waiting["since"]), ("Waiting for the committee members to sign the evaluation report", "Committee members", version.frozen_at))
		self.h_sign(CHAIR)
		waiting = self.one(SECRETARY, he.WAITING, f"sign:waiting:{version.name}")
		self.assertEqual(waiting["action"], f"Waiting for {self.name_of(MEMBER)} and {self.name_of(MEMBER_2)} to sign the evaluation report")
		self.assertEqual(waiting["holder"], f"{self.name_of(MEMBER)} and {self.name_of(MEMBER_2)}")
		self.assertNotIn(f"sign:{version.name}:{CHAIR}", self.ids(CHAIR, he.MY_WORK))

	# ----- Waiting -----

	def test_the_head_waits_for_the_committee_and_the_accounting_officer_for_the_secretary_with_the_roster_holders(self):
		self.prep()
		doc = self.evl_doc()
		waiting = self.one(HOP, he.WAITING, "appoint:waiting")
		self.assertEqual((waiting["title"], waiting["reference"], waiting["since"]), (doc.tender_title, doc.tender_reference, doc.prepared_at or doc.creation))
		self.holders(waiting["action"], "Waiting for ", " to appoint the evaluation committee", people.ACCOUNTING_OFFICER, "an Accounting Officer")
		self.holders(waiting["holder"], "", "", people.ACCOUNTING_OFFICER, "Accounting Officer")
		self.assertEqual((waiting["due"], waiting["destination"]["route"]), (None, ["tenders", doc.tender_reference, "evaluation"]))
		secretary_wait = self.one(AO, he.WAITING, "secretary:waiting")
		self.holders(secretary_wait["action"], "Waiting for ", " to assign the evaluation secretary", people.HEAD_OF_PROCUREMENT, "a Head of Procurement Function")
		self.h_appoint()
		self.assertNotIn("appoint:waiting", self.ids(HOP, he.WAITING))
		self.assign_secretary()
		self.assertNotIn("secretary:waiting", self.ids(AO, he.WAITING))

	def test_the_accounting_officer_waits_for_the_members_who_have_not_declared(self):
		self.prep()
		self.h_appoint()
		appointed = roster.current_appointment(self.case)
		waiting = self.one(AO, he.WAITING, f"declare:waiting:{appointed.name}")
		self.assertEqual((waiting["action"], waiting["holder"], waiting["since"]), ("Waiting for the committee members to declare their interests", "Committee members", appointed.appointed_at))
		self.declare(CHAIR)
		waiting = self.one(AO, he.WAITING, f"declare:waiting:{appointed.name}")
		self.assertEqual(waiting["action"], f"Waiting for {self.name_of(MEMBER)} and {self.name_of(MEMBER_2)} to declare their interests")
		self.declare(MEMBER, MEMBER_2)
		self.assertEqual([r for r in self.ids(AO, he.WAITING) if r.startswith("declare")], [])

	def test_a_clarification_the_chair_awaits_names_the_secretary_then_the_supplier_with_the_reply_deadline(self):
		self.review()
		request = self.authorise_clarification()
		authorised = frappe.get_doc("Evaluation Clarification", request)
		to_send = self.one(CHAIR, he.WAITING, f"send:waiting:{request}")
		self.assertEqual((to_send["action"], to_send["holder"], to_send["since"]), (f"Waiting for {self.name_of(SECRETARY)} to send the clarification", self.name_of(SECRETARY), authorised.authorised_at))
		send = self.one(SECRETARY, he.MY_WORK, f"send:{request}")
		self.assertEqual((send["action"], send["entered_at"], send["destination"]["route"]), ("Send clarification", authorised.authorised_at, ["tenders", self.reference, "evaluation", "clarifications", request]))
		clarification.send(tender=self.name, clarification=request, idempotency_key=key(), user=SECRETARY)
		sent = frappe.get_doc("Evaluation Clarification", request)
		for user in (CHAIR, SECRETARY, MEMBER, MEMBER_2):
			reply = self.one(user, he.WAITING, f"reply:waiting:{request}")
			self.assertEqual((reply["action"], reply["holder"], reply["since"], reply["due"]), (f"Waiting for {BIDDER} to reply to the clarification", BIDDER, sent.sent_at, sent.reply_deadline))
		for user in (AO, HOP):  # who may not read bids is never told whom the committee waits for
			self.assertNotIn(f"reply:waiting:{request}", self.ids(user, he.WAITING))
			self.assertNotIn(BIDDER, json.dumps(self.region(user, he.WAITING) + self.region(user, he.MY_WORK), default=str))

	def test_the_suppliers_reply_is_never_waited_for_by_someone_who_may_not_read_bids(self):
		self.review()
		row = {"task_id": f"{self.case}:reply:waiting:CLR-X", "task_type": "bid_evaluation.reply", "title": f"Waiting for {BIDDER}'s reply", "reference": self.reference,
			"received_at": str(frappe.flags.kt_evl_clock), "route": ["tenders", self.reference, "evaluation"]}
		with mock.patch.object(my_work_provider, "my_work_rows", return_value={"assigned": [], "claimable": [], "waiting": [row]}):
			self.assertEqual(self.mine(self.region(AO, he.WAITING)), [])
			self.assertEqual(self.mine(self.region(HOP, he.WAITING)), [])

	def test_a_waiting_row_with_no_since_is_skipped(self):
		self.review()
		row = {"task_id": f"{self.case}:resolve-appointment:waiting:APT-X", "task_type": "bid_evaluation.resolve-appointment", "title": "Waiting for committee appointment",
			"reference": self.reference, "received_at": "", "route": ["tenders", self.reference, "evaluation"]}
		with mock.patch.object(my_work_provider, "my_work_rows", return_value={"assigned": [], "claimable": [], "waiting": [row]}):
			self.assertEqual(self.region(CHAIR, he.WAITING), [])

	def test_after_a_return_the_head_waits_for_the_corrected_report_and_the_committee_corrects_it(self):
		self.review()
		self.deliver()
		correction.return_report(tender=self.name, comment="Correct the page reference.", idempotency_key=key(), user=HOP)
		delivery = frappe.get_doc("Evaluation Report Delivery", frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": self.case}, "name"))
		waiting = self.one(HOP, he.WAITING, f"correct:waiting:{delivery.name}")
		self.assertEqual(waiting["action"], f"Waiting for {self.name_of(CHAIR)} or {self.name_of(SECRETARY)} to correct the evaluation report")
		self.assertEqual((waiting["since"], waiting["holder"]), (delivery.returned_at, f"{self.name_of(CHAIR)} or {self.name_of(SECRETARY)}"))
		for user in (CHAIR, SECRETARY):
			row = self.one(user, he.MY_WORK, f"correct:{delivery.name}")
			self.assertEqual((row["action"], row["entered_at"], row["destination"]["route"]), ("Correct evaluation report", delivery.returned_at, ["tenders", self.reference, "evaluation", "report"]))
			self.assertNotIn("page reference", json.dumps(row, default=str))  # the return comment is not repeated on Home

	# ----- Records you oversee -----

	def test_before_delivery_the_offices_and_a_contributing_department_are_told_only_that_the_committee_review_is_outstanding(self):
		self.review()
		appointed = roster.current_appointment(self.case)
		for user in (AO, HOP, HOD):
			row = self.one(user, he.OVERSIGHT, "review")
			self.assertEqual((row["action"], row["title"], row["reference"]), ("Committee review outstanding", self.evl_doc().tender_title, self.reference), user)
			self.assertEqual((row["outstanding"], row["since"], row["holder"], row["fact"], row["due"]), (True, appointed.appointed_at, "", "", None), user)
			self.assertEqual((row["root"], row["destination"]), (self.case, {"route": ["tenders", self.reference, "evaluation"], "route_options": {}}), user)
			self.assertEqual(row["action_id"], f"{self.case}:review")
			# nothing of the bids reaches them: no bidder, no count, no finding, no member
			text = json.dumps(row, default=str)
			for forbidden in (BIDDER, "Afya", "bid", "finding", "Meets", self.name_of(CHAIR), self.name_of(MEMBER)):
				self.assertNotIn(forbidden.lower(), text.lower(), (user, forbidden))
		self.h_freeze()  # a version being signed is not delivered
		for user in (AO, HOP, HOD):
			self.assertEqual(self.one(user, he.OVERSIGHT, "review")["since"], appointed.appointed_at)
			self.assertNotIn(BIDDER, json.dumps(self.region(user, he.OVERSIGHT), default=str))

	def test_before_the_committee_exists_the_review_is_outstanding_since_the_case_was_prepared(self):
		self.prep()
		doc = self.evl_doc()
		self.assertEqual(self.one(AO, he.OVERSIGHT, "review")["since"], doc.prepared_at or doc.creation)
		self.assertIn("appoint", self.ids(AO, he.MY_WORK))  # the held matter and the overseen one are different action ids
		self.assertNotEqual(self.one(AO, he.OVERSIGHT, "review")["action_id"], self.one(AO, he.MY_WORK, "appoint")["action_id"])
		frappe.db.set_value("Evaluation Case", self.case, "prepared_at", None, update_modified=False)
		self.assertEqual(self.one(AO, he.OVERSIGHT, "review")["since"], doc.creation)

	def test_oversight_never_carries_a_bid_into_a_home_read_before_delivery(self):
		self.review()
		self.authorise_clarification()
		at = get_datetime(frappe.flags.kt_evl_clock) + timedelta(days=2)
		for user in (AO, HOP, HOD):
			view = self.home(user, at)
			text = json.dumps(view, default=str)
			self.assertNotIn(BIDDER, text, user)
			self.assertNotIn("Afya", text, user)
			row = self.row(user, at, "oversight", "review")
			self.assertEqual((row["module"], row["action"], row["holder"]), ("Evaluation", "Committee review outstanding", ""))
			self.assertTrue(row["timing"].startswith("Outstanding 2 days (since "), row["timing"])

	def test_after_delivery_nothing_is_outstanding_and_a_return_for_correction_is(self):
		self.review()
		self.deliver()
		for user in (AO, HOP, HOD):
			self.assertEqual(self.mine(self.region(user, he.OVERSIGHT)), [], user)
			self.assertIsInstance(self.region(user, he.OVERSIGHT), list)
		correction.return_report(tender=self.name, comment="Correct the page reference.", idempotency_key=key(), user=HOP)
		delivery = oversight.deliveries(self.case)[0]
		for user in (AO, HOP, HOD):
			row = self.one(user, he.OVERSIGHT, "returned")
			self.assertEqual((row["action"], row["since"], row["outstanding"], row["holder"]), ("A corrected report is being prepared.", delivery.returned_at, True, ""), user)
			self.assertNotIn("page reference", json.dumps(row, default=str).lower(), user)  # the return reason is not repeated
			self.assertNotIn(BIDDER, json.dumps(row, default=str))
		self.assertEqual([r for r in self.ids(AO, he.OVERSIGHT) if r == "review"], [])

	def test_a_head_of_department_whose_unit_did_not_contribute_is_told_nothing_and_the_summary_is_not_asked(self):
		self.review()
		calls = []
		original = stage_summary.for_tender

		def watching(**kwargs):
			calls.append(kwargs["user"])
			return original(**kwargs)

		with mock.patch.object(stage_summary, "for_tender", watching):
			self.assertEqual(self.mine(self.region(HOD_OTHER, he.OVERSIGHT)), [])
			self.assertIsInstance(self.region(HOD_OTHER, he.OVERSIGHT), list)
		self.assertEqual(calls, [])  # the owner's read check refused the case first

	def test_a_stage_summary_that_failed_to_load_is_a_failed_read_not_an_empty_one(self):
		self.review()
		failed = [ss.unavailable(stage_summary.KEY, stage_summary.LABEL)]
		with mock.patch.object(stage_summary, "for_tender", return_value=failed):
			with self.assertRaises(RuntimeError):
				self.region(AO, he.OVERSIGHT)
			view = hw.get_workspace(AO, regions=[he.OVERSIGHT], providers=[entries], at=datetime(2027, 6, 1, 10, 0))
		self.assertEqual(view["regions"]["oversight"]["coverage"], hw.UNAVAILABLE)
		self.assertIsNone(view["regions"]["oversight"]["count"])  # never a zero

	def test_only_an_oversight_capable_responsibility_has_the_region(self):
		self.review()
		for user in (CHAIR, MEMBER, MEMBER_2, SECRETARY, AUDITOR, NOBODY, OUTSIDER, SUPPORT, "Administrator"):
			self.assertIsNone(self.region(user, he.OVERSIGHT), user)
		for user in (AO, HOP, HOD, HOD_OTHER):
			self.assertIsInstance(self.region(user, he.OVERSIGHT), list, user)

	# ----- Coming up -----

	def test_the_recorded_evaluation_deadline_is_coming_up_for_those_who_oversee_or_hold_the_evaluation(self):
		self.review()
		deadline = get_datetime(frappe.flags.kt_evl_clock) + timedelta(days=10)
		frappe.db.set_value("Evaluation Case", self.case, "evaluation_deadline", deadline, update_modified=False)
		for user in (AO, HOP, CHAIR, MEMBER, MEMBER_2, SECRETARY):
			row = self.one(user, he.COMING_UP, "deadline")
			self.assertEqual((row["action"], row["scheduled_at"], type(row["scheduled_at"])), ("Evaluation deadline", deadline, datetime), user)
			self.assertEqual((row["title"], row["reference"], row["region"]), (self.evl_doc().tender_title, self.reference, he.COMING_UP))
			self.assertEqual(row["destination"], {"route": ["tenders", self.reference, "evaluation"], "route_options": {}})
		for user in (AUDITOR, HOD, HOD_OTHER, NOBODY, OUTSIDER, SUPPORT, "Administrator"):
			self.assertIsNone(self.region(user, he.COMING_UP), user)
		at = deadline - timedelta(days=10)
		coming = self.row(AO, at, "coming_up", "deadline")
		self.assertEqual((coming["badge"], coming["module"], coming["action"]), ("In 10 days", "Evaluation", "Evaluation deadline"))
		self.assertEqual(coming["exact"], home_time.coming_up(deadline, at)[1])

	def test_a_missing_deadline_means_no_entry_and_the_deadline_comes_from_the_owners_dated_rules(self):
		self.review()
		self.assertEqual(self.mine(self.region(AO, he.COMING_UP)), [])  # none recorded: nothing guessed
		self.assertIsInstance(self.region(AO, he.COMING_UP), list)
		ruled = get_datetime(frappe.flags.kt_evl_clock) + timedelta(days=12)
		with mock.patch.object(timers, "dated", return_value={"evaluation_deadline": ruled}) as dated:
			self.assertEqual(self.one(CHAIR, he.COMING_UP, "deadline")["scheduled_at"], ruled)
		self.assertTrue(dated.called)

	def test_a_case_that_has_ended_has_no_deadline_to_come(self):
		self.review()
		deadline = get_datetime(frappe.flags.kt_evl_clock) + timedelta(days=10)
		frappe.db.set_value("Evaluation Case", self.case, "evaluation_deadline", deadline, update_modified=False)
		self.deliver()  # Report sent
		for user in (AO, HOP, CHAIR, SECRETARY):
			self.assertNotIn("deadline", self.ids(user, he.COMING_UP), user)
			self.assertIsInstance(self.region(user, he.COMING_UP), list)

	# ----- Recently completed actions -----

	def test_the_actors_own_appointment_secretary_report_and_return_are_completed_actions(self):
		self.review()
		appointed = roster.current_appointment(self.case)
		appointed_row = self.done(AO, appointed.name)
		self.assertEqual((appointed_row["action"], appointed_row["title"], appointed_row["completed_at"], appointed_row["reference"]),
			("Appointed evaluation committee", self.evl_doc().tender_title, appointed.appointed_at, self.reference))
		self.assertTrue(appointed_row["sentence"].startswith("You appointed the evaluation committee on ") and appointed_row["sentence"].endswith("."), appointed_row["sentence"])
		self.assertEqual(appointed_row["destination"], {"route": ["tenders", self.reference, "evaluation"], "route_options": {}})
		assigned = frappe.db.get_value("Evaluation Secretary Appointment", {"evaluation_case": self.case}, ["name", "assigned_at"], as_dict=True)
		head = self.done(HOP, assigned.name)
		self.assertEqual((head["action"], head["completed_at"]), ("Assigned evaluation secretary", assigned.assigned_at))
		self.assertTrue(head["sentence"].startswith("You assigned the evaluation secretary on "))
		for user in (CHAIR, MEMBER, SECRETARY, AUDITOR):  # nobody else did either
			self.assertEqual(self.mine(self.region(user, he.COMPLETED)), [], user)
		self.h_freeze()
		version = signing.signing_version(self.evl_doc())
		sent = self.done(SECRETARY, version.name)
		self.assertEqual((sent["action"], sent["completed_at"]), ("Sent report for signing", version.frozen_at))
		self.assertTrue(sent["sentence"].startswith("You sent the evaluation report for signing on "))
		self.h_sign(*MEMBERS)
		self.assertEqual(self.evl_doc().state, "Report sent")
		# the system's own delivery is not a person's action
		actions = {row["action"] for user in (AO, HOP, SECRETARY, *MEMBERS) for row in self.mine(self.region(user, he.COMPLETED))}
		self.assertEqual(actions, {"Appointed evaluation committee", "Assigned evaluation secretary", "Sent report for signing"})
		correction.return_report(tender=self.name, comment="Correct the page reference.", idempotency_key=key(), user=HOP)
		delivery = oversight.deliveries(self.case)[0]
		returned = self.done(HOP, delivery.name)
		self.assertEqual((returned["action"], returned["completed_at"]), ("Returned evaluation report", delivery.returned_at))
		self.assertTrue(returned["sentence"].startswith("You returned the evaluation report for correction on "))

	def test_the_awaiting_clause_names_who_signing_awaits_only_while_the_owners_answer_is_a_wait(self):
		self.review()
		self.h_freeze()
		version = signing.signing_version(self.evl_doc())
		sent = self.done(SECRETARY, version.name)
		self.assertTrue(sent["sentence"].endswith(" It is awaiting signatures by the committee members."), sent["sentence"])
		self.h_sign(CHAIR)
		sent = self.done(SECRETARY, version.name)
		self.assertTrue(sent["sentence"].endswith(f" It is awaiting signatures by {self.name_of(MEMBER)} and {self.name_of(MEMBER_2)}."), sent["sentence"])
		appointed = roster.current_appointment(self.case)
		self.assertNotIn("awaiting", self.done(AO, appointed.name)["sentence"])  # only the action the owner's wait follows
		self.h_sign(MEMBER, MEMBER_2)
		self.assertNotIn("awaiting", self.done(SECRETARY, version.name)["sentence"])  # the report is sent: nothing awaited

	def test_the_thirty_day_cutoff_is_the_providers_own_and_the_core_window_drops_older_actions(self):
		self.review()
		appointed = roster.current_appointment(self.case)
		frappe.db.set_value("Evaluation Appointment", appointed.name, "appointed_at", home_time.now() - timedelta(days=45), update_modified=False)
		self.assertNotIn(appointed.name, [row["action_id"] for row in self.region(AO, he.COMPLETED)])
		frappe.db.set_value("Evaluation Appointment", appointed.name, "appointed_at", home_time.now() - timedelta(days=5), update_modified=False)
		self.assertIn(appointed.name, [row["action_id"] for row in self.region(AO, he.COMPLETED)])
		instant = get_datetime(frappe.db.get_value("Evaluation Appointment", appointed.name, "appointed_at"))
		inside = [row for row in self.all_rows(AO, instant + timedelta(days=1), "completed") if row["key"].endswith(appointed.name)]
		outside = [row for row in self.all_rows(AO, instant + timedelta(days=45), "completed") if row["key"].endswith(appointed.name)]
		self.assertEqual((len(inside), len(outside)), (1, 0))

	def test_an_actor_who_can_no_longer_read_the_case_sees_nothing_of_it_in_completed(self):
		self.review()
		self.assertTrue(self.mine(self.region(AO, he.COMPLETED)))
		denied = {**reads.access(self.evl_doc(), AO), "read": False}
		with mock.patch.object(reads, "access", return_value=denied):
			self.assertEqual(self.mine(self.region(AO, he.COMPLETED)), [])
			self.assertIsInstance(self.region(AO, he.COMPLETED), list)

	# ----- applicability, personas, technical readers -----

	def test_none_versus_empty_by_responsibility(self):
		self.prep()
		for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
			for user in (NOBODY, OUTSIDER, HOD, SUPPORT):
				self.assertIsNone(self.region(user, region), (user, region))
			for user in (AO, HOP, AUDITOR):
				self.assertIsInstance(self.region(user, region), list, (user, region))
		self.assertEqual(self.mine(self.region(AUDITOR, he.MY_WORK)), [])
		# a seat is a responsibility here: the committee has the regions only once appointed
		self.assertIsNone(self.region(CHAIR, he.MY_WORK))
		self.h_appoint()
		self.assign_secretary()
		for user in (*MEMBERS, SECRETARY):
			self.assertIsInstance(self.region(user, he.MY_WORK), list, user)
			self.assertIsInstance(self.region(user, he.WAITING), list, user)
		self.assertIsNone(self.region(HOD, he.COMING_UP))
		self.assertIsInstance(self.region(CHAIR, he.COMING_UP), list)

	def test_the_technical_reader_and_an_unrelated_internal_user_get_nothing(self):
		self.review()
		for user in ("Administrator", NOBODY, OUTSIDER, SUPPORT):
			for region in he.REGIONS:
				self.assertIsNone(self.region(user, region), (user, region))
		at = datetime(2027, 6, 1, 10, 0)
		view = self.home("Administrator", at)
		self.assertEqual((view["empty"], view["regions"]["my_work"]["entries"]), (True, []))
		nobody = self.home(NOBODY, at)
		self.assertEqual(nobody["state"], "ready")
		self.assertFalse(any(region["entries"] for region in nobody["regions"].values()))
		self.assertEqual({region["coverage"] for region in nobody["regions"].values()}, {hw.NOT_APPLICABLE})

	def test_a_user_without_the_responsibility_sees_none_of_it_and_a_revoked_responsibility_removes_it(self):
		self.prep()
		at = get_datetime(frappe.flags.kt_evl_clock) + timedelta(hours=1)
		administration.grant(user=EXTRA, business_role="Accounting Officer", fixture_namespace=EXTRA_NS, actor="Administrator")
		self.addCleanup(_remove_extra)
		self.assertEqual(self.row(EXTRA, at, "my_work", "appoint")["action"], "Appoint the evaluation committee")
		self.assertEqual(self.row(EXTRA, at, "oversight", "review")["action"], "Committee review outstanding")
		self.assertTrue(self.home(EXTRA, at)["regions"]["my_work"]["applicable"])
		assignment = frappe.get_all("User Responsibility Assignment", filters={"user": EXTRA}, pluck="name")[0]
		administration.revoke(assignment, reason="Revoked inside the Home provider test.", actor="Administrator")
		revoked = self.home(EXTRA, at)
		self.assertEqual({region["coverage"] for region in revoked["regions"].values()}, {hw.NOT_APPLICABLE})
		self.assertFalse([row for region in revoked["regions"].values() for row in region["entries"] if row["reference"] == self.reference])
		for region in he.REGIONS:
			self.assertIsNone(self.region(EXTRA, region), region)

	def test_a_committee_member_who_is_removed_from_the_roster_loses_the_rows(self):
		self.prep()
		self.h_appoint()
		self.assertTrue(self.mine(self.region(MEMBER, he.MY_WORK)))
		frappe.db.set_value("Evaluation Committee Member", {"parent": roster.current_appointment(self.case).name, "member_user": MEMBER}, "status", "Replaced", update_modified=False)
		self.assertEqual(self.mine(self.region(MEMBER, he.MY_WORK)), [])
		self.assertIsNone(self.region(MEMBER, he.MY_WORK))

	# ----- writes, cost, destinations -----

	def test_the_provider_writes_nothing(self):
		self.review()
		request = self.authorise_clarification()
		clarification.send(tender=self.name, clarification=request, idempotency_key=key(), user=SECRETARY)
		deadline = get_datetime(frappe.flags.kt_evl_clock) + timedelta(days=10)
		frappe.db.set_value("Evaluation Case", self.case, "evaluation_deadline", deadline, update_modified=False)
		before = frappe.db.transaction_writes
		for user in (AO, HOP, SECRETARY, *MEMBERS, AUDITOR, HOD, HOD_OTHER, NOBODY, OUTSIDER, SUPPORT, "Administrator"):
			for region in he.REGIONS:
				self.region(user, region)
		self.assertEqual(frappe.db.transaction_writes, before)

	def test_the_scan_runs_once_per_home_read(self):
		self.review()
		work, summaries = [], []
		original_work, original_summary = my_work_provider.my_work_rows, stage_summary.for_tender

		def counting_work(user):
			work.append(user)
			return original_work(user)

		def counting_summary(**kwargs):
			summaries.append((kwargs["tender"], kwargs["user"]))
			return original_summary(**kwargs)

		with mock.patch.object(my_work_provider, "my_work_rows", counting_work), mock.patch.object(stage_summary, "for_tender", counting_summary):
			self.home(AO, datetime(2027, 6, 1, 10, 0))
		self.assertEqual(work, [AO])
		self.assertEqual(len(summaries), len(set(summaries)))  # one summary per case per read

	def test_every_destination_opens_a_real_page_the_actor_may_open(self):
		self.assertTrue(frappe.db.exists("Page", "tenders"))
		self.review()
		request = self.authorise_clarification()
		clarification.send(tender=self.name, clarification=request, idempotency_key=key(), user=SECRETARY)
		frappe.db.set_value("Evaluation Case", self.case, "evaluation_deadline", get_datetime(frappe.flags.kt_evl_clock) + timedelta(days=3), update_modified=False)
		seen = set()
		for user in (AO, HOP, SECRETARY, *MEMBERS, HOD):
			for region in he.REGIONS:
				for row in self.mine(self.region(user, region)):
					seen.add(row["destination"]["route"][0])
					self.assertTrue(hw._page_permitted(row["destination"]["route"][0], user), (user, row["destination"]))
		self.assertEqual(seen, {"tenders"})

	# ----- through the Home read -----

	def test_the_accounting_officers_home_renders_the_row_with_the_owners_timing(self):
		self.prep()
		doc = self.evl_doc()
		entered = doc.prepared_at or doc.creation
		at = get_datetime(entered) + timedelta(days=2)
		row = self.row(AO, at, "my_work", "appoint")
		self.assertEqual((row["module"], row["action"], row["title"], row["reference"]), ("Evaluation", "Appoint the evaluation committee", doc.tender_title, doc.tender_reference))
		self.assertEqual(row["timing"], home_time.entered("Received", entered, at))
		self.assertTrue(row["timing"].startswith("Received 2 days ago ("), row["timing"])
		waiting = self.row(HOP, at, "waiting", "appoint:waiting")
		self.assertEqual(waiting["timing"], home_time.waiting(entered, at))
		self.assertTrue(waiting["timing"].startswith("Waiting 2 days (since "), waiting["timing"])
