# Copyright (c) 2026, KenTender and contributors
"""Wave 4R residue for Strategy: RG-40 (the Strategy Command Journal is command-only)
and RG-34 (a read gate no longer authorises the snapshot write endpoint)."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.command_write_guard import CommandWriteError
from kentender_strategy.api import strategy_consumer_api as api
from kentender_strategy.services import strategy_idempotency as idem
from kentender_strategy.tests.fixtures import purge_record


class TestStrategyCommandJournalIsCommandOnly(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.key = f"rg40-{uuid4().hex[:10]}"
		self.addCleanup(self._purge)

	def _purge(self):
		frappe.set_user("Administrator")
		for name in frappe.get_all("Strategy Command Journal", {"idempotency_key": self.key}, pluck="name"):
			purge_record("Strategy Command Journal", name)
		frappe.db.commit()

	def _journalled(self) -> str:
		out = idem.run_idempotent(self.key, "Strategic Plan", "rg40", "rg40_probe", lambda: {"ok": True}, payload={"p": 1})
		self.assertEqual(out, {"ok": True})
		return frappe.db.get_value("Strategy Command Journal", {"idempotency_key": self.key}, "name")

	def test_the_command_still_journals_and_replays(self):
		name = self._journalled()
		self.assertTrue(name)
		self.assertEqual(idem.run_idempotent(self.key, "Strategic Plan", "rg40", "rg40_probe", lambda: {"ok": False}, payload={"p": 1}), {"ok": True})

	def test_a_key_row_cannot_be_deleted_or_rewritten_by_a_technical_user(self):
		name = self._journalled()
		with self.assertRaises(CommandWriteError) as deleted:
			frappe.delete_doc("Strategy Command Journal", name)
		self.assertEqual(deleted.exception.code, "COMMAND_ONLY_DELETE")
		doc = frappe.get_doc("Strategy Command Journal", name)
		doc.payload_hash = "tampered"
		with self.assertRaises(CommandWriteError):
			doc.save()
		self.assertTrue(frappe.db.exists("Strategy Command Journal", name))

	def test_a_key_row_cannot_be_inserted_by_hand(self):
		with self.assertRaises(CommandWriteError):
			frappe.get_doc(
				{"doctype": "Strategy Command Journal", "idempotency_key": self.key, "document_type": "Strategic Plan", "document_name": "x", "action": "x", "actor": "Administrator"}
			).insert()

	def test_no_role_holds_write_create_or_delete(self):
		for permission in frappe.get_meta("Strategy Command Journal").permissions:
			self.assertFalse(permission.write or permission.create or permission.delete, permission.role)


class TestSnapshotWriteIsNotAnEndpoint(IntegrationTestCase):
	def test_create_strategy_snapshot_is_not_whitelisted(self):
		"""It writes an audit event and a journal row, and the only gate was the read gate that every
		internal user passes. Planning calls the service in-process; nothing needs the endpoint."""
		self.assertNotIn(api.create_strategy_snapshot, frappe.whitelisted)

	def test_the_read_endpoints_stay_whitelisted(self):
		for fn in (api.resolve_strategy_context, api.list_strategy_objectives, api.get_strategy_lineage, api.list_active_targets):
			self.assertIn(fn, frappe.whitelisted)
