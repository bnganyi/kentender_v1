# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-18 / AUD-XC-130 / AUD-XC-131 (Proceedings) — a command decides on the latest
committed record, and two requests with one key run once.

Two real connections (`kentender_procurement.tests.two_connections`): a waiter whose
snapshot predates another command's commit must get the typed stale-version refusal,
not a framework timestamp error from `save`, and a duplicate that arrives while the
first request is running waits for it and returns its original result."""

from __future__ import annotations

import frappe

from kentender_procurement.proceedings.services import lifecycle
from kentender_procurement.proceedings.services.errors import ProceedingsError
from kentender_procurement.proceedings.tests.support import CHAIR, NS, OWNER_TYPE, ROSTER, ProceedingsCase
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn


class TestProceedingsCommandEnvelope(ProceedingsCase):
	def setUp(self):
		super().setUp()
		# the other connections commit rows this transaction's snapshot cannot see; end the snapshot before the world is wiped
		self.addCleanup(frappe.db.commit)

	def _in_world(self):
		def setup():
			frappe.flags.kt_prc_owner_adapters = {OWNER_TYPE: self.owner}
			frappe.flags.kt_prc_fixture_namespace = NS
			frappe.flags.kt_prc_clock = "2027-06-12 11:00:12"

		return setup

	def _start(self, created, key, version):
		row = frappe.db.get_value("Proceeding", created["proceeding"], ["owner_type", "owner_id"], as_dict=True)
		return lambda: lifecycle.start_proceeding(
			owner_type=row.owner_type, owner_id=row.owner_id, expected_version=version, roster=ROSTER, custody_reference="TEST-CUSTODY-1",
			owner_event_id=f"start-{created['proceeding']}", idempotency_key=key, actor=CHAIR,
		)

	def test_a_stale_revision_is_the_typed_refusal_not_a_save_timestamp_error(self):
		created = self.create()
		frappe.db.commit()
		before = self.version(created)
		conn_b = Conn(CHAIR, self._start(created, self.key(), before), snapshot_first=True, setup=self._in_world())
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))
		conn_a = Conn(CHAIR, self._start(created, self.key(), before), setup=self._in_world())
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsInstance(conn_b.error, ProceedingsError, repr(conn_b.error))
		self.assertEqual(conn_b.error.code, "PRC_VERSION_CONFLICT")

	def test_two_requests_with_one_key_execute_once_and_both_get_the_result(self):
		created = self.create()
		frappe.db.commit()
		key, before = self.key(), self.version(created)
		conn_a = Conn(CHAIR, self._start(created, key, before), hold=True, setup=self._in_world())
		self.assertTrue(conn_a.ran.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b = Conn(CHAIR, self._start(created, key, before), setup=self._in_world())
		self.assertFalse(conn_b.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first execution")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, conn_b.error)
		self.assertEqual(conn_b.value, conn_a.value)
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Proceeding Command Journal", {"idempotency_key": key}), 1)
		self.assertEqual(self.version(created), conn_a.value["record_version"])
