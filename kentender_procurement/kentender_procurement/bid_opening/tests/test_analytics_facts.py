# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1 — Bid Opening's facts for Procurement Analytics (`bid_opening/services/analytics_facts.py`; plan Phase 2C, FU-ANL-06).

One opening world for the whole module: the published Tender and its prepared case are built once (in `setUpClass`), as the
Home provider's tests do. Each test then sets the case fields the owner's ceremony would have written (state, outcome, completion
instant) inside a transaction that is rolled back afterwards, so every test starts from the prepared case; the ceremony itself is
proven by the ceremony tests, not here. The read only reads. The world and every row it adds are removed at the end and counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.bid_opening.tests.test_analytics_facts
"""

from __future__ import annotations

from datetime import datetime

import frappe

from kentender_procurement.bid_opening.services import records
from kentender_procurement.bid_opening.services.analytics_facts import facts_for
from kentender_procurement.bid_opening.tests.support import AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER, NS, OUTSIDER, SUPPORT, OpeningCase
from kentender_procurement.tenders.tests import fixtures as tender_fx
from kentender_procurement.tenders.tests.test_open_period import OpenPeriodCase

AT = datetime(2027, 6, 19, 10, 0)
COMPLETED = datetime(2027, 6, 12, 15, 30, 5)
WORLD_FLAGS = ("kt_supplier_account_provider", "kt_tender_candidate_registry", "kt_bds_fixture_namespace", "kt_bop_fixture_namespace", "kt_prc_fixture_namespace",
	"kt_bds_clock", "kt_tenders_clock", "kt_bop_clock", "kt_prc_clock")
WORLD: dict = {"attrs": {}, "flags": {}}
OPENING_ROWS = ("Bid Opening Case", "Opening Committee Appointment", "Opening Arrangement", "Opening Command Journal")
ACTORS = (AO, CHAIR, MEMBER, INDEPENDENT, AUDITOR, OUTSIDER, SUPPORT, "Administrator")


def _assert_nothing_left() -> None:
	"""Runs last (registered first): the world and its rows are gone."""
	left = {doctype: frappe.db.count(doctype, {"fixture_namespace": NS}) for doctype in OPENING_ROWS if frappe.get_meta(doctype).has_field("fixture_namespace")}
	left["Tender"] = frappe.db.count("Tender", {"fixture_namespace": tender_fx.NS})
	if any(left.values()):
		raise AssertionError(f"Bid Opening Analytics test rows left behind: {left}")


class TestBidOpeningAnalyticsFacts(OpeningCase):
	@classmethod
	def setUpClass(cls):
		cls.addClassCleanup(_assert_nothing_left)
		super().setUpClass()
		builder = cls("test_a_prepared_opening_has_a_status_and_nothing_else")
		OpeningCase.setUp(builder)  # the ordinary opening-world setup, once: a published Tender, its sealed box, the trusted clocks
		builder.prepare_case()
		frappe.db.commit()
		cls.addClassCleanup(builder.doCleanups)
		WORLD["attrs"] = {k: v for k, v in builder.__dict__.items() if not k.startswith("_")}
		WORLD["flags"] = {k: frappe.flags.get(k) for k in WORLD_FLAGS}
		WORLD["conf"] = frappe.conf.get("kt_bds_simulation_environment")

	def setUp(self):
		super(OpenPeriodCase, self).setUp()  # IntegrationTestCase's own, not the per-test world the base classes build
		frappe.set_user("Administrator")
		self.__dict__.update(WORLD["attrs"])
		for flag, value in WORLD["flags"].items():
			frappe.flags[flag] = value
		frappe.conf["kt_bds_simulation_environment"] = WORLD["conf"]
		self.addCleanup(frappe.set_user, "Administrator")
		self.addCleanup(frappe.db.rollback)  # whatever a test writes is gone; the prepared case stays
		for flag in ("kt_bds_clock", "kt_tenders_clock", "kt_bop_clock", "kt_prc_clock"):
			self.addCleanup(frappe.flags.__setitem__, flag, WORLD["flags"].get(flag))

	# ----- helpers -----

	def facts(self, user: str = "Administrator", tenders: list[str] | None = None) -> dict:
		return facts_for(user=user, tender_names=tenders if tenders is not None else [self.name], at=AT)

	def mine(self, user: str = "Administrator") -> dict:
		return self.facts(user)[self.name]

	def case(self) -> str:
		return records.case_for(self.name)

	def ended(self, state: str, outcome: str = "", completed_at=None) -> None:
		frappe.db.set_value(records.CASE, self.case(), {"state": state, "outcome": outcome, "completed_at": completed_at})

	# ----- the facts -----

	def test_a_prepared_opening_has_a_status_and_nothing_else(self):
		row = self.mine()
		self.assertEqual(row, {"opening_complete_at": None, "outcome": None, "status": frappe.db.get_value(records.CASE, self.case(), "state")})
		self.assertEqual(set(row), {"opening_complete_at", "outcome", "status"})  # no bid count, no sealed content, no bidder identity

	def test_a_completed_nonempty_opening_gives_its_completion_instant(self):
		self.ended("Opening complete", "Bids opened", COMPLETED)
		row = self.mine()
		self.assertEqual(row, {"opening_complete_at": COMPLETED, "outcome": "Bids opened", "status": "Complete"})
		self.assertIsInstance(row["opening_complete_at"], datetime)
		self.assertIsNone(row["opening_complete_at"].tzinfo)

	def test_an_empty_opening_has_the_outcome_and_no_transition_start(self):
		self.ended("Opening complete", "No bids", COMPLETED)
		self.assertEqual(self.mine(), {"opening_complete_at": None, "outcome": "No bids", "status": "Complete"})

	def test_an_opening_that_is_not_final_has_no_outcome_even_when_one_is_already_recorded(self):
		for state, status in (("Opening", "In session"), ("Interrupted", "Paused"), ("Readout complete", "Readout complete"), ("Awaiting attestations", "Awaiting attestations")):
			self.ended(state, "Bids opened")  # the ceremony records the outcome before the opening is final
			self.assertEqual(self.mine(), {"opening_complete_at": None, "outcome": None, "status": status}, state)
		self.ended("Opening", "No bids")  # an empty box is known at the start, but the opening is not final until it is complete
		self.assertEqual(self.mine()["outcome"], None)

	def test_an_opening_not_held_or_ended_by_cancellation_has_no_outcome(self):
		self.ended("Not held")
		self.assertEqual(self.mine(), {"opening_complete_at": None, "outcome": None, "status": "Did not take place"})
		self.ended("Cancelled after start", "Bids opened")
		self.assertEqual(self.mine(), {"opening_complete_at": None, "outcome": None, "status": "Ended — Tender cancelled"})

	def test_every_actor_gets_the_same_facts_technical_readers_included(self):
		self.ended("Opening complete", "Bids opened", COMPLETED)
		expected = self.mine()
		for user in ACTORS:
			self.assertEqual(self.mine(user), expected, user)
		self.assertEqual(expected["opening_complete_at"], COMPLETED)  # `stage_summary` would give the Technical Operator the status only

	def test_a_tender_with_no_case_is_omitted_and_a_duplicate_name_reads_once(self):
		self.assertEqual(list(self.facts(tenders=[self.name, "TND-NO-SUCH-TENDER", "", self.name])), [self.name])
		self.assertEqual(self.facts(tenders=["TND-NO-SUCH-TENDER"]), {})
		self.assertEqual(self.facts(tenders=[]), {})

	def test_a_completed_bids_opened_case_without_a_completion_instant_is_a_failed_read(self):
		self.ended("Opening complete", "Bids opened", None)
		with self.assertRaises(ValueError):
			self.mine()

	def test_the_read_creates_and_marks_nothing(self):
		self.ended("Opening complete", "Bids opened", COMPLETED)
		tables = [*OPENING_ROWS, "Opening Entry", "Audit Event", "Notification Log", "Version", "Proceeding Event", "Support Issue"]
		before = {table: frappe.db.count(table) for table in tables if frappe.db.table_exists(table)}
		stamp = frappe.db.get_value(records.CASE, self.case(), ["modified", "record_version"])
		for user in ACTORS:
			self.mine(user)
		self.assertEqual({table: frappe.db.count(table) for table in before}, before)
		self.assertEqual(frappe.db.get_value(records.CASE, self.case(), ["modified", "record_version"]), stamp)
