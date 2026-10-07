# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-131 / AUD-XC-130 (Needs) — the command envelope authorises before it
answers a replay, binds a key to its actor, command and payload, decides on the
latest committed record, and two requests with one key execute once.

NDS v1.16 section 9: "the same key with a different payload is
`NDS_IDEMPOTENCY_CONFLICT`, never a silent replay"; "a stale write never
overwrites another user's change" (`NDS_STALE_WRITE`).

The concurrency tests are REAL two-connection tests
(`kentender_procurement.tests.two_connections`): each request has its own
MariaDB connection and transaction, so REPEATABLE READ behaves as it does in
production. The rows they need are committed first and purged afterwards.

    bench --site kentender-test.local run-tests --app kentender_procurement \
        --module kentender_procurement.departmental_needs.tests.test_nds_idempotency_envelope
"""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import AUTHOR, FY, REVIEWER
from kentender_procurement.departmental_needs.services import lifecycle
from kentender_procurement.departmental_needs.tests import test_departmental_needs_lifecycle as base
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn


class TestNeedsCommandEnvelope(base.DepartmentalNeedsCommandCase):
	def setUp(self):
		super().setUp()
		self._needs: list[str] = []
		self.addCleanup(self._purge)

	def _purge(self):
		"""The two-connection tests commit; remove every row they made."""
		frappe.db.rollback()
		frappe.set_user("Administrator")
		needs = self._needs or [""]
		for doctype in (
			"Departmental Need Decision", "Departmental Need Review Task", "Departmental Need Event",
			"Departmental Need Revision", "Need Withdrawal Request",
		):
			frappe.db.delete(doctype, {"departmental_need": ("in", needs)})
		frappe.db.delete("Notification Log", {"document_name": ("in", needs)})
		frappe.db.delete("Departmental Need", {"name": ("in", needs)})
		frappe.db.commit()

	def _made(self, result: dict) -> dict:
		self._needs.append(result["need"])
		return result

	def _commit_world(self, result: dict) -> dict:
		self._made(result)
		frappe.db.commit()
		return result

	def _update_args(self, result: dict, **extra) -> dict:
		return dict(
			need=result["need"], expected_version=result["record_version"], idempotency_key=self.key(),
			user=AUTHOR, **self.content(title="Saved exactly once"), **extra,
		)

	# ----- authorisation answers first ----------------------------------------

	def test_a_replay_is_refused_when_the_actor_no_longer_holds_the_authority(self):
		result = self._made(self.create())
		args = self._update_args(result)
		frappe.set_user(AUTHOR)
		self.assertFalse(lifecycle.update_need(**args)["idempotent"])
		denied = DepartmentalNeedError("NDS_SCOPE_DENIED", "denied")
		with mock.patch.object(lifecycle, "require_author_command", side_effect=denied):
			with self.assertRaises(DepartmentalNeedError) as caught:
				lifecycle.update_need(**args)
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	def test_a_user_with_no_responsibility_gets_no_recorded_result(self):
		result = self._made(self.create())
		args = self._update_args(result)
		frappe.set_user(AUTHOR)
		lifecycle.update_need(**args)
		frappe.set_user(base.PLANNER)
		with self.assertRaises(DepartmentalNeedError) as caught:
			lifecycle.update_need(**{**args, "user": base.PLANNER})
		self.assertEqual(caught.exception.code, "NDS_SCOPE_DENIED")

	# ----- a key is bound to its actor, command and payload ---------------------

	def test_another_author_replaying_a_create_key_is_a_conflict_not_the_recorded_result(self):
		key = self.key()
		frappe.set_user(AUTHOR)
		first = self._made(lifecycle.create_need(organisation_unit=self.ou, financial_year=FY, idempotency_key=key, **self.content()))
		other = self.author_reviewer()  # holds a real Departmental Author responsibility for the same unit
		frappe.set_user(other)
		with self.assertRaises(DepartmentalNeedError) as caught:
			lifecycle.create_need(organisation_unit=self.ou, financial_year=FY, idempotency_key=key, **self.content())
		self.assertEqual(caught.exception.code, "NDS_IDEMPOTENCY_CONFLICT")
		self.assertEqual(frappe.db.count("Departmental Need Decision", {"idempotency_key": key}), 1)
		self.assertTrue(first["need"])

	def test_the_same_key_for_another_command_is_a_conflict(self):
		# withdraw and cancel-successor take the same arguments; only the command differs.
		result = self._made(self.create())
		key = self.key()
		frappe.set_user(AUTHOR)
		lifecycle.withdraw_need(need=result["need"], expected_version=result["record_version"], idempotency_key=key, reason="No longer needed")
		with self.assertRaises(DepartmentalNeedError) as caught:
			lifecycle.cancel_accepted_need_successor(need=result["need"], expected_version=result["record_version"], idempotency_key=key, reason="No longer needed")
		self.assertEqual(caught.exception.code, "NDS_IDEMPOTENCY_CONFLICT")

	def test_a_legacy_row_without_an_actor_or_command_binding_replays_only_to_its_own_actor(self):
		"""Rows written before this change carry a payload-only fingerprint."""
		result = self._made(self.create())
		args = self._update_args(result)
		frappe.set_user(AUTHOR)
		first = lifecycle.update_need(**args)
		legacy = lifecycle._legacy_fingerprint(args)
		frappe.db.set_value("Departmental Need Decision", {"idempotency_key": args["idempotency_key"]}, "request_fingerprint", legacy, update_modified=False)
		again = lifecycle.update_need(**args)
		self.assertTrue(again["idempotent"])
		self.assertEqual(again["need"], first["need"])

	# ----- real concurrency ------------------------------------------------------

	def test_two_requests_with_one_key_execute_once_and_both_get_the_result(self):
		result = self._commit_world(self.create())
		args = self._update_args(result)
		conn_a = Conn(AUTHOR, lambda: lifecycle.update_need(**args), hold=True)
		self.assertTrue(conn_a.ran.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b = Conn(AUTHOR, lambda: lifecycle.update_need(**args))
		self.assertFalse(conn_b.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first execution")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, repr(conn_b.error))
		self.assertFalse(conn_a.value["idempotent"])
		self.assertTrue(conn_b.value["idempotent"])
		self.assertEqual(conn_b.value["record_version"], conn_a.value["record_version"])
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Departmental Need Decision", {"idempotency_key": args["idempotency_key"]}), 1)

	def test_two_creates_with_one_key_make_one_need_and_both_get_its_identity(self):
		key = self.key()
		args = dict(organisation_unit=self.ou, financial_year=FY, idempotency_key=key, user=AUTHOR, **self.content())
		frappe.db.commit()
		conn_a = Conn(AUTHOR, lambda: lifecycle.create_need(**args), hold=True)
		self.assertTrue(conn_a.ran.wait(WAIT))
		self.assertIsNone(conn_a.error, repr(conn_a.error))
		conn_b = Conn(AUTHOR, lambda: lifecycle.create_need(**args))
		self.assertFalse(conn_b.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first creation")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self._needs.append(conn_a.value["need"])
		self.assertIsNone(conn_b.error, repr(conn_b.error))
		self.assertEqual(conn_b.value["need"], conn_a.value["need"])
		self.assertTrue(conn_b.value["idempotent"])
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Departmental Need Decision", {"idempotency_key": key}), 1)

	def test_a_stale_version_after_a_competing_commit_is_the_typed_refusal_not_a_save_timestamp_error(self):
		result = self._commit_world(self.create())
		before = result["record_version"]
		conn_b = Conn(
			AUTHOR,
			lambda: lifecycle.update_need(need=result["need"], expected_version=before, idempotency_key=self.key(), user=AUTHOR, **self.content(title="Loser")),
			snapshot_first=True,
		)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))
		conn_a = Conn(AUTHOR, lambda: lifecycle.update_need(need=result["need"], expected_version=before, idempotency_key=self.key(), user=AUTHOR, **self.content(title="Winner")))
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, repr(conn_a.error))
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsInstance(conn_b.error, DepartmentalNeedError, repr(conn_b.error))
		self.assertEqual(conn_b.error.code, "NDS_STALE_WRITE")
		frappe.db.commit()
		revision = frappe.db.get_value("Departmental Need", result["need"], "current_revision")
		self.assertEqual(frappe.db.get_value("Departmental Need Revision", revision, "title"), "Winner")

	def test_a_reference_is_never_taken_twice_when_a_competing_create_committed_after_the_snapshot(self):
		fy = frappe.get_doc("Fiscal Year", FY)
		conn_b = Conn(AUTHOR, lambda: lifecycle._next_reference(fy.name), snapshot_first=True)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))
		frappe.set_user(AUTHOR)
		frappe.db.commit()
		conn_a = Conn(AUTHOR, lambda: lifecycle.create_need(organisation_unit=self.ou, financial_year=FY, idempotency_key=self.key(), user=AUTHOR, **self.content()))
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, repr(conn_a.error))
		self._needs.append(conn_a.value["need"])
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, repr(conn_b.error))
		taken = frappe.db.get_value("Departmental Need", conn_a.value["need"], "need_reference")
		self.assertNotEqual(conn_b.value, taken)
		self.assertGreater(conn_b.value, taken)
