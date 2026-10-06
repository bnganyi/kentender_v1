# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — the Strategy feed to Home (`services/home_provider.py`).

One shared world for the whole module (built once by the first test, read by every test; the provider only reads), built
through Strategy's own commands and then dated on a fixed June 2027 timeline so the exact Home strings can be asserted:

- plan P1: version 1 submitted by the Author (10 June 09:00) and approved by the Approver (12 June 11:00); version 2, a change
  to it, submitted by the dual-role user (17 June 10:00);
- plan P2: version 1 submitted by the Author, undecided (16 June 09:00);
- plan P4: version 1 submitted by the Author (15 June 09:00) and returned by the Approver (15 June 15:00);
- plan P5: a bare Draft (no hand-off, so no row).

`Audit Event.timestamp` is stamped by the real clock, so the world re-dates its events with a direct write; one test shows
the real-clock shape (an event stamped just before the read) arriving as well. Every row the world adds is removed
afterwards and counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_strategy \\
    --module kentender_strategy.tests.test_home_provider
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.utils import getdate

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import home_workspace as hw
from kentender_core.services import responsibility_administration as administration
from kentender_core.services.audit_event_service import purge_audit_events
from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record
from kentender_strategy.services import strategy_readiness as readiness
from kentender_strategy.services.home_provider import entries
from kentender_strategy.services.strategy_authorization import ROLE_STRATEGY_APPROVER, ROLE_STRATEGY_AUTHOR, ensure_strategy_governance_roles
from kentender_strategy.services.strategy_transitions import transition_plan_version
from kentender_strategy.tests.fixtures import ensure_fiscal_year
from kentender_strategy.tests.test_str_technical_read import TechnicalReadTestBase

# A window nothing else occupies (the suite's usual 2040 and the OVS suite's 2060 are taken).
FY, START, END = "2070-2071", "2070-07-01", "2075-06-30"
H = datetime(2027, 6, 18, 10, 0)  # the Home read: two days after the 16 June hand-offs
T_P1_SUBMITTED, T_P1_APPROVED, T_P1V2 = datetime(2027, 6, 10, 9, 0), datetime(2027, 6, 12, 11, 0), datetime(2027, 6, 17, 10, 0)
T_P2 = datetime(2027, 6, 16, 9, 0)
T_P4_SUBMITTED, T_P4_RETURNED = datetime(2027, 6, 15, 9, 0), datetime(2027, 6, 15, 15, 0)
ALL = (he.MY_WORK, he.WAITING, he.OVERSIGHT, he.COMPLETED, he.COMING_UP)
HOOK = "kentender_strategy.services.home_provider.entries"
WORLD: dict = {}
READ_DATE = "kentender_strategy.services.strategy_readiness.today"


class TestStrategyHomeProvider(TechnicalReadTestBase):
	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		cleanup = WORLD.get("cleanup", [])
		names = [name for doctype, name in cleanup if doctype in ("Strategic Plan Version", "Strategic Plan")]
		purge_audit_events({"document_name": ("in", names or ["-"])}, reason="strategy home provider test clean-up")
		for doctype, name in reversed(cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		if WORLD.get("made_fiscal_year") and frappe.db.exists("Fiscal Year", FY):
			frappe.delete_doc("Fiscal Year", FY, force=True, ignore_permissions=True)
		frappe.db.commit()
		left = {
			"Strategic Plan": frappe.db.count("Strategic Plan", {"name": ("in", [n for d, n in cleanup if d == "Strategic Plan"] or ["-"])}),
			"Strategic Plan Version": frappe.db.count("Strategic Plan Version", {"name": ("in", [n for d, n in cleanup if d == "Strategic Plan Version"] or ["-"])}),
			"Audit Event": frappe.db.count("Audit Event", {"document_name": ("in", names or ["-"])}),
			"User": frappe.db.count("User", {"name": ("like", f"kt.test.str.techread.%.{WORLD.get('suffix', '-')}@test.local")}),
			"Fiscal Year": int(bool(WORLD.get("made_fiscal_year") and frappe.db.exists("Fiscal Year", FY))),
		}
		WORLD.clear()
		if any(left.values()):
			raise AssertionError(f"Strategy Home test rows left behind: {left}")

	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, "Administrator")
		ensure_strategy_governance_roles()
		if not WORLD:
			WORLD["made_fiscal_year"] = not frappe.db.exists("Fiscal Year", FY)
			ensure_fiscal_year(2070)
			WORLD["suffix"] = uuid4().hex[:8]
			WORLD["cleanup"] = []
		self.suffix, self._cleanup = WORLD["suffix"], WORLD["cleanup"]
		if "built" not in WORLD:
			WORLD["built"] = False  # a build that fails is not retried by every test
			with patch("kentender_strategy.tests.test_str_technical_read.FY", FY), patch(READ_DATE, return_value=getdate("2099-12-31")):
				self._build()
			WORLD["built"] = True
		elif not WORLD["built"]:
			self.fail("the Strategy Home world did not build; see the first error")
		home_support.reset()

	def tearDown(self):
		frappe.set_user("Administrator")

	# ----- the world -----

	def _as(self, user: str, fn, *args, **kwargs):
		frappe.set_user(user)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def _stamp(self, version: str, action: str, at: datetime):
		for name in frappe.get_all("Audit Event", filters={"document_type": "Strategic Plan Version", "document_name": version, "action": action}, pluck="name"):
			frappe.db.set_value("Audit Event", name, "timestamp", at, update_modified=False)

	def _submitted(self, label: str, by: str, *, version_number: int = 1, plan=None, effective_from: str = START, **fields):
		plan = plan or self._plan(title=f"Home {label} {self.suffix}", period_start=START, period_end=END)
		version = self._version(plan, version_number=version_number, effective_from=effective_from, effective_to=END, **fields)
		self._hierarchy(version)
		self._as(by, transition_plan_version, version.name, "Submit for approval")
		return plan, version

	def _build(self):
		w = WORLD
		w["author"], w["approver"], w["dual"] = self._user("author"), self._user("approver"), self._user("dual")
		w["auditor"], w["ao"], w["hopf"], w["hod"], w["nobody"] = (self._user(label) for label in ("auditor", "ao", "hopf", "hod", "nobody"))
		self._grant(w["author"], ROLE_STRATEGY_AUTHOR)
		self._grant(w["approver"], ROLE_STRATEGY_APPROVER)
		self._grant(w["dual"], ROLE_STRATEGY_AUTHOR)
		self._grant(w["dual"], ROLE_STRATEGY_APPROVER)
		self._grant(w["auditor"], "Auditor")
		unit = frappe.db.get_value("Organisation Unit", {"status": "Active"}, "name")
		for label, role, ou in (("ao", "Accounting Officer", ""), ("hopf", "Head of Procurement Function", ""), ("hod", "Head of User Department", unit)):
			outcome = administration.grant(user=w[label], business_role=role, organisation_unit=ou, fixture_namespace="STR_TECHREAD_TESTS", actor="Administrator")
			self._cleanup.append(("User Responsibility Assignment", outcome["assignment"]))

		p1, v1 = self._submitted("P1", w["author"])
		self._as(w["approver"], transition_plan_version, v1.name, "Approve")
		_p, v1b = self._submitted("P1", w["dual"], version_number=2, plan=p1, effective_from="2072-07-01", based_on_plan_version_id=v1.name)
		p2, v2 = self._submitted("P2", w["author"])
		p4, v4 = self._submitted("P4", w["author"])
		self._as(w["approver"], transition_plan_version, v4.name, "Return", reason="Name the department on every programme before resubmitting.")
		p5 = self._plan(title=f"Home P5 {self.suffix}", period_start=START, period_end=END)
		v5 = self._version(p5, effective_from=START, effective_to=END)
		w.update(p1=p1, v1=v1, v1b=v1b, p2=p2, v2=v2, p4=p4, v4=v4, p5=p5, v5=v5)

		self._stamp(v1.name, "Submit for approval", T_P1_SUBMITTED)
		self._stamp(v1.name, "Approve", T_P1_APPROVED)
		self._stamp(v1b.name, "Submit for approval", T_P1V2)
		self._stamp(v2.name, "Submit for approval", T_P2)
		self._stamp(v4.name, "Submit for approval", T_P4_SUBMITTED)
		self._stamp(v4.name, "Return", T_P4_RETURNED)
		frappe.db.commit()

	# ----- helpers -----

	def region(self, user: str, region: str):
		home_support.reset()
		return entries(user=user, region=region)

	def mine(self, rows) -> list[dict]:
		roots = {WORLD[key].name for key in ("v1", "v1b", "v2", "v4", "v5")}
		return [row for row in rows or [] if row["root"] in roots]

	def one(self, user: str, region: str, key: str, suffix: str = "") -> dict:
		root = WORLD[key].name
		rows = [row for row in self.region(user, region) or [] if row["root"] == root and row["action_id"].endswith(suffix)]
		self.assertEqual(len(rows), 1, f"{user} {region} {key}: {rows}")
		return rows[0]

	def title(self, plan_key: str) -> str:
		return WORLD[plan_key].title

	def home(self, user: str, at: datetime = H):
		return hw.get_workspace(user, providers=[entries], at=at)

	def all_rows(self, user: str, region: str, at: datetime = H) -> list[dict]:
		rows, cursor = [], None
		while True:
			page = hw.get_workspace(user, regions=[region], cursors={region: cursor} if cursor else None, providers=[entries], at=at)["regions"][region]
			rows += page["entries"]
			cursor = page["next_cursor"]
			if not cursor:
				return rows

	def row(self, user: str, region: str, key: str, at: datetime = H) -> dict:
		reference = WORLD[key].plan_version_id
		rows = [row for row in self.all_rows(user, region, at) if row["reference"] == reference]
		self.assertEqual(len(rows), 1, f"{user} {region} {key}: {rows}")
		return rows[0]

	def holders_text(self, text: str, *, without: str) -> None:
		"""`text` reads "Waiting for {the Strategy Approver holders other than `without`, or a Strategy Approver} to review the plan"."""
		prefix, suffix = "Waiting for ", " to review the plan"
		self.assertTrue(text.startswith(prefix) and text.endswith(suffix), text)
		people = text[len(prefix) : len(text) - len(suffix)]
		users = frappe.get_all("User Responsibility Assignment", filters={"business_role": ROLE_STRATEGY_APPROVER, "status": "Enabled"}, pluck="user", distinct=True)
		holders = [u for u in users if u != without and authorise_record(user=u, business_role=ROLE_STRATEGY_APPROVER, organisation_unit="", purpose=PURPOSE_COMMAND).allowed]
		if len(holders) <= 2:
			self.assertEqual(set(people.split(" or ")), {frappe.db.get_value("User", u, "full_name") for u in holders}, text)
		else:
			self.assertEqual(people, f"a {ROLE_STRATEGY_APPROVER}", text)

	# ----- My work -----

	def test_the_approver_reviews_a_new_plan_and_plan_changes(self):
		w = WORLD
		new = self.one(w["approver"], he.MY_WORK, "v2", ":review")
		self.assertEqual((new["title"], new["action"], new["reference"]), (self.title("p2"), "Review new plan", w["v2"].plan_version_id))
		self.assertEqual((new["entered_at"], new["entered_verb"], new["action_id"]), (T_P2, "Submitted", f"{w['v2'].name}:review"))
		self.assertEqual(new["destination"], {"route": ["strategy", "approval", w["v2"].plan_version_id], "route_options": {}})
		self.assertIsInstance(new["entered_at"], datetime)  # the raw instant, never a display string
		changes = self.one(w["approver"], he.MY_WORK, "v1b", ":review")
		self.assertEqual((changes["title"], changes["action"], changes["entered_at"]), (self.title("p1"), "Review plan changes", T_P1V2))

	def test_a_version_that_starts_in_the_future_cannot_be_approved_yet_and_says_so_in_the_owners_words(self):
		w = WORLD
		row = self.one(w["approver"], he.MY_WORK, "v2", ":review")
		self.assertTrue(row["blocked"])
		self.assertTrue(row["reason"].startswith("This version cannot be approved yet. It starts on 1 Jul 2070."), row["reason"])
		self.assertEqual(row["reason"], readiness.get_version_approval_blockers(w["v2"].name)["future_effective"]["headline"])
		self.assertIn("1 Jul 2072", self.one(w["approver"], he.MY_WORK, "v1b", ":review")["reason"])
		view = self.row(w["approver"], he.MY_WORK, "v2")
		self.assertTrue(view["blocked"] and view["reason"] == row["reason"])

	def test_a_version_that_can_become_current_now_is_not_blocked(self):
		with patch(READ_DATE, return_value=getdate("2099-12-31")):
			row = self.one(WORLD["approver"], he.MY_WORK, "v2", ":review")
		self.assertEqual((row["blocked"], row["reason"]), (False, ""))

	def test_the_author_corrects_a_returned_draft_and_a_bare_draft_is_no_row(self):
		w = WORLD
		row = self.one(w["author"], he.MY_WORK, "v4", ":correct")
		self.assertEqual((row["title"], row["action"], row["reference"]), (self.title("p4"), "Correct and resubmit", w["v4"].plan_version_id))
		self.assertEqual((row["entered_at"], row["entered_verb"], row["action_id"]), (T_P4_RETURNED, "Received", f"{w['v4'].name}:correct"))
		self.assertEqual(row["destination"], {"route": ["strategy", "plan", w["p4"].plan_id, "version", "1", "structure"], "route_options": {}})
		self.assertEqual((row["blocked"], row["reason"]), (False, ""))
		self.assertEqual([r for r in self.region(w["author"], he.MY_WORK) if r["root"] == w["v5"].name], [])  # a bare Draft has no hand-off instant
		self.assertEqual([r for r in self.region(w["approver"], he.MY_WORK) if r["root"] == w["v4"].name], [])  # the Approver cannot author it
		self.assertEqual([r for r in self.region(w["author"], he.MY_WORK) if r["action_id"].endswith(":review")], [])

	def test_nobody_decides_what_they_submitted_and_a_dual_role_user_still_decides_the_others(self):
		w = WORLD
		dual = [r for r in self.region(w["dual"], he.MY_WORK) if r["root"] in (w["v1b"].name, w["v2"].name)]
		self.assertEqual([r["root"] for r in dual], [w["v2"].name])  # not their own version 2
		self.assertEqual(self.one(w["dual"], he.MY_WORK, "v4", ":correct")["action"], "Correct and resubmit")  # and they may author too
		self.assertEqual([r for r in self.region(w["author"], he.MY_WORK) if r["root"] == w["v2"].name], [])  # the Author is not an Approver

	# ----- Waiting -----

	def test_the_author_waits_for_an_approver_on_their_own_submission(self):
		w = WORLD
		row = self.one(w["author"], he.WAITING, "v2")
		self.assertEqual((row["title"], row["reference"], row["action_id"], row["since"]), (self.title("p2"), w["v2"].plan_version_id, f"{w['v2'].name}:review", T_P2))
		self.holders_text(row["action"], without=w["author"])
		self.assertTrue(row["holder"])
		self.assertEqual(row["destination"], {"route": ["strategy", "approval", w["v2"].plan_version_id], "route_options": {}})
		self.assertEqual([r for r in self.region(w["author"], he.WAITING) if r["root"] in (w["v4"].name, w["v1b"].name, w["v5"].name)], [])

	def test_a_dual_role_submitter_waits_for_another_approver(self):
		row = self.one(WORLD["dual"], he.WAITING, "v1b")
		self.assertEqual(row["since"], T_P1V2)
		self.holders_text(row["action"], without=WORLD["dual"])

	def test_the_approver_waits_for_nothing(self):
		self.assertEqual(self.mine(self.region(WORLD["approver"], he.WAITING)), [])

	# ----- Records you oversee -----

	def test_the_auditor_sees_the_versions_awaiting_approval_read_only_with_since_and_the_holder(self):
		w = WORLD
		rows = {row["root"]: row for row in self.mine(self.region(w["auditor"], he.OVERSIGHT))}
		self.assertEqual(set(rows), {w["v2"].name, w["v1b"].name})  # not the returned draft, the approved or the bare draft
		for key, since in (("v2", T_P2), ("v1b", T_P1V2)):
			row = rows[w[key].name]
			self.assertEqual((row["since"], row["outstanding"], row["action_id"], row["reference"]), (since, True, f"{w[key].name}:review", w[key].plan_version_id))
			self.holders_text(row["action"], without="")
		self.assertEqual(rows[w["v2"].name]["title"], self.title("p2"))
		for key in (he.MY_WORK, he.WAITING, he.COMPLETED):
			self.assertEqual(self.mine(self.region(w["auditor"], key)), [], key)

	def test_the_same_action_id_as_my_work_deduplicates_an_actor_who_holds_and_oversees(self):
		w = WORLD
		self.assertEqual(self.one(w["auditor"], he.OVERSIGHT, "v2")["identity"], self.one(w["approver"], he.MY_WORK, "v2", ":review")["identity"])
		self.assertEqual(self.one(w["auditor"], he.OVERSIGHT, "v2")["identity"], self.one(w["author"], he.WAITING, "v2")["identity"])

	def test_only_an_auditor_oversees_and_approved_only_readers_have_no_outstanding_concept(self):
		w = WORLD
		for user in (w["author"], w["approver"], w["dual"]):
			self.assertIsNone(self.region(user, he.OVERSIGHT), user)
		for user in (w["ao"], w["hopf"], w["hod"]):
			for region in ALL:
				self.assertIsNone(self.region(user, region), (user, region))
			view = self.home(user)
			self.assertEqual({r["coverage"] for r in view["regions"].values()}, {hw.NOT_APPLICABLE}, user)

	# ----- Coming up -----

	def test_strategy_contributes_nothing_to_coming_up(self):
		w = WORLD
		for user in (w["author"], w["approver"], w["dual"], w["auditor"], w["ao"]):
			self.assertIsNone(self.region(user, he.COMING_UP), user)

	# ----- Recently completed actions -----

	def test_the_authors_own_submissions_newest_first(self):
		w = WORLD
		rows = [r for r in self.all_rows(w["author"], he.COMPLETED) if r["reference"] in {w[k].plan_version_id for k in ("v1", "v2", "v4")}]
		self.assertEqual(
			[(r["title"], r["action"], r["sentence"]) for r in rows],
			[
				(self.title("p2"), "Submitted plan version for approval", "You submitted this plan version for approval on 16 June 2027, 09:00 EAT."),
				(self.title("p4"), "Submitted plan version for approval", "You submitted this plan version for approval on 15 June 2027, 09:00 EAT."),
				(self.title("p1"), "Submitted plan version for approval", "You submitted this plan version for approval on 10 June 2027, 09:00 EAT."),
			],
		)
		self.assertEqual(rows[0]["destination"], {"route": ["strategy", "plan", w["p2"].plan_id], "route_options": {}})
		self.assertEqual([r["sentence"] for r in self.all_rows(w["dual"], he.COMPLETED) if r["reference"] == w["v1b"].plan_version_id], ["You submitted this plan version for approval on 17 June 2027, 10:00 EAT."])

	def test_the_approvers_own_return_and_approval_and_nobody_elses(self):
		w = WORLD
		rows = {r["reference"]: r for r in self.all_rows(w["approver"], he.COMPLETED)}
		self.assertEqual((rows[w["v4"].plan_version_id]["action"], rows[w["v4"].plan_version_id]["sentence"]), ("Returned plan version", "You returned this plan version for correction on 15 June 2027, 15:00 EAT."))
		self.assertEqual((rows[w["v1"].plan_version_id]["action"], rows[w["v1"].plan_version_id]["sentence"]), ("Approved plan version", "You approved this plan version on 12 June 2027, 11:00 EAT."))
		self.assertNotIn(w["v2"].plan_version_id, rows)  # they did not submit it
		self.assertEqual(self.mine(self.region(w["auditor"], he.COMPLETED)), [])

	def test_the_core_window_drops_a_completed_action_older_than_thirty_days(self):
		w = WORLD
		event = frappe.get_all("Audit Event", filters={"document_name": w["v4"].name, "action": "Submit for approval"}, pluck="name")[0]
		frappe.db.set_value("Audit Event", event, "timestamp", datetime(2027, 5, 1, 9, 0), update_modified=False)
		self.addCleanup(frappe.db.set_value, "Audit Event", event, "timestamp", T_P4_SUBMITTED, update_modified=False)
		self.assertEqual([r for r in self.all_rows(w["author"], he.COMPLETED) if r["sentence"].endswith("1 May 2027, 09:00 EAT.")], [])

	def test_an_event_stamped_by_the_real_clock_arrives_when_the_read_is_on_the_same_clock(self):
		"""`Audit Event.timestamp` uses the real clock, so on a test environment whose Home clock is a fixture timeline the
		owner's events fall outside the window; read on the real clock they arrive."""
		w = WORLD
		now = home_time.now()
		event = frappe.get_all("Audit Event", filters={"document_name": w["v2"].name, "action": "Submit for approval"}, pluck="name")[0]
		frappe.db.set_value("Audit Event", event, "timestamp", now - timedelta(hours=2), update_modified=False)
		self.addCleanup(frappe.db.set_value, "Audit Event", event, "timestamp", T_P2, update_modified=False)
		rows = [r for r in self.all_rows(w["author"], he.COMPLETED, at=now) if r["reference"] == w["v2"].plan_version_id]
		self.assertEqual(len(rows), 1)
		self.assertTrue(rows[0]["sentence"].startswith("You submitted this plan version for approval on "))
		self.assertEqual(self.all_rows(w["author"], he.COMPLETED, at=H + timedelta(days=60)), [])  # and a read two months later shows none of them

	# ----- applicability, personas, technical readers -----

	def test_none_versus_empty_by_responsibility(self):
		w = WORLD
		for region in (he.MY_WORK, he.WAITING, he.OVERSIGHT, he.COMPLETED):
			self.assertIsNone(self.region(w["nobody"], region), region)
		for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
			for user in (w["author"], w["approver"], w["auditor"]):
				self.assertIsInstance(self.region(user, region), list, (user, region))
		self.assertIsInstance(self.region(w["auditor"], he.OVERSIGHT), list)
		self.assertEqual(self.mine(self.region(w["auditor"], he.MY_WORK)), [])

	def test_the_technical_reader_and_an_unrelated_internal_user_get_nothing(self):
		w = WORLD
		for region in he.REGIONS:
			self.assertIsNone(self.region("Administrator", region), region)
			self.assertIsNone(self.region(w["nobody"], region), region)
		view = self.home("Administrator")
		self.assertEqual((view["empty"], view["regions"]["my_work"]["entries"]), (True, []))
		nobody = self.home(w["nobody"])
		self.assertEqual(nobody["state"], "ready")
		self.assertFalse(any(region["entries"] for region in nobody["regions"].values()))
		self.assertEqual({region["coverage"] for region in nobody["regions"].values()}, {hw.NOT_APPLICABLE})

	def test_a_user_without_the_role_sees_none_of_it_and_a_revoked_responsibility_removes_it(self):
		w = WORLD
		extra = self._user("extra")
		self._grant(extra, ROLE_STRATEGY_APPROVER)
		self.assertEqual(self.row(extra, he.MY_WORK, "v2")["action"], "Review new plan")
		self.assertTrue(self.home(extra)["regions"]["my_work"]["applicable"])
		assignment = frappe.get_all("User Responsibility Assignment", filters={"user": extra}, pluck="name")[0]
		administration.revoke(assignment, reason="Revoked inside the Home provider test.", actor="Administrator")
		revoked = self.home(extra)
		self.assertEqual({region["coverage"] for region in revoked["regions"].values()}, {hw.NOT_APPLICABLE})
		self.assertFalse([row for region in revoked["regions"].values() for row in region["entries"]])
		for region in he.REGIONS:
			self.assertIsNone(self.region(extra, region), region)
		self.assertTrue(w["v2"].name)

	def test_the_provider_writes_nothing(self):
		w = WORLD
		frappe.db.commit()
		before = frappe.db.transaction_writes
		for user in (w["author"], w["approver"], w["dual"], w["auditor"], w["ao"], w["hopf"], w["hod"], w["nobody"], "Administrator"):
			for region in he.REGIONS:
				self.region(user, region)
		self.assertEqual(frappe.db.transaction_writes, before)

	def test_an_unknown_region_is_refused(self):
		with self.assertRaises(ValueError):
			entries(user=WORLD["author"], region="not_a_region")
		self.assertIsNone(entries(user="Guest", region=he.MY_WORK))

	# ----- destinations, hook -----

	def test_the_provider_is_registered_on_the_home_hook(self):
		self.assertIn(HOOK, frappe.get_hooks("kt_home_providers") or [])

	def test_every_destination_opens_a_real_page_the_actor_may_open(self):
		w = WORLD
		self.assertTrue(frappe.db.exists("Page", "strategy"))
		seen = set()
		for user in (w["author"], w["approver"], w["dual"], w["auditor"]):
			for region in (he.MY_WORK, he.WAITING, he.OVERSIGHT, he.COMPLETED):
				for row in self.mine(self.region(user, region)):
					seen.add(row["destination"]["route"][0])
					self.assertTrue(hw._page_permitted(row["destination"]["route"][0], user), (user, row["destination"]))
		self.assertEqual(seen, {"strategy"})

	# ----- through the Home read -----

	def test_the_approvers_home_renders_the_timing_strings(self):
		w = WORLD
		new = self.row(w["approver"], he.MY_WORK, "v2")
		self.assertEqual((new["module"], new["timing"], new["action"]), ("Strategy", "Submitted 2 days ago (16 June, 09:00)", "Review new plan"))
		self.assertEqual(self.row(w["approver"], he.MY_WORK, "v1b")["timing"], "Submitted yesterday (17 June, 10:00)")

	def test_the_authors_home_renders_work_and_waiting(self):
		w = WORLD
		self.assertEqual(self.row(w["author"], he.MY_WORK, "v4")["timing"], "Received 3 days ago (15 June, 15:00)")
		waiting = self.row(w["author"], he.WAITING, "v2")
		self.assertEqual(waiting["timing"], "Waiting 2 days (since 16 June, 09:00)")
		self.assertTrue(waiting["holder"])
		view = self.home(w["author"])
		self.assertTrue(view["regions"]["my_work"]["applicable"] and view["regions"]["waiting"]["applicable"])
		self.assertFalse(view["regions"]["oversight"]["applicable"])

	def test_the_auditors_home_counts_outstanding_matters(self):
		w = WORLD
		view = self.home(w["auditor"])
		self.assertTrue(view["regions"]["oversight"]["applicable"])
		self.assertFalse(view["regions"]["my_work"]["entries"])
		self.assertEqual(self.row(w["auditor"], he.OVERSIGHT, "v2")["timing"], "Outstanding 2 days (since 16 June, 09:00)")
