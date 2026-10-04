"""CFG-CHG-002 v0.14 §7.1 (CFG10-AC-023) — one idempotency key, one request.

"Same key/same canonical payload returns original result; same key/different
payload returns CFG_IDEMPOTENCY_CONFLICT." Before 24 Sep 2026 the journal
stored only the result, so a reused key with different content silently
replayed the first result as if the second request had succeeded.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_cfg_idempotency
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import procurement_settings as settings
from kentender_core.services.configuration_errors import ConfigurationError
from kentender_core.services.reference_data_idempotency import run_idempotent

PREFIX = "kt-test-idem-"
SOURCE = "KT Test Idempotency Source"


def _purge():
	frappe.db.delete("Reference Data Command Journal", {"idempotency_key": ["like", f"{PREFIX}%"]})
	for name in frappe.get_all("Funding Source", filters={"label": ["like", "KT Test Idempotency%"]}, pluck="name"):
		frappe.db.delete("Audit Event", {"document_type": "Funding Source", "document_name": name})
		frappe.delete_doc("Funding Source", name, force=True, ignore_permissions=True)


class TestConfigurationIdempotency(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		_purge()
		frappe.db.commit()
		cls.addClassCleanup(lambda: (_purge(), frappe.db.commit()))

	def test_same_key_same_payload_replays_the_original_result_without_running_again(self):
		calls = []

		def fn():
			calls.append(1)
			return {"n": len(calls)}

		first = run_idempotent(f"{PREFIX}a", "X", "x", "act", fn, payload={"a": 1, "b": [1, 2]})
		# Key order is not content: the canonical form is compared.
		again = run_idempotent(f"{PREFIX}a", "X", "x", "act", fn, payload={"b": [1, 2], "a": 1})
		self.assertEqual(first, again)
		self.assertEqual(len(calls), 1)

	def test_same_key_different_payload_is_refused_and_does_not_run(self):
		calls = []
		run_idempotent(f"{PREFIX}b", "X", "x", "act", lambda: calls.append(1) or {"ok": True}, payload={"a": 1})
		with self.assertRaises(ConfigurationError) as caught:
			run_idempotent(f"{PREFIX}b", "X", "x", "act", lambda: calls.append(2) or {"ok": True}, payload={"a": 2})
		self.assertEqual(caught.exception.code, "CFG_IDEMPOTENCY_CONFLICT")
		self.assertEqual(str(caught.exception), "We could not save these changes with this request.")
		self.assertEqual(calls, [1])

	def test_callers_that_pass_no_payload_keep_their_replay_behaviour(self):
		"""Shared helper: the legacy reference-data and STD configuration APIs
		do not pass a payload and are unchanged."""
		run_idempotent(f"{PREFIX}c", "X", "x", "act", lambda: {"v": 1})
		self.assertEqual(run_idempotent(f"{PREFIX}c", "X", "x", "act", lambda: {"v": 2}), {"v": 1})

	def test_a_funding_source_add_replayed_with_a_different_name_is_refused(self):
		settings.add_funding_source(label=SOURCE, idempotency_key=f"{PREFIX}fs")
		with self.assertRaises(ConfigurationError) as caught:
			settings.add_funding_source(label=f"{SOURCE} 2", idempotency_key=f"{PREFIX}fs")
		self.assertEqual(caught.exception.code, "CFG_IDEMPOTENCY_CONFLICT")
		self.assertFalse(frappe.db.exists("Funding Source", f"{SOURCE} 2"))
