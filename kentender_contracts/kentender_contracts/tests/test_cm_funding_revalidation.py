# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FU-CM-81 (the Project Owner's decision of 16 October 2026): "Approve a narrowly scoped amendment to Budget's 6 October decision. Allow the authorised CM integration to request Budget-owned revalidation of the exact
reservations in the contract's approved funding package. This grants no general Budget access or power to change funds."

A reservation can stop being available between the award and the signing. Contract Management used to find out when the conversion was refused, after both signatures. It now asks the funding owner to revalidate the
exact reservations its award names before the agreement is sent, at each signing attempt, and again at the moment of conversion. Budget decides each status, nothing is moved, and a reservation that cannot be drawn on is
a hold in plain words (the same kind as the other signing checks) that names who clears it."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_contracts.services import errors, formation, holds, work
from kentender_contracts.simulation.funding import LEDGER
from kentender_contracts.tests import native_world as world  # noqa: F401  (the native world is built once for the class)
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase
from kentender_core.services import contract_funding_contract as seam

STALE = "no longer has funding behind it"


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class TestFundingIsRevalidatedBeforeItIsReliedOn(ContractCase):
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
		frappe.flags.pop("kt_cm_funding_fault", None)
		self.addCleanup(lambda: frappe.flags.pop("kt_cm_funding_fault", None))
		self.p = self.people
		self.n = 0

	def k(self):
		self.n += 1
		return f"k-{self.id().rsplit('.', 1)[-1][:30]}-{self.n}"

	def version(self, case):
		return int(frappe.db.get_value("Contract Case", case, "record_version"))

	def prepared(self):
		out = tw.receive(self.p)
		case = out["contract"]
		formation.save_particulars(case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["brian"], values=tw.package_particulars(self.p))
		return case

	def send(self, case):
		return formation.request_signatures(case, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p["charles"])

	def sign(self, case, party, who):
		return formation.sign_contract(case, party=party, expected_version=self.version(case), idempotency_key=self.k(), actor=self.p[who])

	def reasons(self, exc):
		return [r["detail"].get("reason", "") for r in exc.reasons]

	def test_a_reservation_that_stopped_being_available_stops_the_agreement_being_sent_and_names_who_clears_it(self):
		case = self.prepared()
		frappe.flags.kt_cm_funding_fault = "stale"
		exc = refusal(self.send, case)
		self.assertEqual(exc.code, "CM_HOLD")
		found = [r["detail"] for r in exc.reasons if STALE in r["detail"].get("reason", "")]
		self.assertTrue(found, self.reasons(exc))
		self.assertEqual((found[0]["holder"], found[0]["consequence"]), ("Budget owner", "new_signing_attempt"))
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Preparing", "nothing was frozen or sent")
		frappe.flags.pop("kt_cm_funding_fault")
		self.assertEqual(self.send(case)["lifecycle"], "Awaiting signatures")

	def test_each_signing_attempt_asks_again_and_a_refusal_keeps_the_same_step_for_the_same_person(self):
		case = self.prepared()
		self.send(case)
		frappe.flags.kt_cm_funding_fault = "stale"
		exc = refusal(self.sign, case, "Supplier", "mary")
		self.assertEqual(exc.code, "CM_HOLD")
		self.assertIn(STALE, " ".join(self.reasons(exc)))
		self.assertEqual(frappe.db.get_value("Contract Signature", {"contract_case": case, "party": "Supplier"}, "state"), "Requested", "the supplier's turn is still theirs")
		frappe.flags.pop("kt_cm_funding_fault")
		self.assertEqual(self.sign(case, "Supplier", "mary")["state"], "Signed")
		frappe.flags.kt_cm_funding_fault = "stale"
		self.assertEqual(refusal(self.sign, case, "Entity", "amina").code, "CM_HOLD")
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Awaiting signatures")
		frappe.flags.pop("kt_cm_funding_fault")
		self.assertEqual(self.sign(case, "Entity", "amina")["lifecycle"], "Active")

	def test_it_is_asked_again_when_the_agreement_takes_effect_and_a_refusal_there_is_the_funding_owners_own(self):
		case = self.prepared()
		self.send(case)
		self.sign(case, "Supplier", "mary")
		asked = []

		def answer(_case, _terms, step):
			asked.append(step)
			return ["Reservation RSV-1 has been released."] if step == "convert" else []

		with mock.patch.object(formation, "funding_problems", side_effect=answer):
			done = self.sign(case, "Entity", "amina")
		self.assertEqual(done["lifecycle"], "Active", "both people signed")
		self.assertEqual(asked, ["sign-entity", "convert"])
		self.assertEqual(frappe.db.count(LEDGER, {"contract": case}), 0, "nothing was converted")
		self.assertIn("operation", {h.key.split(":")[0] for h in holds.open_holds(case)})
		self.assertTrue([t for t in work.live(case) if t["command"] == "RestoreContractOperation" and t["holder"] == self.p["daniel"]], "the technical operator is asked to restore it")
		restored = formation.restore_operations(case, actor=self.p["daniel"])
		self.assertEqual({o["kind"]: o["state"] for o in restored["operations"]}, {"Purchase order": "Reconciled", "Funding conversion": "Succeeded"}, "the order already existed and is linked; the conversion is made now")
		self.assertEqual(frappe.db.count(LEDGER, {"contract": case}), 1)
		self.assertEqual(holds.open_holds(case), [])

	def test_the_owner_is_asked_about_exactly_the_reservations_the_award_names_and_nothing_wider(self):
		case = self.prepared()
		asked = []

		def owner(identity, *, contract, allocations):
			asked.append((identity, contract, allocations))
			return {"reservations": [], "problems": []}

		with mock.patch.object(seam, "revalidate", side_effect=owner):
			self.send(case)
		allocations = frappe.parse_json(frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Awaiting signatures"}, "terms_json"))["funding"]["allocations"]
		self.assertEqual(len(asked), 1)
		self.assertEqual(asked[0][1], case)
		self.assertEqual(asked[0][2], allocations, "the exact allocations of the funding package, none added")
		self.assertIn("Funding revalidation", asked[0][0])

	def test_with_no_funding_owner_able_to_revalidate_there_is_nothing_to_ask_and_the_step_goes_ahead(self):
		case = self.prepared()
		with mock.patch.object(seam, "revalidate", return_value=None):
			self.assertEqual(self.send(case)["lifecycle"], "Awaiting signatures")

	def test_a_refusal_from_the_owner_is_a_finding_in_plain_words_and_any_other_failure_is_not_hidden(self):
		case = self.prepared()
		said = "Contract Management may revalidate only the reservations its own contract's award names."
		with mock.patch.object(seam, "revalidate", side_effect=seam.Refused(said)):
			exc = refusal(self.send, case)
		self.assertEqual(exc.code, "CM_HOLD")
		self.assertIn(said, self.reasons(exc))
		with mock.patch.object(seam, "revalidate", side_effect=RuntimeError("The funding owner did not answer.")):
			with self.assertRaises(RuntimeError):  # unknown is not a finding: the step is tried again
				self.send(case)
		self.assertEqual(frappe.db.get_value("Contract Case", case, "lifecycle"), "Preparing")

	def test_a_contract_with_no_funding_allocation_asks_nobody(self):
		self.assertEqual(formation.funding_problems("CM-NONE", {"funding": {"external": True}}, "send"), [])
		self.assertEqual(formation.funding_problems("CM-NONE", {}, "send"), [])
