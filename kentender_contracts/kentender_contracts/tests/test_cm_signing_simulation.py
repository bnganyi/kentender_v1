# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 plan D8, FU-CM-49 (tracker CM8-305): Contract Management's simulation provider is idempotent on the correlation
identity, can reconcile, answers only on a simulation site and only for its own consumer, and its faults are the ones the recovery
rules must survive: a provider that never received the request, a lost reply, a refusal.

Reached through the real core facade and the real hook, so this also proves the registration."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import records, simulation
from kentender_core.services import signing

NS = "CM_TEST"
CONTROLS = "Contract Test Environment Controls"
SIGNER = "amina.hassan@moh.example.test"
DIGEST = "a" * 64


def attest(correlation_id="C-1", member=SIGNER, digest=DIGEST, consumer="contracts"):
	return signing.attest(member=member, target_id="agreement-1", target_digest=digest, minutes_version="", action="Sign", correlation_id=correlation_id, consumer=consumer)


class TestSigningSimulation(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.flags.kt_cm_fixture_namespace = NS
		self.had_flags = {flag: frappe.conf.get(flag) for flag in simulation.FLAGS}
		frappe.conf.kt_cm_simulation_environment = 1
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		frappe.db.commit()

	def tearDown(self) -> None:
		for flag, value in self.had_flags.items():
			frappe.conf[flag] = value
		frappe.flags.kt_cm_fixture_namespace = ""
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		records.wipe(NS)
		frappe.db.commit()

	def held(self):
		return frappe.db.count("Contract Simulated Signature", {"fixture_namespace": NS})

	def test_the_provider_is_found_through_the_hook_for_contracts_and_signs(self):
		result = attest()
		self.assertEqual(result["outcome"], signing.VERIFIED)
		self.assertTrue(result["proof_reference"].startswith("CMSIM-"))
		self.assertEqual(result["correlation_id"], "C-1")

	def test_the_same_correlation_identity_returns_the_same_proof_and_holds_one_signature(self):
		first, second = attest(), attest()
		self.assertEqual(first["proof_reference"], second["proof_reference"])
		self.assertEqual(self.held(), 1)

	def test_another_identity_is_another_proof(self):
		self.assertNotEqual(attest("C-1")["proof_reference"], attest("C-2")["proof_reference"])

	def test_an_identity_reused_for_a_different_signer_or_document_is_refused_not_answered_with_the_earlier_proof(self):
		attest()
		for changed in (attest(member="someone.else@example.test"), attest(digest="b" * 64)):
			self.assertEqual((changed["outcome"], changed["proof_reference"]), (signing.REJECTED, ""))
		self.assertEqual(self.held(), 1)

	def test_a_provider_that_never_received_the_request_is_unavailable_and_holds_nothing(self):
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "Unavailable")
		self.assertEqual(attest()["outcome"], signing.UNAVAILABLE)
		self.assertEqual(self.held(), 0)
		found = signing.reconcile("C-1", consumer="contracts")
		self.assertEqual((found["known"], found["outcome"]), (False, signing.UNAVAILABLE))

	def test_a_lost_reply_is_indeterminate_yet_reconcile_finds_the_signature_and_a_retry_adds_none(self):
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "Indeterminate")
		self.assertEqual(attest()["outcome"], signing.INDETERMINATE)
		self.assertEqual(self.held(), 1)
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		found = signing.reconcile("C-1", consumer="contracts")
		self.assertEqual((found["known"], found["outcome"]), (True, signing.VERIFIED))
		self.assertEqual(attest()["proof_reference"], found["proof_reference"])
		self.assertEqual(self.held(), 1)

	def test_a_refusal_is_held_and_reconciles_as_rejected_with_no_proof(self):
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "Rejected")
		self.assertEqual((attest()["outcome"], attest()["proof_reference"]), (signing.REJECTED, ""))
		found = signing.reconcile("C-1", consumer="contracts")
		self.assertEqual((found["known"], found["outcome"], found["proof_reference"]), (True, signing.REJECTED, ""))

	def test_it_answers_only_on_a_simulation_site(self):
		for flag in simulation.FLAGS:
			frappe.conf[flag] = 0
		# another provider on the site may answer (a full site has Proceedings' double); this one never does and holds nothing
		self.assertFalse(attest()["proof_reference"].startswith("CMSIM-"))
		self.assertEqual(self.held(), 0)
		self.assertIsNone(signing.reconcile("C-1", consumer="contracts")["known"])

	def test_it_never_answers_for_another_modules_request(self):
		result = attest(consumer="proceedings")
		self.assertFalse(result["proof_reference"].startswith("CMSIM-"))
		self.assertEqual(self.held(), 0)
		self.assertNotIn("ContractSigningSimulation", type(signing.service("proceedings")).__name__)
