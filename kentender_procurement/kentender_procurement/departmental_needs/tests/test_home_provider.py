# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — the Departmental Needs feed to Home (`departmental_needs/services/home_provider.py`).

The module's own command world (`DepartmentalNeedsCommandCase`: Grace Wanjiku, Peter Kimani, Julia Njeri, Mercy Kilonzo, Naomi
Chebet on Digital Health). Each test builds its own Needs through the owner's real commands and sets the §10B instants on the
records (17-18 June 2027), as the Tenders test does; the provider only reads. A decision that would send an acceptance event to
Planning is not driven: the Need is moved to Accepted for planning in place and its decision row is inserted (the provider reads
the rows, not the event). Every Need a test makes, and what hangs from it, is removed afterwards and counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.departmental_needs.tests.test_home_provider
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import frappe

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import home_workspace as hw
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.departmental_needs.constants import REASON_REQUIRED_ACTIONS
from kentender_procurement.departmental_needs.seeds import playwright_ui_fixtures as pw_fixtures
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	ACTING_REVIEWER,
	AUDITOR,
	AUTHOR,
	DEPARTMENTAL_AUTHOR,
	FY,
	HEAD_OF_USER_DEPARTMENT,
	PLANNER,
	REVIEWER,
	_granted_units,
)
from kentender_procurement.departmental_needs.services import guidance, home_provider, lifecycle
from kentender_procurement.departmental_needs.services.home_provider import entries
from kentender_procurement.departmental_needs.tests.test_departmental_needs_lifecycle import NS_TEST_GRANT, REASON, DepartmentalNeedsCommandCase

AO = "amina.hassan@moh.example.test"
HOPF = "charles.mutiso@moh.example.test"
OFFICER = "brian.wafula@moh.example.test"  # a Procurement Officer: no Needs responsibility
NO_GRANT = "samuel.otieno@moh.example.test"  # his Head of User Department assignment ended in August
EXTRA = "ndst.home.extra@example.test"  # an unrelated internal user until a test grants it something
EXTRA_NS = "KT_TEST_NDSHOME"
H12 = datetime(2027, 6, 18, 10, 0)
SUBMITTED_AT, RETURNED_AT, DECIDED_AT = "2027-06-17 14:00:00", "2027-06-18 09:00:00", "2027-06-18 10:00:00"
SPEC_PAGES = ("departmental-needs",)
NEEDS_TABLES = ("Departmental Need", "Departmental Need Revision", "Departmental Need Decision", "Departmental Need Review Task", "Need Withdrawal Request", "Departmental Need Event")


def _dt(text: str) -> datetime:
	return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")


def _counts() -> dict[str, int]:
	counts = {doctype: frappe.db.count(doctype) for doctype in NEEDS_TABLES}
	counts["Notification Log"] = frappe.db.count("Notification Log", {"document_type": "Departmental Need"})
	counts["Need Planning Intake Projection"] = frappe.db.count("Need Planning Intake Projection")
	counts["Need Planning Usage Projection"] = frappe.db.count("Need Planning Usage Projection")
	counts["extra_user"] = frappe.db.count("User", {"name": EXTRA})
	counts["assignments"] = frappe.db.count("User Responsibility Assignment", {"fixture_namespace": ("in", [EXTRA_NS, NS_TEST_GRANT])})
	return counts


class HomeCase(DepartmentalNeedsCommandCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.before = _counts()
		cls.addClassCleanup(cls.remove_extra)
		if not frappe.db.exists("User", EXTRA):
			user = frappe.get_doc({"doctype": "User", "email": EXTRA, "first_name": "NDST Extra", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True)
			user.add_roles("Desk User")
		frappe.db.commit()

	@classmethod
	def remove_extra(cls):
		frappe.set_user("Administrator")
		for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": EXTRA_NS}, pluck="name"):
			frappe.delete_doc("User Responsibility Assignment", name, force=1, ignore_permissions=True)
		for name in frappe.get_all("Contact Email", filters={"email_id": EXTRA}, pluck="parent"):
			frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
		if frappe.db.exists("User", EXTRA):
			frappe.delete_doc("User", EXTRA, force=1, ignore_permissions=True)
		frappe.db.commit()
		after = _counts()
		if after != cls.before:
			raise AssertionError(f"Needs Home test rows left behind: before {cls.before}, after {after}")

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		home_support.reset()
		self.needs: list[str] = []
		started = frappe.utils.now()
		self.addCleanup(self.purge, started)
		self.addCleanup(self.release_grants)

	def purge(self, started: str) -> None:
		"""Every Need this test made (not the §14 seed: nothing it made before `started`), and what hangs from it."""
		frappe.set_user("Administrator")
		pw_fixtures.purge_untagged_needs_since(started)

	def release_grants(self) -> None:
		"""The grants a test made inside this module's namespaces: revoked (so the Role projection follows), then removed."""
		frappe.set_user("Administrator")
		for namespace in (EXTRA_NS, NS_TEST_GRANT):
			for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": namespace}, pluck="name"):
				if frappe.db.get_value("User Responsibility Assignment", name, "status") == "Enabled":
					administration.revoke(name, reason="Revoked inside the Home provider test.", actor="Administrator")
				frappe.delete_doc("User Responsibility Assignment", name, force=1, ignore_permissions=True)
		frappe.db.commit()

	# ----- the owner's commands, then the §10B instants set on the records -----

	def made(self, title: str = "Clinical deployment laptops for rollout", at: str = SUBMITTED_AT) -> dict:
		"""A Need Grace created and submitted; Peter's task opened and the submission stamped at `at`."""
		submitted = self.submit(self.create(title=title))
		self.stamp_submission(submitted, at)
		self.needs.append(submitted["need"])
		return submitted

	def stamp_submission(self, submitted: dict, at: str) -> None:
		frappe.set_user("Administrator")
		frappe.db.set_value("Departmental Need Review Task", submitted["task"], "opened_at", _dt(at), update_modified=False)
		frappe.db.set_value("Departmental Need Decision", {"review_task": submitted["task"], "action": ("in", ["Submit", "Resubmit", "Submit successor"])}, "occurred_at", _dt(at), update_modified=False)

	def stamp_decision(self, need: str, action: str, at: str) -> str:
		name = frappe.db.get_value("Departmental Need Decision", {"departmental_need": need, "action": action}, "name", order_by="creation desc")
		frappe.db.set_value("Departmental Need Decision", name, "occurred_at", _dt(at), update_modified=False)
		return name

	def returned(self, submitted: dict, at: str = RETURNED_AT) -> dict:
		result = self.decide(submitted, "return", reason=REASON)
		frappe.set_user("Administrator")
		self.stamp_decision(submitted["need"], "Return for correction", at)
		return result

	def add_decision(self, need: str, action: str, *, actor: str, at: datetime, prior: str = "Submitted", result: str = "Accepted for planning") -> str:
		doc = frappe.get_doc({
			"doctype": "Departmental Need Decision", "decision_id": f"NDD-{uuid4().hex.upper()}", "departmental_need": need,
			"need_revision": frappe.db.get_value("Departmental Need", need, "current_revision"), "action": action, "actor": actor, "occurred_at": at,
			"prior_state": prior, "result_state": result, "idempotency_key": f"nds-home-{uuid4().hex}", "reason": REASON if action in REASON_REQUIRED_ACTIONS else "",
		}).insert(ignore_permissions=True)
		return doc.name

	def accept_quietly(self, submitted: dict) -> None:
		"""Accepted for planning without the acceptance event Planning would receive: the state, the accepted revision, the closed
		task and the decision row the command writes."""
		frappe.set_user("Administrator")
		need = submitted["need"]
		revision = frappe.db.get_value("Departmental Need", need, "current_revision")
		frappe.db.set_value("Departmental Need Revision", revision, "revision_status", "Accepted", update_modified=False)
		frappe.db.set_value("Departmental Need", need, {"current_state": "Accepted for planning", "current_accepted_revision": revision}, update_modified=False)
		frappe.db.set_value("Departmental Need Review Task", submitted["task"], "status", "Completed", update_modified=False)
		self.add_decision(need, "Accept for planning", actor=REVIEWER, at=_dt(DECIDED_AT))

	def version_of(self, need: str) -> int:
		return int(frappe.db.get_value("Departmental Need", need, "record_version"))

	def grant(self, user: str, role: str, unit: str = "") -> None:
		administration.grant(user=user, business_role=role, organisation_unit=unit or self.ou, fixture_namespace=EXTRA_NS, actor="Administrator")

	# ----- reads -----

	def region(self, user: str, region: str):
		home_support.reset()
		return entries(user=user, region=region)

	def one(self, user: str, region: str, need: str, action_id: str = ""):
		rows = [row for row in self.region(user, region) or [] if row["root"] == need and (not action_id or row["action_id"] == action_id)]
		self.assertEqual(len(rows), 1, f"{user} {region} {need}: {rows}")
		return rows[0]

	def about(self, user: str, region: str, need: str) -> list[dict]:
		return [row for row in self.region(user, region) or [] if row["root"] == need]

	def name(self, user: str) -> str:
		return frappe.db.get_value("User", user, "full_name")

	def home(self, user: str, at: datetime = H12):
		return hw.get_workspace(user, providers=[entries], at=at)

	def rows_of(self, user: str, region: str, at: datetime = H12) -> list[dict]:
		"""Every presented row of the region, following Show more (the test site also holds the seeded Needs)."""
		rows, cursor = [], None
		while True:
			page = hw.get_workspace(user, regions=[region], cursors={region: cursor} if cursor else None, providers=[entries], at=at)["regions"][region]
			rows += page["entries"]
			cursor = page["next_cursor"]
			if not cursor:
				return rows

	def row(self, user: str, region: str, need: str, at: datetime = H12) -> dict:
		reference = frappe.db.get_value("Departmental Need", need, "need_reference")
		rows = [row for row in self.rows_of(user, region, at) if row["reference"] == reference]
		self.assertEqual(len(rows), 1, f"{user} {region}: {rows}")
		return rows[0]

	def title_of(self, need: str) -> str:
		return frappe.db.get_value("Departmental Need Revision", frappe.db.get_value("Departmental Need", need, "current_revision"), "title")


class TestNeedsHomeProvider(HomeCase):
	# ----- My work: the Head of User Department -----

	def test_peters_review_row_is_the_specs_requirement_row(self):
		submitted = self.made()
		need = submitted["need"]
		row = self.one(REVIEWER, he.MY_WORK, need)
		self.assertEqual((row["title"], row["action"], row["reference"]), ("Clinical deployment laptops for rollout", "Decide whether this requirement is available to Procurement Planning", need))
		self.assertEqual((row["entered_at"], row["entered_verb"], row["action_id"]), (_dt(SUBMITTED_AT), "Submitted", submitted["task"]))
		self.assertEqual(row["destination"], {"route": ["departmental-needs", "review", submitted["task"]], "route_options": {}})
		self.assertEqual((row["blocked"], row["reason"], row["owner"], row["region"]), (False, "", "needs", he.MY_WORK))
		self.assertEqual(row["source_revision"], self.token(submitted["task"]))
		self.assertIsInstance(row["entered_at"], datetime)  # the raw instant, never the display string the old provider built
		# the acting Head of the unit holds the same task
		self.assertEqual(self.one(ACTING_REVIEWER, he.MY_WORK, need)["action_id"], submitted["task"])
		# the owner's own wording, from the same answer the page shows
		answer = guidance.need_guidance(frappe.get_doc("Departmental Need", need), principal=REVIEWER, actions=[{"code": "review"}], intake_open=True)["next_step"]
		self.assertEqual(row["action"], answer["headline"])

	def test_the_home_read_renders_peters_submitted_yesterday_row(self):
		need = self.made()["need"]
		row = self.row(REVIEWER, "my_work", need)
		self.assertEqual((row["action"], row["timing"], row["module"]), ("Decide whether this requirement is available to Procurement Planning", "Submitted yesterday (17 June, 14:00)", "Needs"))
		self.assertEqual(row["title"], "Clinical deployment laptops for rollout")
		self.assertEqual(self.row(REVIEWER, "my_work", need, at=datetime(2027, 6, 19, 10, 0))["timing"], "Submitted 2 days ago (17 June, 14:00)")

	def test_only_the_reviewers_in_scope_are_offered_the_row(self):
		need = self.made()["need"]
		for user in (AUTHOR, PLANNER, AUDITOR, AO, HOPF, EXTRA, NO_GRANT, OFFICER):
			self.assertEqual(self.about(user, he.MY_WORK, need), [], user)

	def test_the_author_who_is_also_a_head_never_reviews_their_own_need_but_waits_for_another(self):
		user, second = self.author_reviewer(), self.second_reviewer()  # Peter also authors; Grace also heads the unit
		created = self.create_as(user)
		frappe.set_user(user)
		submitted = lifecycle.submit_need(need=created["need"], expected_version=created["record_version"], idempotency_key=self.key())
		self.stamp_submission(submitted, SUBMITTED_AT)
		need = submitted["need"]
		self.assertEqual(self.about(user, he.MY_WORK, need), [])
		self.assertEqual(self.one(second, he.MY_WORK, need)["action_id"], submitted["task"])
		wait = self.one(user, he.WAITING, need)
		self.assertEqual(wait["action"], "Waiting for another Head of User Department to review this requirement")
		self.assertEqual(wait["since"], _dt(SUBMITTED_AT))

	def test_a_withdrawal_request_is_the_heads_decision_and_the_authors_wait(self):
		submitted = self.made()
		self.accept_quietly(submitted)
		need = submitted["need"]
		frappe.set_user(AUTHOR)
		requested = lifecycle.request_withdrawal(need=need, expected_version=self.version_of(need), idempotency_key=self.key(), reason=REASON)
		frappe.set_user("Administrator")
		frappe.db.set_value("Departmental Need Review Task", requested["task"], "opened_at", _dt(SUBMITTED_AT), update_modified=False)
		self.stamp_decision(need, "Request withdrawal", SUBMITTED_AT)
		row = self.one(REVIEWER, he.MY_WORK, need)
		self.assertEqual((row["action"], row["entered_verb"], row["entered_at"], row["action_id"]), ("Decide the withdrawal request", "Received", _dt(SUBMITTED_AT), requested["task"]))
		self.assertEqual(row["destination"]["route"], ["departmental-needs", "review", requested["task"], "withdrawal"])
		wait = self.one(AUTHOR, he.WAITING, need)
		self.assertTrue(wait["action"].startswith("Waiting for ") and wait["action"].endswith("to decide the withdrawal request"), wait["action"])
		self.assertEqual(wait["since"], _dt(SUBMITTED_AT))
		self.assertEqual(self.about(AUTHOR, he.MY_WORK, need), [])
		# the Auditor oversees the same matter under the same action
		self.assertEqual(self.one(AUDITOR, he.OVERSIGHT, need)["action_id"], requested["task"])
		completed = self.one(AUTHOR, he.COMPLETED, need, self.stamp_decision(need, "Request withdrawal", SUBMITTED_AT))
		self.assertEqual(completed["action"], "Requested withdrawal")
		self.assertTrue(completed["sentence"].startswith("You asked to withdraw this requirement on 17 June 2027, 14:00 ") and "awaiting the withdrawal decision by " in completed["sentence"], completed["sentence"])

	def test_an_update_under_review_is_the_heads_decision_and_a_returned_update_the_authors_correction(self):
		submitted = self.made()
		self.accept_quietly(submitted)
		need = submitted["need"]
		frappe.set_user(AUTHOR)
		opened = lifecycle.create_accepted_need_successor(need=need, expected_version=self.version_of(need), idempotency_key=self.key())
		# an update the author still holds is nobody's hand-off
		for user, region in ((AUTHOR, he.MY_WORK), (AUTHOR, he.WAITING), (REVIEWER, he.MY_WORK), (AUDITOR, he.OVERSIGHT)):
			self.assertEqual(self.about(user, region, need), [], (user, region))
		sent = lifecycle.submit_need(need=need, expected_version=self.version_of(need), idempotency_key=self.key())
		self.stamp_submission(sent, SUBMITTED_AT)
		row = self.one(REVIEWER, he.MY_WORK, need)
		self.assertEqual((row["action"], row["entered_verb"], row["action_id"], row["entered_at"]), ("Decide whether the proposed changes replace the accepted requirement", "Submitted", sent["task"], _dt(SUBMITTED_AT)))
		wait = self.one(AUTHOR, he.WAITING, need)
		self.assertTrue(wait["action"].endswith("to review the proposed changes"), wait["action"])
		self.decide({**sent, "record_version": self.version_of(need)}, "return", reason=REASON)
		frappe.set_user("Administrator")
		self.stamp_decision(need, "Return successor", RETURNED_AT)
		self.assertEqual(self.about(AUTHOR, he.WAITING, need), [])
		correction = self.one(AUTHOR, he.MY_WORK, need)
		self.assertEqual((correction["action_id"], correction["entered_at"], correction["entered_verb"]), (f"{need}:correct", _dt(RETURNED_AT), "Received"))
		self.assertEqual(correction["action"], "Continue the update and submit it for review")  # the owner's own answer for the author of a returned update
		self.assertEqual(correction["destination"]["route"], ["departmental-needs", need, "edit"])
		# the author holds a Draft copy made from the returned update
		current = frappe.db.get_value("Departmental Need", need, "current_revision")
		self.assertNotEqual(current, opened["successor_revision"])
		self.assertEqual(frappe.db.get_value("Departmental Need Revision", current, "based_on_revision"), opened["successor_revision"])

	# ----- My work: the author -----

	def test_a_returned_need_is_the_authors_correction_with_the_owners_wording(self):
		submitted = self.made()
		need = submitted["need"]
		self.returned(submitted)
		row = self.one(AUTHOR, he.MY_WORK, need)
		self.assertEqual((row["title"], row["action"], row["reference"]), ("Clinical deployment laptops for rollout", "Make the requested changes and resubmit", need))
		self.assertEqual((row["entered_at"], row["entered_verb"], row["action_id"]), (_dt(RETURNED_AT), "Received", f"{need}:correct"))
		self.assertEqual(row["destination"], {"route": ["departmental-needs", need, "edit"], "route_options": {}})
		self.assertEqual((row["blocked"], row["reason"]), (False, ""))
		self.assertEqual(self.row(AUTHOR, "my_work", need)["timing"], "Received today (18 June, 09:00)")
		# the head who returned it has nothing left to do, and the wait is over
		self.assertEqual(self.about(REVIEWER, he.MY_WORK, need), [])
		self.assertEqual(self.about(AUTHOR, he.WAITING, need), [])

	def test_a_returned_need_is_blocked_only_while_submissions_are_closed_and_says_why(self):
		submitted = self.made()
		need = submitted["need"]
		self.returned(submitted)
		self.close_window()
		row = self.one(AUTHOR, he.MY_WORK, need)
		self.assertEqual((row["blocked"], row["reason"], row["action"]), (True, "New submissions are closed", "Make the requested changes and resubmit"))
		self.assertTrue(self.row(AUTHOR, "my_work", need)["blocked"])
		# nobody else is told the author is blocked
		self.assertEqual(self.about(REVIEWER, he.MY_WORK, need), [])

	def test_a_review_row_is_never_blocked_even_when_submissions_are_closed(self):
		need = self.made()["need"]
		self.close_window()
		row = self.one(REVIEWER, he.MY_WORK, need)
		self.assertEqual((row["blocked"], row["reason"]), (False, ""))

	# ----- Waiting -----

	def test_the_author_waits_for_the_heads_with_the_owners_wording_and_the_submission_instant(self):
		need = self.made()["need"]
		wait = self.one(AUTHOR, he.WAITING, need)
		self.assertEqual((wait["title"], wait["reference"], wait["since"], wait["due"]), ("Clinical deployment laptops for rollout", need, _dt(SUBMITTED_AT), None))
		self.assertTrue(wait["action"].startswith("Waiting for ") and wait["action"].endswith("(Head of User Department) to review the requirement"), wait["action"])
		self.assertIn(self.name(REVIEWER), wait["action"])
		self.assertEqual(wait["action"], f"Waiting for {wait['holder']} to review the requirement")  # the holder is the owner's display, once
		self.assertEqual((wait["action_id"], wait["destination"]["route"]), (f"{need}:waiting", ["departmental-needs", need]))
		view = self.row(AUTHOR, "waiting", need)
		self.assertEqual((view["timing"], view["holder"]), ("Waiting 1 day (since 17 June, 14:00)", wait["holder"]))
		# the title is the requirement's, the stage is not swapped in (the old provider put "Waiting for…" in the title)
		self.assertNotIn("Waiting", wait["title"])
		for user in (REVIEWER, PLANNER, AUDITOR, EXTRA):
			self.assertEqual(self.about(user, he.WAITING, need), [], user)

	def test_a_waiting_row_without_a_recorded_start_is_not_listed(self):
		need = self.made()["need"]
		frappe.db.delete("Departmental Need Decision", {"departmental_need": need, "action": "Submit"})
		self.assertEqual(self.about(AUTHOR, he.WAITING, need), [])
		self.assertIsInstance(self.region(AUTHOR, he.WAITING), list)  # the region still answers; it does not raise

	# ----- Records you oversee -----

	def test_the_head_sees_the_matter_under_the_same_action_as_the_task_so_it_shows_once(self):
		submitted = self.made()
		need = submitted["need"]
		overseen = self.one(REVIEWER, he.OVERSIGHT, need)
		self.assertEqual((overseen["action_id"], overseen["outstanding"], overseen["since"], overseen["title"]), (submitted["task"], True, _dt(SUBMITTED_AT), "Clinical deployment laptops for rollout"))
		self.assertEqual(self.one(REVIEWER, he.MY_WORK, need)["action_id"], submitted["task"])
		self.assertEqual(len([r for r in self.rows_of(REVIEWER, "my_work") if r["reference"] == need]), 1)
		self.assertFalse([r for r in self.rows_of(REVIEWER, "oversight") if r["reference"] == need])  # not shown twice
		# the author does not oversee their own Need
		self.assertEqual(self.about(AUTHOR, he.OVERSIGHT, need), [])

	def test_the_auditor_the_accounting_officer_and_the_head_of_procurement_see_a_need_awaiting_review(self):
		need = self.made()["need"]
		for user in (AUDITOR, AO, HOPF):
			row = self.one(user, he.OVERSIGHT, need)
			self.assertEqual((row["outstanding"], row["since"], row["title"], row["reference"]), (True, _dt(SUBMITTED_AT), "Clinical deployment laptops for rollout", need), user)
			self.assertTrue(row["action"].startswith("Waiting for ") and row["action"].endswith("to review the requirement"), row["action"])
			self.assertEqual(row["destination"]["route"], ["departmental-needs", need])
			self.assertIn(self.name(REVIEWER), row["holder"])
		self.assertEqual(self.row(AUDITOR, "oversight", need)["timing"], "Outstanding 1 day (since 17 June, 14:00)")

	def test_a_returned_need_is_overseen_by_its_head_and_the_auditor_but_not_by_the_two_offices(self):
		submitted = self.made()
		need = submitted["need"]
		self.returned(submitted)
		for user in (AUDITOR, REVIEWER):
			row = self.one(user, he.OVERSIGHT, need)
			self.assertEqual((row["action_id"], row["since"], row["outstanding"]), (f"{need}:correct", _dt(RETURNED_AT), True), user)
			self.assertEqual(row["action"], f"Waiting for {self.name(AUTHOR)} to correct and resubmit the requirement")
			self.assertEqual(row["holder"], f"{self.name(AUTHOR)} (Departmental Author)")
		for user in (AO, HOPF, AUTHOR, PLANNER, EXTRA):  # a returned Need is the author's again (OVS); the author has it in My work
			self.assertEqual(self.about(user, he.OVERSIGHT, need), [], user)

	def test_oversight_applies_only_to_a_head_the_auditor_and_the_two_offices(self):
		self.made()
		for user in (REVIEWER, ACTING_REVIEWER, AUDITOR, AO, HOPF):
			self.assertIsInstance(self.region(user, he.OVERSIGHT), list, user)
		for user in (PLANNER, OFFICER, NO_GRANT, EXTRA):
			self.assertIsNone(self.region(user, he.OVERSIGHT), user)
		self.grant(EXTRA, DEPARTMENTAL_AUTHOR)  # an author who is not a head
		self.assertIsNone(self.region(EXTRA, he.OVERSIGHT))
		self.assertEqual(self.region(EXTRA, he.MY_WORK), [])

	def test_a_heads_oversight_is_limited_to_their_own_unit(self):
		need = self.made()["need"]
		other = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)["Human Resources Management and Development"]
		frappe.set_user(AUTHOR)
		elsewhere = lifecycle.create_need(organisation_unit=other, financial_year=FY, idempotency_key=self.key(), **self.content(title="Recruitment portal"))
		elsewhere = lifecycle.submit_need(need=elsewhere["need"], expected_version=elsewhere["record_version"], idempotency_key=self.key())
		self.stamp_submission(elsewhere, SUBMITTED_AT)
		self.assertEqual(len(self.about(REVIEWER, he.OVERSIGHT, need)), 1)
		self.assertEqual(self.about(ACTING_REVIEWER, he.OVERSIGHT, elsewhere["need"]), [])  # Julia heads Digital Health only
		self.assertEqual(len(self.about(AUDITOR, he.OVERSIGHT, elsewhere["need"])), 1)

	# ----- Coming up -----

	def test_needs_contribute_nothing_to_coming_up_in_v1(self):
		self.made()
		for user in (AUTHOR, REVIEWER, AUDITOR, PLANNER, AO, EXTRA):
			self.assertIsNone(self.region(user, he.COMING_UP), user)

	# ----- Recently completed actions -----

	def test_the_authors_submission_names_who_review_awaits(self):
		submitted = self.made()
		need = submitted["need"]
		decision = frappe.db.get_value("Departmental Need Decision", {"review_task": submitted["task"], "action": "Submit"}, "name")
		row = self.one(AUTHOR, he.COMPLETED, need, decision)
		self.assertEqual((row["title"], row["action"], row["completed_at"], row["reference"]), ("Clinical deployment laptops for rollout", "Submitted requirement for review", _dt(SUBMITTED_AT), need))
		self.assertTrue(row["sentence"].startswith("You submitted this requirement for review on 17 June 2027, 14:00 "), row["sentence"])
		clause = row["sentence"].split(". ", 1)[1]
		self.assertTrue(clause.startswith("It is awaiting review by ") and clause.endswith("."), clause)
		self.assertEqual(row["destination"]["route"], ["departmental-needs", need])
		self.assertEqual(self.row(AUTHOR, "completed", need)["action"], "Submitted requirement for review")

	def test_a_head_accepting_a_need_reads_as_the_spec_does_and_names_no_one_to_wait_for(self):
		submitted = self.made()
		need = submitted["need"]
		self.accept_quietly(submitted)
		decision = frappe.db.get_value("Departmental Need Decision", {"departmental_need": need, "action": "Accept for planning"}, "name")
		self.assertEqual(self.stamp_decision(need, "Accept for planning", DECIDED_AT), decision)
		row = self.one(REVIEWER, he.COMPLETED, need, decision)
		self.assertEqual((row["action"], row["completed_at"], row["title"]), ("Accepted requirement for planning", _dt(DECIDED_AT), "Clinical deployment laptops for rollout"))
		self.assertTrue(row["sentence"].startswith("You accepted this requirement for planning on 18 June 2027, 10:00 ") and row["sentence"].endswith("."), row["sentence"])
		self.assertNotIn("awaiting", row["sentence"])
		self.assertEqual(self.row(REVIEWER, "completed", need)["action"], "Accepted requirement for planning")

	def test_a_returning_head_is_told_the_author_has_it_while_that_is_so(self):
		submitted = self.made()
		need = submitted["need"]
		self.returned(submitted)
		decision = frappe.db.get_value("Departmental Need Decision", {"departmental_need": need, "action": "Return for correction"}, "name")
		row = self.one(REVIEWER, he.COMPLETED, need, decision)
		self.assertEqual(row["action"], "Returned requirement for correction")
		self.assertTrue(row["sentence"].startswith("You returned this requirement for correction on 18 June 2027, 09:00 "), row["sentence"])
		self.assertEqual(row["sentence"].split(". ", 1)[1], f"It is awaiting correction by {self.name(AUTHOR)}.")
		# once the author has resubmitted, the earlier return is not what anyone is waiting on
		frappe.db.set_value("Departmental Need", need, "current_state", "Draft", update_modified=False)
		frappe.db.set_value("Departmental Need Revision", frappe.db.get_value("Departmental Need", need, "current_revision"), "revision_status", "Draft", update_modified=False)
		self.add_decision(need, "Return for correction", actor=REVIEWER, at=_dt(DECIDED_AT), prior="Submitted", result="Returned")
		self.assertNotIn("awaiting", self.one(REVIEWER, he.COMPLETED, need, decision)["sentence"])

	def test_only_the_whitelisted_business_actions_of_the_actor_inside_thirty_days(self):
		need = self.made()["need"]
		created = [row["action_id"] for row in self.region(AUTHOR, he.COMPLETED) if row["root"] == need]
		actions = {row["action"] for row in self.region(AUTHOR, he.COMPLETED) if row["root"] == need}
		self.assertEqual(actions, {"Submitted requirement for review"})  # the Create decision is not a completed action
		self.assertEqual(len(created), 1)
		for excluded in ("Create", "Save draft", "Save successor", "Cancel successor", "Create successor"):
			self.assertNotIn(excluded, home_provider.COMPLETED)
		old = self.add_decision(need, "Resubmit", actor=AUTHOR, at=home_time.now() - timedelta(days=45), prior="Returned", result="Submitted")
		recent = self.add_decision(need, "Resubmit", actor=AUTHOR, at=home_time.now() - timedelta(days=5), prior="Returned", result="Submitted")
		ids = [row["action_id"] for row in self.region(AUTHOR, he.COMPLETED)]
		self.assertIn(recent, ids)
		self.assertNotIn(old, ids)
		self.assertNotIn(recent, [row["action_id"] for row in self.region(REVIEWER, he.COMPLETED)])  # Peter did not take it
		keys = [row["key"].split("|")[-1] for row in hw.get_workspace(AUTHOR, regions=["completed"], providers=[entries], at=H12)["regions"]["completed"]["entries"]]
		self.assertNotIn(old, keys)

	def test_every_whitelisted_action_has_a_sentence(self):
		need = self.made()["need"]
		for action in home_provider.COMPLETED:
			self.add_decision(need, action, actor=REVIEWER, at=_dt(DECIDED_AT))
		rows = [row for row in self.region(REVIEWER, he.COMPLETED) if row["root"] == need]
		self.assertEqual({row["action"] for row in rows}, {label for label, _did in home_provider.COMPLETED.values()})
		for row in rows:
			self.assertTrue(row["sentence"].startswith("You ") and " on 18 June 2027, 10:00 " in row["sentence"], row["sentence"])

	def test_an_actor_who_lost_scope_sees_nothing_of_the_need(self):
		# an extra Head of the unit returns it, then loses the unit and keeps only another department's authorship
		submitted = self.made()
		need = submitted["need"]
		self.grant(EXTRA, HEAD_OF_USER_DEPARTMENT)
		self.assertEqual(self.one(EXTRA, he.MY_WORK, need)["action_id"], submitted["task"])
		frappe.set_user(EXTRA)
		lifecycle.review_need(
			need=need, decision="return", task=submitted["task"], expected_version=self.version_of(need), decision_token=self.token(submitted["task"]),
			idempotency_key=self.key(), reason=REASON,
		)
		frappe.set_user("Administrator")
		self.assertEqual(len(self.about(EXTRA, he.COMPLETED, need)), 1)
		self.release_grants()
		self.assertIsNone(self.region(EXTRA, he.COMPLETED))  # no responsibility: the region does not apply
		other = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)["Human Resources Management and Development"]
		self.grant(EXTRA, DEPARTMENTAL_AUTHOR, other)
		self.assertEqual(self.region(EXTRA, he.COMPLETED), [])  # applies, but the unit is not theirs
		self.assertEqual((self.region(EXTRA, he.MY_WORK), self.region(EXTRA, he.WAITING)), ([], []))
		for region in ("my_work", "waiting", "completed"):
			self.assertFalse([row for row in self.rows_of(EXTRA, region) if row["reference"] == need], region)

	# ----- applicability, personas, technical readers -----

	def test_none_versus_empty_by_responsibility(self):
		self.made()
		for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
			for user in (AUTHOR, REVIEWER, ACTING_REVIEWER, PLANNER, AUDITOR):
				self.assertIsInstance(self.region(user, region), list, (user, region))
			for user in (AO, HOPF, OFFICER, NO_GRANT, EXTRA):  # no Needs work of their own (the two offices only read)
				self.assertIsNone(self.region(user, region), (user, region))
		self.assertEqual(self.region(PLANNER, he.MY_WORK), [])  # the Planner holds nothing in this module's own queue
		self.assertEqual(self.region(AUDITOR, he.WAITING), [])

	def test_the_technical_reader_and_an_unrelated_internal_user_get_nothing(self):
		self.made()
		for region in he.REGIONS:
			self.assertIsNone(self.region("Administrator", region), region)
			self.assertIsNone(self.region("Guest", region), region)
			self.assertIsNone(self.region(EXTRA, region), region)
		view = self.home("Administrator")
		self.assertEqual((view["empty"], view["regions"]["my_work"]["entries"]), (True, []))
		nobody = self.home(EXTRA)
		self.assertEqual(nobody["state"], "ready")
		self.assertFalse(any(region["entries"] for region in nobody["regions"].values()))
		self.assertEqual({region["coverage"] for region in nobody["regions"].values()}, {hw.NOT_APPLICABLE})

	def test_the_provider_writes_nothing(self):
		self.made()
		self.returned(self.made(title="A second requirement"))
		self.accept_quietly(self.made(title="A third requirement"))
		frappe.db.commit()
		before = frappe.db.transaction_writes
		for user in (AUTHOR, REVIEWER, ACTING_REVIEWER, PLANNER, AUDITOR, AO, HOPF, OFFICER, NO_GRANT, EXTRA, "Administrator"):
			for region in he.REGIONS:
				self.region(user, region)
		self.home(REVIEWER)
		self.home(AUTHOR)
		self.assertEqual(frappe.db.transaction_writes, before)
		self.close_window()
		frappe.db.commit()
		before = frappe.db.transaction_writes
		for region in he.REGIONS:  # the blocked path reads the intake state too
			self.region(AUTHOR, region)
		self.assertEqual(frappe.db.transaction_writes, before)

	def test_the_owners_guidance_runs_once_per_need_per_read(self):
		self.made()
		self.returned(self.made(title="A second requirement"))
		calls = []
		original = home_provider.need_guidance

		def counting(doc, **kwargs):
			calls.append((doc.name, tuple(a["code"] for a in kwargs["actions"]), kwargs["intake_open"], kwargs["principal"]))
			return original(doc, **kwargs)

		home_provider.need_guidance = counting
		self.addCleanup(setattr, home_provider, "need_guidance", original)
		for user in (REVIEWER, AUTHOR, AUDITOR):
			calls.clear()
			self.home(user)
			self.assertEqual(len(calls), len(set(calls)), (user, calls))

	# ----- destinations, tables -----

	def test_every_destination_opens_a_real_page_the_actor_may_open(self):
		for page in SPEC_PAGES:
			self.assertTrue(frappe.db.exists("Page", page), page)
		self.made()
		self.returned(self.made(title="A second requirement"))
		seen = set()
		for user in (AUTHOR, REVIEWER, ACTING_REVIEWER, AUDITOR, AO, HOPF):
			for region in (he.MY_WORK, he.WAITING, he.OVERSIGHT, he.COMPLETED):
				for row in self.region(user, region) or []:
					if row["root"] in self.needs:
						seen.add(row["destination"]["route"][0])
						self.assertTrue(hw._page_permitted(row["destination"]["route"][0], user), (user, row["destination"]))
		self.assertEqual(seen, {"departmental-needs"})

	def test_the_owners_tables_cover_every_decision_and_use_no_display_string(self):
		meta = frappe.get_meta("Departmental Need Decision").get_field("action").options.split("\n")
		excluded = {"Create", "Save draft", "Create successor", "Save successor", "Cancel successor"}
		self.assertEqual(set(home_provider.COMPLETED) | excluded, set(meta))
		for label, did in home_provider.COMPLETED.values():
			self.assertTrue(label and did and "{" not in did, (label, did))
		self.assertEqual(home_provider.COMPLETED["Accept for planning"][1], "accepted this requirement for planning")
