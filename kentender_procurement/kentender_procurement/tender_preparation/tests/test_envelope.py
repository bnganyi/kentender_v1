# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §11.2 — the command envelope's own low-level mechanics
(idempotency replay/conflict, record-version staleness, row locking and
the `atomic()` savepoint), tested directly."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_procurement.tender_preparation.services import envelope
from kentender_procurement.tender_preparation.services.errors import TenderPreparationError
from kentender_procurement.tender_preparation.tests import fixtures as fx


class TenderEnvelopeCase(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_tender_rows()
		self.addCleanup(frappe.set_user, "Administrator")


class TestReplayAndFingerprint(TenderEnvelopeCase):
	def test_a_fresh_key_has_no_replay(self):
		self.assertIsNone(envelope.replay_or_none(fx.key(), {"a": 1}))

	def test_the_same_key_with_the_same_payload_replays(self):
		key = fx.key()
		envelope.record_command(idempotency_key=key, command="Test", payload={"a": 1}, result={"ok": True, "value": 1})
		replay = envelope.replay_or_none(key, {"a": 1})
		self.assertTrue(replay["idempotent"])
		self.assertEqual(replay["value"], 1)

	def test_the_same_key_with_a_different_payload_is_a_conflict(self):
		key = fx.key()
		envelope.record_command(idempotency_key=key, command="Test", payload={"a": 1}, result={"ok": True})
		with self.assertRaises(TenderPreparationError) as ctx:
			envelope.replay_or_none(key, {"a": 2})
		self.assertEqual(ctx.exception.code, "TPR_IDEMPOTENCY_CONFLICT")

	def test_fingerprint_ignores_user_and_idempotency_key(self):
		self.assertEqual(
			envelope.fingerprint({"a": 1, "user": "x", "idempotency_key": "y"}),
			envelope.fingerprint({"a": 1, "user": "z", "idempotency_key": "w"}),
		)

	def test_an_empty_idempotency_key_is_refused(self):
		with self.assertRaises(TenderPreparationError) as ctx:
			envelope.replay_or_none("", {"a": 1})
		self.assertEqual(ctx.exception.code, "TPR_STALE_VERSION")

	def test_the_journal_is_append_only(self):
		key = fx.key()
		envelope.record_command(idempotency_key=key, command="Test", payload={"a": 1}, result={"ok": True})
		row = frappe.get_doc("Tender Preparation Command Journal", {"idempotency_key": key})
		row.command = "Tampered"
		with self.assertRaises(frappe.ValidationError):
			row.save(ignore_permissions=True)


class TestRecordVersionAndLocking(TenderEnvelopeCase):
	def test_check_record_version_passes_on_a_match_and_fails_otherwise(self):
		doc = frappe._dict(record_version=3)
		envelope.check_record_version(doc, 3)
		with self.assertRaises(TenderPreparationError) as ctx:
			envelope.check_record_version(doc, 4)
		self.assertEqual(ctx.exception.code, "TPR_STALE_VERSION")
		with self.assertRaises(TenderPreparationError):
			envelope.check_record_version(doc, "")

	def test_locked_raises_not_found_for_a_missing_record(self):
		with self.assertRaises(frappe.DoesNotExistError):
			envelope.locked("Prepared Tender", "TPR-DOES-NOT-EXIST")


class TestAtomicSavepoint(TenderEnvelopeCase):
	def _journal(self, key: str) -> None:
		frappe.get_doc(
			{
				"doctype": "Tender Preparation Command Journal", "idempotency_key": key, "command": "Test",
				"request_fingerprint": "x", "actor": "Administrator", "result": "{}", "occurred_at": now_datetime(),
			}
		).insert(ignore_permissions=True)

	def test_a_successful_block_keeps_its_writes(self):
		key = fx.key()
		with envelope.atomic("test"):
			self._journal(key)
		self.assertTrue(frappe.db.exists("Tender Preparation Command Journal", {"idempotency_key": key}))

	def test_a_failing_block_rolls_back_only_its_own_writes(self):
		before, inside = fx.key(), fx.key()
		self._journal(before)
		with self.assertRaises(RuntimeError):
			with envelope.atomic("test"):
				self._journal(inside)
				raise RuntimeError("forced failure inside the savepoint")
		self.assertTrue(frappe.db.exists("Tender Preparation Command Journal", {"idempotency_key": before}))
		self.assertFalse(frappe.db.exists("Tender Preparation Command Journal", {"idempotency_key": inside}))
