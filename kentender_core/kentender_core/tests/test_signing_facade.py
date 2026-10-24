"""The shared signing facade (TRUST-ADR-001 v0.1 §1(2), §4; CM-CHG-001 v0.8 plan D8, FU-CM-30, FU-CM-49): one lookup of the
`kt_trust_signing_services` hook, one of the four TRUST outcomes with one correlation identity for every answer, and a
`reconcile(correlation_id)` so an attempt whose outcome is unknown can be settled by asking the provider, never by signing again.

Providers here are in-test fakes reached through the real hook lookup."""

from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import signing

HOOK = signing.HOOK
PROVIDERS: dict[str, object] = {}


def plain():
	return PROVIDERS.get("plain")


def contracts():
	return PROVIDERS.get("contracts")


class Plain:
	"""A provider as Proceedings has today: attest only, serves every consumer."""

	def attest(self, **kw):
		return {"outcome": kw.get("outcome", "Accepted/Verified"), "method": "plain", "proof_reference": "P-1"}


class Idempotent:
	"""A provider that serves one consumer, is idempotent on the correlation id and answers reconcile."""

	serves = ("contracts",)

	def __init__(self):
		self.seen: dict[str, dict] = {}
		self.calls = 0

	def attest(self, *, correlation_id, **kw):
		self.calls += 1
		return self.seen.setdefault(correlation_id, {"outcome": "Accepted/Verified", "method": "sim", "proof_reference": f"S-{len(self.seen) + 1}"})

	def reconcile(self, correlation_id):
		found = self.seen.get(correlation_id)
		return {"known": True, **found} if found else {"known": False}


def attest(consumer="", **extra):
	return signing.attest(member="u@example.test", target_id="T-1", target_digest="d" * 64, minutes_version="", action="Sign", correlation_id="C-1", consumer=consumer, **extra)


class TestSigningFacade(IntegrationTestCase):
	def setUp(self):
		PROVIDERS.clear()
		real = frappe.get_hooks

		def hooks(hook=None, *args, **kwargs):
			if hook == HOOK:
				return [f"{__name__}.plain", f"{__name__}.contracts"]  # later entries are asked first
			return real(hook, *args, **kwargs)

		patcher = mock.patch.object(frappe, "get_hooks", side_effect=hooks)
		patcher.start()
		self.addCleanup(patcher.stop)

	def test_no_provider_is_unavailable_and_never_a_verified_proof(self):
		result = attest()
		self.assertEqual((result["outcome"], result["proof_reference"], result["correlation_id"]), (signing.UNAVAILABLE, "", "C-1"))

	def test_a_provider_answer_is_returned_with_the_callers_correlation_id(self):
		PROVIDERS["plain"] = Plain()
		result = attest()
		self.assertEqual((result["outcome"], result["proof_reference"], result["correlation_id"]), (signing.VERIFIED, "P-1", "C-1"))

	def test_a_provider_failure_is_indeterminate_and_logged_not_a_proof(self):
		class Broken:
			def attest(self, **kw):
				raise RuntimeError("down")

		PROVIDERS["plain"] = Broken()
		with mock.patch.object(frappe, "log_error") as logged:
			result = attest()
		self.assertEqual((result["outcome"], result["proof_reference"]), (signing.INDETERMINATE, ""))
		logged.assert_called_once()

	def test_an_outcome_outside_the_four_is_indeterminate(self):
		class Odd:
			def attest(self, **kw):
				return {"outcome": "Maybe", "proof_reference": "X"}

		PROVIDERS["plain"] = Odd()
		self.assertEqual(attest()["outcome"], signing.INDETERMINATE)

	def test_a_provider_that_serves_one_consumer_is_skipped_for_the_others(self):
		PROVIDERS["plain"], PROVIDERS["contracts"] = Plain(), Idempotent()
		self.assertEqual(attest(consumer="contracts")["proof_reference"], "S-1")
		self.assertEqual(attest(consumer="proceedings")["proof_reference"], "P-1")
		self.assertEqual(attest()["proof_reference"], "P-1", "a caller that names no consumer is served by a provider that serves everyone")

	def test_the_same_correlation_id_returns_the_same_proof_from_an_idempotent_provider(self):
		PROVIDERS["contracts"] = Idempotent()
		self.assertEqual(attest(consumer="contracts")["proof_reference"], attest(consumer="contracts")["proof_reference"])

	def test_reconcile_asks_the_provider_and_never_signs(self):
		provider = PROVIDERS["contracts"] = Idempotent()
		attest(consumer="contracts")
		calls = provider.calls
		found = signing.reconcile("C-1", consumer="contracts")
		self.assertEqual((found["known"], found["outcome"], found["proof_reference"], found["correlation_id"]), (True, signing.VERIFIED, "S-1", "C-1"))
		self.assertEqual(provider.calls, calls)

	def test_reconcile_of_an_id_the_provider_never_received_says_so(self):
		PROVIDERS["contracts"] = Idempotent()
		found = signing.reconcile("NEVER", consumer="contracts")
		self.assertEqual((found["known"], found["outcome"], found["proof_reference"]), (False, signing.UNAVAILABLE, ""))

	def test_reconcile_cannot_tell_when_there_is_no_provider_or_it_cannot_reconcile(self):
		self.assertEqual(signing.reconcile("C-1")["known"], None)
		PROVIDERS["plain"] = Plain()
		found = signing.reconcile("C-1")
		self.assertEqual((found["known"], found["outcome"]), (None, signing.UNAVAILABLE))

	def test_a_failing_reconcile_is_indeterminate_and_unknown(self):
		class Broken(Idempotent):
			def reconcile(self, correlation_id):
				raise RuntimeError("down")

		PROVIDERS["contracts"] = Broken()
		with mock.patch.object(frappe, "log_error"):
			found = signing.reconcile("C-1", consumer="contracts")
		self.assertEqual((found["known"], found["outcome"]), (None, signing.INDETERMINATE))

	def test_the_service_lookup_still_answers_none_without_a_provider(self):
		self.assertIsNone(signing.service())
