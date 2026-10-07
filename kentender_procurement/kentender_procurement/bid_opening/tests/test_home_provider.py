# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — the Bid Opening feed to Home (`bid_opening/services/home_provider.py`).

One opening world for the whole module: the published Tender and its prepared case are built once (in `setUpClass`), and each test
moves the case on with the owner's own commands (appoint, publish) or inserts journal rows inside a transaction that is rolled back
afterwards, so every test starts from the prepared case. The provider only reads. The world and every row it adds are removed at the
end and counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.bid_opening.tests.test_home_provider
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest import mock

import frappe
from kentender_core.services.command_write_guard import purge_doc
from frappe.tests import IntegrationTestCase
from frappe.utils import get_datetime

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import home_workspace as hw
from kentender_core.services import next_step as ns
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.bid_opening.services import appointment, home_provider, my_work_provider, next_steps, people, records
from kentender_procurement.bid_opening.services.home_provider import entries
from kentender_procurement.bid_opening.tests.support import AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER, NS, OUTSIDER, SUPPORT, OpeningCase
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.tenders.tests import fixtures as tender_fx
from kentender_procurement.tenders.tests.test_open_period import OpenPeriodCase

NOBODY = tender_fx.NOBODY
EXTRA = "bopt.home.extra@example.test"  # a second Accounting Officer, granted and revoked inside one test
EXTRA_NS = "KT_TEST_BOPHOME"
WORLD_FLAGS = ("kt_supplier_account_provider", "kt_tender_candidate_registry", "kt_bds_fixture_namespace", "kt_bop_fixture_namespace", "kt_prc_fixture_namespace",
	"kt_bds_clock", "kt_tenders_clock", "kt_bop_clock", "kt_prc_clock")
WORLD: dict = {"attrs": {}, "flags": {}}
OPENING_ROWS = ("Bid Opening Case", "Opening Committee Appointment", "Opening Arrangement", "Opening Command Journal")


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
	left = {doctype: frappe.db.count(doctype, {"fixture_namespace": NS}) for doctype in OPENING_ROWS if frappe.get_meta(doctype).has_field("fixture_namespace")}
	left["Tender"] = frappe.db.count("Tender", {"fixture_namespace": tender_fx.NS})
	left["extra user"] = int(bool(frappe.db.exists("User", EXTRA)))
	if any(left.values()):
		raise AssertionError(f"Bid Opening Home test rows left behind: {left}")


class TestBidOpeningHomeProvider(OpeningCase):
	@classmethod
	def setUpClass(cls):
		cls.addClassCleanup(_assert_nothing_left)
		super().setUpClass()
		cls.addClassCleanup(_remove_extra)
		tender_fx._user(EXTRA, "BOPT Extra Accounting Officer")
		builder = cls("test_none_versus_empty_by_responsibility")
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
		home_support.reset()
		self.addCleanup(frappe.set_user, "Administrator")
		self.addCleanup(frappe.db.rollback)  # whatever a test appoints, publishes or inserts is gone; the prepared case stays
		for flag in ("kt_bds_clock", "kt_tenders_clock", "kt_bop_clock", "kt_prc_clock"):
			self.addCleanup(frappe.flags.__setitem__, flag, WORLD["flags"].get(flag))

	# ----- helpers -----

	def region(self, user: str, region: str):
		home_support.reset()
		return entries(user=user, region=region)

	def case(self) -> str:
		return records.case_for(self.name)

	def doc(self):
		return frappe.get_doc(records.CASE, self.case())

	def mine(self, rows):
		"""The rows about this world's case (the test site also holds the canonical opening)."""
		return [row for row in rows or [] if row["root"] == self.case()]

	def one(self, user: str, region: str, action_id: str) -> dict:
		rows = [row for row in self.region(user, region) or [] if row["action_id"] == f"{self.case()}:{action_id}"]
		self.assertEqual(len(rows), 1, f"{user} {region} {action_id}: {rows}")
		return rows[0]

	def ids(self, user: str, region: str) -> list[str]:
		return [row["action_id"].split(":", 1)[1] for row in self.mine(self.region(user, region))]

	def name_of(self, user: str) -> str:
		return frappe.db.get_value("User", user, "full_name")

	def effective_deadline(self) -> datetime:
		return get_datetime(self.doc().effective_deadline)

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
		rows = [row for row in self.all_rows(user, at, region) if row["key"].endswith(f"|{self.case()}:{action_id}")]
		self.assertEqual(len(rows), 1, f"{region} {action_id}: {rows}")
		return rows[0]

	def holders(self, text: str, prefix: str, suffix: str, *, role: str = "an Accounting Officer") -> None:
		"""`text` is prefix + the Accounting Officers (either order) when there are two or fewer, otherwise the responsibility (`role`) + suffix."""
		self.assertTrue(text.startswith(prefix) and text.endswith(suffix), text)
		who = text[len(prefix) : len(text) - len(suffix)]
		officers = people.accounting_officers()
		if len(officers) <= 2:
			self.assertEqual(set(who.split(" or ")), {people.full_name(user) for user in officers}, text)
		else:
			self.assertEqual(who, role, text)

	def journal(self, command: str, *, actor: str, at: datetime, result: str = "{}") -> str:
		doc = records.insert(frappe.get_doc({
			"doctype": records.JOURNAL, "idempotency_key": key(), "command": command, "payload_hash": "x", "result_json": result, "actor": actor,
			"opening_case": self.case(), "recorded_at": at,
		}))
		return doc.name

	# ----- My work -----

	def test_the_accounting_officers_appointment_row_is_worded_by_the_owner_without_the_reference(self):
		self.prepare_case()
		doc = self.doc()
		row = self.one(AO, he.MY_WORK, "appoint")
		self.assertEqual((row["title"], row["action"], row["reference"]), (doc.tender_title, "Appoint opening committee", doc.tender_reference))
		self.assertNotEqual(row["title"], row["reference"])
		self.assertEqual((row["owner"], row["region"], row["root"], row["blocked"], row["reason"], row["due"]), ("bid_opening", he.MY_WORK, doc.name, False, "", None))
		self.assertEqual((row["entered_at"], row["entered_verb"], type(row["entered_at"])), (doc.creation, "Received", datetime))
		self.assertEqual(row["destination"], {"route": ["tenders", doc.tender_reference, "opening"], "route_options": {}})
		self.assertTrue(all(r["owner"] == "bid_opening" and r["region"] == he.MY_WORK for r in self.mine(self.region(AO, he.MY_WORK))))

	def test_once_appointed_the_accounting_officer_publishes_and_each_member_joins_from_the_appointment_instant(self):
		self.appoint()
		appointed = appointment.current(self.case())
		self.assertEqual(self.ids(AO, he.MY_WORK), ["publish"])
		publish = self.one(AO, he.MY_WORK, "publish")
		self.assertEqual((publish["action"], publish["entered_at"]), ("Publish how to attend", appointed.appointed_at))
		for user in (MEMBER, INDEPENDENT, CHAIR):
			join = self.one(user, he.MY_WORK, "join")
			self.assertEqual((join["action"], join["entered_at"], join["title"]), ("Join opening", appointed.appointed_at, self.doc().tender_title))
			self.assertEqual(join["destination"]["route"], ["tenders", self.reference, "opening"])
		self.publish()
		self.assertEqual(self.ids(AO, he.MY_WORK), [])  # the row clears on its business transition
		self.assertIsInstance(self.region(AO, he.MY_WORK), list)

	def test_the_chairs_start_is_coming_up_until_the_deadline_and_my_work_after_it_never_both(self):
		self.prepared()
		deadline = self.effective_deadline()
		self.at(deadline - timedelta(minutes=30))
		self.assertNotIn("start", self.ids(CHAIR, he.MY_WORK))
		coming = self.one(CHAIR, he.COMING_UP, "start")
		self.assertEqual((coming["action"], coming["scheduled_at"], type(coming["scheduled_at"])), ("Start opening", deadline, datetime))
		self.assertEqual((coming["title"], coming["reference"]), (self.doc().tender_title, self.reference))
		self.assertEqual((coming["destination"], coming["region"]), ({"route": ["tenders", self.reference, "opening"], "route_options": {}}, he.COMING_UP))
		self.at(deadline + timedelta(minutes=1))
		self.assertNotIn("start", self.ids(CHAIR, he.COMING_UP))
		start = self.one(CHAIR, he.MY_WORK, "start")  # the same action id
		self.assertEqual((start["action"], start["entered_at"], start["blocked"]), ("Start opening", appointment.current(self.case()).appointed_at, False))
		self.assertEqual(start["action_id"], coming["action_id"])
		# a member who is not the chair never has the row, either way
		for user in (MEMBER, INDEPENDENT):
			self.assertNotIn("start", self.ids(user, he.MY_WORK) + self.ids(user, he.COMING_UP))

	def test_only_the_chair_has_coming_up_and_none_elsewhere(self):
		self.prepared()
		self.at(self.effective_deadline() - timedelta(hours=1))
		self.assertEqual(self.ids(CHAIR, he.COMING_UP), ["start"])
		for user in (AO, MEMBER, INDEPENDENT, AUDITOR, NOBODY, OUTSIDER):
			self.assertIsNone(self.region(user, he.COMING_UP), user)

	def test_the_owners_action_table_matches_the_owners_own_row_titles(self):
		self.prepared()
		self.at(self.effective_deadline() + timedelta(minutes=1))
		seen = set()
		for user in (AO, CHAIR, MEMBER, INDEPENDENT):
			for row in my_work_provider.my_work_rows(user)["assigned"]:
				if row["reference"] != self.reference:
					continue
				key_ = row["task_type"].removeprefix("bid_opening.")
				seen.add(key_)
				action = home_provider.ACTIONS[key_]
				expected = row["title"].split(" for ")[0] if key_ != "start" else "Start opening"
				self.assertEqual(action, expected, row["title"])
				self.assertNotIn(self.reference, action)
		self.assertEqual(seen, {"join", "start"})
		self.assertEqual(home_provider.ACTIONS["start"], "Start opening")  # the spec's own wording
		self.assertEqual({"appoint", "publish", "decide", "paused", "replacement", "join", "start", "prepare-record", "sign", "register"}, set(home_provider.ACTIONS))

	def test_a_start_row_is_blocked_only_where_the_owners_answer_says_so(self):
		self.prepared()
		self.at(self.effective_deadline() + timedelta(minutes=1))
		self.assertEqual(self.one(CHAIR, he.MY_WORK, "start")["blocked"], False)
		blocker = ns.answer(ns.KIND_BLOCKED, headline="Bid opening isn’t available yet.", stage="open")
		with mock.patch.object(next_steps, "answer_for", return_value=blocker):
			blocked = self.one(CHAIR, he.MY_WORK, "start")
			self.assertEqual((blocked["blocked"], blocked["reason"], blocked["action"]), (True, "Bid opening isn’t available yet.", "Start opening"))
			self.assertFalse(self.one(CHAIR, he.MY_WORK, "join")["blocked"])  # only the start row asks the owner
		waiting = ns.answer(ns.KIND_WAITING, headline="Waiting for members to join", stage="open", holder=ns.holder("Committee member", ["X"]))
		with mock.patch.object(next_steps, "answer_for", return_value=waiting):
			self.assertEqual(self.one(CHAIR, he.MY_WORK, "start")["blocked"], False)  # a wait is not a blocked turn

	# ----- Waiting -----

	def test_the_head_of_procurement_waits_for_the_accounting_officer_to_appoint_with_the_case_creation_as_since(self):
		self.prepare_case()
		waiting = self.one(CHAIR, he.WAITING, "await-appointment")
		self.assertEqual((waiting["title"], waiting["reference"], waiting["since"]), (self.doc().tender_title, self.reference, self.doc().creation))
		self.holders(waiting["action"], "Waiting for ", " to appoint the opening committee")
		self.holders(waiting["holder"], "", "", role="Accounting Officer")
		self.assertEqual((waiting["due"], waiting["destination"]["route"]), (None, ["tenders", self.reference, "opening"]))
		self.appoint()
		self.assertEqual(self.ids(CHAIR, he.WAITING), [])  # gone once the committee is appointed
		self.assertNotIn("await-appointment", self.ids(AO, he.WAITING))

	def test_a_named_accounting_officer_reads_as_the_spec_does(self):
		with mock.patch.object(people, "accounting_officers", return_value=[AO]):
			waiting = self.one(CHAIR, he.WAITING, "await-appointment")
		self.assertEqual((waiting["action"], waiting["holder"]), (f"Waiting for {self.name_of(AO)} to appoint the opening committee", self.name_of(AO)))

	def test_a_waiting_row_without_a_since_is_skipped_and_the_owners_other_waiting_answers_are_not_entries(self):
		row = {"task_id": f"{self.case()}:await-appointment", "task_type": "bid_opening.await-appointment", "title": "x", "reference": self.reference, "status": "Waiting",
			"holder": ns.holder(people.ACCOUNTING_OFFICER, ["Amina Hassan"]), "since": None}
		with mock.patch.object(my_work_provider, "my_work_rows", return_value={"assigned": [], "claimable": [], "waiting": [row]}):
			self.assertEqual(self.region(CHAIR, he.WAITING), [])
		self.appoint()
		self.assertEqual(self.ids(MEMBER, he.WAITING), [])  # "waiting for the chair to start" has no hand-off instant, so it is not an entry
		self.assertIsInstance(self.region(MEMBER, he.WAITING), list)

	# ----- Records you oversee -----

	def test_bid_opening_has_no_oversight_for_anyone(self):
		self.prepared()
		for user in (AO, CHAIR, MEMBER, INDEPENDENT, AUDITOR, NOBODY, OUTSIDER, "Administrator", SUPPORT):
			self.assertIsNone(self.region(user, he.OVERSIGHT), user)

	# ----- applicability -----

	def test_none_versus_empty_by_responsibility(self):
		for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
			for user in (NOBODY, OUTSIDER):
				self.assertIsNone(self.region(user, region), (user, region))
			for user in (AO, CHAIR, MEMBER, AUDITOR):
				self.assertIsInstance(self.region(user, region), list, (user, region))
		self.assertEqual(self.mine(self.region(AUDITOR, he.MY_WORK)), [])  # the Auditor holds nothing in an opening
		self.assertEqual(self.mine(self.region(AUDITOR, he.WAITING)), [])
		# a committee seat is a responsibility here: the independent member applies only once appointed
		self.assertIsNone(self.region(INDEPENDENT, he.MY_WORK))
		self.appoint()
		self.assertEqual(self.ids(INDEPENDENT, he.MY_WORK), ["join"])
		self.assertIsNone(self.region(INDEPENDENT, he.OVERSIGHT))

	def test_the_technical_reader_and_an_unrelated_internal_user_get_nothing(self):
		self.prepared()
		for user in ("Administrator", SUPPORT, NOBODY, OUTSIDER):
			for region in he.REGIONS:
				self.assertIsNone(self.region(user, region), (user, region))
		view = self.home("Administrator", datetime(2027, 6, 1, 10, 0))
		self.assertEqual((view["empty"], view["regions"]["my_work"]["entries"]), (True, []))
		nobody = self.home(NOBODY, datetime(2027, 6, 1, 10, 0))
		self.assertEqual(nobody["state"], "ready")
		self.assertFalse(any(region["entries"] for region in nobody["regions"].values()))
		self.assertEqual({region["coverage"] for region in nobody["regions"].values()}, {hw.NOT_APPLICABLE})

	def test_a_user_without_the_responsibility_sees_none_of_it_and_a_revoked_responsibility_removes_it(self):
		self.prepare_case()
		at = datetime(2027, 5, 19, 12, 0)
		administration.grant(user=EXTRA, business_role="Accounting Officer", fixture_namespace=EXTRA_NS, actor="Administrator")
		self.addCleanup(_remove_extra)
		self.assertEqual(self.row(EXTRA, at, "my_work", "appoint")["action"], "Appoint opening committee")
		self.assertTrue(self.home(EXTRA, at)["regions"]["my_work"]["applicable"])
		assignment = frappe.get_all("User Responsibility Assignment", filters={"user": EXTRA}, pluck="name")[0]
		administration.revoke(assignment, reason="Revoked inside the Home provider test.", actor="Administrator")
		revoked = self.home(EXTRA, at)
		self.assertEqual({region["coverage"] for region in revoked["regions"].values()}, {hw.NOT_APPLICABLE})
		self.assertFalse([row for region in revoked["regions"].values() for row in region["entries"] if row["reference"] == self.reference])
		self.assertIsNone(self.region(EXTRA, he.MY_WORK))
		self.assertIsNone(self.region(EXTRA, he.COMPLETED))

	# ----- Recently completed actions -----

	def test_the_accounting_officers_own_appointment_and_publication_are_completed_actions(self):
		self.prepared()
		appointed = appointment.current(self.case())
		rows = {row["action"]: row for row in self.mine(self.region(AO, he.COMPLETED))}
		self.assertEqual(set(rows), {"Appointed opening committee", "Published how to attend"})
		row = rows["Appointed opening committee"]
		self.assertEqual((row["title"], row["reference"], row["completed_at"], row["action_id"]), (self.doc().tender_title, self.reference, appointed.appointed_at, appointed.name))
		self.assertTrue(row["sentence"].startswith("You appointed the opening committee on 19 May 2027, 09:20 ") and row["sentence"].endswith("."), row["sentence"])
		self.assertEqual(row["destination"], {"route": ["tenders", self.reference, "opening"], "route_options": {}})
		published = rows["Published how to attend"]
		self.assertTrue(published["sentence"].startswith("You published how to attend this opening on 19 May 2027, 09:20 "), published["sentence"])
		# nobody else appointed or published
		for user in (CHAIR, MEMBER, AUDITOR):
			self.assertEqual(self.mine(self.region(user, he.COMPLETED)), [], user)

	def test_the_journal_commands_on_the_whitelist_are_completed_actions_and_nothing_else_is(self):
		self.prepared()
		base = home_time.now() - timedelta(days=2)
		secret = "SECRET-BID-DETAIL-4471"
		ids = {
			command: self.journal(command, actor=CHAIR, at=base + timedelta(minutes=i), result=json.dumps({"bidder": secret}))
			for i, command in enumerate(("BeginOpening", "FinishCeremony", "RecordOpeningNotHeld", "ProvideOpeningRegister", "AttestOpeningTarget"))
		}
		skipped = [self.journal(command, actor=CHAIR, at=base) for command in ("OpenNextTender", "RecordReadout", "JoinOpening", "AppointOpeningCommittee")]
		other = self.journal("BeginOpening", actor=MEMBER, at=base)
		rows = {row["action"]: row for row in self.mine(self.region(CHAIR, he.COMPLETED))}
		self.assertEqual(set(rows), {"Started opening", "Finished opening", "Recorded opening not held", "Provided opening register", "Signed opening record"})
		self.assertEqual({row["action_id"] for row in rows.values()}, set(ids.values()))
		self.assertTrue(set(skipped).isdisjoint(row["action_id"] for row in rows.values()))
		self.assertNotIn(other, [row["action_id"] for row in rows.values()])
		self.assertTrue(rows["Started opening"]["sentence"].startswith("You started the opening on "))
		self.assertTrue(rows["Recorded opening not held"]["sentence"].startswith("You recorded that the opening did not take place on "))
		self.assertTrue(rows["Provided opening register"]["sentence"].startswith("You provided the opening register on "))
		self.assertTrue(rows["Signed opening record"]["sentence"].startswith("You signed the opening record on "))
		self.assertNotIn(secret, json.dumps(self.region(CHAIR, he.COMPLETED), default=str))
		self.assertEqual([row["action_id"] for row in self.mine(self.region(MEMBER, he.COMPLETED))], [other])

	def test_the_journal_is_read_without_its_stored_result(self):
		self.prepared()
		self.journal("BeginOpening", actor=CHAIR, at=home_time.now() - timedelta(days=1), result='{"bidder": "x"}')
		real, seen = frappe.get_all, []

		def watching(doctype, *args, **kwargs):
			if doctype == records.JOURNAL:
				seen.append(kwargs.get("fields"))
			return real(doctype, *args, **kwargs)

		with mock.patch.object(frappe, "get_all", watching):
			self.region(CHAIR, he.COMPLETED)
		self.assertEqual(seen, [["name", "command", "opening_case", "recorded_at"]])

	def test_a_repeated_signature_is_one_line_the_latest_and_the_thirty_day_cutoff_is_the_providers_own(self):
		self.prepared()
		now = home_time.now()
		old = self.journal("BeginOpening", actor=CHAIR, at=now - timedelta(days=45))
		first = self.journal("AttestOpeningTarget", actor=MEMBER, at=now - timedelta(days=3))
		latest = self.journal("AttestOpeningTarget", actor=MEMBER, at=now - timedelta(days=2))
		recent = self.journal("FinishCeremony", actor=CHAIR, at=now - timedelta(days=5))
		ids = [row["action_id"] for row in self.region(MEMBER, he.COMPLETED)]
		self.assertIn(latest, ids)
		self.assertNotIn(first, ids)
		chair_ids = [row["action_id"] for row in self.region(CHAIR, he.COMPLETED)]
		self.assertIn(recent, chair_ids)
		self.assertNotIn(old, chair_ids)

	def test_the_core_window_drops_a_completed_action_older_than_thirty_days(self):
		self.prepared()
		appointed = appointment.current(self.case()).appointed_at
		inside = self.all_rows(AO, appointed + timedelta(days=1), "completed")
		self.assertTrue([row for row in inside if row["reference"] == self.reference])
		outside = self.all_rows(AO, appointed + timedelta(days=45), "completed")
		self.assertFalse([row for row in outside if row["reference"] == self.reference])

	def test_the_awaiting_clause_is_added_only_while_the_owners_answer_for_the_actor_is_a_named_wait(self):
		self.prepared()
		at = home_time.now() - timedelta(days=1)
		self.journal("AttestOpeningTarget", actor=MEMBER, at=at)
		self.journal("BeginOpening", actor=MEMBER, at=at - timedelta(minutes=5))
		wait = ns.answer(ns.KIND_WAITING, headline="Waiting for X to sign the opening record", stage="record", holder=ns.holder("Committee member", ["Fred Odhiambo"]))
		with mock.patch.object(next_steps, "answer_for", return_value=wait):
			rows = {row["action"]: row for row in self.mine(self.region(MEMBER, he.COMPLETED))}
		self.assertTrue(rows["Signed opening record"]["sentence"].endswith(" It is awaiting signature by Fred Odhiambo."), rows["Signed opening record"]["sentence"])
		self.assertNotIn("awaiting", rows["Started opening"]["sentence"])  # only the command the owner's wait follows
		done = ns.answer(ns.KIND_DONE, headline="Done", stage="record")
		with mock.patch.object(next_steps, "answer_for", return_value=done):
			rows = {row["action"]: row for row in self.mine(self.region(MEMBER, he.COMPLETED))}
		self.assertNotIn("awaiting", rows["Signed opening record"]["sentence"])
		without_holder = ns.answer(ns.KIND_WAITING, headline="Waiting", stage="record", holder=ns.holder("Committee member", []))
		with mock.patch.object(next_steps, "answer_for", return_value=without_holder):
			rows = {row["action"]: row for row in self.mine(self.region(MEMBER, he.COMPLETED))}
		self.assertNotIn("awaiting", rows["Signed opening record"]["sentence"])

	def test_an_actor_who_can_no_longer_read_the_case_sees_nothing_of_it_in_completed(self):
		self.prepared()
		self.assertTrue(self.mine(self.region(AO, he.COMPLETED)))
		with mock.patch("kentender_procurement.bid_opening.services.reads.can_read", return_value=False):
			self.assertEqual(self.mine(self.region(AO, he.COMPLETED)), [])
			self.assertIsInstance(self.region(AO, he.COMPLETED), list)

	# ----- writes, cost, destinations -----

	def test_the_provider_writes_nothing(self):
		self.prepared()
		self.journal("BeginOpening", actor=CHAIR, at=home_time.now() - timedelta(days=1))
		before = frappe.db.transaction_writes
		for stamp in (self.effective_deadline() - timedelta(hours=1), self.effective_deadline() + timedelta(minutes=1)):
			self.at(stamp)
			for user in (AO, CHAIR, MEMBER, INDEPENDENT, AUDITOR, NOBODY, OUTSIDER, SUPPORT, "Administrator"):
				for region in he.REGIONS:
					self.region(user, region)
		self.assertEqual(frappe.db.transaction_writes, before)

	def test_the_scan_runs_once_per_home_read(self):
		self.prepared()
		calls = []
		original = my_work_provider.my_work_rows

		def counting(user):
			calls.append(user)
			return original(user)

		with mock.patch.object(my_work_provider, "my_work_rows", counting):
			self.home(CHAIR, datetime(2027, 5, 25, 10, 0))
		self.assertEqual(calls, [CHAIR])

	def test_every_destination_opens_a_real_page_the_actor_may_open(self):
		self.assertTrue(frappe.db.exists("Page", "tenders"))
		self.prepared()
		self.at(self.effective_deadline() + timedelta(minutes=1))
		self.journal("BeginOpening", actor=CHAIR, at=home_time.now() - timedelta(days=1))
		seen = set()
		for user in (AO, CHAIR, MEMBER, INDEPENDENT):
			for region in (he.MY_WORK, he.COMING_UP, he.WAITING, he.COMPLETED):
				for row in self.mine(self.region(user, region)):
					seen.add(row["destination"]["route"][0])
					self.assertTrue(hw._page_permitted(row["destination"]["route"][0], user), (user, row["destination"]))
		self.assertEqual(seen, {"tenders"})

	# ----- through the Home read -----

	def test_the_accounting_officers_home_renders_the_row_with_the_owners_timing(self):
		self.prepare_case()
		doc = self.doc()
		at = get_datetime(doc.creation) + timedelta(days=2)
		row = self.row(AO, at, "my_work", "appoint")
		self.assertEqual((row["module"], row["action"], row["title"], row["reference"]), ("Bid opening", "Appoint opening committee", doc.tender_title, doc.tender_reference))
		self.assertEqual(row["timing"], home_time.entered("Received", doc.creation, at))
		self.assertTrue(row["timing"].startswith("Received 2 days ago ("), row["timing"])
		waiting = self.row(CHAIR, at, "waiting", "await-appointment")
		self.assertEqual(waiting["timing"], home_time.waiting(doc.creation, at))
		self.assertTrue(waiting["timing"].startswith("Waiting 2 days (since "), waiting["timing"])

	def test_the_chairs_home_shows_start_opening_in_coming_up_with_the_spec_badge_and_nowhere_else(self):
		self.prepared()
		deadline = self.effective_deadline()
		self.at(deadline - timedelta(hours=2))
		at = deadline - timedelta(days=7)
		coming = self.row(CHAIR, at, "coming_up", "start")
		self.assertEqual((coming["action"], coming["badge"], coming["module"]), ("Start opening", "In 7 days", "Bid opening"))
		self.assertEqual(coming["exact"], home_time.coming_up(deadline, at)[1])
		self.assertFalse([r for r in self.all_rows(CHAIR, at, "my_work") if r["key"].endswith(f"|{self.case()}:start")])
		# a chair who also has the same row in My work is shown it once, in My work (core de-duplication)
		self.at(deadline + timedelta(minutes=1))
		later = deadline + timedelta(minutes=2)
		self.assertTrue(self.row(CHAIR, later, "my_work", "start"))
		self.assertFalse([r for r in self.all_rows(CHAIR, later, "coming_up") if r["key"].endswith(f"|{self.case()}:start")])
