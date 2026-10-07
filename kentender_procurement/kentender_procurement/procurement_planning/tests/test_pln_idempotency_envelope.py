# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-131 / AUD-XC-130 (Planning) — the command journal binds a key to its
actor, command and payload, answers a replay only to an actor who still holds
the standing they acted with, claims the key with a unique insert so two
requests with one key execute once, and the typed refusals are reachable under
real concurrency (PLN v1.29 section 8: `PLN_IDEMPOTENCY_CONFLICT`,
`PLN_STALE_WRITE`).

The concurrency tests are REAL two-connection tests
(`kentender_procurement.tests.two_connections`): each request has its own
MariaDB connection and transaction, so REPEATABLE READ behaves as it does in
production. The world they need is committed first and purged afterwards.

    bench --site kentender-test.local run-tests --app kentender_procurement \
        --module kentender_procurement.procurement_planning.tests.test_pln_idempotency_envelope
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest import mock

import frappe

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import dpp_lifecycle, envelope, references
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests import test_dpp_lifecycle as base
from kentender_procurement.procurement_planning.write_family import planning_command
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn

key = base.key


@planning_command
def _first(*, idempotency_key: str, user: str | None = None) -> dict:
	"""A stand-in command: same payload shape as `_second`, another command."""
	payload = {"subject": "same"}
	if replay := envelope.replay_or_none(idempotency_key, payload):
		return replay
	result = {"ok": True, "idempotent": False, "ran": "first"}
	envelope.record_command(
		idempotency_key=idempotency_key, command="First", payload=payload, result=result,
		actor=user or frappe.session.user, fixture_namespace=fx.NS,
	)
	return result


@planning_command
def _second(*, idempotency_key: str, user: str | None = None) -> dict:
	payload = {"subject": "same"}
	if replay := envelope.replay_or_none(idempotency_key, payload):
		return replay
	result = {"ok": True, "idempotent": False, "ran": "second"}
	envelope.record_command(
		idempotency_key=idempotency_key, command="Second", payload=payload, result=result,
		actor=user or frappe.session.user, fixture_namespace=fx.NS,
	)
	return result


class TestPlanningCommandEnvelope(base.PlanningCommandCase):
	def _open_args(self, **extra) -> dict:
		return dict(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(),
			fixture_namespace=fx.NS, **extra,
		)

	def _commit_world(self):
		"""Commit what the other connections must see and let go of the advisory
		locks this long-lived connection took (a web request releases them when
		its connection closes; this one stays open)."""
		frappe.db.commit()
		frappe.db.sql("select release_all_locks()")
		self.addCleanup(self._purge)

	def _purge(self):
		frappe.db.rollback()
		frappe.db.sql("select release_all_locks()")
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		frappe.db.commit()

	# ----- a key is bound to its actor, command and payload ---------------------

	def test_another_actor_replaying_a_key_is_a_conflict_not_the_recorded_result(self):
		args = self._open_args()
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.open_departmental_plan(**args)
		frappe.set_user(fx.HOD)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_lifecycle.open_departmental_plan(**args)
		self.assertEqual(caught.exception.code, "PLN_IDEMPOTENCY_CONFLICT")
		self.assertEqual(frappe.db.count("Planning Command Journal", {"idempotency_key": args["idempotency_key"]}), 1)

	def test_the_same_key_with_another_payload_is_the_idempotency_conflict_not_a_stale_write(self):
		args = self._open_args()
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.open_departmental_plan(**args)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_lifecycle.open_departmental_plan(**{**args, "fiscal_year": fx.FY_CLOSED})
		self.assertEqual(caught.exception.code, "PLN_IDEMPOTENCY_CONFLICT")

	def test_the_same_key_for_another_command_is_a_conflict(self):
		frappe.set_user(fx.AUTHOR)
		one = key()
		self.assertEqual(_first(idempotency_key=one)["ran"], "first")
		with self.assertRaises(ProcurementPlanningError) as caught:
			_second(idempotency_key=one)
		self.assertEqual(caught.exception.code, "PLN_IDEMPOTENCY_CONFLICT")

	def test_a_replay_is_refused_when_the_actor_no_longer_holds_what_they_acted_with(self):
		args = self._open_args()
		frappe.set_user(fx.AUTHOR)
		dpp_lifecycle.open_departmental_plan(**args)
		with mock.patch.object(envelope, "standing", return_value=[]):
			with self.assertRaises(frappe.DoesNotExistError):
				dpp_lifecycle.open_departmental_plan(**args)

	def test_a_failed_command_leaves_no_claim_and_its_key_can_be_used_again(self):
		frappe.set_user(fx.AUTHOR)
		one = key()
		with self.assertRaises(ProcurementPlanningError):
			dpp_lifecycle.open_departmental_plan(
				organisation_unit="OU-DOES-NOT-EXIST", fiscal_year=fx.FY_OPEN, idempotency_key=one, fixture_namespace=fx.NS,
			)
		self.assertEqual(frappe.db.count("Planning Command Journal", {"idempotency_key": one}), 0)
		done = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=one, fixture_namespace=fx.NS,
		)
		self.assertTrue(done["ok"])

	def test_a_row_recorded_before_the_change_replays_only_to_its_own_actor(self):
		"""Rows written before AUD-XC-131 carry a payload-only fingerprint and no standing."""
		args = self._open_args()
		frappe.set_user(fx.AUTHOR)
		first = dpp_lifecycle.open_departmental_plan(**args)
		payload = {"organisation_unit": fx.OU_ALPHA, "fiscal_year": fx.FY_OPEN}
		frappe.db.set_value(
			"Planning Command Journal", {"idempotency_key": args["idempotency_key"]},
			{"request_fingerprint": envelope.legacy_fingerprint(payload), "standing": None}, update_modified=False,
		)
		again = dpp_lifecycle.open_departmental_plan(**args)
		self.assertEqual(again["departmental_plan"], first["departmental_plan"])
		frappe.set_user(fx.HOD)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_lifecycle.open_departmental_plan(**args)
		self.assertEqual(caught.exception.code, "PLN_IDEMPOTENCY_CONFLICT")

	def test_every_command_that_replays_a_key_also_records_it(self):
		"""A command that claimed a key but never recorded it would leave a claim with no result."""
		services = Path(inspect.getfile(envelope)).parent
		for path in sorted(services.glob("*.py")):
			if path.name == "envelope.py":
				continue
			tree = ast.parse(path.read_text())
			for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
				names = {c.func.attr for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}
				if "replay_or_none" in names:
					self.assertIn("record_command", names, f"{path.name}::{fn.name} replays a key but never records it")
					decorators = {ast.unparse(d) for d in fn.decorator_list}
					self.assertIn("planning_command", decorators, f"{path.name}::{fn.name} is not a planning_command")

	# ----- real concurrency ------------------------------------------------------

	def test_two_requests_with_one_key_execute_once_and_both_get_the_result(self):
		self._commit_world()
		args = self._open_args(user=fx.AUTHOR)
		conn_a = Conn(fx.AUTHOR, lambda: dpp_lifecycle.open_departmental_plan(**args), hold=True)
		self.assertTrue(conn_a.ran.wait(WAIT))
		self.assertIsNone(conn_a.error, repr(conn_a.error))
		conn_b = Conn(fx.AUTHOR, lambda: dpp_lifecycle.open_departmental_plan(**args))
		self.assertFalse(conn_b.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first execution")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, repr(conn_b.error))
		self.assertEqual(conn_b.value["departmental_plan"], conn_a.value["departmental_plan"])
		self.assertTrue(conn_b.value["idempotent"])
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Planning Command Journal", {"idempotency_key": args["idempotency_key"]}), 1)
		self.assertEqual(frappe.db.count("Departmental Plan", {"organisation_unit": fx.OU_ALPHA}), 1)

	def test_a_stale_version_after_a_competing_commit_is_the_typed_refusal(self):
		opened = self.open_alpha()
		self._commit_world()

		def save(title):
			return lambda: dpp_lifecycle.save_direct_requirement(
				dpp_version=opened["current_version"], values=fx.direct_values(title=title),
				expected_record_version=opened["record_version"], idempotency_key=key(),
			)

		conn_b = Conn(fx.AUTHOR, save("Loser"), snapshot_first=True)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))
		conn_a = Conn(fx.AUTHOR, save("Winner"))
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, repr(conn_a.error))
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsInstance(conn_b.error, ProcurementPlanningError, repr(conn_b.error))
		self.assertEqual(conn_b.error.code, "PLN_STALE_WRITE")

	def test_a_reference_is_never_taken_twice_when_a_competing_create_committed_after_the_snapshot(self):
		self._commit_world()
		conn_b = Conn(fx.AUTHOR, lambda: references.dpp_reference(fx.OU_ALPHA, fx.FY_OPEN), snapshot_first=True)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))
		args = self._open_args(user=fx.AUTHOR)
		conn_a = Conn(fx.AUTHOR, lambda: dpp_lifecycle.open_departmental_plan(**args))
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, repr(conn_a.error))
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, repr(conn_b.error))
		self.assertNotEqual(conn_b.value, conn_a.value["dpp_reference"])
		self.assertGreater(conn_b.value, conn_a.value["dpp_reference"])
