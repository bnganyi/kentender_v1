# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §7 (common envelope), plan D3/D4/D19 (tracker CM8-301): every write goes through `records` under the
Contract Management write window; a command runs once per key under the case lock and commits all its writes or none; a
replay returns the original; a conflicting reuse is refused; time comes from the trusted clock."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D, short_instant  # noqa: F401
import unittest

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import get_datetime

from kentender_contracts.services import clock, errors, records
from kentender_core.services import command_write_guard as errors_guard

NS = "CM_TEST"


def make_case(contract_id: str):
	return records.new("Contract Case", contract_id=contract_id, source_kind="External record", fixture_namespace=NS)


class TestContractRecords(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.flags.kt_cm_fixture_namespace = NS

	def tearDown(self) -> None:
		frappe.flags.kt_cm_fixture_namespace = ""
		frappe.flags.kt_cm_clock = None
		records.wipe(NS)
		frappe.db.commit()

	# -- the writes ------------------------------------------------------------------------------------------------
	def test_writes_go_through_the_window_and_a_bare_save_is_still_refused(self):
		case = make_case("CM-TEST-R1")
		self.assertEqual(case.lifecycle, "Preparing")
		self.assertEqual(case.fixture_namespace, NS)
		again = frappe.get_doc("Contract Case", case.name)
		again.lifecycle = "Active"
		with self.assertRaises(errors_guard.CommandWriteError):
			again.save(ignore_permissions=True)
		again = frappe.get_doc("Contract Case", case.name)  # the refused save had already stamped the in-memory copy
		records.update(again, lifecycle="Active")
		self.assertEqual(frappe.db.get_value("Contract Case", case.name, "lifecycle"), "Active")

	def test_bump_advances_the_record_revision(self):
		case = make_case("CM-TEST-R2")
		self.assertEqual(case.record_version, 1)
		records.bump(case, lifecycle="Awaiting signatures")
		self.assertEqual(frappe.db.get_value("Contract Case", case.name, "record_version"), 2)

	def test_the_namespace_defaults_from_the_flag(self):
		case = records.new("Contract Case", contract_id="CM-TEST-R3", source_kind="External record")
		self.assertEqual(case.fixture_namespace, NS)

	# -- the clock ---------------------------------------------------------------------------------------------------
	def test_the_clock_honours_an_injected_instant_then_the_trusted_test_clock_then_the_site_clock(self):
		frappe.flags.kt_cm_clock = D("2027-07-02 09:00:00")
		self.assertEqual(clock.now(), get_datetime(D("2027-07-02 09:00:00")))
		frappe.flags.kt_cm_clock = None
		self.assertIsNotNone(clock.now())
		self.assertEqual(clock.when(D("2027-07-02 09:01:00")), short_instant("2027-07-02 09:01:00"))
		self.assertEqual(clock.when(None), "")

	# -- the command envelope ------------------------------------------------------------------------------------------
	def run_command(self, case, key="k-1", name="TestCommand", actor="Administrator", payload=None, body=None, authorise=None):
		return records.command(name, case=case.name, idempotency_key=key, actor=actor, payload=payload or {"n": 1}, body=body or (lambda: {"ok": True, "contract": case.name}), authorise=authorise)

	def test_a_command_runs_once_per_key_and_a_replay_returns_the_original(self):
		case = make_case("CM-TEST-C1")
		calls = []

		def body():
			calls.append(1)
			records.bump(frappe.get_doc("Contract Case", case.name), lifecycle="Awaiting signatures")
			return {"ok": True, "contract": case.name, "marker": len(calls)}

		first = self.run_command(case, body=body)
		second = self.run_command(case, body=body)
		self.assertEqual(first, second)
		self.assertEqual(len(calls), 1)
		self.assertEqual(frappe.db.get_value("Contract Case", case.name, "record_version"), 2)
		row = frappe.db.get_value("Contract Command Journal", {"idempotency_key": "k-1"}, ["command", "contract_case", "actor", "fixture_namespace"], as_dict=True)
		self.assertEqual((row.command, row.contract_case, row.actor, row.fixture_namespace), ("TestCommand", case.name, "Administrator", NS))

	def test_a_reused_key_with_another_payload_command_or_actor_is_a_conflict(self):
		case = make_case("CM-TEST-C2")
		self.run_command(case)
		for kwargs in ({"payload": {"n": 2}}, {"name": "OtherCommand"}, {"actor": "Guest"}):
			with self.assertRaises(errors.ContractError) as caught:
				self.run_command(case, **kwargs)
			self.assertEqual(caught.exception.code, "CM_CHANGED")
			self.assertEqual(caught.exception.detail.get("reason"), "idempotency_key_reused")

	def test_a_missing_key_is_refused(self):
		case = make_case("CM-TEST-C3")
		with self.assertRaises(errors.ContractError) as caught:
			self.run_command(case, key="  ")
		self.assertEqual(caught.exception.code, "CM_CHANGED")
		self.assertEqual(caught.exception.detail.get("reason"), "idempotency_key_required")

	def test_a_failing_body_commits_nothing_and_does_not_claim_the_key(self):
		case = make_case("CM-TEST-C4")

		def broken():
			records.bump(frappe.get_doc("Contract Case", case.name), lifecycle="Active")
			raise RuntimeError("boom")

		with self.assertRaises(RuntimeError):
			self.run_command(case, key="k-fail", body=broken)
		self.assertEqual(frappe.db.get_value("Contract Case", case.name, "lifecycle"), "Preparing")
		self.assertFalse(frappe.db.exists("Contract Command Journal", {"idempotency_key": "k-fail"}))
		result = self.run_command(case, key="k-fail")
		self.assertTrue(result["ok"])

	def test_a_refusal_returned_as_data_is_not_journalled_so_a_corrected_retry_runs(self):
		case = make_case("CM-TEST-C5")
		refused = self.run_command(case, key="k-refuse", body=lambda: {"ok": False, "code": "CM_HOLD"})
		self.assertFalse(refused["ok"])
		self.assertFalse(frappe.db.exists("Contract Command Journal", {"idempotency_key": "k-refuse"}))
		self.assertTrue(self.run_command(case, key="k-refuse")["ok"])

	def test_authorisation_runs_before_a_recorded_result_is_answered(self):
		case = make_case("CM-TEST-C6")
		self.run_command(case, key="k-auth")

		def deny():
			errors.fail("CM_AUTHORITY")

		with self.assertRaises(errors.ContractError) as caught:
			self.run_command(case, key="k-auth", authorise=deny)
		self.assertEqual(caught.exception.code, "CM_AUTHORITY")

	def test_a_stale_revision_is_a_conflict_that_returns_the_current_record_version(self):
		case = make_case("CM-TEST-C7")
		records.bump(case, lifecycle="Awaiting signatures")
		locked = records.lock(case.name)
		with self.assertRaises(errors.ContractError) as caught:
			records.check_version(locked, 1)
		self.assertEqual(caught.exception.code, "CM_CHANGED")
		self.assertEqual(caught.exception.detail["record_version"], 2)
		records.check_version(locked, 2)
		with self.assertRaises(errors.ContractError):
			records.check_version(locked, None)

	def test_lock_of_an_unknown_case_is_not_found(self):
		with self.assertRaises(frappe.DoesNotExistError):
			records.lock("CM-NOPE")

	# -- numbering, json helpers, wipe -----------------------------------------------------------------------------------
	# core's allocation_lock is MariaDB SQL; the independence site is SQLite and proves installation, not the engine
	@unittest.skipIf(frappe.db.db_type != "mariadb", "kentender_core allocation_lock needs MariaDB")
	def test_numbering_is_the_next_committed_number_and_json_helpers_round_trip(self):
		self.assertEqual(records.next_number("Contract Operation Intent", {"contract_case": "CM-NO-SUCH"}, "subject_version"), 1)
		self.assertEqual(records.loads(None), {})
		self.assertEqual(records.loads(records.dumps({"b": 1, "a": [2]})), {"a": [2], "b": 1})
		self.assertEqual(records.digest({"a": 1, "b": 2}), records.digest({"b": 2, "a": 1}))
		case = make_case("CM-TEST-N1")
		records.append_json(case, "attempts_json", {"x": 1}) if case.meta.has_field("attempts_json") else None

	def test_wipe_removes_only_the_named_namespace(self):
		make_case("CM-TEST-W1")
		other = records.new("Contract Case", contract_id="CM-TEST-W2", source_kind="External record", fixture_namespace="CM_TEST_OTHER")
		self.assertEqual(records.wipe(NS), 1)
		self.assertTrue(frappe.db.exists("Contract Case", other.name))
		self.assertEqual(records.wipe("CM_TEST_OTHER"), 1)
		with self.assertRaises(ValueError):
			records.wipe("")
