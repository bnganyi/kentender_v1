# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1 — Bid Evaluation's facts for Procurement Analytics (`bid_evaluation/services/analytics_facts.py`; plan Phase 2C, FU-ANL-06).

Uses the module's shared evaluation world (the published Tender, the bid and the completed opening are built once; every test starts
from a clean evaluation, as the other Bid Evaluation tests do) and moves the case on with the owner's own commands. The read only
reads. The case states a ceremony cannot reach cheaply (no bids, cancelled) are set directly on the case. The world and every row it
adds are removed at the end and counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.bid_evaluation.tests.test_analytics_facts
"""

from __future__ import annotations

import json
import re
import unittest
from datetime import datetime, timedelta

import frappe

from kentender_procurement.bid_evaluation.services import appointment, correction, declaration, oversight, people, preparation, records, report, roster, secretary, signing
from kentender_procurement.bid_evaluation.services.analytics_facts import facts_for
from kentender_procurement.bid_evaluation.tests.support import AO, AUDITOR, CHAIR, HOP, MEMBER, MEMBER_2, NS, OUTSIDER, ROSTER, SECRETARY, SUPPORT, EvaluationCase
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.tenders.tests import fixtures as tender_fx

AT = datetime(2027, 6, 19, 10, 0)
BIDDER = "Afya Digital Supplies Limited"
MEMBERS = (CHAIR, MEMBER, MEMBER_2)
ACTORS = (AO, HOP, AUDITOR, OUTSIDER, SUPPORT, tender_fx.NOBODY, "Administrator")
EVALUATION_ROWS = ("Evaluation Case", "Evaluation Appointment", "Evaluation Secretary Appointment", "Evaluation Report Version", "Evaluation Report Delivery",
	"Evaluation Command Journal", "Evaluation Source Event", "Evaluation Source Intake")


def _assert_nothing_left() -> None:
	"""Runs last (registered first): the world and its rows are gone."""
	left = {doctype: frappe.db.count(doctype, {"fixture_namespace": NS}) for doctype in EVALUATION_ROWS if frappe.get_meta(doctype).has_field("fixture_namespace")}
	left["Tender"] = frappe.db.count("Tender", {"fixture_namespace": tender_fx.NS})
	if any(left.values()):
		raise AssertionError(f"Bid Evaluation Analytics test rows left behind: {left}")


class TestEvaluationAnalyticsFacts(EvaluationCase):
	@classmethod
	def setUpClass(cls):
		unittest.addModuleCleanup(_assert_nothing_left)
		super().setUpClass()

	# ----- helpers -----

	def facts(self, user: str = "Administrator", tenders: list[str] | None = None) -> dict:
		return facts_for(user=user, tender_names=tenders if tenders is not None else [self.name], at=AT)

	def mine(self, user: str = "Administrator") -> dict:
		return self.facts(user)[self.name]

	def prep(self) -> str:
		self.case = preparation.ensure_preparation(tender=self.name)["evaluation"]
		return self.case

	def evl_doc(self):
		return frappe.get_doc("Evaluation Case", self.case)

	def evl_version(self) -> int:
		return int(frappe.db.get_value("Evaluation Case", self.case, "record_version"))

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

	def name_of(self, user: str) -> str:
		return people.full_name(user)

	def extra_delivery(self, n: int, status: str, delivered_at: str):
		first = oversight.deliveries(self.case)[0] if status == "Delivered" else frappe.get_all("Evaluation Report Delivery", filters={"evaluation_case": self.case}, fields=["*"])[0]
		return records.insert(frappe.get_doc({"doctype": "Evaluation Report Delivery", "delivery_id": f"{self.case}-ANL-DLV-{n}", "evaluation_case": self.case,
			"report_version": first.report_version, "delivery_key": f"{self.case}:anl-test-{n}", "recipient_user": HOP, "status": status, "attempts": 1,
			"delivered_at": delivered_at, "review_state": "Open"}))

	# ----- the shape and the omissions -----

	def test_a_tender_with_no_case_is_omitted_and_nothing_is_returned_for_no_names(self):
		self.assertEqual(self.facts(), {})
		self.prep()
		self.assertEqual(list(self.facts(tenders=[self.name, "TND-NO-SUCH-TENDER", "", self.name])), [self.name])
		self.assertEqual(self.facts(tenders=["TND-NO-SUCH-TENDER"]), {})
		self.assertEqual(self.facts(tenders=[]), {})

	def test_a_prepared_case_waits_for_its_committee_from_the_preparation_instant(self):
		self.prep()
		doc = self.evl_doc()
		row = self.mine()
		self.assertEqual(set(row), {"case_state", "no_evaluation_required", "report_sent_at", "opening_completed_at", "outstanding", "position"})
		self.assertEqual((row["case_state"], row["no_evaluation_required"], row["report_sent_at"]), ("Preparing", False, None))
		self.assertEqual(row["opening_completed_at"], get_dt(doc.opening_completed_at))
		holders = people.holders(people.ACCOUNTING_OFFICER)
		holder = " or ".join(self.name_of(u) for u in holders) if 0 < len(holders) <= 2 else people.ACCOUNTING_OFFICER
		self.assertEqual(row["position"], "committee not yet appointed")
		self.assertEqual(row["outstanding"], {"text": "The evaluation committee has not been appointed.", "holder": holder, "since": doc.prepared_at or doc.creation})
		frappe.db.set_value("Evaluation Case", self.case, "prepared_at", None, update_modified=False)  # Home's own fallback: the case's creation
		self.assertEqual(self.mine()["outstanding"]["since"], doc.creation)

	# ----- committee review -----

	def test_committee_review_is_outstanding_from_when_the_checks_ran_and_the_committee_existed(self):
		self.review()
		doc = self.evl_doc()
		intake = frappe.db.get_value("Evaluation Source Intake", doc.source_intake, "received_at")
		appointed = roster.current_appointment(self.case).appointed_at
		row = self.mine()
		self.assertEqual((row["case_state"], row["no_evaluation_required"], row["report_sent_at"]), ("Reviewing", False, None))
		self.assertEqual(row["opening_completed_at"], get_dt(doc.opening_completed_at))
		self.assertIsNotNone(row["opening_completed_at"])
		self.assertEqual(row["outstanding"]["text"], f"Automatic checks complete; committee review outstanding. {self.name_of(CHAIR)} chairs the appointed committee.")
		self.assertEqual(row["outstanding"]["holder"], self.name_of(CHAIR))
		self.assertEqual(row["position"], "automatic checks complete; committee review outstanding")
		self.assertEqual(row["outstanding"]["since"], max(get_dt(intake), get_dt(appointed)))  # the raw instant, not a display string
		self.assertIsInstance(row["outstanding"]["since"], datetime)
		self.assertIsNone(re.search(r"\d", row["outstanding"]["text"]))  # no instant in the owner's words
		self.assertNotIn(BIDDER.lower(), json.dumps(row, default=str).lower())  # no supplier, finding or score

	def test_every_actor_gets_the_same_facts_technical_readers_included(self):
		self.review()
		expected = self.mine()
		for user in ACTORS:
			self.assertEqual(self.mine(user), expected, user)
		self.assertIsNotNone(expected["outstanding"])

	# ----- signing, delivery -----

	def test_waiting_for_signatures_is_outstanding_from_the_freeze(self):
		self.review()
		self.h_freeze()
		doc = self.evl_doc()
		self.assertEqual(doc.state, "Signing")
		frozen = signing.signing_version(doc)
		row = self.mine()
		self.assertEqual((row["case_state"], row["report_sent_at"], row["position"]), ("Signing", None, "waiting for the report to be signed"))
		pending = [s["member"] for s in signing.signatures(frozen) if not s["signed_at"]]
		self.assertEqual(row["outstanding"]["text"], f"Waiting for {_names(pending, self.name_of)} to sign report {frozen.version_number}.")
		self.assertEqual(row["outstanding"]["since"], get_dt(frozen.frozen_at))
		self.h_sign(CHAIR)
		after = self.mine()["outstanding"]
		self.assertNotIn(self.name_of(CHAIR), after["text"])
		self.assertEqual(after["since"], get_dt(frozen.frozen_at))

	def test_a_delivered_report_gives_the_report_sent_instant_and_no_outstanding_matter(self):
		self.review()
		self.deliver()
		delivered = oversight.deliveries(self.case)[0].delivered_at
		row = self.mine()
		self.assertEqual((row["case_state"], row["report_sent_at"], row["outstanding"]), ("Report sent", get_dt(delivered), None))
		self.assertEqual(row["position"], "")  # delivery already reached Award, which took the report up (review state With Award)
		self.assertEqual(oversight.deliveries(self.case)[0].review_state, "With Award")
		frappe.db.set_value("Evaluation Report Delivery", oversight.deliveries(self.case)[0].name, "review_state", "Open")  # as before Award's receipt
		self.assertEqual(self.mine()["position"], "report delivered — Award receipt pending")
		self.assertIsNone(row["report_sent_at"].tzinfo)

	def test_the_report_sent_instant_is_the_earliest_delivered_one_and_other_deliveries_do_not_count(self):
		self.review()
		self.deliver()
		first = get_dt(oversight.deliveries(self.case)[0].delivered_at)
		self.extra_delivery(1, "Delivered", str(first + timedelta(days=3)))  # a later corrected report
		self.extra_delivery(2, "Failed", str(first - timedelta(days=5)))  # never delivered
		self.extra_delivery(3, "Pending", str(first - timedelta(days=6)))
		self.assertEqual(self.mine()["report_sent_at"], first)
		earlier = first - timedelta(hours=2)
		self.extra_delivery(4, "Delivered", str(earlier))
		self.assertEqual(self.mine()["report_sent_at"], earlier)

	def test_a_report_returned_for_correction_keeps_its_report_sent_instant_and_is_outstanding_from_the_return(self):
		self.review()
		self.deliver()
		sent = get_dt(oversight.deliveries(self.case)[0].delivered_at)
		correction.return_report(tender=self.name, comment="Correct the page reference.", idempotency_key=key(), user=HOP)
		returned = oversight.deliveries(self.case)[0].returned_at
		row = self.mine()
		self.assertEqual((row["case_state"], row["report_sent_at"], row["position"]), ("Reviewing", sent, "report returned for correction"))
		self.assertEqual(row["outstanding"], {"text": "A corrected report is being prepared.",
			"holder": f"{self.name_of(CHAIR)} or {self.name_of(SECRETARY)}", "since": get_dt(returned)})
		self.assertNotIn("page reference", json.dumps(row, default=str).lower())  # the return reason is not repeated

	# ----- the other case states -----

	def test_no_evaluation_required_and_a_cancelled_case_have_no_outstanding_matter(self):
		self.prep()
		frappe.db.set_value("Evaluation Case", self.case, "state", "No evaluation required", update_modified=False)
		self.assertEqual((self.mine()["case_state"], self.mine()["no_evaluation_required"], self.mine()["outstanding"], self.mine()["report_sent_at"]),
			("No evaluation required", True, None, None))
		self.assertEqual(self.mine()["position"], "no bids were received")
		frappe.db.set_value("Evaluation Case", self.case, "state", "Cancelled", update_modified=False)
		self.assertEqual((self.mine()["case_state"], self.mine()["no_evaluation_required"], self.mine()["outstanding"]), ("Cancelled", False, None))
		self.assertEqual(self.mine()["position"], "evaluation ended")

	def test_a_recorded_suspension_is_outstanding_from_when_it_was_received(self):
		self.review()
		doc = self.evl_doc()
		event = records.insert(frappe.get_doc({"doctype": "Evaluation Source Event", "source_event_id": f"{doc.name}-SE-ANL", "evaluation_case": doc.name,
			"event_key": f"anl-suspend:{doc.name}", "source": "Simulation", "kind": "Suspension", "instruction_reference": "MOH/REVIEW/TEST-ANL", "authority": AO,
			"received_at": "2027-06-11 08:55:00", "permitted_actions_json": "[]"}))
		records.bump(doc, suspended=1, suspension_event=event.name)
		self.assertEqual(self.mine()["outstanding"], {"text": "Evaluation is paused by the recorded instruction.", "holder": self.name_of(AO),
			"since": datetime(2027, 6, 11, 8, 55)})
		self.assertEqual(self.mine()["position"], "paused by the recorded instruction")

	def test_a_matter_with_no_recorded_instant_is_none_not_invented(self):
		self.review()
		doc = self.evl_doc()
		frappe.db.set_value("Evaluation Case", self.case, "suspended", 1, update_modified=False)  # suspended, with no event recorded
		self.assertIsNone(doc.suspension_event)
		self.assertIsNone(self.mine()["outstanding"])

	def test_a_case_appointed_before_the_opening_is_taken_up_waits_for_the_opening(self):
		self.review()
		frappe.db.set_value("Evaluation Case", self.case, {"state": "Preparing", "source_intake": ""}, update_modified=False)
		self.assertEqual(self.mine()["position"], "waiting for the opening to complete")

	# ----- reading changes nothing -----

	def test_the_read_creates_and_marks_nothing(self):
		self.review()
		self.deliver()
		tables = [*EVALUATION_ROWS, "Audit Event", "Notification Log", "Version", "Support Issue", "Evaluation Source Event", "Evaluation Check Run", "Evaluation Bid"]
		before = {table: frappe.db.count(table) for table in tables}
		stamp = frappe.db.get_value("Evaluation Case", self.case, ["modified", "record_version"])
		for user in ACTORS:
			self.mine(user)
		self.assertEqual({table: frappe.db.count(table) for table in tables}, before)
		self.assertEqual(frappe.db.get_value("Evaluation Case", self.case, ["modified", "record_version"]), stamp)


def get_dt(value):
	from frappe.utils import get_datetime

	return get_datetime(value) if value else None


def _names(users: list[str], full_name) -> str:
	shown = [full_name(u) for u in users]
	return shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + " and " + shown[-1] if shown else ""
