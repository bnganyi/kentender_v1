"""The published seam between the owners of contract source material and Contract Management (CM-CHG-001 v0.8 plan D20, section 19.4).

Owners (Tenders and the template release, Bid Submission, Evaluation, Award, site configuration) register a provider on `kt_contract_source_provider`; Contract Management asks this
module, never the owner's code or tables. `describe` answers what a reference is, `fetch` returns its bytes with their digest, and `verify` recomputes the digest. A provider answers
only the references it owns (it returns None for the others); the first answer wins. Without any provider a caller must fail closed: no source, no agreement."""

import hashlib
from contextlib import contextmanager
from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import contract_source_contract as seam


def digest(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


class Owner:
	"""A provider that owns the references starting with its prefix."""

	def __init__(self, prefix: str, content: dict[str, bytes], tamper: set[str] = frozenset()):
		self.prefix, self.content, self.tamper = prefix, content, set(tamper)

	def describe(self, *, reference):
		if not reference.startswith(self.prefix) or reference not in self.content:
			return None
		data = self.content[reference]
		return {"reference": reference, "version": 1, "sha256": digest(data), "media_type": "text/plain", "size": len(data), "owner": self.prefix.rstrip(":")}

	def fetch(self, *, reference):
		if not reference.startswith(self.prefix) or reference not in self.content:
			return None
		data = self.content[reference] + (b"!" if reference in self.tamper else b"")
		return {"content": data, "digest": digest(data)}


@contextmanager
def providers(*owners):
	previous = frappe.flags.get("kt_contract_source_providers")
	frappe.flags.kt_contract_source_providers = list(owners)
	try:
		yield
	finally:
		frappe.flags.kt_contract_source_providers = previous


class TestContractSourceSeam(IntegrationTestCase):
	def test_the_seam_names_its_functions_and_finds_a_contract_that_lacks_one(self):
		self.assertEqual(seam.FUNCTIONS, ("describe", "fetch"))
		self.assertEqual(seam.missing_functions(Owner("T:", {})), [])
		self.assertEqual(seam.missing_functions(object()), ["describe", "fetch"])

	def test_with_no_provider_everything_fails_closed(self):
		with providers():
			self.assertIsNone(seam.describe("T:1"))
			self.assertIsNone(seam.fetch("T:1"))
			self.assertFalse(seam.verify("T:1"))
			self.assertEqual(seam.providers(), [])

	def test_a_reference_is_answered_by_the_provider_that_owns_it(self):
		with providers(Owner("T:", {"T:form": b"form"}), Owner("A:", {"A:notice": b"notice"})):
			self.assertEqual(seam.describe("T:form")["owner"], "T")
			self.assertEqual(seam.describe("A:notice")["owner"], "A")
			self.assertIsNone(seam.describe("X:unknown"))
			self.assertEqual(seam.fetch("A:notice")["content"], b"notice")

	def test_verify_recomputes_the_digest_and_a_changed_source_fails(self):
		with providers(Owner("T:", {"T:ok": b"a", "T:bad": b"b"}, tamper={"T:bad"})):
			self.assertTrue(seam.verify("T:ok"))
			self.assertFalse(seam.verify("T:bad"))

	def test_a_provider_that_fails_never_breaks_the_others_or_verifies_anything(self):
		class Broken:
			def describe(self, **kw):
				raise RuntimeError("down")

			def fetch(self, **kw):
				raise RuntimeError("down")

		with providers(Broken(), Owner("T:", {"T:ok": b"a"})), mock.patch.object(frappe, "log_error") as logged:
			self.assertTrue(seam.verify("T:ok"))
			self.assertIsNone(seam.describe("Z:none"))
		self.assertTrue(logged.called)
