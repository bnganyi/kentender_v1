# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 — the Award feed to Home (`award/services/home_provider.py`).

Award's own fast synthetic world (a case in under a second, no Tender built); the provider only reads. Charles Mutiso
(Head of Procurement Function), Amina Hassan (Accounting Officer), Naomi Chebet (Auditor) and Daniel Otieno (Technical
Operator) are the Award test world's own actors. The one Head of User Department test needs a real Tender (the department
rule reads its contributing units), so it adds one Tender, one Version and two users, and removes them after, counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.award.tests.test_home_provider
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import frappe
from kentender_core.services.command_write_guard import purge_doc

from kentender_core.services.command_write_guard import maintenance_write
from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import home_workspace as hw
from kentender_core.services import responsibility_administration as administration
from kentender_procurement.award.services import decision, issues, notices, opinion, people, records, simulation, state, tasks
from kentender_procurement.award.services.home_provider import entries
from kentender_procurement.award.tests.support import AO, CASE, DANIEL, HOP, MARY, NAOMI, NS, REF, AwardCase
from kentender_procurement.tenders.services import envelope
from kentender_procurement.tenders.tests import sample

TITLE = "Supply and delivery of business laptops"
NAME37, REF37 = "AWD-AWT-2100-037", "TND-AWT-2100-037"
OUTSIDER = "brian.wafula@moh.example.test"  # a Procurement Officer: no Award responsibility
EXTRA, HOD, HOD_OTHER = "awdhome.extra@example.test", "awdhome.hod@example.test", "awdhome.hodother@example.test"
HOME_NS = "KT_TEST_AWDHOME"
USERS = (EXTRA, HOD, HOD_OTHER)
DECIDED = datetime(2027, 6, 17, 10, 0)
SIGNED = datetime(2027, 6, 17, 9, 10)
RECEIVED = datetime(2027, 6, 16, 14, 7, 1)
AWARD_DOCTYPES = records.DOCTYPES


def _remove_extras() -> None:
	"""The users, assignments, Tender and Version this module adds; nothing else is touched."""
	frappe.set_user("Administrator")
	for name in frappe.get_all("User Responsibility Assignment", filters={"user": ("in", USERS)}, pluck="name"):
		purge_doc("User Responsibility Assignment", name)
	for name in frappe.get_all("Contact Email", filters={"email_id": ("in", USERS)}, pluck="parent"):
		frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
	for email in USERS:
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=1, ignore_permissions=True)
	tenders = frappe.get_all("Tender", filters={"fixture_namespace": HOME_NS}, pluck="name")
	for doctype, field in (("Tender Version", "tender"), ("Tender", "name")):
		for name in frappe.get_all(doctype, filters={field: ("in", tenders)}, pluck="name") if tenders else []:
			doc = frappe.get_doc(doctype, name)
			with maintenance_write("Tenders", reason="test clean-up"):
				doc.delete(ignore_permissions=True, force=True)
	frappe.db.commit()


def _assert_clean() -> None:
	"""Every fixture row is gone: Award's own namespace, and this module's users, grants and Tender."""
	frappe.set_user("Administrator")
	left = {doctype: frappe.db.count(doctype, {"fixture_namespace": NS}) for doctype in AWARD_DOCTYPES}
	left.update({
		"User": frappe.db.count("User", {"name": ("in", USERS)}), "User Responsibility Assignment": frappe.db.count("User Responsibility Assignment", {"user": ("in", USERS)}),
		"Tender": frappe.db.count("Tender", {"fixture_namespace": HOME_NS}), "Tender Version": frappe.db.count("Tender Version", {"fixture_namespace": HOME_NS}),
	})
	left = {name: count for name, count in left.items() if count}
	if left:
		raise AssertionError(f"Award Home test rows left behind: {left}")


class TestAwardHomeProvider(AwardCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(_assert_clean)
		cls.addClassCleanup(_remove_extras)

	def setUp(self):
		super().setUp()
		home_support.reset()
		self.addCleanup(frappe.set_user, "Administrator")

	# ----- helpers -----

	def region(self, user: str, region: str):
		home_support.reset()
		return entries(user=user, region=region)

	def mine(self, rows, reference: str = REF):
		"""The rows about this test's Tender (the test site also holds the canonical Award)."""
		return [row for row in rows or [] if row["reference"].startswith("TND-AWT-2100") and (not reference or row["reference"] == reference)]

	def one(self, user: str, region: str, reference: str = REF):
		rows = self.mine(self.region(user, region), reference)
		self.assertEqual(len(rows), 1, f"{user} {region}: {rows}")
		return rows[0]

	def row(self, user: str, at: datetime, region: str, reference: str = REF) -> dict:
		"""The presented row of the region, following Show more (the test site also holds the canonical Award)."""
		rows, cursor = [], None
		while True:
			page = hw.get_workspace(user, regions=[region], cursors={region: cursor} if cursor else None, providers=[entries], at=at)["regions"][region]
			rows += page["entries"]
			cursor = page["next_cursor"]
			if not cursor:
				break
		rows = [row for row in rows if row["reference"] == reference]
		self.assertEqual(len(rows), 1, f"{region}: {rows}")
		return rows[0]

	def home(self, user: str, at: datetime):
		return hw.get_workspace(user, providers=[entries], at=at)

	def who(self, role: str, fallback: str) -> str:
		"""What the owner names for the holder: the person when exactly one holds the role, otherwise the role (the site decides)."""
		found = people.holders(role)
		return people.full_name(found[0]) if len(found) == 1 else fallback

	def subject(self, role: str) -> str:
		"""A waiting row's subject: the people (two or fewer) or "an Accounting Officer"."""
		names = [people.full_name(user) for user in people.holders(role)]
		return " or ".join(names) if 0 < len(names) <= 2 else f"an {role}"

	def failed_notice_case(self):
		self.deliver("037")
		simulation.set_controls(email_failure_organisations="Afya Digital Supplies Limited")
		self.awarded(NAME37)
		return self.case(NAME37)

	# ----- My work -----

	def test_the_head_of_procurement_function_prepares_the_opinion_worded_by_the_owner_without_the_reference(self):
		self.deliver()
		row = self.one(HOP, he.MY_WORK)
		item = tasks.all_for_user(HOP)
		key = next(t["key"] for t in item if t["award"] == CASE)
		self.assertEqual((row["title"], row["reference"], row["action"]), (TITLE, REF, "Prepare professional opinion"))
		self.assertEqual((row["entered_at"], row["entered_verb"], row["action_id"], row["owner"], row["region"]), (RECEIVED, "Received", key, "award", he.MY_WORK))
		self.assertEqual(row["entered_at"], self.case().received_at)
		self.assertEqual((row["blocked"], row["reason"], row["due"]), (False, "", None))
		self.assertEqual(row["destination"], {"route": ["award", CASE], "route_options": {}})
		# the Accounting Officer holds nothing yet
		self.assertEqual(self.mine(self.region(AO, he.MY_WORK)), [])

	def test_the_accounting_officers_decision_carries_the_signed_opinions_instant(self):
		self.deliver()
		self.signed_opinion()
		row = self.one(AO, he.MY_WORK)
		self.assertEqual((row["title"], row["action"], row["entered_at"]), (TITLE, "Decide award", SIGNED))
		self.assertEqual(row["entered_at"], state.signed_opinion(self.case()).signed_at)
		self.assertEqual((row["action_id"], row["destination"]["route"]), (next(t["key"] for t in tasks.all_for_user(AO) if t["award"] == CASE), ["award", CASE]))
		self.assertEqual([t["since"] for t in tasks.all_for_user(AO) if t["award"] == CASE], [""])  # the owner's own item has no instant: the provider supplies one
		self.assertEqual(self.mine(self.region(HOP, he.MY_WORK)), [])

	def test_a_returned_decision_and_a_no_award_next_action_keep_the_owners_wording_and_instants(self):
		self.deliver()
		self.signed_opinion()
		self.at("2027-06-17 11:00:00")
		self.run_as(AO, decision.record, award=CASE, outcome="Return for correction", reason="Explain the unresolved funding concern before recommending an award.",
			expected_version=self.version())
		returned = self.one(HOP, he.MY_WORK)
		self.assertEqual((returned["action"], returned["entered_at"]), ("Resolve returned decision", datetime(2027, 6, 17, 11, 0)))
		self.signed_opinion(conclusion="No current recommendation", reason="Tender validity expired before an award could be notified.")
		self.at("2027-06-18 08:00:00")
		self.run_as(AO, decision.record, award=CASE, outcome="No award", reason="Tender validity expired before an award could be notified.",
			next_action="Review whether the tender should be cancelled", expected_version=self.version())
		follow = self.one(HOP, he.MY_WORK)
		self.assertEqual((follow["action"], follow["entered_at"]), ("Review whether the tender should be cancelled", datetime(2027, 6, 18, 8, 0)))

	def test_a_failed_notice_is_blocked_and_says_what_the_owner_says(self):
		self.failed_notice_case()
		row = self.one(HOP, he.MY_WORK, REF37)
		issue = issues.open_issues(self.case(NAME37), subtype=notices.DELIVERY_SUBTYPE)[0]
		self.assertEqual((row["action"], row["blocked"], row["reason"]), ("Resolve notice delivery", True, "A required notice is not yet confirmed."))
		self.assertEqual((row["entered_at"], row["action_id"], row["title"]), (issue.received_at, f"{NAME37}:1:issue:{issue.name}", TITLE))
		shown = self.row(HOP, datetime(2027, 6, 19, 10, 0), "my_work", REF37)
		self.assertEqual((shown["action"], shown["blocked"], shown["reason"], shown["timing"]), ("Resolve notice delivery", True, "A required notice is not yet confirmed.", "Received 2 days ago (17 June, 10:00)"))
		self.assertEqual(shown["module"], "Award")

	def test_an_incomplete_report_blocks_the_opinion_and_a_plain_opinion_is_not_blocked(self):
		self.deliver(overrides={"missing_annex": True})
		row = self.one(HOP, he.MY_WORK)
		self.assertEqual((row["action"], row["blocked"], row["reason"]), ("Prepare professional opinion", True, "The evaluation report is incomplete. The Head of Procurement has been notified."))
		self.assertEqual(self.one(HOP, he.MY_WORK)["entered_at"], RECEIVED)
		self.deliver("036")
		plain = self.one(HOP, he.MY_WORK, "TND-AWT-2100-036")
		self.assertEqual((plain["blocked"], plain["reason"]), (False, ""))

	def test_the_decision_row_renders_the_signed_instant_through_home(self):
		self.deliver()
		self.signed_opinion()
		decide = self.row(AO, datetime(2027, 6, 19, 10, 0), "my_work")
		self.assertEqual((decide["action"], decide["timing"], decide["title"], decide["blocked"]), ("Decide award", "Received 2 days ago (17 June, 09:10)", TITLE, False))
		self.assertEqual(decide["module"], "Award")

	def test_the_opinion_row_renders_received_two_days_ago(self):
		self.deliver()
		row = self.row(HOP, datetime(2027, 6, 18, 10, 0), "my_work")
		self.assertEqual((row["action"], row["timing"]), ("Prepare professional opinion", "Received 2 days ago (16 June, 14:07)"))

	# ----- Waiting -----

	def test_the_head_of_procurement_function_waits_for_the_accounting_officers_decision(self):
		self.deliver()
		self.signed_opinion()
		waiting = self.one(HOP, he.WAITING)
		self.assertEqual((waiting["title"], waiting["reference"], waiting["since"], waiting["due"]), (TITLE, REF, SIGNED, None))
		self.assertEqual(waiting["action"], f"Waiting for {self.subject(people.ACCOUNTING_OFFICER)} to decide the award")
		names = [people.full_name(user) for user in people.holders(people.ACCOUNTING_OFFICER)]
		self.assertEqual(waiting["holder"], " or ".join(names) if len(names) <= 2 else people.ACCOUNTING_OFFICER)
		self.assertEqual(waiting["destination"]["route"], ["award", CASE])
		shown = self.row(HOP, datetime(2027, 6, 19, 10, 0), "waiting")
		self.assertEqual(shown["timing"], "Waiting 2 days (since 17 June, 09:10)")
		self.assertEqual(shown["action"], waiting["action"])

	def test_the_accounting_officers_wait_for_the_opinion_is_oversight_not_a_waiting_row(self):
		self.deliver()
		self.assertEqual(self.mine(self.region(AO, he.WAITING)), [])
		self.assertEqual(self.mine(self.region(HOP, he.WAITING)), [])  # the opinion is the Head of Procurement Function's own work
		self.signed_opinion()
		self.assertEqual(self.mine(self.region(AO, he.WAITING)), [])  # the decision is the Accounting Officer's own work

	def test_waiting_applies_to_the_two_holders_only(self):
		self.deliver()
		self.assertIsInstance(self.region(HOP, he.WAITING), list)
		self.assertIsInstance(self.region(AO, he.WAITING), list)
		for user in (NAOMI, OUTSIDER, DANIEL, "Administrator", "Guest"):
			self.assertIsNone(self.region(user, he.WAITING), user)

	# ----- Records you oversee -----

	def test_the_accounting_officer_and_the_auditor_see_who_the_opinion_waits_on(self):
		self.deliver()
		who = self.who(people.HEAD_OF_PROCUREMENT, "the Head of Procurement Function")
		for user in (AO, NAOMI):
			row = self.one(user, he.OVERSIGHT)
			self.assertEqual(row["action"], f"Awaiting professional opinion by {who}")
			self.assertEqual((row["outstanding"], row["since"], row["title"], row["action_id"]), (True, RECEIVED, TITLE, f"{CASE}:oversight"))
			self.assertEqual((row["destination"]["route"], row["reference"]), (["award", CASE], REF))
		shown = self.row(AO, datetime(2027, 6, 18, 10, 0), "oversight")
		self.assertEqual((shown["timing"], shown["action"]), ("Outstanding 2 days (since 16 June, 14:07)", f"Awaiting professional opinion by {who}"))

	def evaluation_says(self, links, *, state="ok"):
		"""Evaluation's own stage summary for the Tender: what it discloses to this reader, with its own links."""
		from kentender_procurement.bid_evaluation.services import stage_summary as evaluation_summary
		from kentender_procurement.tenders.services import stage_summary as ss

		original = evaluation_summary.for_tender
		shown = ss.summary(key="bid-evaluation", label="Bid evaluation", status="Report sent", disclosure=ss.FULL, links=links)
		evaluation_summary.for_tender = lambda **kwargs: [shown if state == "ok" else ss.unavailable("bid-evaluation", "Bid evaluation")]
		self.addCleanup(setattr, evaluation_summary, "for_tender", original)

	def test_an_oversight_row_carries_the_evaluations_own_view_report_link_and_the_delivery_instant(self):
		from kentender_procurement.tenders.services import stage_summary as ss

		self.deliver()
		self.evaluation_says([ss.link("view-record", "View evaluation", ["tenders", REF, "evaluation"]), ss.link("view-report", "View report", ["tenders", REF, "evaluation", "report"])])
		row = self.one(AO, he.OVERSIGHT)
		self.assertEqual(row["link"], {"label": "View report", "destination": {"route": ["tenders", REF, "evaluation", "report"], "route_options": {}}})
		self.assertEqual(row["fact"], "Evaluation report delivered")
		self.assertEqual(row["fact_at"], RECEIVED)
		shown = self.row(AO, datetime(2027, 6, 18, 10, 0), "oversight")
		self.assertEqual((shown["fact"], shown["link"]["label"], shown["destination"]["route"]), ("Evaluation report delivered 16 June, 14:07", "View report", ["award", CASE]))

	def test_no_view_report_link_when_evaluation_offers_none_or_cannot_be_read(self):
		self.deliver()
		self.evaluation_says([])  # a reader Evaluation does not let read the report
		row = self.one(AO, he.OVERSIGHT)
		self.assertEqual((row["link"], row["fact"]), (None, ""))
		self.evaluation_says([], state="unavailable")  # a failed Evaluation read never hides or breaks Award's own row
		row = self.one(AO, he.OVERSIGHT)
		self.assertEqual((row["link"], row["fact"]), (None, ""))

	def test_the_decision_stage_is_overseen_by_the_auditor_and_not_twice_by_those_who_hold_or_wait_on_it(self):
		self.deliver()
		self.signed_opinion()
		row = self.one(NAOMI, he.OVERSIGHT)
		self.assertEqual(row["action"], f"Awaiting award decision by {self.who(people.ACCOUNTING_OFFICER, 'the Accounting Officer')}")
		self.assertEqual((row["since"], row["outstanding"]), (SIGNED, True))
		# Amina holds the decision (My work) and Charles waits on it (Waiting): neither sees it again
		self.assertEqual(self.mine(self.region(AO, he.OVERSIGHT)), [])
		self.assertEqual(self.mine(self.region(HOP, he.OVERSIGHT)), [])
		# and the Head of Procurement Function does not oversee the opinion he holds
		self.deliver("036")
		self.assertEqual(self.mine(self.region(HOP, he.OVERSIGHT), "TND-AWT-2100-036"), [])

	def test_a_full_reader_is_told_a_notice_is_not_confirmed_and_who_resolves_it(self):
		self.failed_notice_case()
		issue = issues.open_issues(self.case(NAME37), subtype=notices.DELIVERY_SUBTYPE)[0]
		for user in (AO, NAOMI):
			row = self.one(user, he.OVERSIGHT, REF37)
			self.assertEqual(row["action"], "A required notice is not yet confirmed; resolution by " + people.full_name(issue.owner_user))
			self.assertEqual((row["since"], row["outstanding"], row["action_id"], row["holder"]), (issue.received_at, True, f"{NAME37}:oversight", people.full_name(issue.owner_user)))
		shown = self.row(NAOMI, datetime(2027, 6, 19, 10, 0), "oversight", REF37)
		self.assertEqual(shown["timing"], "Outstanding 2 days (since 17 June, 10:00)")
		# the Head of Procurement Function holds the matter (My work), so it is not also overseen
		self.assertEqual(self.mine(self.region(HOP, he.OVERSIGHT), REF37), [])

	def test_oversight_applies_to_readers_and_to_no_one_else(self):
		self.deliver()
		for user in (HOP, AO, NAOMI):
			self.assertIsInstance(self.region(user, he.OVERSIGHT), list, user)
		for user in (OUTSIDER, MARY, DANIEL, "Administrator", "Guest"):
			self.assertIsNone(self.region(user, he.OVERSIGHT), user)
		self.assertEqual(self.mine(self.region(HOP, he.OVERSIGHT)), [])

	def test_a_head_of_user_department_gets_the_summary_line_and_never_the_notice_information(self):
		unit, other = [row.name for row in frappe.get_all("Organisation Unit", filters={"status": "Active"}, fields=["name", "lft", "rgt"], order_by="lft asc") if row.rgt == row.lft + 1][:2]
		for email, name in ((HOD, "Awd Home Head"), (HOD_OTHER, "Awd Home Other Head")):
			frappe.get_doc({"doctype": "User", "email": email, "first_name": name, "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True).add_roles("Desk User")
		administration.grant(user=HOD, business_role="Head of User Department", organisation_unit=unit, fixture_namespace=HOME_NS, actor="Administrator")
		administration.grant(user=HOD_OTHER, business_role="Head of User Department", organisation_unit=other, fixture_namespace=HOME_NS, actor="Administrator")
		tender, _version = sample.insert_tender_with_version(reference="TND-AWT-2100-037", fixture_namespace=HOME_NS)
		envelope.bump(tender, lead_org_unit=unit, contributing_org_unit_ids=json.dumps([unit]))
		self.deliver("037")
		synthetic = self.case(NAME37).tender
		frappe.db.set_value(records.CASE, NAME37, "tender", tender.name)  # the department rule reads a real Tender's units
		who = self.who(people.HEAD_OF_PROCUREMENT, "the Head of Procurement Function")
		# the Opinion stage: the owner's own outstanding line, read-only
		row = self.one(HOD, he.OVERSIGHT, REF37)
		self.assertEqual((row["action"], row["outstanding"], row["since"], row["title"]), (f"Awaiting professional opinion by {who}", True, RECEIVED, TITLE))
		self.assertEqual(self.mine(self.region(HOD_OTHER, he.OVERSIGHT), REF37), [])  # another unit
		self.assertIsInstance(self.region(HOD_OTHER, he.OVERSIGHT), list)
		# the Notices stage with a failed notice: nothing about the notice reaches the department head
		simulation.set_controls(email_failure_organisations="Afya Digital Supplies Limited")
		frappe.db.set_value(records.CASE, NAME37, "tender", synthetic)  # the synthetic sources answer for their own tender
		self.awarded(NAME37)
		frappe.db.set_value(records.CASE, NAME37, "tender", tender.name)
		self.assertEqual(self.case(NAME37).stage, "Notices")
		shown = self.region(HOD, he.OVERSIGHT)
		self.assertEqual(self.mine(shown, REF37), [])
		self.assertNotIn("notice", json.dumps(shown, default=str).lower())
		self.assertEqual(self.one(AO, he.OVERSIGHT, REF37)["action"].startswith("A required notice is not yet confirmed"), True)  # a full reader still is told
		# a department head holds no Award work, wait or completed action
		for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
			self.assertIsNone(self.region(HOD, region), region)
		self.assertEqual(self.home(HOD, datetime(2027, 6, 19, 10, 0))["state"], "ready")

	def test_a_failed_summary_read_is_raised_not_hidden(self):
		self.deliver()
		from kentender_procurement.award.services import stage_summary
		from kentender_procurement.tenders.services import stage_summary as ss

		original = stage_summary.for_tender
		stage_summary.for_tender = lambda **kwargs: [ss.unavailable("award", "Award")]
		self.addCleanup(setattr, stage_summary, "for_tender", original)
		with self.assertRaises(RuntimeError):
			self.region(AO, he.OVERSIGHT)

	# ----- Coming up -----

	def test_award_contributes_nothing_to_coming_up(self):
		self.deliver()
		for user in (HOP, AO, NAOMI, DANIEL, OUTSIDER, "Administrator"):
			self.assertIsNone(self.region(user, he.COMING_UP), user)

	# ----- Recently completed actions -----

	def test_the_accounting_officers_award_decision_names_what_is_still_open(self):
		self.deliver()
		self.awarded()
		row = self.one(AO, he.COMPLETED)
		self.assertEqual((row["title"], row["action"], row["completed_at"], row["reference"]), (TITLE, "Recorded award decision", DECIDED, REF))
		self.assertEqual(row["sentence"], "You recorded the award decision on 17 June 2027, 10:00 EAT.")  # every notice was given at once
		decided = frappe.get_all(state.DECISION, filters={"award_case": CASE}, pluck="name")
		self.assertEqual((row["action_id"], row["destination"]["route"]), (decided[0], ["award", CASE]))
		self.failed_notice_case()
		failed = self.one(AO, he.COMPLETED, REF37)
		self.assertEqual(failed["sentence"], "You recorded the award decision on 17 June 2027, 10:00 EAT. Required bidder notices are not yet confirmed.")

	def test_the_head_of_procurement_functions_signed_opinion_is_a_completed_action(self):
		self.deliver()
		self.signed_opinion()
		row = self.one(HOP, he.COMPLETED)
		self.assertEqual((row["action"], row["completed_at"], row["sentence"]), ("Signed professional opinion", SIGNED, "You signed the professional opinion on 17 June 2027, 09:10 EAT."))
		shown = self.row(HOP, datetime(2027, 6, 19, 10, 0), "completed")
		self.assertEqual(shown["sentence"], row["sentence"])
		self.assertEqual(self.mine(self.region(AO, he.COMPLETED)), [])  # Amina has decided nothing yet

	def test_a_no_award_decision_names_the_next_action_and_its_owner(self):
		self.deliver()
		self.signed_opinion(conclusion="No current recommendation", reason="Tender validity expired before an award could be notified.")
		self.at("2027-06-18 08:00:00")
		self.run_as(AO, decision.record, award=CASE, outcome="No award", reason="Tender validity expired before an award could be notified.",
			next_action="Review whether the tender should be cancelled", expected_version=self.version())
		row = self.one(AO, he.COMPLETED)
		owner = people.full_name(frappe.db.get_value(state.DECISION, {"award_case": CASE, "outcome": "No award"}, "next_action_owner"))
		self.assertEqual((row["action"], row["sentence"]), ("Recorded no award", f"You recorded that no award is made on 18 June 2027, 08:00 EAT. Next: {owner} to review whether the tender should be cancelled."))

	def test_only_the_actors_own_recent_actions_of_a_case_they_can_still_read(self):
		self.deliver()
		self.awarded()
		name = frappe.get_all(state.DECISION, filters={"award_case": CASE}, pluck="name")[0]
		# inside and outside the provider's own 30-day cutoff
		frappe.db.set_value(state.DECISION, name, "decided_at", home_time.now() - timedelta(days=5))
		self.assertIn(name, [row["action_id"] for row in self.region(AO, he.COMPLETED)])
		frappe.db.set_value(state.DECISION, name, "decided_at", home_time.now() - timedelta(days=45))
		self.assertNotIn(name, [row["action_id"] for row in self.region(AO, he.COMPLETED)])
		frappe.db.set_value(state.DECISION, name, "decided_at", DECIDED)
		# Charles did not take Amina's decision, and a draft-stage return is no completed action
		self.assertNotIn(name, [row["action_id"] for row in self.region(HOP, he.COMPLETED)])
		# the journal's own rows are read without their result
		journal = frappe.get_all(records.JOURNAL, filters={"award_case": CASE, "command": "SignProfessionalOpinion"}, pluck="name")
		self.assertEqual(len(journal), 1)
		frappe.db.set_value(records.JOURNAL, journal[0], "recorded_at", home_time.now() - timedelta(days=45))
		self.assertEqual([row for row in self.mine(self.region(HOP, he.COMPLETED))], [])

	def test_a_correction_decision_is_one_row_and_a_separate_one_is_worded_neutrally(self):
		self.deliver()
		self.awarded()
		name = frappe.get_all(state.DECISION, filters={"award_case": CASE}, pluck="name")[0]
		frappe.db.set_value(state.DECISION, name, "kind", "Correction")
		self.assertEqual(self.one(AO, he.COMPLETED)["sentence"].split(" on ")[0], "You recorded the corrected award decision")
		journal = records.insert(frappe.get_doc({"doctype": records.JOURNAL, "idempotency_key": self.key("c1"), "command": "RecordAwardCorrectionDecision", "payload_hash": "x",
			"result_json": json.dumps({"secret": "never read"}), "actor": AO, "award_case": CASE, "recorded_at": DECIDED, "fixture_namespace": NS}))
		self.assertEqual(len(self.mine(self.region(AO, he.COMPLETED))), 1)  # the same action as the committed decision
		frappe.db.set_value(records.JOURNAL, journal.name, "recorded_at", DECIDED + timedelta(hours=3))
		rows = sorted(self.mine(self.region(AO, he.COMPLETED)), key=lambda row: row["completed_at"])
		self.assertEqual([row["action"] for row in rows], ["Recorded corrected award", "Recorded correction decision"])
		self.assertEqual(rows[1]["sentence"], "You recorded a decision on the reported correction on 17 June 2027, 13:00 EAT.")
		self.assertNotIn("never read", json.dumps(rows, default=str))

	def test_the_core_window_drops_a_completed_action_older_than_thirty_days(self):
		self.deliver()
		self.awarded()
		self.assertEqual(self.row(AO, datetime(2027, 7, 1, 10, 0), "completed")["action"], "Recorded award decision")
		self.assertEqual([row for row in self.home(AO, datetime(2027, 7, 30, 10, 0))["regions"]["completed"]["entries"] if row["reference"] == REF], [])

	# ----- applicability, personas, technical readers -----

	def test_none_versus_empty_by_responsibility(self):
		self.deliver()
		for region in (he.MY_WORK, he.WAITING, he.COMPLETED):
			for user in (HOP, AO):
				self.assertIsInstance(self.region(user, region), list, (user, region))
			for user in (OUTSIDER, NAOMI):
				self.assertIsNone(self.region(user, region), (user, region))
		self.assertIsInstance(self.region(NAOMI, he.OVERSIGHT), list)  # the Auditor oversees but holds no work
		self.assertTrue(self.mine(self.region(NAOMI, he.OVERSIGHT)))

	def test_the_technical_reader_and_an_unrelated_internal_user_get_nothing(self):
		self.deliver()
		self.awarded()
		for user in ("Administrator", DANIEL, OUTSIDER, MARY, "Guest"):
			for region in he.REGIONS:
				self.assertIsNone(self.region(user, region), (user, region))
		view = self.home(OUTSIDER, datetime(2027, 6, 19, 10, 0))
		self.assertEqual(view["state"], "ready")
		self.assertFalse([row for region in view["regions"].values() for row in region["entries"] if row["reference"] == REF])
		self.assertEqual({region["coverage"] for region in view["regions"].values()}, {hw.NOT_APPLICABLE})
		technical = self.home("Administrator", datetime(2027, 6, 19, 10, 0))
		self.assertEqual((technical["empty"], technical["regions"]["my_work"]["entries"]), (True, []))

	def test_a_user_without_the_responsibility_sees_none_of_it_and_a_revoked_responsibility_removes_it(self):
		self.deliver()
		frappe.get_doc({"doctype": "User", "email": EXTRA, "first_name": "Awd Home Extra", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True).add_roles("Desk User")
		self.assertIsNone(self.region(EXTRA, he.MY_WORK))
		administration.grant(user=EXTRA, business_role="Head of Procurement Function", fixture_namespace=HOME_NS, actor="Administrator")
		at = datetime(2027, 6, 18, 10, 0)
		self.assertEqual(self.row(EXTRA, at, "my_work")["action"], "Prepare professional opinion")
		self.assertTrue(self.home(EXTRA, at)["regions"]["my_work"]["applicable"])
		assignment = frappe.get_all("User Responsibility Assignment", filters={"user": EXTRA}, pluck="name")[0]
		administration.revoke(assignment, reason="Revoked inside the Home provider test.", actor="Administrator")
		revoked = self.home(EXTRA, at)
		self.assertEqual({region["coverage"] for region in revoked["regions"].values()}, {hw.NOT_APPLICABLE})
		self.assertFalse([row for region in revoked["regions"].values() for row in region["entries"] if row["reference"] == REF])
		self.assertIsNone(self.region(EXTRA, he.MY_WORK))

	def test_the_provider_writes_nothing(self):
		users = (HOP, AO, NAOMI, DANIEL, OUTSIDER, "Administrator", "Guest")
		self.deliver()
		self.deliver("036")
		self.deliver("037")
		self.awarded(NAME37)  # the Opinion stage, the Decision stage (Amina's) and a delivered notice, read through the owner's answers
		self.signed_opinion()
		simulation.set_controls(email_failure_organisations="Afya Digital Supplies Limited")
		self.deliver("033", reference="TND-AWT-2100-040")
		self.awarded("AWD-AWT-2100-040")
		self.at("2027-06-20 08:00:00")
		frappe.db.commit()
		before = frappe.db.transaction_writes
		for user in users:
			for region in he.REGIONS:
				self.region(user, region)
		self.home(AO, datetime(2027, 6, 19, 10, 0))
		self.assertEqual(frappe.db.transaction_writes, before)

	def test_the_scan_runs_once_per_home_read(self):
		self.deliver()
		self.signed_opinion()
		calls = []
		original = tasks.all_for_user

		def counting(user):
			calls.append(user)
			return original(user)

		tasks.all_for_user = counting
		self.addCleanup(setattr, tasks, "all_for_user", original)
		self.home(AO, datetime(2027, 6, 19, 10, 0))
		self.assertEqual(calls, [AO])

	# ----- destinations, tables -----

	def test_every_destination_opens_the_award_page_the_actor_may_open(self):
		self.assertTrue(frappe.db.exists("Page", "award"))
		self.deliver("037")
		self.awarded(NAME37)
		self.deliver()
		self.signed_opinion()
		seen = set()
		for user in (HOP, AO, NAOMI):
			for region in (he.MY_WORK, he.WAITING, he.OVERSIGHT, he.COMPLETED):
				for row in self.mine(self.region(user, region), ""):
					seen.add(row["destination"]["route"][0])
					self.assertEqual(row["destination"]["route"], ["award", row["root"]])
					self.assertTrue(hw._page_permitted(row["destination"]["route"][0], user), (user, row["destination"]))
		self.assertEqual(seen, {"award"})

	def test_the_owners_wording_table_covers_every_task_the_owner_derives(self):
		from kentender_procurement.award.services import home_provider

		spec = {"Prepare professional opinion", "Resolve notice delivery", "Decide award"}
		self.assertTrue(spec <= set(home_provider.ACTIONS))
		for task, wording in home_provider.ACTIONS.items():
			self.assertTrue(wording and "{" not in wording and "TND-" not in wording and wording == task, task)
		self.assertTrue(all(task in home_provider.ACTIONS for blocked in home_provider.BLOCKS.values() for task in blocked))
