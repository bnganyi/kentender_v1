# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EVL-CHG-001 v0.8 §3 (Secretary), §7.2 (AppointEvaluationCommittee,
DelegateEvaluationSecretary), §8 (EVL_SECRETARY_OFFICE_UNCLEAR,
EVL_SECRETARY_INELIGIBLE), §9.12 (Appointment history), EVL-A20; the default
Head of Procurement Function secretary, the Head's written delegation under
section 46(4)(c) of the Act, the unauthorised attempts and the preserved
history.

`bench run-tests` has no rollback on this bench: nothing here edits a
responsibility; the clock-free assertions read what each command wrote."""

from __future__ import annotations

import re
from unittest import mock

import frappe

from kentender_core.services import responsibility_administration as administration
from kentender_procurement.bid_evaluation.services import appointment, people, reads, report, roster, secretary
from kentender_procurement.bid_evaluation.tests.support import NS, AO, AUDITOR, CHAIR, HOP, MEMBER, MEMBER_2, OUTSIDER, REPLACEMENT, SECRETARY, SUPPORT
from kentender_procurement.bid_evaluation.tests.test_evl_committee import CommitteeCase, titles
from kentender_procurement.bid_submission.tests.support import key

SECRETARY_ROWS = "Evaluation Secretary Appointment"


class SecretaryCase(CommitteeCase):
	def records(self) -> list[dict]:
		return frappe.get_all(SECRETARY_ROWS, filters={"evaluation_case": self.evaluation}, fields=["*"], order_by="creation asc, name asc")

	def current(self) -> dict:
		return frappe.get_doc(SECRETARY_ROWS, {"evaluation_case": self.evaluation, "status": "Current"}).as_dict()

	def delegate(self, who=SECRETARY, user=HOP, k=None, version=None):
		return secretary.delegate_secretary(tender=self.name, secretary=who, expected_version=version or self.evl_version(), idempotency_key=k or key(), user=user)

	def reference_base(self) -> str:
		entity, year, seq = re.match(r"^TND-([A-Z0-9]+)-(\d{4})-(\d+)$", self.reference).groups()
		return f"{entity}/EVAL/SEC/{int(seq):03d}/{year}"


class TestTheHeadIsSecretaryByOffice(SecretaryCase):
	def test_the_appointment_records_the_head_as_secretary_in_the_same_transaction(self):
		out = self.evl_appoint()
		self.assertTrue(out["ok"], out)
		self.assertEqual(roster.secretary(self.evaluation), HOP)
		rows = self.records()
		self.assertEqual(len(rows), 1, rows)
		row = self.current()
		self.assertEqual((row.basis, row.status, row.secretary_user, row.assigned_by), ("By office", "Current", HOP, AO))
		self.assertEqual(row.appointment_reference, self.reference_base())
		self.assertTrue(row.assigned_at)
		current = roster.current_appointment(self.evaluation)
		self.assertEqual(row.source_appointment, current.name)
		self.assertIn(frappe.db.get_value("User", AO, "full_name"), row.appointing_authority)
		self.assertIn(current.appointment_reference, row.appointing_authority)
		self.assertEqual(frappe.db.get_value("Evaluation Case", self.evaluation, "secretary_appointment"), row.name)

	def test_no_secretary_task_waiting_item_or_hand_off_exists_for_anyone(self):
		self.evl_appoint()
		for user in (AO, HOP, SECRETARY, CHAIR):
			for kind in ("assigned", "waiting"):
				found = [t for t in titles(user, kind) if "secretary" in t.lower()]
				self.assertEqual(found, [], (user, kind, found))
		self.assertFalse([t for t in titles(HOP) if t.startswith("Assign evaluation secretary")])

	def test_before_the_appointment_nobody_waits_for_or_owes_a_secretary(self):
		for user in (AO, HOP):
			for kind in ("assigned", "waiting"):
				self.assertEqual([t for t in titles(user, kind) if "secretary" in t.lower()], [], (user, kind))
		self.assertIn(f"Appoint evaluation committee for {self.reference}", titles(AO))

	def test_an_unclear_holder_refuses_the_whole_appointment_and_writes_nothing(self):
		for holders in ([], [HOP, SECRETARY]):
			with mock.patch.object(people, "head_holders", return_value=holders):
				error = self.refused(self.evl_appoint)
			self.assertEqual(error.code, "EVL_SECRETARY_OFFICE_UNCLEAR", holders)
			self.assertEqual(error.args[0], "The Head of Procurement Function could not be identified.")
			self.assertFalse(roster.current_appointment(self.evaluation))
			self.assertEqual(self.records(), [])

	def test_the_accounting_officer_as_the_holder_refuses_the_whole_appointment(self):
		with mock.patch.object(people, "head_holders", return_value=[AO]):
			error = self.refused(self.evl_appoint)
		self.assertEqual(error.code, "EVL_SECRETARY_INELIGIBLE")
		self.assertEqual(error.args[0], "This person cannot be the secretary of this evaluation.")
		self.assertFalse(roster.current_appointment(self.evaluation))
		self.assertEqual(self.records(), [])

	def test_a_replay_returns_the_original_and_records_one_secretary(self):
		k, version = key(), self.evl_version()
		first = appointment.appoint_committee(tender=self.name, members=[{"user": CHAIR, "capacity": "Chair"}, {"user": MEMBER, "capacity": "Member"},
			{"user": MEMBER_2, "capacity": "Member"}], expected_version=version, idempotency_key=k, user=AO)
		again = appointment.appoint_committee(tender=self.name, members=[{"user": CHAIR, "capacity": "Chair"}, {"user": MEMBER, "capacity": "Member"},
			{"user": MEMBER_2, "capacity": "Member"}], expected_version=version, idempotency_key=k, user=AO)
		self.assertEqual(again, first)
		self.assertEqual(len(self.records()), 1)

	def test_a_secretary_has_no_evaluator_authority(self):
		self.evl_appoint()
		view = reads.resolve(tender_reference=self.reference, user=HOP)
		self.assertTrue(view["viewer"]["secretary"])
		self.assertFalse(view["viewer"]["member"] or view["viewer"]["chair"] or view["viewer"]["eligible"])
		self.assertNotIn(HOP, roster.member_users(self.evaluation))


class TestDelegation(SecretaryCase):
	def setUp(self):
		super().setUp()
		self.evl_appoint()

	def test_the_head_delegates_in_writing_with_a_generated_reference_and_the_history_is_kept(self):
		out = self.delegate()
		self.assertTrue(out["ok"], out)
		self.assertEqual(roster.secretary(self.evaluation), SECRETARY)
		rows = self.records()
		self.assertEqual([r.status for r in rows], ["Superseded", "Current"])
		row = self.current()
		self.assertEqual((row.basis, row.secretary_user, row.assigned_by), ("Written appointment", SECRETARY, HOP))
		self.assertEqual(row.appointment_reference, f"{self.reference_base()}-R1")
		self.assertTrue(row.assigned_at)
		self.assertIn(frappe.db.get_value("User", HOP, "full_name"), row.appointing_authority)
		self.assertIn("Head of Procurement Function", row.appointing_authority)
		first = rows[0]
		self.assertEqual((first.basis, first.secretary_user, first.appointment_reference), ("By office", HOP, self.reference_base()))  # never edited
		self.assertEqual(frappe.db.get_value("Evaluation Case", self.evaluation, "secretary_appointment"), row.name)

	def test_a_later_delegation_supersedes_and_keeps_every_earlier_record(self):
		outcome = administration.grant(user=REPLACEMENT, business_role=people.PROCUREMENT_OFFICER, organisation_unit="", fixture_namespace=NS, actor="Administrator")
		self.addCleanup(lambda: administration.revoke(outcome["assignment"], reason="Revoked inside the delegation test.", actor="Administrator"))
		frappe.db.commit()
		self.assertTrue(self.delegate()["ok"])
		self.assertTrue(self.delegate(who=REPLACEMENT)["ok"])
		rows = self.records()
		self.assertEqual([(r.secretary_user, r.status) for r in rows], [(HOP, "Superseded"), (SECRETARY, "Superseded"), (REPLACEMENT, "Current")])
		self.assertEqual([r.appointment_reference for r in rows], [self.reference_base(), f"{self.reference_base()}-R1", f"{self.reference_base()}-R2"])
		self.assertEqual(roster.secretary(self.evaluation), REPLACEMENT)

	def test_a_replay_returns_the_original_and_adds_nothing(self):
		k, version = key(), self.evl_version()
		first = self.delegate(k=k, version=version)
		again = self.delegate(k=k, version=version)
		self.assertEqual(again, first)
		self.assertEqual(len(self.records()), 2)

	def test_the_officer_must_be_an_active_procurement_officer_who_is_not_the_current_secretary(self):
		cases = ((MEMBER, "not_procurement_officer"), (AO, "accounting_officer"), (HOP, "already_secretary"))
		for who, reason in cases:
			error = self.refused(self.delegate, who=who)
			self.assertEqual(error.code, "EVL_SECRETARY_INELIGIBLE", who)
			self.assertEqual(error.args[0], "This person cannot be the secretary of this evaluation.")
			self.assertIn(reason, {r["detail"].get("reason") for r in error.reasons}, (who, error.reasons))
		self.delegate()
		error = self.refused(self.delegate, who=SECRETARY)
		self.assertIn("already_secretary", {r["detail"].get("reason") for r in error.reasons})
		self.assertEqual(len(self.records()), 2)  # nothing written by any refusal

	def test_only_the_authorised_head_can_delegate_everyone_else_gets_not_found_and_nothing_is_written(self):
		before = self.records()
		for user in (SECRETARY, AO, CHAIR, MEMBER, MEMBER_2, AUDITOR, OUTSIDER, SUPPORT, "Administrator"):
			with self.assertRaises(frappe.DoesNotExistError, msg=user):
				self.delegate(user=user)
		self.assertEqual(self.records(), before)
		self.assertEqual(roster.secretary(self.evaluation), HOP)

	def test_after_a_delegation_the_delegate_cannot_delegate_further_and_the_head_still_can(self):
		self.delegate()
		with self.assertRaises(frappe.DoesNotExistError):
			self.delegate(user=SECRETARY)
		self.assertEqual(roster.secretary(self.evaluation), SECRETARY)

	def test_the_delegate_acts_as_secretary_with_no_evaluator_authority(self):
		self.delegate()
		view = reads.resolve(tender_reference=self.reference, user=SECRETARY)
		self.assertTrue(view["viewer"]["secretary"])
		self.assertFalse(view["viewer"]["member"] or view["viewer"]["chair"] or view["viewer"]["eligible"])
		self.assertNotIn(SECRETARY, roster.member_users(self.evaluation))
		# the Head no longer holds the secretary seat but keeps the office's own access
		self.assertFalse(reads.resolve(tender_reference=self.reference, user=HOP)["viewer"]["secretary"])

	def test_no_command_takes_a_typed_department_or_reference(self):
		for extra in ({"department": "Typed"}, {"appointment_reference": "TYPED/1"}):
			with self.assertRaises(TypeError):
				secretary.delegate_secretary(tender=self.name, secretary=SECRETARY, expected_version=self.evl_version(), idempotency_key=key(), user=HOP, **extra)

	def test_the_report_recipient_is_the_head_whether_the_duties_are_held_by_office_or_delegated(self):
		from kentender_procurement.bid_evaluation.services import signing

		doc = frappe.get_doc("Evaluation Case", self.evaluation)
		self.assertEqual(signing._recipient(doc), HOP)  # by office: the record was made by the Accounting Officer, who is never the recipient
		self.delegate()
		self.assertEqual(signing._recipient(doc), HOP)  # delegated: the Head who delegated

	def test_the_delegation_makes_no_new_task_for_anyone(self):
		self.delegate()
		for user in (AO, HOP, SECRETARY):
			for kind in ("assigned", "waiting"):
				self.assertEqual([t for t in titles(user, kind) if "secretary" in t.lower() and "Evaluation secretary for" not in t], [], (user, kind))


class TestTheCommitteeRecordShowsTheSecretary(SecretaryCase):
	def setUp(self):
		super().setUp()
		self.evl_appoint()

	def test_the_committee_read_names_the_current_secretary_with_basis_reference_authority_and_time(self):
		committee = reads.resolve(tender_reference=self.reference, user=AO)["committee"]
		sec = committee["secretary"]
		self.assertEqual((sec["user"], sec["name"], sec["basis"]), (HOP, frappe.db.get_value("User", HOP, "full_name"), "By office"))
		self.assertEqual(sec["reference"], self.reference_base())
		self.assertIn(frappe.db.get_value("User", AO, "full_name"), sec["authority"])
		self.assertTrue(sec["at"])
		self.delegate()
		sec = reads.resolve(tender_reference=self.reference, user=AO)["committee"]["secretary"]
		self.assertEqual((sec["user"], sec["basis"], sec["reference"]), (SECRETARY, "Written appointment", f"{self.reference_base()}-R1"))
		self.assertIn(frappe.db.get_value("User", HOP, "full_name"), sec["authority"])

	def test_only_the_authorised_head_is_offered_delegate_secretary_duties(self):
		offered = {user: reads.resolve(tender_reference=self.reference, user=user)["committee"]["can_delegate"] for user in (HOP, AO, CHAIR, MEMBER, AUDITOR)}
		self.assertEqual({u for u, v in offered.items() if v}, {HOP}, offered)
		with self.assertRaises(frappe.DoesNotExistError):  # a procurement officer who is not yet involved reads nothing, so no control reaches them
			reads.resolve(tender_reference=self.reference, user=SECRETARY)
		technical = reads.resolve(tender_reference=self.reference, user="Administrator")
		self.assertNotIn("committee", technical)  # a technical reader sees no committee, so no control either

	def test_the_pick_list_offers_procurement_officers_who_are_not_the_current_secretary(self):
		rows = reads.candidates(tender_reference=self.reference, user=HOP, purpose="secretary")
		users = [r["user"] for r in rows]
		self.assertIn(SECRETARY, users)
		self.assertNotIn(HOP, users)
		self.assertNotIn(AO, users)
		with self.assertRaises(frappe.DoesNotExistError):
			reads.candidates(tender_reference=self.reference, user=AO, purpose="secretary")

	def test_the_appointment_history_lists_every_secretary_record_in_order(self):
		self.delegate()
		history = report._committee(frappe.get_doc("Evaluation Case", self.evaluation))["history"]
		entries = [h for h in history if h["kind"] in ("Secretary by office", "Delegated")]
		self.assertEqual([h["kind"] for h in entries], ["Secretary by office", "Delegated"])
		by_office, delegated = entries
		self.assertEqual((by_office["person"], by_office["reference"]), (frappe.db.get_value("User", HOP, "full_name"), self.reference_base()))
		self.assertEqual((delegated["person"], delegated["reference"]), (frappe.db.get_value("User", SECRETARY, "full_name"), f"{self.reference_base()}-R1"))
		self.assertIn(frappe.db.get_value("User", HOP, "full_name"), delegated["authority"])
		self.assertTrue(by_office["at"] and delegated["at"])
		self.assertEqual(report._committee(frappe.get_doc("Evaluation Case", self.evaluation))["secretary"]["user"], SECRETARY)

