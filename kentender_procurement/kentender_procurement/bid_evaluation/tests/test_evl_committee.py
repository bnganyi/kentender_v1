# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The committee (EVL-CHG-001 v0.4 §3, §5.7, §7.2, §7.3 rows 3–4; tracker
EVL4-403…410; acceptance EVL-A01, EVL-A06 (service parts); boards D02-A,
D02-S, D02-D, D02-CONFLICT, D02-REPLACE, D02-INELIGIBLE, D02-UNABLE).

The Accounting Officer appoints 3–5 eligible members with one Chair; every
ineligible person is reported together with the specific reason; the Head of
Procurement assigns a secretary who is themself or a procurement officer;
each member declares personally with the confidentiality acceptance; a
conflict stops eligibility at once and creates the Accounting Officer's
work; a reasoned replacement keeps history; inability to serve never
silently removes a member; a suspension pauses appointment and declaration
unless its instruction permits them."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.bid_evaluation.services import (
	appointment, declaration, my_work_provider, preparation, records, roster, secretary,
)
from kentender_procurement.bid_evaluation.services.errors import EvaluationError
from kentender_procurement.bid_evaluation.tests.support import (
	AO, CHAIR, HOP, MEMBER, MEMBER_2, OUTSIDER, REPLACEMENT, SECRETARY, EvaluationCase,
)
from kentender_procurement.bid_opening.tests.support import INDEPENDENT
from kentender_procurement.bid_submission.tests.support import DAVID, key

ROSTER = [
	{"user": CHAIR, "department": "Human Resource Management and Development", "capacity": "Chair"},
	{"user": MEMBER, "department": "ICT", "capacity": "Member"},
	{"user": MEMBER_2, "department": "Finance", "capacity": "Member"},
]


def titles(user: str, kind: str = "assigned") -> list[str]:
	return [r["title"] for r in my_work_provider.my_work_rows(user)[kind] if r["module"] == "Bid Evaluation"]


class CommitteeCase(EvaluationCase):
	def setUp(self):
		super().setUp()
		self.evaluation = preparation.ensure_preparation(tender=self.name)["evaluation"]

	def evl_version(self) -> int:
		return int(frappe.db.get_value("Evaluation Case", self.evaluation, "record_version"))

	def evl_appoint(self, members=None, user=AO, reference="MOH/EVAL/TEST/2101") -> dict[str, Any]:
		return appointment.appoint_committee(tender=self.name, members=members or ROSTER, appointment_reference=reference, expected_version=self.evl_version(),
			idempotency_key=key(), user=user)

	def evl_declare(self, user, choice="No conflict to declare", accepted=True, description=""):
		return declaration.declare_interest(tender=self.name, choice=choice, confidentiality_accepted=accepted, conflict_description=description,
			idempotency_key=key(), user=user)

	def refused(self, fn, *args, **kwargs) -> EvaluationError:
		with self.assertRaises(EvaluationError) as ctx:
			fn(*args, **kwargs)
		return ctx.exception


class TestAppointment(CommitteeCase):
	def test_the_accounting_officer_appoints_three_to_five_members(self):
		out = self.evl_appoint()
		self.assertTrue(out["ok"], out)
		self.assertEqual(roster.member_users(self.evaluation), [CHAIR, MEMBER, MEMBER_2])
		self.assertEqual(roster.chair(self.evaluation), CHAIR)
		members = frappe.get_all("Proceeding Member", filters={"parent": frappe.db.get_value("Evaluation Case", self.evaluation, "proceeding"), "active": 1},
			pluck="member_user")
		self.assertEqual(sorted(members), sorted([CHAIR, MEMBER, MEMBER_2]))  # attributed roster history; no authority from it
		for user in (CHAIR, MEMBER, MEMBER_2):
			self.assertIn(f"Declare interests for {self.reference}", titles(user))
		self.assertIn("Waiting for committee declarations", titles(AO, "waiting"))
		self.assertNotIn(f"Appoint evaluation committee for {self.reference}", titles(AO))
		self.assertFalse(roster.complete(self.evaluation)["complete"])  # declarations still owed

	def test_a_person_already_on_the_evaluation_committee_cannot_be_the_independent_opening_member(self):
		"""AUD-EVL-013: BOP-A17 holds in both orders (the evaluation side is test_every_ineligible_person_is_reported_together)."""
		from kentender_procurement.bid_opening.services import appointment as opening_appointment

		self.evl_appoint()
		opening_roster = self.roster()
		members = [opening_roster[0], opening_roster[1], {"user": MEMBER, "committee_role": "Independent member"}]
		refused = opening_appointment.validate(self.name, members)
		self.assertEqual(refused["code"], "BOP_INDEPENDENT_MEMBER_REQUIRED", refused)
		self.assertEqual(refused["errors"], {MEMBER: "Appointed to evaluate this Tender."})
		self.assertTrue(next(c for c in opening_appointment.candidates(self.name) if c["user"] == MEMBER)["involved"])
		# someone outside the evaluation committee is still acceptable
		self.assertIsNone(opening_appointment.validate(self.name, opening_roster))

	def test_only_the_accounting_officer_appoints(self):
		with self.assertRaises(frappe.DoesNotExistError):
			self.evl_appoint(user=HOP)

	def test_every_ineligible_person_is_reported_together(self):
		self.prepared()  # the opening committee, with its independent member; David Ouma's supplier account
		error = self.refused(self.evl_appoint, members=[
			{"user": CHAIR, "department": "HRM", "capacity": "Chair"},
			{"user": INDEPENDENT, "department": "Budget", "capacity": "Member"},
			{"user": DAVID, "department": "ICT", "capacity": "Member"},
		])
		self.assertEqual(error.code, "EVL_MEMBER_INELIGIBLE", error.detail)
		by_person = {r["detail"].get("person"): r["detail"].get("reason") for r in error.reasons}
		self.assertEqual(by_person, {INDEPENDENT: "opening_independent", DAVID: "not_internal"})
		self.assertFalse(roster.current_appointment(self.evaluation))  # no partial roster

	def test_a_department_scoped_person_can_serve(self):
		"""Most staff hold a responsibility only inside their department; that is
		an active KenTender responsibility for committee eligibility (§3)."""
		from kentender_core.services import responsibility_administration as administration

		from kentender_procurement.bid_evaluation.services import people

		unit = frappe.db.get_value("Organisation Unit", {}, "name")
		email = "evlt.departmental@example.test"
		if not frappe.db.exists("User", email):
			frappe.get_doc({"doctype": "User", "email": email, "first_name": "Test Departmental Member", "send_welcome_email": 0, "enabled": 1,
				"user_type": "System User"}).insert(ignore_permissions=True)
			frappe.get_doc("User", email).add_roles("Desk User")
		self.addCleanup(lambda: (frappe.db.delete("User Responsibility Assignment", {"user": email}), frappe.delete_doc("User", email, force=True,
			ignore_permissions=True), frappe.db.commit()))
		administration.grant(user=email, business_role="Departmental Author", organisation_unit=unit, fixture_namespace="EVL_TEST", actor="Administrator")
		self.assertEqual(people.internal(email), (True, "Departmental Author"))
		self.assertEqual(people.internal(OUTSIDER)[0], people.internal(OUTSIDER)[0])  # unchanged for everyone else

	def test_a_staff_account_with_no_responsibility_can_serve(self):
		"""KT-STD-001 v1.13 §8.3: a committee member's authority is the
		appointment alone ("Appointed tender only"), so a Ministry staff
		account needs no standing responsibility to be appointed, and the
		Accounting Officer can pick it. A supplier or public account (a
		Website User) and a technical reader still cannot serve."""
		from kentender_procurement.bid_evaluation.services import people, reads

		email = "evlt.staff@example.test"
		if not frappe.db.exists("User", email):
			frappe.get_doc({"doctype": "User", "email": email, "first_name": "Test Staff Member", "send_welcome_email": 0, "enabled": 1,
				"user_type": "System User"}).insert(ignore_permissions=True)
			frappe.get_doc("User", email).add_roles("Desk User")
		self.addCleanup(lambda: (frappe.delete_doc("User", email, force=True, ignore_permissions=True), frappe.db.commit()))
		self.assertFalse(frappe.db.exists("User Responsibility Assignment", {"user": email}))
		self.assertEqual(people.internal(email), (True, ""))
		self.assertIn(email, [r["user"] for r in reads.candidates(tender_reference=self.reference, user=AO, purpose="committee")])
		self.assertFalse(people.internal(DAVID)[0])
		self.assertFalse(people.internal("Administrator")[0])

	def test_size_and_one_chair(self):
		error = self.refused(self.evl_appoint, members=ROSTER[:2])
		self.assertEqual([r["detail"]["reason"] for r in error.reasons], ["committee_size"])
		error = self.refused(self.evl_appoint, members=[{**r, "capacity": "Chair"} for r in ROSTER])
		self.assertEqual([r["detail"]["reason"] for r in error.reasons], ["one_chair"])


class TestSecretary(CommitteeCase):
	def assign(self, who, user=HOP):
		return secretary.assign_secretary(tender=self.name, secretary=who, appointment_reference="MOH/EVAL/SEC/TEST", expected_version=self.evl_version(),
			idempotency_key=key(), user=user)

	def test_the_head_assigns_a_procurement_officer_or_themself(self):
		self.assertTrue(self.assign(SECRETARY)["ok"])
		self.assertEqual(roster.secretary(self.evaluation), SECRETARY)
		self.assertNotIn(f"Assign evaluation secretary for {self.reference}", titles(HOP))
		self.assertTrue(self.assign(HOP)["ok"])
		self.assertEqual(roster.secretary(self.evaluation), HOP)
		self.assertEqual(frappe.db.count("Evaluation Secretary Appointment", {"evaluation_case": self.evaluation}), 2)  # history kept
		error = self.refused(self.assign, MEMBER)
		self.assertEqual(error.reasons[0]["detail"]["reason"], "not_procurement_officer")
		with self.assertRaises(frappe.DoesNotExistError):
			self.assign(SECRETARY, user=AO)


class TestDeclarationAndReplacement(CommitteeCase):
	def setUp(self):
		super().setUp()
		self.evl_appoint()

	def test_each_member_declares_personally(self):
		error = self.refused(self.evl_declare, CHAIR, accepted=False)
		self.assertEqual((error.code, list(error.detail["fields"])), ("EVL_DECLARATION_REQUIRED", ["confidentiality_accepted"]))
		with self.assertRaises(frappe.DoesNotExistError):
			self.evl_declare(OUTSIDER)  # not a member
		for user in (CHAIR, MEMBER, MEMBER_2):
			self.assertTrue(self.evl_declare(user)["ok"])
		self.assertTrue(roster.complete(self.evaluation)["complete"])
		self.assertNotIn(f"Declare interests for {self.reference}", titles(MEMBER))

	def test_a_conflict_stops_eligibility_and_goes_to_the_accounting_officer(self):
		for user in (CHAIR, MEMBER_2):
			self.evl_declare(user)
		out = self.evl_declare(MEMBER, choice="Declare a conflict", description="I have a financial interest in the bidder.")
		self.assertTrue(out["ok"])
		self.assertEqual(roster.status(self.evaluation, MEMBER)["reasons"], ["declared_conflict"])
		self.assertFalse(roster.complete(self.evaluation)["complete"])
		self.assertIn(f"Resolve committee appointment for {self.reference}", titles(AO))
		self.assertIn("Waiting for committee appointment", titles(CHAIR, "waiting"))
		error = self.refused(self.evl_declare, MEMBER_2, choice="Declare a conflict")
		self.assertIn("conflict_description", error.detail["fields"])

	def test_a_conflicted_member_cannot_clear_their_own_conflict(self):
		"""AUD-EVL-001: only the Accounting Officer's reasoned replacement ends a declared conflict."""
		for user in (CHAIR, MEMBER_2):
			self.evl_declare(user)
		self.evl_declare(MEMBER, choice="Declare a conflict", description="I have a financial interest in the bidder.")
		error = self.refused(self.evl_declare, MEMBER)  # re-declaring "No conflict to declare"
		self.assertEqual((error.code, error.detail.get("reason")), ("EVL_MEMBER_INELIGIBLE", "declared_conflict"))
		self.assertEqual(roster.status(self.evaluation, MEMBER)["reasons"], ["declared_conflict"])
		self.assertEqual(frappe.db.count("Evaluation Declaration", {"evaluation_case": self.evaluation, "member_user": MEMBER}), 1)  # nothing superseded
		self.assertIn(f"Resolve committee appointment for {self.reference}", titles(AO))

	def test_a_reasoned_replacement_keeps_history(self):
		for user in (CHAIR, MEMBER_2):
			self.evl_declare(user)
		self.evl_declare(MEMBER, choice="Declare a conflict", description="I have a financial interest in the bidder.")
		# the conflicted person cannot be the incoming member (board D02-INELIGIBLE)
		error = self.refused(appointment.replace_member, tender=self.name, outgoing=MEMBER, incoming={"user": MEMBER, "department": "ICT"},
			appointment_reference="R0", reason="x", expected_version=self.evl_version(), idempotency_key=key(), user=AO)
		self.assertEqual((error.reasons[0]["detail"]["reason"], error.reasons[0]["detail"]["explanation"]),
			("declared_conflict", "Test Evaluation Member has an unresolved declared conflict for this tender."))
		self.assertEqual(len(roster.member_users(self.evaluation)), 3)  # nothing appointed
		out = appointment.replace_member(tender=self.name, outgoing=MEMBER, incoming={"user": REPLACEMENT, "department": "ICT"},
			appointment_reference="MOH/EVAL/TEST/2101-R1", reason="Replace the member who declared a financial interest.", expected_version=self.evl_version(),
			idempotency_key=key(), user=AO)
		self.assertTrue(out["ok"], out)
		self.assertEqual(roster.member_users(self.evaluation), [CHAIR, MEMBER_2, REPLACEMENT])
		appointments = frappe.get_all("Evaluation Appointment", filters={"evaluation_case": self.evaluation}, fields=["name", "status", "change_kind"],
			order_by="version_number asc")
		self.assertEqual([(a.status, a.change_kind) for a in appointments], [("Superseded", "Initial"), ("Current", "Replacement")])
		replaced = frappe.get_all("Evaluation Committee Member", filters={"parent": appointments[1].name, "member_user": MEMBER}, fields=["status", "replaced_by_user"])
		self.assertEqual([(r.status, r.replaced_by_user) for r in replaced], [("Replaced", REPLACEMENT)])
		self.assertNotIn(f"Resolve committee appointment for {self.reference}", titles(AO))
		self.assertIn(f"Declare interests for {self.reference}", titles(REPLACEMENT))
		self.assertEqual(titles(MEMBER), [])  # the replaced member's personal tasks close as replaced

	def test_inability_to_serve_never_removes_the_member_silently(self):
		for user in (CHAIR, MEMBER, MEMBER_2):
			self.evl_declare(user)
		out = declaration.record_unavailability(tender=self.name, reason="I am unavailable for the remaining evaluation period.", idempotency_key=key(),
			user=MEMBER)
		self.assertTrue(out["ok"])
		self.assertIn(MEMBER, roster.member_users(self.evaluation))
		self.assertEqual(roster.complete(self.evaluation)["pending"], [{"user": MEMBER, "reasons": ["unable_to_serve"]}])
		self.assertIn(f"Resolve committee appointment for {self.reference}", titles(AO))


class TestSuspensionScope(CommitteeCase):
	def suspend(self, permitted: list[str]) -> None:
		doc = frappe.get_doc("Evaluation Case", self.evaluation)
		event = records.insert(frappe.get_doc({
			"doctype": "Evaluation Source Event", "source_event_id": f"{doc.name}-SE-T1", "evaluation_case": doc.name, "event_key": f"test-suspend:{doc.name}",
			"source": "Simulation", "kind": "Suspension", "instruction_reference": "MOH/REVIEW/TEST-PREP", "authority": AO, "received_at": "2027-06-11 08:55:00",
			"permitted_actions_json": json.dumps(permitted),
		}))
		records.bump(doc, suspended=1, suspension_event=event.name)

	def test_permitted_administrative_actions_continue_and_nothing_else(self):
		self.suspend(["appointments"])
		self.assertTrue(self.evl_appoint()["ok"])  # §9.13 P-PREP: appointments permitted
		error = self.refused(self.evl_declare, CHAIR)
		self.assertEqual((error.code, error.detail["instruction"]), ("EVL_SUSPENDED", "MOH/REVIEW/TEST-PREP"))
