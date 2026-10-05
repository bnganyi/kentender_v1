# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1 — Award's facts for Procurement Analytics (`award/services/analytics_facts.py`; plan Phase 2C, FU-ANL-07).

Award's own fast synthetic world (a case in under a second, no Tender built); the read only reads. Charles Mutiso (Head of
Procurement Function), Amina Hassan (Accounting Officer), Naomi Chebet (Auditor) and Daniel Otieno (Technical Operator) are
the Award test world's own actors; the Head of User Department is a real user granted the responsibility for one test class
and removed after, counted.

Run:
  bench --site kentender-test.local run-tests --app kentender_procurement \\
    --module kentender_procurement.award.tests.test_analytics_facts
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import frappe

from kentender_core.services import responsibility_administration as administration
from kentender_procurement.award.services import corrections, decision, issues, people, reads, records, restrictions, simulation, state
from kentender_procurement.award.services.analytics_facts import facts_for
from kentender_procurement.award.test_services import sources as syn
from kentender_procurement.award.tests.support import AO, CASE, DANIEL, HOP, NAOMI, NS, REF, AwardCase
from kentender_procurement.award.tests.test_awd_corrections import CORRECTION

AT = datetime(2027, 6, 19, 10, 0)
HOD = "awdanl.hod@example.test"
OUTSIDER = "brian.wafula@moh.example.test"  # a Procurement Officer: no Award responsibility
ANL_NS = "KT_TEST_AWDANL"
RECEIVED = datetime(2027, 6, 16, 14, 7, 1)
SIGNED = datetime(2027, 6, 17, 9, 10)
DECIDED = datetime(2027, 6, 17, 10, 0)
AMOUNT = Decimal("46400000.00")
REASON = "The reported calculation issue may affect the recommendation."


def _remove_hod() -> None:
	frappe.set_user("Administrator")
	for name in frappe.get_all("User Responsibility Assignment", filters={"user": HOD}, pluck="name"):
		frappe.delete_doc("User Responsibility Assignment", name, force=1, ignore_permissions=True)
	for name in frappe.get_all("Contact Email", filters={"email_id": HOD}, pluck="parent"):
		frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
	if frappe.db.exists("User", HOD):
		frappe.delete_doc("User", HOD, force=1, ignore_permissions=True)
	frappe.db.commit()


def _assert_clean() -> None:
	"""Runs last (registered first): Award's namespace and this module's user and grant are gone."""
	frappe.set_user("Administrator")
	left = {doctype: frappe.db.count(doctype, {"fixture_namespace": NS}) for doctype in records.DOCTYPES}
	left["User"] = frappe.db.count("User", {"name": HOD})
	left["User Responsibility Assignment"] = frappe.db.count("User Responsibility Assignment", {"user": HOD})
	left = {name: count for name, count in left.items() if count}
	if left:
		raise AssertionError(f"Award Analytics test rows left behind: {left}")


class TestAwardAnalyticsFacts(AwardCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(_assert_clean)
		cls.addClassCleanup(_remove_hod)

	def setUp(self):
		super().setUp()
		self.addCleanup(frappe.set_user, "Administrator")

	# ----- helpers -----

	def facts(self, user: str = HOP, tenders: list[str] | None = None) -> dict:
		return facts_for(user=user, tender_names=tenders if tenders is not None else [self.case().tender], at=AT)

	def mine(self, user: str = HOP) -> dict:
		return self.facts(user)[self.case().tender]

	def who(self, role: str, fallback: str) -> str:
		found = people.holders(role)
		return people.full_name(found[0]) if len(found) == 1 else fallback

	def hod(self) -> str:
		if not frappe.db.exists("User", HOD):
			unit = [row.name for row in frappe.get_all("Organisation Unit", filters={"status": "Active"}, fields=["name", "lft", "rgt"], order_by="lft asc")
				if row.rgt == row.lft + 1][0]
			frappe.get_doc({"doctype": "User", "email": HOD, "first_name": "Awd Analytics Head", "send_welcome_email": 0, "enabled": 1}).insert(
				ignore_permissions=True).add_roles("Desk User")
			administration.grant(user=HOD, business_role="Head of User Department", organisation_unit=unit, fixture_namespace=ANL_NS, actor="Administrator")
			frappe.db.commit()
		return HOD

	def to_cycle_two(self):
		"""Award recorded in cycle 1, then a reported correction and a corrected evaluation report open cycle 2."""
		self.deliver()
		self.awarded()
		self.at("2027-06-18 10:00:00")
		syn.add_correction(self.case().tender, CORRECTION)
		corrections.pull_case(self.case().name)
		issue = issues.open_issues(self.case(), issue_type="Source correction")[0]
		self.run_as(HOP, restrictions.disposition, award=self.case().name, issue=issue.name, outcome="Request corrected evaluation", reason=REASON,
			evidence="CN-1", next_action="Request a corrected evaluation report.")
		self.run_as(AO, corrections.record, award=self.case().name, outcome="Request corrected evaluation", reason=REASON, expected_version=self.version())
		self.at("2027-06-19 09:00:00")
		self.deliver(version=2, delivered_at="2027-06-19 09:00:00")

	def counts(self) -> dict:
		tables = [*records.DOCTYPES, "Support Issue", "Audit Event", "Notification Log", "Version", "Error Log"]
		return {**{table: frappe.db.count(table) for table in tables}, "case": frappe.db.get_value(records.CASE, CASE, "modified")}

	# ----- the shape -----

	def test_the_case_before_any_decision(self):
		self.deliver()
		who = self.who(people.HEAD_OF_PROCUREMENT, "the Head of Procurement Function")
		row = self.mine()
		self.assertEqual(set(row), {"position", "stage", "received_at", "decision_at", "decision_outcome", "decision_events", "award_amount", "award_amount_visible",
			"sent_to_contracting", "closed", "cancelled", "outstanding"})
		self.assertEqual((row["stage"], row["received_at"], row["decision_at"], row["decision_outcome"], row["decision_events"]), ("Opinion", RECEIVED, None, None, []))
		self.assertEqual((row["award_amount"], row["award_amount_visible"], row["sent_to_contracting"], row["closed"], row["cancelled"]), (None, True, False, False, False))
		self.assertEqual(row["outstanding"], {"text": f"Awaiting professional opinion by {who}.", "holder": who if who != "the Head of Procurement Function" else
			people.HEAD_OF_PROCUREMENT, "since": RECEIVED})  # the raw instant the report was received, not a display string
		self.assertIsInstance(row["outstanding"]["since"], datetime)

	def test_only_tenders_with_a_case_are_returned(self):
		self.deliver()
		self.assertEqual(list(self.facts(tenders=[self.case().tender, "TND-NO-SUCH-TENDER", ""])), [self.case().tender])
		self.assertEqual(self.facts(tenders=["TND-NO-SUCH-TENDER"]), {})
		self.assertEqual(self.facts(tenders=[]), {})

	def test_the_award_decision_amount_and_instants(self):
		self.deliver()
		self.awarded()
		row = self.mine()
		self.assertEqual((row["decision_at"], row["decision_outcome"], row["decision_events"]), (DECIDED, "Award", [DECIDED]))
		self.assertEqual(row["award_amount"], AMOUNT)
		self.assertIsInstance(row["award_amount"], Decimal)
		self.assertEqual((row["stage"], row["sent_to_contracting"], row["closed"], row["outstanding"]), ("Waiting to proceed", False, False, None))
		self.assertEqual(row["received_at"], RECEIVED)

	def test_a_decision_still_with_the_accounting_officer_has_no_instant_or_amount(self):
		self.deliver()
		self.signed_opinion()
		who = self.who(people.ACCOUNTING_OFFICER, "the Accounting Officer")
		row = self.mine()
		self.assertEqual((row["stage"], row["decision_at"], row["decision_outcome"], row["decision_events"], row["award_amount"]), ("Decision", None, None, [], None))
		self.assertEqual(row["outstanding"]["text"], f"Awaiting award decision by {who}.")
		self.assertEqual(row["outstanding"]["since"], SIGNED)

	def test_return_for_correction_is_not_a_decision_and_the_first_decision_stands(self):
		self.deliver()
		self.signed_opinion()
		self.at("2027-06-17 09:30:00")
		self.run_as(AO, decision.record, award=CASE, outcome="Return for correction", reason="Explain the unresolved funding concern before recommending an award.",
			expected_version=self.version())
		row = self.mine()
		self.assertEqual((row["stage"], row["decision_at"], row["decision_outcome"], row["decision_events"], row["award_amount"]), ("Opinion", None, None, [], None))
		self.assertEqual(row["outstanding"]["since"], datetime(2027, 6, 17, 9, 30))  # back with the Head of Procurement Function since the return
		self.signed_opinion()
		self.at("2027-06-17 11:00:00")
		self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="I accept the recommendation in the signed evaluation report and professional opinion.",
			expected_version=self.version())
		row = self.mine()
		self.assertEqual((row["decision_at"], row["decision_outcome"], row["decision_events"], row["award_amount"]), (datetime(2027, 6, 17, 11, 0), "Award", [datetime(2027, 6, 17, 11, 0)], AMOUNT))

	def test_no_award_has_an_outcome_no_amount_and_the_recorded_next_action(self):
		self.deliver()
		self.signed_opinion(conclusion="No current recommendation", reason="Tender validity expired before an award could be notified.")
		self.at("2027-06-17 10:00:00")
		self.run_as(AO, decision.record, award=CASE, outcome="No award", reason="Tender validity expired before an award could be notified.",
			next_action="Review whether the tender should be cancelled", expected_version=self.version())
		row = self.mine()
		self.assertEqual((row["stage"], row["decision_at"], row["decision_outcome"], row["decision_events"], row["award_amount"], row["award_amount_visible"], row["closed"]),
			("Closed", DECIDED, "No award", [DECIDED], None, True, True))
		self.assertEqual(row["outstanding"], {"text": "Review whether the tender should be cancelled.",
			"holder": people.full_name(state.committed_decision(self.case()).next_action_owner), "since": DECIDED})  # whoever the owner named, as the site holds it

	def test_the_amount_is_the_current_cycles_award_and_a_correction_does_not_move_the_first_decision(self):
		self.to_cycle_two()
		row = self.mine()
		# cycle 2 is open and undecided: cycle 1's award is superseded history, so no amount; the first decision is untouched
		self.assertEqual((row["stage"], row["decision_at"], row["decision_outcome"], row["decision_events"]), ("Opinion", DECIDED, "Award", [DECIDED]))
		self.assertIsNone(row["award_amount"])
		self.signed_opinion(reason="The corrected report confirms the recommendation.")
		self.at("2027-06-19 10:00:00")
		self.run_as(AO, corrections.record, award=CASE, outcome="Record corrected award", reason="The corrected report confirms the recommendation.", expected_version=self.version())
		row = self.mine()
		self.assertEqual((row["decision_at"], row["decision_outcome"], row["decision_events"]), (DECIDED, "Award", [DECIDED, datetime(2027, 6, 19, 10, 0)]))
		current = state.committed_decision(self.case())
		self.assertEqual((current.kind, current.cycle), ("Correction", 2))
		self.assertEqual(row["award_amount"], Decimal(current.submitted_amount))

	def test_a_no_award_correction_after_an_award_has_no_amount_but_keeps_the_first_outcome(self):
		self.to_cycle_two()
		self.signed_opinion(conclusion="No current recommendation", reason="The calculation discrepancy remains unresolved.")
		self.at("2027-06-19 10:00:00")
		self.run_as(AO, corrections.record, award=CASE, outcome="Record no award", reason="The calculation discrepancy remains unresolved.",
			next_action="Review whether the tender should be cancelled", expected_version=self.version())
		row = self.mine()
		self.assertEqual((row["stage"], row["closed"], row["decision_at"], row["decision_outcome"], row["award_amount"]), ("Closed", True, DECIDED, "Award", None))
		self.assertEqual(row["decision_events"], [DECIDED, datetime(2027, 6, 19, 10, 0)])

	def test_an_award_waiting_for_its_notices_is_outstanding_from_the_decision(self):
		simulation.set_controls(email_failure_organisations="Afya Digital Supplies Limited")
		self.deliver()
		self.awarded()
		row = self.mine()
		self.assertEqual(row["stage"], "Notices")
		hop = issues.hop_for(self.case())
		self.assertEqual(row["outstanding"], {"text": "Award decision recorded. Required bidder notices are awaiting delivery.",
			"holder": people.full_name(hop) if hop else people.HEAD_OF_PROCUREMENT, "since": DECIDED})
		self.assertEqual(row["award_amount"], AMOUNT)  # a decision with delayed notices is still the current Award decision

	def test_a_review_or_order_hold_is_outstanding_from_its_own_instant(self):
		self.deliver()
		self.awarded()
		self.assertIsNone(self.mine()["outstanding"])
		self.at("2027-06-20 11:00:00")
		self.run_as(HOP, restrictions.record_external, award=CASE, basis="Authoritative order", source="Review Board suspension notice",
			received_at="2027-06-20 11:00:00", evidence="PPARB/2027/33", reason="Suspension received.")
		self.assertEqual(self.mine()["outstanding"], {"text": "This award is on hold.", "holder": people.full_name(issues.hop_for(self.case())), "since": datetime(2027, 6, 20, 11, 0)})

	def test_the_position_phrase_follows_the_stage_the_hold_and_the_closed_outcome(self):
		self.deliver()
		self.assertEqual(self.mine()["position"], "professional opinion outstanding")
		self.signed_opinion()
		self.assertEqual(self.mine()["position"], "award decision outstanding")
		self.at("2027-06-17 09:30:00")
		self.run_as(AO, decision.record, award=CASE, outcome="Return for correction", reason="Explain the unresolved funding concern before recommending an award.",
			expected_version=self.version())
		self.assertEqual(self.mine()["position"], "professional opinion outstanding")  # back with the Head of Procurement Function
		self.signed_opinion()
		self.at("2027-06-17 10:00:00")
		self.run_as(AO, decision.record, award=CASE, outcome="Award", reason="I accept the recommendation in the signed evaluation report and professional opinion.",
			expected_version=self.version())
		self.assertEqual(self.mine()["position"], "waiting period running")
		self.at("2027-06-20 11:00:00")
		self.run_as(HOP, restrictions.record_external, award=CASE, basis="Authoritative order", source="Review Board suspension notice",
			received_at="2027-06-20 11:00:00", evidence="PPARB/2027/33", reason="Suspension received.")
		self.assertEqual(self.mine()["position"], "on hold")
		frappe.db.set_value(records.CASE, CASE, {"delivered_at": "2027-06-24 10:00:00", "stage": "Sent to Contracting"})
		self.assertEqual(self.mine()["position"], "sent to Contract Management")  # a hold does not undo a durable delivery
		frappe.db.set_value(records.CASE, CASE, {"cancelled": 1})
		self.assertEqual(self.mine()["position"], "tender cancelled; award ended")

	def test_the_position_phrase_for_notices_and_a_closed_no_award(self):
		simulation.set_controls(email_failure_organisations="Afya Digital Supplies Limited")
		self.deliver()
		self.awarded()
		self.assertEqual(self.mine()["position"], "required bidder notices awaiting delivery")
		simulation.set_controls(email_failure_organisations="")
		self.deliver("036")
		name = "AWD-AWT-2100-036"
		self.signed_opinion(name, conclusion="No current recommendation", reason="Refer the unresolved tie to the Accounting Officer for a lawful next step.")
		self.at("2027-06-17 10:00:00")
		self.run_as(AO, decision.record, award=name, outcome="No award", reason="The tie is unresolved.",
			next_action="Prepare a lawful next procurement step for the Accounting Officer's decision", expected_version=self.version(name))
		self.assertEqual(self.facts(tenders=[self.case(name).tender])[self.case(name).tender]["position"], "no award was made")

	def test_cancelled_and_sent_to_contracting_are_separate_facts(self):
		self.deliver()
		self.awarded()
		frappe.db.set_value(records.CASE, CASE, {"cancelled": 1})
		row = self.mine()
		self.assertEqual((row["cancelled"], row["closed"], row["outstanding"]), (True, False, None))
		frappe.db.set_value(records.CASE, CASE, {"cancelled": 0, "delivered_at": "2027-06-24 10:00:00", "stage": "Sent to Contracting"})
		row = self.mine()
		self.assertEqual((row["sent_to_contracting"], row["cancelled"], row["stage"], row["outstanding"]), (True, False, "Sent to Contracting", None))

	# ----- who gets the amount -----

	def test_the_amount_goes_to_the_offices_and_technical_readers_and_never_to_a_department_head(self):
		self.deliver()
		self.awarded()
		for user in (HOP, AO, NAOMI, DANIEL, "Administrator"):
			row = self.mine(user)
			self.assertEqual((row["award_amount"], row["award_amount_visible"]), (AMOUNT, True), user)
			self.assertEqual((row["decision_at"], row["decision_outcome"], row["received_at"]), (DECIDED, "Award", RECEIVED), user)  # the instants are for every actor
		frappe.set_user(self.hod())
		for user in (HOD, OUTSIDER):
			row = self.mine(user)
			self.assertEqual((row["award_amount"], row["award_amount_visible"]), (None, False), user)
			self.assertEqual((row["decision_at"], row["decision_outcome"], row["decision_events"], row["stage"]), (DECIDED, "Award", [DECIDED], "Waiting to proceed"), user)

	def test_technical_readers_get_the_full_facts_the_technical_view_withholds(self):
		self.deliver()
		self.signed_opinion()
		for user in (DANIEL, "Administrator"):
			row = self.mine(user)
			self.assertEqual((row["stage"], row["received_at"], row["award_amount_visible"]), ("Decision", RECEIVED, True), user)
			self.assertTrue(row["outstanding"]["text"].startswith("Awaiting award decision by"), user)
			self.assertEqual(row["outstanding"]["since"], SIGNED, user)
		old = reads.technical_view(self.case())  # the owner's own technical view: operations only, no decision facts
		self.assertNotIn("received_at", old)
		self.assertNotIn("outstanding", old)

	def test_a_failed_read_raises_instead_of_returning_zeros(self):
		self.deliver()
		self.awarded()
		frappe.db.set_value(state.DECISION, state.committed_decision(self.case()).name, "submitted_amount", "not a number")
		with self.assertRaises(ValueError):
			self.mine()
		self.assertIsNone(self.mine(OUTSIDER)["award_amount"])  # no amount is read for an actor who may not have it

	# ----- reading changes nothing -----

	def test_the_read_creates_and_marks_nothing(self):
		simulation.set_controls(email_failure_organisations="Afya Digital Supplies Limited")
		self.deliver()
		self.awarded()
		before = self.counts()
		for user in (HOP, AO, NAOMI, DANIEL, "Administrator", OUTSIDER):
			self.facts(user)
		self.assertEqual(self.counts(), before)
