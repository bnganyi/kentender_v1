# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-18 / AUD-XC-130 / AUD-XC-131 (Bid Opening) — a command decides on the latest
committed case, and two requests with one key run once.

Two real connections (`kentender_procurement.tests.two_connections`), against the
Bid Opening test world: the waiter whose snapshot predates another command's commit
gets the typed stale-version refusal, not a framework timestamp error from `save`,
and a duplicate that arrives while the first is running waits for it and returns the
original result."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_opening.services import appointment
from kentender_procurement.bid_opening.services.errors import BidOpeningError
from kentender_procurement.bid_opening.tests.support import AO, NS, OpeningCase
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn


def _in_world():
	frappe.flags.kt_bop_fixture_namespace = NS
	frappe.flags.kt_prc_fixture_namespace = NS


class TestOpeningCommandEnvelope(OpeningCase):
	def setUp(self):
		super().setUp()
		# the other connections commit rows this transaction's snapshot cannot see; end the snapshot before the world is wiped
		self.addCleanup(frappe.db.commit)

	def _appoint(self, idempotency_key, version):
		return lambda: appointment.appoint_opening_committee(tender=self.name, members=self.roster(), expected_version=version, idempotency_key=idempotency_key, user=AO)

	def test_a_stale_revision_is_the_typed_refusal_not_a_save_timestamp_error(self):
		self.prepare_case()
		frappe.db.commit()
		before = self.case_version()
		conn_b = Conn(AO, self._appoint(key(), before), snapshot_first=True, setup=_in_world)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))
		conn_a = Conn(AO, self._appoint(key(), before), setup=_in_world)
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsInstance(conn_b.error, BidOpeningError, repr(conn_b.error))
		self.assertEqual(conn_b.error.code, "BOP_VERSION_CONFLICT")

	def test_two_requests_with_one_key_execute_once_and_both_get_the_result(self):
		self.prepare_case()
		frappe.db.commit()
		request_key, before = key(), self.case_version()
		conn_a = Conn(AO, self._appoint(request_key, before), hold=True, setup=_in_world)
		self.assertTrue(conn_a.ran.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b = Conn(AO, self._appoint(request_key, before), setup=_in_world)
		self.assertFalse(conn_b.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first execution")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, conn_b.error)
		self.assertEqual(conn_b.value, conn_a.value)
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Opening Command Journal", {"idempotency_key": request_key}), 1)
		case = frappe.db.get_value("Bid Opening Case", {"tender": self.name})
		self.assertEqual(frappe.db.count("Opening Committee Appointment", {"opening_case": case}), 1)
