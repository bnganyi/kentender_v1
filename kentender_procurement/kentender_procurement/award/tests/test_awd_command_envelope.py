# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-131 / AUD-XC-130 (Award) — the command envelope answers a replay only
after authorisation, takes the case lock before it reads the journal, decides
on the latest committed record, and two requests with one key execute once
(AWD-CHG-001 v0.5 section 7: "A duplicate accepted command returns its original
result"; "Conflicting concurrent writes return the current record")."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_procurement.award.services import opinion, records, state
from kentender_procurement.award.services.errors import AwardError
from kentender_procurement.award.tests.support import AO, CASE, HOP, NS, AwardCase
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn

REASON = "The signed report identifies Afya Digital Supplies Limited as the lowest evaluated responsive tenderer. No unresolved issue prevents the proposed award."


def _in_world():
	frappe.flags.kt_awd_fixture_namespace = NS
	frappe.flags.kt_awd_clock = "2027-06-17 09:00:00"


class TestAwardCommandEnvelope(AwardCase):
	def _save(self, user=HOP, key=None, reason=REASON, expected=None):
		return self.run_as(user, opinion.save, award=CASE, conclusion="Recommend award", reason=reason,
			expected_version=self.version() if expected is None else expected, idempotency_key=key)

	# ----- authorisation answers first ---------------------------------------

	def test_a_replay_is_refused_when_the_actor_no_longer_holds_the_authority(self):
		self.deliver()
		self.at("2027-06-17 09:00:00")
		key, v = self.key("save"), self.version()
		first = self._save(key=key, expected=v)
		self.assertTrue(first["ok"])
		with mock.patch("kentender_procurement.award.services.people.holds", return_value=False):
			with self.assertRaises(frappe.DoesNotExistError):
				self._save(key=key, expected=v)
		# the recorded result was not handed back
		self.assertEqual(len([o for o in state.opinions(self.case())]), 1)

	def test_a_replay_by_another_user_is_a_conflict_not_the_recorded_result(self):
		self.deliver()
		self.at("2027-06-17 09:00:00")
		key, v = self.key("save"), self.version()
		self._save(key=key, expected=v)
		with self.assertRaises(AwardError) as caught:
			self.run_as(AO, opinion.save, award=CASE, conclusion="Recommend award", reason=REASON, expected_version=v, idempotency_key=key)
		self.assertNotEqual(caught.exception.code, "")

	# ----- the key is bound to its payload ------------------------------------

	def test_the_same_key_with_another_payload_is_refused(self):
		self.deliver()
		self.at("2027-06-17 09:00:00")
		key, v = self.key("save"), self.version()
		self._save(key=key, expected=v)
		with self.assertRaises(AwardError) as caught:
			self._save(key=key, reason=REASON + " Changed.", expected=v)
		self.assertEqual(caught.exception.code, "AWD_RECORD_CHANGED")

	# ----- real concurrency -----------------------------------------------------

	def _committed(self):
		frappe.db.commit()

	def test_two_requests_with_one_key_execute_once_and_both_get_the_result(self):
		self.deliver()
		self.at("2027-06-17 09:00:00")
		self._committed()
		key = self.key("race")
		args = dict(award=CASE, conclusion="Recommend award", reason=REASON, expected_version=self.version(), idempotency_key=key, user=HOP)
		conn_a = Conn(HOP, lambda: opinion.save(**args), hold=True, setup=_in_world)
		self.assertTrue(conn_a.ran.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b = Conn(HOP, lambda: opinion.save(**args), setup=_in_world)
		self.assertFalse(conn_b.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first execution")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, conn_b.error)
		self.assertEqual(conn_b.value, conn_a.value)
		frappe.db.commit()
		self.assertEqual(len(state.opinions(self.case())), 1)
		self.assertEqual(frappe.db.count(records.JOURNAL, {"idempotency_key": key}), 1)

	def test_a_stale_revision_is_the_typed_refusal_not_a_save_timestamp_error(self):
		self.deliver()
		self.at("2027-06-17 09:00:00")
		self._committed()
		before = self.version()
		conn_b = Conn(
			HOP,
			lambda: opinion.return_report(award=CASE, reason="The report needs a correction.", expected_version=before, idempotency_key=self.key("stale-b"), user=HOP),
			snapshot_first=True,
			setup=_in_world,
		)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))
		conn_a = Conn(HOP, lambda: opinion.save(award=CASE, conclusion="Recommend award", reason=REASON, expected_version=before, idempotency_key=self.key("stale-a"), user=HOP), setup=_in_world)
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		self.assertGreater(int(frappe.db.get_value(records.CASE, CASE, "record_version") or 0), 0)
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsInstance(conn_b.error, AwardError, repr(conn_b.error))
		self.assertEqual(conn_b.error.code, "AWD_RECORD_CHANGED")
