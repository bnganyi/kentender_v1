# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AWD-CHG-001 v0.4 section 5.8 (AWD-IF-05), CM-CHG-001 v0.8 sections 5.2, 7 (plan Phase 5; tracker CM8-501, 502, 510; FU-CM-33): Contract Management as Award's Contracting receiver.

Every answer carries a durable receipt, once per Award reference; events and updates wait for their package; a restriction holds signing and activation until the owner's resolution is recorded; and
where another receiver answers, Contract Management declines unless the site names it."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_contracts import award_receiver as receiving
from kentender_contracts.boards import router
from kentender_contracts.services import errors, formation, holds, work
from kentender_contracts.simulation import sources
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class TestPrecedence(ContractCase):
	def test_it_declines_where_another_receiver_answers_unless_the_site_names_it(self):
		saved = frappe.conf.get(receiving.SETTING)
		self.addCleanup(lambda: frappe.conf.update({receiving.SETTING: saved}) if saved is not None else frappe.conf.pop(receiving.SETTING, None))
		frappe.conf.pop(receiving.SETTING, None)
		with mock.patch.object(receiving, "_another_answers", return_value=True):
			self.assertIsNone(receiving.receiver(), "the stand-in keeps answering where it does")
			frappe.conf[receiving.SETTING] = "contracts"
			self.assertIsInstance(receiving.receiver(), receiving.Receiver, "named by the site, it answers over the stand-in")
		frappe.conf.pop(receiving.SETTING, None)
		with mock.patch.object(receiving, "_another_answers", return_value=False):
			self.assertIsInstance(receiving.receiver(), receiving.Receiver, "on a live site nothing else answers, so it does")
			frappe.conf[receiving.SETTING] = "simulation"
			self.assertIsNone(receiving.receiver(), "the site can also name the stand-in")

	def test_it_is_registered_where_award_looks(self):
		self.assertIn(receiving.PATH, frappe.get_hooks(receiving.HOOK))


class TestReceiver(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: self.env.__exit__(None, None, None))
		self.p, self.n = self.people, 0
		self.receiver = receiving.Receiver()

	def k(self):
		self.n += 1
		return f"rcv-{self.id().rsplit('.', 1)[-1]}-{self.n}"

	def package(self, **o):
		award = sources.award_package()
		return {**award, "reference": "AWD-PKG-01", "package_digest": "d" * 64, "handoff": sources.source_handoff(award["award_case"]), "managing_unit": tw.unit(), "fixture_namespace": "CM_TEST", **o}

	def event(self, outcome="Award", reference="DEC-1-EVT"):
		return {"event_type": "AwardDecisionRecorded", "event_version": 1, "event_id": reference, "reference": reference, "award_case": sources.CASE, "decision": "DEC-1", "outcome": outcome, "fixture_namespace": "CM_TEST"}

	def update(self, issue="ISS-1", reference="AWD-PKG-01:UPD:ISS-1"):
		return {"reference": reference, "award_case": sources.CASE, "package": "AWD-PKG-01", "kind": "Restriction", "issue": issue, "basis": "Reported challenge", "scope": "This award",
			"effective_at": "2027-07-03 09:00:00", "fixture_namespace": "CM_TEST"}

	def mine(self, case):
		ours = set(self.p.values())
		return {(t["command"], t["holder"], t["state"]) for t in work.live(case) if t["holder"] in ours}

	def inbox(self, **filters):
		return frappe.get_all("Contract Award Inbox", filters={"fixture_namespace": "CM_TEST", **filters}, fields=["name", "kind", "state", "contract_case", "receipt"])

	# -- the package ----------------------------------------------------------------------------------------------------------------
	def test_a_package_makes_one_case_one_task_and_one_receipt_and_a_retry_returns_them(self):
		first = self.receiver.receive_package(self.package())
		again = self.receiver.receive_package(self.package())
		self.assertEqual((first["receipt"], first["duplicate"], again["duplicate"]), (again["receipt"], False, True))
		self.assertTrue(first["receipt"].startswith("CMR-") and first["task_user"])
		case = frappe.get_doc("Contract Case", first["contract"])
		self.assertEqual((case.source_kind, case.source_reference, case.lifecycle, case.managing_unit), ("KenTender award", sources.CASE, "Preparing", tw.unit()))
		self.assertEqual(frappe.db.count("Contract Case", {"fixture_namespace": "CM_TEST"}), 1)
		self.assertEqual(len(self.inbox(kind="Package")), 1)
		self.assertIn(("RequestContractSignatures", self.p["charles"], "actionable"), self.mine(case.name))

	def test_a_package_the_module_cannot_accept_is_not_acknowledged(self):
		bad = self.package()
		bad["decision"] = {**bad["decision"], "outcome": "No award"}
		with self.assertRaises(RuntimeError) as caught:
			self.receiver.receive_package(bad)
		self.assertIn("cannot accept the package", str(caught.exception))
		self.assertEqual(frappe.db.count("Contract Case", {"fixture_namespace": "CM_TEST"}), 0)

	# -- events ---------------------------------------------------------------------------------------------------------------------
	def test_an_event_that_arrives_first_waits_and_is_applied_when_the_package_comes(self):
		early = self.receiver.receive_decision_event(self.event())
		self.assertTrue(early["receipt"])
		self.assertEqual([(r.kind, r.state, r.contract_case) for r in self.inbox(kind="Decision event")], [("Decision event", "Received", None)])
		self.assertEqual(self.receiver.receive_decision_event(self.event())["duplicate"], True)
		case = self.receiver.receive_package(self.package())["contract"]
		self.assertEqual([(r.state, r.contract_case) for r in self.inbox(kind="Decision event")], [("Applied", case)])
		self.assertEqual(frappe.db.count("Contract Event", {"contract_case": case, "event_type": "Award decision recorded"}), 1)

	def test_a_no_award_event_is_kept_and_creates_no_case(self):
		receipt = self.receiver.receive_decision_event(self.event(outcome="No award", reference="DEC-2-EVT"))
		self.assertTrue(receipt["receipt"])
		self.assertEqual(frappe.db.count("Contract Case", {"fixture_namespace": "CM_TEST"}), 0)

	# -- updates ---------------------------------------------------------------------------------------------------------------------
	def test_a_restriction_holds_signing_and_activation_until_the_owners_resolution_is_recorded(self):
		case = self.receiver.receive_package(self.package())["contract"]
		self.receiver.receive_update(self.update())
		blocking = holds.open_holds(case)
		self.assertEqual([(h.key, sorted(h.blocks)) for h in blocking], [("award restriction:ISS-1", ["activate_contract", "new_signing_attempt"])])
		self.assertIn(("ReviewAwardRestriction", self.p["charles"], "actionable"), self.mine(case))
		out = formation.save_particulars(case, expected_version=frappe.db.get_value("Contract Case", case, "record_version"), idempotency_key=self.k(), actor=self.p["brian"], values=tw.package_particulars(self.p))
		exc = refusal(formation.request_signatures, case, expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		self.assertEqual(exc.code, "CM_HOLD")
		self.assertEqual(refusal(receiving.release_restriction, case, issue="ISS-1", reason=" ", reference="", expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["charles"]).fields.keys(), {"reason", "reference"})
		self.assertEqual(refusal(receiving.release_restriction, case, issue="ISS-1", reason="Court order set aside", reference="HC/2027/88", expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["julia"]).code, "CM_AUTHORITY")
		receiving.release_restriction(case, issue="ISS-1", reason="Court order set aside", reference="HC/2027/88", expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		self.assertEqual(holds.open_holds(case), [])
		self.assertEqual([(r.state) for r in self.inbox(kind="Update")], ["Released"])
		sent = formation.request_signatures(case, expected_version=frappe.db.get_value("Contract Case", case, "record_version"), idempotency_key=self.k(), actor=self.p["charles"])
		self.assertTrue(sent["package"])

	def test_an_update_that_arrives_first_is_applied_with_its_package(self):
		self.receiver.receive_update(self.update())
		self.assertEqual([r.state for r in self.inbox(kind="Update")], ["Received"])
		case = self.receiver.receive_package(self.package())["contract"]
		self.assertEqual([h.key for h in holds.open_holds(case)], ["award restriction:ISS-1"])

	def test_an_update_never_reaches_back_into_an_agreement_already_in_force(self):
		case = self.receiver.receive_package(self.package())["contract"]
		out = formation.save_particulars(case, expected_version=frappe.db.get_value("Contract Case", case, "record_version"), idempotency_key=self.k(), actor=self.p["brian"], values=tw.package_particulars(self.p))
		sent = formation.request_signatures(case, expected_version=out["record_version"], idempotency_key=self.k(), actor=self.p["charles"])
		first = formation.sign_contract(case, party="Supplier", expected_version=sent["record_version"], idempotency_key=self.k(), actor=self.p["mary"])
		formation.sign_contract(case, party="Entity", expected_version=first["record_version"], idempotency_key=self.k(), actor=self.p["amina"])
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Active")
		self.receiver.receive_update(self.update(issue="ISS-9", reference="AWD-PKG-01:UPD:ISS-9"))
		self.assertEqual(holds.open_holds(case), [], "an agreement already in force is not overwritten or held by a later update")
		self.assertEqual(frappe.db.count("Contract Event", {"contract_case": case, "event_type": "Award restriction received"}), 1, "it is recorded")
		self.assertFalse([1 for c, _h, _s in self.mine(case) if c == "ReviewAwardRestriction"])

	def test_the_head_of_procurements_step_on_a_restriction_is_a_screen_with_one_dialog(self):
		case = self.receiver.receive_package(self.package())["contract"]
		self.receiver.receive_update(self.update())
		self.assertTrue([t for t in work.live(case) if t["command"] == "RecordContractAwardPublication" and t["holder"] == self.p["charles"]], "the head's publication task is open and older (FU-CM-108)")
		board = router.board_for(case, self.p["charles"])  # the task that blocks signing leads the standing duty (the Project Owner, 16 October 2026, FU-CM-133)
		self.assertEqual((board["p"], board["dialogs"]["resolution"]["command"], board["dialogs"]["resolution"]["args"]), ("Record the resolution", "RecordRestrictionResolution", {"issue": "ISS-1"}))
		from kentender_contracts.api import commands

		self.assertIn("RecordRestrictionResolution", commands.COMMANDS)
