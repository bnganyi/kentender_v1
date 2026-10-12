# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-131 / AUD-XC-130 (Evaluation) — the command envelope answers a replay
only to an actor who still holds the standing they acted with, locks the case
with a locking read, claims the key by unique insert, and so returns the
original result to a duplicate and the typed version refusal to a stale
request (EVL-CHG-001 v0.4 section 7.2: "Replays return the original result;
stale or conflicting requests have no partial effect")."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_procurement.bid_evaluation.services import appointment, findings, records, roster
from kentender_procurement.bid_evaluation.services.errors import EvaluationError
from kentender_procurement.bid_evaluation.tests.support import AO, CLOCKS, MEMBER, MEMBER_2, REPLACEMENT, WORLD_FLAGS, EvaluationCase
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn


class TestEvaluationCommandEnvelope(EvaluationCase):
	def setUp(self):
		super().setUp()
		self.case = self.reviewing()
		self.requirement_key = self.requirement(self.case, "Service location")["requirement_key"]
		self.bid = self.requirement(self.case, "Service location")["bid"]
		self.flags = {k: frappe.flags.get(k) for k in (*CLOCKS, *WORLD_FLAGS, "kt_evl_fixture_namespace")}

	def _thread_flags(self):
		for name, value in self.flags.items():
			frappe.flags[name] = value

	def _finding(self, idem, user=MEMBER):
		return lambda: findings.record_evidence_finding(tender=self.name, bid=self.bid, requirement_key=self.requirement_key, result="Meets",
			reason="Recorded evidence reviewed.", evidence_reference="Kenya service-centre details", idempotency_key=idem, user=user)

	def _version(self):
		return int(frappe.db.get_value("Evaluation Case", self.case, "record_version"))

	# ----- authorisation answers first ------------------------------------------

	def test_a_replay_is_refused_when_the_actor_no_longer_has_the_standing_they_acted_with(self):
		idem = key()
		first = self._finding(idem)()
		self.assertTrue(first["ok"])
		self.assertEqual(self._finding(idem)(), first)  # still a member: the replay answers
		with mock.patch.object(roster, "member_users", return_value=[]):
			with self.assertRaises(frappe.DoesNotExistError):
				self._finding(idem)()

	def test_the_same_key_for_another_payload_is_refused(self):
		idem = key()
		self._finding(idem)()
		with self.assertRaises(EvaluationError) as caught:
			findings.record_evidence_finding(tender=self.name, bid=self.bid, requirement_key=self.requirement_key, result="Does not meet",
				reason="Another reason.", evidence_reference="Kenya service-centre details", idempotency_key=idem, user=MEMBER)
		self.assertEqual(caught.exception.code, "EVL_VERSION_CONFLICT")

	# ----- real concurrency --------------------------------------------------------

	def test_two_requests_with_one_key_execute_once_and_both_get_the_result(self):
		idem = key()
		frappe.db.commit()
		before = frappe.db.count(findings.FINDING) if hasattr(findings, "FINDING") else None
		conn_a = Conn(MEMBER, self._finding(idem), hold=True, setup=self._thread_flags)
		self.assertTrue(conn_a.ran.wait(WAIT))
		self.assertIsNone(conn_a.error, repr(conn_a.error))
		conn_b = Conn(MEMBER, self._finding(idem), setup=self._thread_flags)
		self.assertFalse(conn_b.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first execution")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, repr(conn_b.error))
		self.assertEqual(conn_b.value, conn_a.value)
		frappe.db.commit()
		self.assertEqual(frappe.db.count(records.JOURNAL, {"idempotency_key": idem}), 1)
		if before is not None:
			self.assertEqual(frappe.db.count(findings.FINDING), before + 1)

	def test_a_stale_revision_is_the_typed_refusal_not_a_save_timestamp_error(self):
		frappe.db.commit()
		before = self._version()

		def replace(idem):
			return lambda: appointment.replace_member(tender=self.name, outgoing=MEMBER_2, incoming={"user": REPLACEMENT}, reason="Replace the member.",
				expected_version=before, idempotency_key=idem, user=AO)

		conn_b = Conn(AO, replace(key()), snapshot_first=True, setup=self._thread_flags)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))
		conn_a = Conn(AO, replace(key()), setup=self._thread_flags)
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, repr(conn_a.error))
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsInstance(conn_b.error, EvaluationError, repr(conn_b.error))
		self.assertEqual(conn_b.error.code, "EVL_VERSION_CONFLICT")
