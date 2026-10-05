# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — the Budget & Funding feed to Home (`services/home_provider.py`).

One shared world for the whole module (built once by the first test, read by every test; the provider only reads), built
through Budget's own commands and then dated on a fixed June 2027 timeline so the exact Home strings can be asserted:

- version A: a baseline the Budget Officer submitted, undecided (16 June 09:00);
- version B: a baseline the Officer submitted (10 June) and the Approver approved (12 June), then two Open revision
  requests on it, one still Open (16 June 14:00) and one the Officer declined (17 June 11:30);
- version C: a baseline the dual-role user (Officer and Approver) submitted (17 June 10:00);
- version D: a baseline the Officer submitted (15 June 09:00) and the Approver returned (15 June 15:00).

Every row the world adds is removed afterwards and counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_budget \\
    --module kentender_budget.tests.test_home_provider
"""

from __future__ import annotations

from datetime import datetime

import frappe

from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.services import budget_revision_request_contracts as brr
from kentender_budget.services.home_provider import entries
from kentender_budget.tests.test_bud_chg_001_v111_revision_request import DHI, HWD, _RevisionRequestBase, recording_consumer
from kentender_core.services import home_entries as he
from kentender_core.services import home_support
from kentender_core.services import home_workspace as hw
from kentender_core.services import responsibility_administration as administration
from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

H = datetime(2027, 6, 18, 10, 0)  # the Home read: two days after the 16 June hand-offs
T_A = datetime(2027, 6, 16, 9, 0)
T_B_SUBMITTED, T_B_APPROVED = datetime(2027, 6, 10, 9, 0), datetime(2027, 6, 12, 11, 0)
T_R1, T_R2_DECLINED = datetime(2027, 6, 16, 14, 0), datetime(2027, 6, 17, 11, 30)
T_C = datetime(2027, 6, 17, 10, 0)
T_D_SUBMITTED, T_D_RETURNED = datetime(2027, 6, 15, 9, 0), datetime(2027, 6, 15, 15, 0)
ALL = (he.MY_WORK, he.WAITING, he.OVERSIGHT, he.COMPLETED, he.COMING_UP)
HOOK = "kentender_budget.services.home_provider.entries"


class TestBudgetHomeProvider(_RevisionRequestBase):
	world: dict = {}

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.world = {}
		cls.ao = cls._make_user("ao", ("Accounting Officer",))
		cls.hopf = cls._make_user("hopf", ("Head of Procurement Function",))
		cls.hod = cls._make_user("hod", ())
		outcome = administration.grant(user=cls.hod, business_role="Head of User Department", organisation_unit=cls.ou_dhp, fixture_namespace="BUD_CHG_001_TESTS", actor="Administrator")
		cls._cleanup.append(("User Responsibility Assignment", outcome["assignment"]))
		cls.finance = cls.finance_officer

	@classmethod
	def tearDownClass(cls):
		budgets = list(cls._budgets)
		requests = [name for budget in budgets for name in frappe.get_all("Budget Revision Request", filters={"budget": budget}, pluck="name")]
		super().tearDownClass()
		frappe.db.commit()
		left = {
			"Procurement Budget": [b for b in budgets if frappe.db.exists("Procurement Budget", b)],
			"Procurement Budget Version": frappe.db.count("Procurement Budget Version", {"budget": ("in", budgets or ["-"])}),
			"Budget Revision Request": frappe.db.count("Budget Revision Request", {"name": ("in", requests or ["-"])}),
			"Budget Audit Event": frappe.db.count("Budget Audit Event", {"budget": ("in", budgets or ["-"])}),
		}
		if any(left.values()):
			raise AssertionError(f"Budget Home test rows left behind: {left}")

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.addCleanup(frappe.set_user, "Administrator")
		if not type(self).world:
			self._build()
		home_support.reset()

	# ----- the world -----

	def _stamp(self, version: str, event_type: str, at: datetime, **fields):
		for name in frappe.get_all("Budget Audit Event", filters={"budget_version": version, "event_type": event_type, **fields}, pluck="name"):
			frappe.db.set_value("Budget Audit Event", name, "event_at", at, update_modified=False)

	def _build(self):
		w = type(self).world
		_fy, w["budget_a"], w["a"] = self._draft(submit=True)
		frappe.db.set_value("Procurement Budget Version", w["a"], "submitted_at", T_A, update_modified=False)
		self._stamp(w["a"], "Budget version submitted", T_A)

		w["fy_b"], w["budget_b"], w["b"] = self._active()
		frappe.db.set_value("Procurement Budget Version", w["b"], "submitted_at", T_B_SUBMITTED, update_modified=False)
		self._stamp(w["b"], "Budget version submitted", T_B_SUBMITTED)
		self._stamp(w["b"], "Budget version approved and activated", T_B_APPROVED)
		w["r1"] = self.request(self.receive(w["fy_b"], self._line(w["b"], HWD), 62_000_000)).name
		frappe.db.set_value("Budget Revision Request", w["r1"], "requested_at", T_R1, update_modified=False)
		r2 = self.request(self.receive(w["fy_b"], self._line(w["b"], DHI), 101_000_000))
		w["r2"] = r2.name
		with recording_consumer():
			self._as(self.officer)
			declined = brr.decline_budget_revision_request({"budget_revision_request": r2.name, "reason": "No further allocation this year."})
			self.assertTrue(declined["ok"], declined)
		self._stamp(w["b"], "Budget revision request declined", T_R2_DECLINED)

		_fy, w["budget_c"], w["c"] = self._draft()
		self._as(self.dual)
		submitted = readiness.submit_budget_version({"budget_version": w["c"]})
		self.assertTrue(submitted["ok"], submitted.get("blockers"))
		frappe.db.set_value("Procurement Budget Version", w["c"], "submitted_at", T_C, update_modified=False)
		self._stamp(w["c"], "Budget version submitted", T_C)

		_fy, w["budget_d"], w["d"] = self._draft(submit=True)
		self._as(self.approver)
		returned = readiness.return_budget_version({"budget_version": w["d"], "return_reason": "Line titles must name the department before activation."})
		self.assertTrue(returned["ok"], returned)
		self._stamp(w["d"], "Budget version submitted", T_D_SUBMITTED)
		self._stamp(w["d"], "Budget version returned", T_D_RETURNED)
		frappe.set_user("Administrator")
		frappe.db.commit()

	# ----- helpers -----

	@property
	def w(self) -> dict:
		return type(self).world

	def region(self, user: str, region: str):
		home_support.reset()
		return entries(user=user, region=region)

	def mine(self, rows) -> list[dict]:
		roots = set(self.w.values())
		return [row for row in rows or [] if row["root"] in roots]

	def one(self, user: str, region: str, root: str) -> dict:
		rows = [row for row in self.region(user, region) or [] if row["root"] == root]
		self.assertEqual(len(rows), 1, f"{user} {region} {root}: {rows}")
		return rows[0]

	def title(self, budget: str) -> str:
		return frappe.db.get_value("Procurement Budget", budget, "title")

	def reference(self, version: str) -> str:
		return frappe.db.get_value("Procurement Budget Version", version, "generated_reference")

	def home(self, user: str, at: datetime = H):
		return hw.get_workspace(user, providers=[entries], at=at)

	def all_rows(self, user: str, region: str, at: datetime = H) -> list[dict]:
		"""Every presented row of the region, following Show more."""
		rows, cursor = [], None
		while True:
			page = hw.get_workspace(user, regions=[region], cursors={region: cursor} if cursor else None, providers=[entries], at=at)["regions"][region]
			rows += page["entries"]
			cursor = page["next_cursor"]
			if not cursor:
				return rows

	def row(self, user: str, region: str, reference: str, at: datetime = H) -> dict:
		rows = [row for row in self.all_rows(user, region, at) if row["reference"] == reference]
		self.assertEqual(len(rows), 1, f"{user} {region} {reference}: {rows}")
		return rows[0]

	def holders_text(self, text: str, prefix: str, suffix: str, role: str, *, without: str) -> None:
		"""`text` is prefix + the people who hold `role` site-wide other than `without` (either order) when there are two or fewer,
		otherwise "a {role}" + suffix. How many people hold it depends on the site."""
		self.assertTrue(text.startswith(prefix) and text.endswith(suffix), text)
		people = text[len(prefix) : len(text) - len(suffix)]
		users = frappe.get_all("User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"}, pluck="user", distinct=True)
		holders = [u for u in users if u != without and authorise_record(user=u, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND).allowed]
		if len(holders) <= 2:
			self.assertEqual(set(people.split(" or ")), {frappe.db.get_value("User", u, "full_name") for u in holders}, text)
		else:
			self.assertEqual(people, f"a {role}", text)

	# ----- My work -----

	def test_the_approver_approves_a_submitted_version_and_the_row_leads_with_the_budget_title(self):
		w = self.w
		row = self.one(self.approver, he.MY_WORK, w["a"])
		self.assertEqual((row["title"], row["action"], row["reference"]), (self.title(w["budget_a"]), "Approve budget version", self.reference(w["a"])))
		self.assertEqual((row["entered_at"], row["entered_verb"], row["action_id"]), (T_A, "Submitted", w["a"]))
		self.assertEqual((row["blocked"], row["reason"]), (False, ""))
		self.assertEqual(row["destination"], {"route": ["budget-funding", "review", w["a"]], "route_options": {}})
		later = self.one(self.approver, he.MY_WORK, w["c"])
		self.assertEqual(later["entered_at"], T_C)
		self.assertIsInstance(later["entered_at"], datetime)  # the raw instant, never a display string

	def test_the_budget_officer_answers_an_open_revision_request(self):
		w = self.w
		row = self.one(self.officer, he.MY_WORK, w["r1"])
		request_id = frappe.db.get_value("Budget Revision Request", w["r1"], "budget_revision_request_id")
		self.assertEqual((row["title"], row["reference"], row["action_id"]), (self.title(w["budget_b"]), request_id, w["r1"]))
		self.assertEqual(row["action"], "Revise Digital health workforce development for the plan update")
		self.assertEqual((row["entered_at"], row["entered_verb"]), (T_R1, "Received"))
		self.assertEqual(row["destination"], {"route": ["budget-funding"], "route_options": {"fiscal_year": w["fy_b"]}})
		# the declined request is answered: not work any more
		self.assertEqual([r for r in self.region(self.officer, he.MY_WORK) if r["root"] == w["r2"]], [])

	def test_nobody_approves_what_they_submitted_and_a_dual_role_user_still_approves_the_others(self):
		w = self.w
		self.assertEqual([r for r in self.region(self.dual, he.MY_WORK) if r["root"] == w["c"]], [])
		self.assertEqual(self.one(self.dual, he.MY_WORK, w["a"])["action"], "Approve budget version")
		self.assertEqual(self.one(self.approver, he.MY_WORK, w["c"])["action"], "Approve budget version")
		# the Officer holds no approval and a returned or active version is no one's approval
		self.assertEqual([r for r in self.region(self.officer, he.MY_WORK) if r["root"] in (w["a"], w["b"], w["c"], w["d"])], [])
		self.assertEqual([r for r in self.region(self.approver, he.MY_WORK) if r["root"] in (w["b"], w["d"])], [])

	# ----- Waiting -----

	def test_the_officer_waits_for_an_approver_on_their_own_submission(self):
		w = self.w
		row = self.one(self.officer, he.WAITING, w["a"])
		self.assertEqual((row["title"], row["reference"], row["action_id"], row["since"]), (self.title(w["budget_a"]), self.reference(w["a"]), w["a"], T_A))
		self.holders_text(row["action"], "Waiting for ", " to approve the budget version", "Budget Approver", without=self.officer)
		self.assertEqual(row["destination"], {"route": ["budget-funding", "review", w["a"]], "route_options": {}})
		self.assertTrue(row["holder"])
		# a version someone else submitted is not their wait
		self.assertEqual([r for r in self.region(self.officer, he.WAITING) if r["root"] == w["c"]], [])

	def test_a_dual_role_submitter_waits_for_another_approver(self):
		w = self.w
		row = self.one(self.dual, he.WAITING, w["c"])
		self.assertEqual(row["since"], T_C)
		self.holders_text(row["action"], "Waiting for ", " to approve the budget version", "Budget Approver", without=self.dual)

	def test_a_decided_or_returned_version_is_not_waiting_and_the_approver_waits_for_nothing(self):
		w = self.w
		self.assertEqual([r for r in self.region(self.officer, he.WAITING) if r["root"] in (w["b"], w["d"])], [])
		self.assertEqual(self.mine(self.region(self.approver, he.WAITING)), [])

	# ----- Records you oversee -----

	def test_the_auditor_sees_what_is_outstanding_read_only_with_since_and_the_holder(self):
		w = self.w
		rows = {row["root"]: row for row in self.mine(self.region(self.auditor, he.OVERSIGHT))}
		self.assertEqual(set(rows), {w["a"], w["c"], w["r1"]})  # not the returned, active or declined ones
		for root, since in ((w["a"], T_A), (w["c"], T_C), (w["r1"], T_R1)):
			self.assertEqual((rows[root]["since"], rows[root]["outstanding"], rows[root]["action_id"]), (since, True, root))
		self.holders_text(rows[w["a"]]["action"], "Waiting for ", " to approve the budget version", "Budget Approver", without="")
		self.holders_text(rows[w["r1"]]["action"], "Waiting for ", " to revise Digital health workforce development for the plan update", "Budget Officer", without="")
		self.assertEqual(rows[w["r1"]]["title"], self.title(w["budget_b"]))
		for key in (he.MY_WORK, he.WAITING, he.COMPLETED):
			self.assertEqual(self.mine(self.region(self.auditor, key)), [], key)

	def test_what_is_the_actors_to_do_or_to_wait_on_is_not_overseen_and_the_same_action_id_deduplicates(self):
		w = self.w
		self.assertEqual({r["root"] for r in self.mine(self.region(self.approver, he.OVERSIGHT))}, {w["r1"]})  # a and c are theirs to approve
		self.assertEqual({r["root"] for r in self.mine(self.region(self.officer, he.OVERSIGHT))}, {w["c"]})  # a is waited on, r1 is theirs
		self.assertEqual(self.mine(self.region(self.dual, he.OVERSIGHT)), [])
		# an actor who both holds and oversees would show the matter once: the identities are the same
		auditor_a = self.one(self.auditor, he.OVERSIGHT, w["a"])
		approver_a = self.one(self.approver, he.MY_WORK, w["a"])
		self.assertEqual(auditor_a["identity"], approver_a["identity"])
		self.assertEqual(self.one(self.auditor, he.OVERSIGHT, w["r1"])["identity"], self.one(self.officer, he.MY_WORK, w["r1"])["identity"])

	def test_the_finance_confirmation_officer_has_the_region_but_the_owners_read_check_shows_her_nothing(self):
		"""She holds a Budget responsibility, but the version and request DocTypes grant her no read (DocPerm), so the owner's
		own read check removes every outstanding row: Home never discloses what the owner's read would refuse."""
		w = self.w
		rows = self.region(self.finance, he.OVERSIGHT)
		self.assertIsInstance(rows, list)
		self.assertFalse(frappe.has_permission("Procurement Budget Version", "read", doc=w["a"], user=self.finance))
		self.assertEqual(self.mine(rows), [])

	def test_approved_only_readers_have_no_outstanding_concept(self):
		for user in (self.ao, self.hopf, self.hod):
			for region in ALL:
				self.assertIsNone(self.region(user, region), (user, region))
			view = self.home(user)
			self.assertEqual({r["coverage"] for r in view["regions"].values()}, {hw.NOT_APPLICABLE}, user)

	# ----- Coming up -----

	def test_budget_contributes_nothing_to_coming_up(self):
		for user in (self.officer, self.approver, self.dual, self.auditor, self.ao):
			self.assertIsNone(self.region(user, he.COMING_UP), user)

	# ----- Recently completed actions -----

	def test_the_approvers_own_decisions_in_the_last_thirty_days(self):
		w = self.w
		approved = self.row(self.approver, he.COMPLETED, self.reference(w["b"]))
		self.assertEqual((approved["title"], approved["action"]), (self.title(w["budget_b"]), "Approved budget version"))
		self.assertEqual(approved["sentence"], "You approved and activated this budget version on 12 June 2027, 11:00 EAT.")
		self.assertEqual(approved["destination"]["route"][0], "budget-funding")
		returned = self.row(self.approver, he.COMPLETED, self.reference(w["d"]))
		self.assertEqual((returned["action"], returned["sentence"]), ("Returned budget version", "You returned this budget version on 15 June 2027, 15:00 EAT."))
		self.assertEqual([r["sentence"].split(" on ")[0] for r in self.all_rows(self.approver, he.COMPLETED) if r["reference"] in (self.reference(w["b"]), self.reference(w["d"]))], ["You returned this budget version", "You approved and activated this budget version"])  # newest first

	def test_the_officers_submissions_and_their_decline_and_nobody_elses(self):
		w = self.w
		rows = [r for r in self.all_rows(self.officer, he.COMPLETED) if r["reference"] in {self.reference(v) for v in (w["a"], w["b"], w["c"], w["d"])}]
		self.assertEqual(
			[(r["reference"], r["action"], r["sentence"]) for r in rows],
			[
				(self.reference(w["b"]), "Declined budget revision request", "You declined a budget revision request on 17 June 2027, 11:30 EAT."),
				(self.reference(w["a"]), "Submitted budget version for approval", "You submitted this budget version for approval on 16 June 2027, 09:00 EAT."),
				(self.reference(w["d"]), "Submitted budget version for approval", "You submitted this budget version for approval on 15 June 2027, 09:00 EAT."),
				(self.reference(w["b"]), "Submitted budget version for approval", "You submitted this budget version for approval on 10 June 2027, 09:00 EAT."),
			],
		)
		# the dual-role user's own submission is theirs alone
		self.assertEqual([r["sentence"] for r in self.all_rows(self.dual, he.COMPLETED) if r["reference"] == self.reference(w["c"])], ["You submitted this budget version for approval on 17 June 2027, 10:00 EAT."])
		self.assertEqual([r for r in self.all_rows(self.officer, he.COMPLETED) if r["reference"] == self.reference(w["c"])], [])

	def test_the_core_window_drops_a_completed_action_older_than_thirty_days(self):
		w = self.w
		event = frappe.get_all("Budget Audit Event", filters={"budget_version": w["d"], "event_type": "Budget version submitted"}, pluck="name")[0]
		frappe.db.set_value("Budget Audit Event", event, "event_at", datetime(2027, 5, 1, 9, 0), update_modified=False)
		self.addCleanup(frappe.db.set_value, "Budget Audit Event", event, "event_at", T_D_SUBMITTED, update_modified=False)
		self.assertNotIn(self.reference(w["d"]), [r["reference"] for r in self.all_rows(self.officer, he.COMPLETED)])

	def test_a_closure_decline_is_not_the_actors_decision_and_system_events_are_ignored(self):
		w = self.w
		frappe.db.commit()
		budget = frappe.get_doc({"doctype": "Budget Audit Event", "budget": w["budget_b"], "budget_version": w["b"], "event_type": "Budget revision request declined", "event_at": datetime(2027, 6, 17, 12, 0), "actor": self.officer, "actor_kind": "user", "correlation_id": "home-closure", "reason": brr.CLOSED_BUDGET_REASON}).insert(ignore_permissions=True)
		system = frappe.get_doc({"doctype": "Budget Audit Event", "budget": w["budget_b"], "budget_version": w["b"], "event_type": "Budget version approved and activated", "event_at": datetime(2027, 6, 17, 12, 5), "actor": self.officer, "actor_kind": "system", "correlation_id": "home-system"}).insert(ignore_permissions=True)

		def remove():
			frappe.flags.allow_budget_audit_purge = True
			try:
				for doc in (budget, system):
					frappe.delete_doc("Budget Audit Event", doc.name, force=True, ignore_permissions=True)
			finally:
				frappe.flags.allow_budget_audit_purge = False
			frappe.db.commit()

		self.addCleanup(remove)
		keys = [r["key"].split("|")[-1] for r in self.all_rows(self.officer, he.COMPLETED)]
		self.assertNotIn(budget.name, keys)
		self.assertNotIn(system.name, keys)

	# ----- applicability, personas, technical readers -----

	def test_none_versus_empty_by_responsibility(self):
		for region in (he.MY_WORK, he.WAITING, he.OVERSIGHT, he.COMPLETED):
			self.assertIsNone(self.region(self.nobody, region), region)
			self.assertIsNone(self.region(self.planner, region), region)  # a Planner holds nothing in Budget
			for user in (self.officer, self.approver, self.auditor, self.finance):
				self.assertIsInstance(self.region(user, region), list, (user, region))
		self.assertEqual(self.mine(self.region(self.auditor, he.MY_WORK)), [])

	def test_the_technical_reader_and_an_unrelated_internal_user_get_nothing(self):
		for region in he.REGIONS:
			self.assertIsNone(self.region("Administrator", region), region)
			self.assertIsNone(self.region(self.nobody, region), region)
		view = self.home("Administrator")
		self.assertEqual((view["empty"], view["regions"]["my_work"]["entries"]), (True, []))
		nobody = self.home(self.nobody)
		self.assertEqual(nobody["state"], "ready")
		self.assertFalse(any(region["entries"] for region in nobody["regions"].values()))
		self.assertEqual({region["coverage"] for region in nobody["regions"].values()}, {hw.NOT_APPLICABLE})

	def test_a_user_without_the_role_sees_none_of_it_and_a_revoked_responsibility_removes_it(self):
		w = self.w
		extra = self._make_user("extra", ("Budget Approver",))
		self.assertEqual(self.row(extra, he.MY_WORK, self.reference(w["a"]))["action"], "Approve budget version")
		self.assertTrue(self.home(extra)["regions"]["my_work"]["applicable"])
		assignment = frappe.get_all("User Responsibility Assignment", filters={"user": extra}, pluck="name")[0]
		administration.revoke(assignment, reason="Revoked inside the Home provider test.", actor="Administrator")
		revoked = self.home(extra)
		self.assertEqual({region["coverage"] for region in revoked["regions"].values()}, {hw.NOT_APPLICABLE})
		self.assertFalse([row for region in revoked["regions"].values() for row in region["entries"]])
		for region in he.REGIONS:
			self.assertIsNone(self.region(extra, region), region)

	def test_the_provider_writes_nothing(self):
		frappe.db.commit()
		before = frappe.db.transaction_writes
		for user in (self.officer, self.approver, self.dual, self.auditor, self.finance, self.ao, self.hopf, self.hod, self.planner, self.nobody, "Administrator"):
			for region in he.REGIONS:
				self.region(user, region)
		self.assertEqual(frappe.db.transaction_writes, before)

	def test_an_unknown_region_is_refused(self):
		with self.assertRaises(ValueError):
			entries(user=self.officer, region="not_a_region")
		self.assertIsNone(entries(user="Guest", region=he.MY_WORK))

	# ----- destinations, hook -----

	def test_the_provider_is_registered_on_the_home_hook(self):
		self.assertIn(HOOK, frappe.get_hooks("kt_home_providers") or [])

	def test_every_destination_opens_a_real_page_the_actor_may_open(self):
		self.assertTrue(frappe.db.exists("Page", "budget-funding"))
		seen = set()
		for user in (self.officer, self.approver, self.dual, self.auditor, self.finance):
			for region in (he.MY_WORK, he.WAITING, he.OVERSIGHT, he.COMPLETED):
				for row in self.mine(self.region(user, region)):
					seen.add(row["destination"]["route"][0])
					self.assertTrue(hw._page_permitted(row["destination"]["route"][0], user), (user, row["destination"]))
		self.assertEqual(seen, {"budget-funding"})

	# ----- through the Home read -----

	def test_the_approvers_home_renders_the_timing_strings(self):
		w = self.w
		row = self.row(self.approver, he.MY_WORK, self.reference(w["a"]))
		self.assertEqual((row["module"], row["timing"], row["action"]), ("Budget & Funding", "Submitted 2 days ago (16 June, 09:00)", "Approve budget version"))
		self.assertEqual(self.row(self.approver, he.MY_WORK, self.reference(w["c"]))["timing"], "Submitted yesterday (17 June, 10:00)")
		oversight = self.row(self.approver, he.OVERSIGHT, frappe.db.get_value("Budget Revision Request", w["r1"], "budget_revision_request_id"))
		self.assertEqual(oversight["timing"], "Outstanding 2 days (since 16 June, 14:00)")

	def test_the_officers_home_renders_work_and_waiting(self):
		w = self.w
		request_id = frappe.db.get_value("Budget Revision Request", w["r1"], "budget_revision_request_id")
		self.assertEqual(self.row(self.officer, he.MY_WORK, request_id)["timing"], "Received 2 days ago (16 June, 14:00)")
		waiting = self.row(self.officer, he.WAITING, self.reference(w["a"]))
		self.assertEqual(waiting["timing"], "Waiting 2 days (since 16 June, 09:00)")
		self.assertTrue(waiting["holder"])
		view = self.home(self.officer)
		self.assertTrue(view["regions"]["my_work"]["applicable"] and view["regions"]["waiting"]["applicable"])

	def test_the_auditors_home_counts_outstanding_matters(self):
		w = self.w
		view = self.home(self.auditor)
		self.assertTrue(view["regions"]["oversight"]["applicable"])
		self.assertFalse(view["regions"]["my_work"]["entries"])
		self.assertEqual(self.row(self.auditor, he.OVERSIGHT, self.reference(w["a"]))["timing"], "Outstanding 2 days (since 16 June, 09:00)")
