# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §7.4/§11.1 — the command envelope's own mechanics
(idempotency replay/conflict, staleness, `bump()` under the lifecycle flag,
the immutability guard on the controllers, and the `atomic()` savepoint)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tenders.services import envelope
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fixtures as fx


class TendersEnvelopeCase(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_tender_rows()
		self.addCleanup(frappe.set_user, "Administrator")


class TestReplayAndFingerprint(TendersEnvelopeCase):
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
		with self.assertRaises(TendersError) as ctx:
			envelope.replay_or_none(key, {"a": 2})
		self.assertEqual(ctx.exception.code, "TND_IDEMPOTENCY_CONFLICT")

	def test_fingerprint_ignores_user_and_idempotency_key(self):
		self.assertEqual(
			envelope.fingerprint({"a": 1, "user": "x", "idempotency_key": "y"}),
			envelope.fingerprint({"a": 1, "user": "z", "idempotency_key": "w"}),
		)

	def test_an_empty_idempotency_key_is_refused(self):
		with self.assertRaises(TendersError) as ctx:
			envelope.replay_or_none("", {"a": 1})
		self.assertEqual(ctx.exception.code, "TND_STALE_VERSION")


class TestImmutabilityAndVersions(TendersEnvelopeCase):
	def _tender(self):
		doc = frappe.get_doc({"doctype": "Tender", "tender_reference": "TND-TEST-ENV-001", "overall_status": "Draft", "record_version": 0, "fixture_namespace": fx.NS})
		return envelope.insert(doc)

	def test_check_record_version_passes_on_a_match_and_fails_on_a_mismatch(self):
		root = self._tender()
		envelope.check_record_version(root, root.record_version)
		with self.assertRaises(TendersError) as ctx:
			envelope.check_record_version(root, root.record_version + 1)
		self.assertEqual(ctx.exception.code, "TND_STALE_VERSION")
		with self.assertRaises(TendersError):
			envelope.check_record_version(root, "")

	def test_bump_increments_the_record_version_under_the_lifecycle_flag(self):
		root = self._tender()
		before = root.record_version
		envelope.bump(root, overall_status="Awaiting procurement approval")
		root.reload()
		self.assertEqual(root.record_version, before + 1)
		self.assertEqual(root.overall_status, "Awaiting procurement approval")

	def test_an_immutable_row_refuses_a_plain_save_and_a_plain_delete(self):
		root = self._tender()
		inserted = envelope.insert(frappe.get_doc({"doctype": "Tender Version", "tender": root.name, "version_number": 1, "status": "Draft", "record_version": 0, "fixture_namespace": fx.NS}))
		version = frappe.get_doc("Tender Version", inserted.name)  # a fresh object: no lifecycle flag
		version.status = "Approved"
		with self.assertRaises(frappe.ValidationError):
			version.save(ignore_permissions=True)
		version.reload()
		with self.assertRaises(frappe.ValidationError):
			version.delete(ignore_permissions=True)
		self.assertTrue(frappe.db.exists("Tender Version", version.name))

	def test_locked_masks_a_missing_row_as_not_found(self):
		with self.assertRaises(frappe.DoesNotExistError):
			envelope.locked("Tender", "TDR-does-not-exist")

	def test_atomic_rolls_back_to_the_savepoint_on_failure(self):
		root = self._tender()
		try:
			with envelope.atomic("test"):
				envelope.insert(frappe.get_doc({"doctype": "Tender Version", "tender": root.name, "version_number": 9, "status": "Draft", "record_version": 0}))
				raise RuntimeError("boom")
		except RuntimeError:
			pass
		self.assertFalse(frappe.db.exists("Tender Version", {"tender": root.name, "version_number": 9}))
