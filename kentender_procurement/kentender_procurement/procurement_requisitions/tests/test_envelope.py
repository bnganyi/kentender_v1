# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §10 — the command envelope's own low-level mechanics
(idempotency replay/conflict, record-version staleness, row locking,
`bump()`, and the `atomic()` savepoint), tested directly rather than only
through the higher-level command tests that already exercise it indirectly.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import draft_commands as cmd, envelope
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


class RequisitionEnvelopeCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_requisition_rows()
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")


class TestReplayAndFingerprint(RequisitionEnvelopeCase):
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
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			envelope.replay_or_none(key, {"a": 2})
		self.assertEqual(ctx.exception.code, "REQ_IDEMPOTENCY_CONFLICT")

	def test_fingerprint_ignores_user_and_idempotency_key(self):
		self.assertEqual(
			envelope.fingerprint({"a": 1, "user": "x", "idempotency_key": "y"}),
			envelope.fingerprint({"a": 1, "user": "z", "idempotency_key": "w"}),
		)

	def test_an_empty_idempotency_key_is_refused(self):
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			envelope.replay_or_none("", {"a": 1})
		self.assertEqual(ctx.exception.code, "REQ_STALE_VERSION")


class TestRecordVersionAndLocking(RequisitionEnvelopeCase):
	def _prepared(self) -> dict:
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		return cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())

	def test_check_record_version_passes_on_a_match(self):
		prepared = self._prepared()
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		envelope.check_record_version(root, root.record_version)  # must not raise

	def test_check_record_version_fails_on_a_mismatch(self):
		prepared = self._prepared()
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			envelope.check_record_version(root, root.record_version + 1)
		self.assertEqual(ctx.exception.code, "REQ_STALE_VERSION")

	def test_check_record_version_fails_on_an_empty_expectation(self):
		prepared = self._prepared()
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		with self.assertRaises(ProcurementRequisitionsError):
			envelope.check_record_version(root, "")

	def test_locked_raises_not_found_for_a_missing_record(self):
		with self.assertRaises(frappe.DoesNotExistError):
			envelope.locked("Procurement Requisition", "PRQ-DOES-NOT-EXIST")

	def test_bump_increments_record_version_and_sets_fields(self):
		prepared = self._prepared()
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		before = root.record_version
		envelope.bump(root, lead_org_unit=root.lead_org_unit)
		self.assertEqual(root.record_version, before + 1)
		root.reload()
		self.assertEqual(root.record_version, before + 1)


class TestAtomicSavepoint(RequisitionEnvelopeCase):
	def test_a_successful_block_keeps_its_writes(self):
		prepared_from = None
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		with envelope.atomic("test"):
			envelope.bump(root, lead_org_unit=root.lead_org_unit)
		root.reload()
		self.assertEqual(root.record_version, 1)

	def test_a_failing_block_rolls_back_only_its_own_writes(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		# a write that happens BEFORE the savepoint is opened must survive
		envelope.bump(root, lead_org_unit=root.lead_org_unit)
		version_before_failure = root.record_version
		with self.assertRaises(RuntimeError):
			with envelope.atomic("test"):
				envelope.bump(root, lead_org_unit=root.lead_org_unit)
				raise RuntimeError("forced failure inside the savepoint")
		root.reload()
		self.assertEqual(root.record_version, version_before_failure)
