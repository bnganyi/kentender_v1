# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whole-Tender cancellation recovery under concurrency and in lock order (REQ-CR-AC-005 and AC-007; the lock order the specifications
leave to 'a proven common transaction and lock order').

The global order is: Tender, Award case, Requisition root, its handoff, the recovery, Requisition Version, Budget Version rows, Budget
Line rows, Funding Reservations, Annual Plan Item, Annual Plan Version, Plan Item root, Planning's recovery holds, Source Allocations,
Drawdowns. `test_every_command_takes_its_locks_in_the_global_order` records the order each command really takes them in, and the
two-connection tests show the serialisation that order buys: a new Requisition's authorisation and the recovery of the cancelled one
never interleave."""

from __future__ import annotations

import re
from contextlib import contextmanager
from unittest.mock import patch
from uuid import uuid4

import frappe

from kentender_core.services import contract_reservation_authority as authority

from kentender_procurement.procurement_requisitions.services import authorise as authorise_service
from kentender_procurement.procurement_requisitions.services import cancellation_recovery as recovery_service
from kentender_procurement.procurement_requisitions.services import recovery_sweep
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import cancellation_world as world
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx
from kentender_procurement.procurement_requisitions.tests.test_cancellation_recovery_integration import WorldCase
from kentender_procurement.tenders.tests import fixtures as tnd_fx
from kentender_procurement.tenders.tests.test_open_period import OpenPeriodCase
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn

#: Tender, Award Tender Authority, Award case, Requisition root, handoff, recovery, Version; Budget; Planning — a table never appears after one below it.
RECOVERY_DOCTYPE = recovery_service.DOCTYPE
LOCK_ORDER = (
	"Tender", "Award Tender Authority", "Award Case", "Procurement Requisition", "Authorised Requisition Handoff", "Cancellation Resource Recovery", "Requisition Version",
	"Procurement Budget Version", "Procurement Budget Line", "Funding Reservation",
	"Annual Plan Item", "Annual Plan Version", "Plan Item", "Plan Cancellation Recovery Hold", "Plan Source Allocation", "Plan Drawdown Reference",
)
_RANK = {name: index for index, name in enumerate(LOCK_ORDER)}
_TABLE = re.compile(r"from\s+`tab([^`]+)`", re.IGNORECASE)


@contextmanager
def lock_log():
	"""Every `... FOR UPDATE` statement the code under test runs, as the table it locks, in order."""
	from frappe.database.database import Database

	seen: list[str] = []
	real = Database.sql

	def spy(self, query, *args, **kwargs):
		text = query if isinstance(query, str) else str(query)
		if "for update" in text.lower():
			match = _TABLE.search(text)
			if match:
				seen.append(match.group(1).strip())
		return real(self, query, *args, **kwargs)

	with patch.object(Database, "sql", spy):
		yield seen


def first_locks(seen: list[str]) -> list[str]:
	order: list[str] = []
	for table in seen:
		if table in _RANK and table not in order:
			order.append(table)
	return order


def in_global_order(seen: list[str]) -> bool:
	ranks = [_RANK[t] for t in first_locks(seen)]
	return ranks == sorted(ranks)


class TestLockOrderOfCancellation(OpenPeriodCase):
	"""A published, uncancelled Tender: the cancellation's own locks, in order, then rolled back."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.addClassCleanup(setattr, frappe.flags, "kt_tenders_clock", None)
		tnd_fx.wipe_all()
		cls.authorised = world.single_source_requisition()
		cls.tender = world.publish_tender(OpenPeriodCase("setUp"), cls.authorised)
		frappe.db.commit()

	def setUp(self):
		super(OpenPeriodCase, self).setUp()
		frappe.set_user("Administrator")

	def test_cancelling_takes_the_tender_then_the_requisition_then_planning_in_order(self):
		name = "cancel_order"
		frappe.db.savepoint(name)
		try:
			with lock_log() as seen:
				world.cancel_tender(self.tender)
			order = first_locks(seen)
			self.assertTrue(in_global_order(seen), order)
			for expected in ("Tender", "Procurement Requisition", "Authorised Requisition Handoff", "Plan Item"):
				self.assertIn(expected, order)
			self.assertLess(order.index("Tender"), order.index("Procurement Requisition"))
		finally:
			frappe.db.rollback(save_point=name)
		self.assertEqual(frappe.db.get_value("Tender", self.tender, "overall_status"), "Published — open")


class TestRecoveryAndANewRequisition(WorldCase):
	"""A second Requisition for the same Plan Item (30 units / KES 3m) is submitted before the first Tender is cancelled; the cancellation
	then holds the first Requisition's source, and the second waits for the recovery."""

	@classmethod
	def build_world(cls):
		cls.first = world.single_source_requisition()
		cls._item_id = cls.first["item_id"]
		return cls.first

	@classmethod
	def before_cancel(cls) -> None:
		# prepared after the first Tender consumed the handoff (which frees the Plan Item's open slot) and before it is cancelled
		cls.second = cls._submit_second()

	@classmethod
	def _submit_second(cls) -> str:
		requisition = req_fx.prepare(cls._item_id)["requisition"]
		req_fx.fill_request_information(requisition)
		line = req_fx.editor(requisition)["equipment"]["add_rows"][0]["drawdown_line_id"]
		req_fx.add_laptops(requisition, quantities={line: 30})
		req_fx.enter_estimates(requisition, values={line: "3000000.00"})
		req_fx.apply_standard_package(requisition)
		req_fx.send(requisition)
		req_fx.submit_as_hod(requisition)
		frappe.set_user("Administrator")
		return requisition

	@classmethod
	def snapshot(cls) -> dict:
		reservations = world.reservations_of(cls.authorised["requisition"])
		line = world.budget_line_of(reservations[0])
		return {"item": world.planning_remaining(cls._item_id), "line": line, "position": world.budget_position(line), "reservations": reservations}

	def authorise_second(self):
		return req_fx.authorise(self.second)

	def test_every_command_takes_its_locks_in_the_global_order(self):
		name = "recover_order"
		frappe.db.savepoint(name)
		try:
			with lock_log() as seen:
				outcome = recovery_sweep.run_one(self.recovery)
			self.assertEqual(outcome["status"], "Completed")
			order = first_locks(seen)
			self.assertTrue(in_global_order(seen), order)
			for expected in ("Procurement Requisition", "Authorised Requisition Handoff", "Cancellation Resource Recovery", "Funding Reservation", "Plan Item", "Plan Drawdown Reference"):
				self.assertIn(expected, order)
		finally:
			frappe.db.rollback(save_point=name)
		# and the order authorisation already takes is the same order, so the two can only queue, never cross
		frappe.db.savepoint(name)
		try:
			with lock_log() as seen:
				try:
					self.authorise_second()
				except ProcurementRequisitionsError:
					pass  # refused by the hold: it still took its locks in order up to the refusal
			self.assertTrue(in_global_order(seen), first_locks(seen))
		finally:
			frappe.db.rollback(save_point=name)

	def test_a_held_source_refuses_the_second_authorisation_and_names_why(self):
		with self.trial():
			with self.assertRaises(ProcurementRequisitionsError) as caught:
				self.authorise_second()
			self.assertEqual(caught.exception.code, "REQ_CANCELLATION_RECOVERY_PENDING")
			self.assertEqual(frappe.db.count("Funding Reservation", {"caller_reference": frappe.db.get_value("Procurement Requisition", self.second, "requisition_reference")}), 0)
			self.assertEqual(frappe.db.get_value("Procurement Requisition", self.second, "current_state"), "Submitted to Procurement")
			self.assertEqual(world.planning_remaining(self._item_id), self.sources_before["item"])

	def test_a_needs_attention_recovery_refuses_it_with_the_invalid_code(self):
		from kentender_procurement.tenders.services import award_seam

		with self.trial():
			with patch.object(award_seam, "downstream_disposition", return_value={"known": True, "notification_status": "Issued", "case": "AWC-1", "package_status": ""}):
				recovery_sweep.run_one(self.recovery)
			with self.assertRaises(ProcurementRequisitionsError) as caught:
				self.authorise_second()
			self.assertEqual(caught.exception.code, "REQ_CANCELLATION_RECOVERY_INVALID")

	def test_zz_the_recovery_holds_the_item_while_it_runs_and_the_authorisation_neither_passes_nor_is_lost(self):
		"""Two real connections. The recovery runs and holds its uncommitted effects, and with them the Plan Item locks every authorisation takes
		first. A second Requisition's authorisation started now is refused for the source being restored (never passed on a stale read), and
		the same authorisation, retried once the recovery has committed, succeeds against the restored, still-eligible allowance."""
		frappe.db.commit()
		recovery_conn = Conn("Administrator", lambda: recovery_sweep.run_one(self.recovery), hold=True)
		try:
			self.assertTrue(recovery_conn.ran.wait(WAIT))
			self.assertIsNone(recovery_conn.error, recovery_conn.error)
			self.assertEqual(recovery_conn.value["status"], "Completed")
			item_row = frappe.db.get_value("Plan Item", self._item_id, "name")
			with self.assertRaises(Exception) as locked:  # the Plan Item root is held by the recovery: an authorisation's guard would wait here
				frappe.db.sql("select name from `tabPlan Item` where name=%s for update nowait", item_row)
			self.assertIn("lock", str(locked.exception).lower())
			frappe.db.rollback()
			attempt = Conn(req_fx.HOPF, self.authorise_second)
			self.assertTrue(attempt.finished.wait(WAIT))
			self.assertIsInstance(attempt.error, ProcurementRequisitionsError)
			self.assertEqual(attempt.error.code, "REQ_CANCELLATION_RECOVERY_PENDING")
		finally:
			recovery_conn.commit()
		frappe.db.commit()  # a fresh snapshot of what the recovery committed
		self.assertEqual(frappe.db.get_value(RECOVERY_DOCTYPE, self.recovery, "status"), "Completed")
		self.authorise_second()
		frappe.db.commit()
		self.assertEqual(frappe.db.get_value("Procurement Requisition", self.second, "current_state"), "Authorised")
		self.assertEqual([float(x) for x in world.planning_remaining(self._item_id)], [70.0, 7_000_000.0])  # 100 restored, 30 drawn by the second
		position, before = world.budget_position(self.sources_before["line"]), self.sources_before["position"]
		self.assertEqual(float(position["reserved"]), 3_000_000.0)
		self.assertEqual(float(position["available"]), float(before["available"]) + 3_000_000.0)
		self.assertEqual(frappe.db.get_value("Funding Reservation", self.sources_before["reservations"][0], "status"), "Released")
		self.assertEqual(frappe.db.get_value("Tender", self.tender, "overall_status"), "Cancelled")


CONTRACT_PREFIX = "CTR-CR-"


def purge_conversions() -> dict[str, int]:
	"""Remove what the races' contract conversions left on the Budget Line: their commitments and every audit event that names the contract or
	one of those commitments. A conversion commits on its own connection, so no rollback undoes it, and a commitment left behind would sit on
	the shared Budget Line for every later run."""
	from kentender_core.services.command_write_guard import purge_doc

	frappe.set_user("Administrator")
	commitments = frappe.get_all("Procurement Commitment", filters={"contract": ["like", f"{CONTRACT_PREFIX}%"]}, pluck="name")
	events = set(frappe.get_all("Budget Audit Event", filters={"downstream_reference": ["like", f"{CONTRACT_PREFIX}%"]}, pluck="name"))
	events |= set(frappe.get_all("Budget Audit Event", filters={"commitment": ["in", commitments or ["-"]]}, pluck="name"))
	for name in commitments:
		purge_doc("Procurement Commitment", name)
	frappe.flags.allow_budget_audit_purge = True
	try:
		for name in sorted(events):
			purge_doc("Budget Audit Event", name)
	finally:
		frappe.flags.allow_budget_audit_purge = False
	frappe.db.commit()
	return {"commitments": len(commitments), "audit_events": len(events)}


class RaceWorld(WorldCase):
	"""One cancelled Tender whose single reservation a contract may convert while its recovery is being carried out (REQ-CR-AC-005 / PLN-CR-AC-005)."""

	@classmethod
	def tearDownClass(cls):
		try:
			purge_conversions()
		finally:
			super().tearDownClass()

	@classmethod
	def build_world(cls):
		return world.single_source_requisition()

	@classmethod
	def snapshot(cls) -> dict:
		reservations = world.reservations_of(cls.authorised["requisition"])
		line = world.budget_line_of(reservations[0])
		return {"item": world.planning_remaining(cls.authorised["item_id"]), "line": line, "position": world.budget_position(line), "reservations": reservations}

	def convert(self):
		"""A contract's conversion of the reservation, on whatever connection calls it (the lineage seam is stood in for: the subject is the race)."""
		from kentender_budget.services import budget_commitment_contracts as commit
		from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, service_caller

		reservation = self.sources_before["reservations"][0]
		contract = f"{CONTRACT_PREFIX}{uuid4().hex[:6]}"
		with authority.awarded(contract, reservation):
			return commit.convert_reservation(
				reservation, contract, 1_000_000, uuid4().hex, contract_event_id=f"{contract}:signed", contract_event_type="ContractSigned",
				caller=service_caller(PRINCIPAL_CONTRACT, reference=contract),
			)


class TestRecoveryAheadOfConversion(RaceWorld):
	def test_a_conversion_waiting_for_the_recovery_is_refused_on_the_released_reservation(self):
		"""The recovery holds its uncommitted release. A contract's conversion of the same reservation waits for the lock, then decides from what the
		recovery committed: the reservation is Released, so nothing converts and the released money funds no obligation."""
		frappe.db.commit()
		recovery_conn = Conn("Administrator", lambda: recovery_sweep.run_one(self.recovery), hold=True)
		try:
			self.assertTrue(recovery_conn.ran.wait(WAIT))
			self.assertIsNone(recovery_conn.error, recovery_conn.error)
			self.assertEqual(recovery_conn.value["status"], "Completed")
			attempt = Conn("Administrator", self.convert)
			self.assertFalse(attempt.finished.wait(BLOCKED_FOR), "the conversion must wait for the recovery's lock")
		finally:
			recovery_conn.commit()
		self.assertTrue(attempt.finished.wait(WAIT))
		self.assertIsNotNone(attempt.error, "a Released reservation cannot be converted")
		frappe.db.commit()
		reservation = self.sources_before["reservations"][0]
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "status"), "Released")
		self.assertEqual(frappe.db.get_value(RECOVERY_DOCTYPE, self.recovery, "status"), "Completed")
		self.assertEqual([float(x) for x in world.planning_remaining(self.authorised["item_id"])], [100.0, 10_000_000.0])


class TestConversionAheadOfRecovery(RaceWorld):
	def test_a_recovery_waiting_for_a_conversion_restores_nothing_and_says_why(self):
		"""The conversion holds its uncommitted effect. The recovery, which read the reservation as Active before the conversion committed, waits for
		the lock and re-checks what it pinned: the reservation has changed, so it releases nothing and restores nothing, and states the reason."""
		frappe.db.commit()
		conversion = Conn("Administrator", self.convert, hold=True)
		try:
			self.assertTrue(conversion.ran.wait(WAIT))
			self.assertIsNone(conversion.error, conversion.error)
			attempt = Conn("Administrator", lambda: recovery_sweep.run_one(self.recovery))
			self.assertFalse(attempt.finished.wait(BLOCKED_FOR), "the recovery must wait for the conversion's lock")
		finally:
			conversion.commit()
		self.assertTrue(attempt.finished.wait(WAIT))
		self.assertIsNone(attempt.error, attempt.error)
		self.assertEqual(attempt.value["status"], "Needs attention")  # the owner's refusal, with its own reason, never a guess
		self.assertTrue(attempt.value["reason"])
		frappe.db.commit()
		reservation = self.sources_before["reservations"][0]
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "status"), "Partially Converted")
		self.assertEqual(world.planning_remaining(self.authorised["item_id"]), self.sources_before["item"])  # nothing restored
		self.assertEqual(frappe.db.count("Plan Cancellation Recovery Hold", {"recovery_id": self.recovery, "state": "Active"}), 1)  # the source stays held
		self.assertEqual(frappe.db.get_value(RECOVERY_DOCTYPE, self.recovery, "status"), "Needs attention")


class TestTwoWorkersAtOnce(RaceWorld):
	def test_a_second_worker_neither_repeats_nor_adds_to_the_first_workers_effect(self):
		"""Two workers pick up the same recovery. The first holds its uncommitted effect; the second, asked to do the same recovery now, waits or is
		turned away, and once the first commits it finds the recorded outcome and does nothing: one reversal and one release, whoever ran first."""
		frappe.db.commit()
		first = Conn("Administrator", lambda: recovery_sweep.run_one(self.recovery), hold=True)
		try:
			self.assertTrue(first.ran.wait(WAIT))
			self.assertIsNone(first.error, first.error)
			self.assertEqual((first.value["status"], first.value["acted"]), ("Completed", True))
			second = Conn("Administrator", lambda: recovery_sweep.run_one(self.recovery))
		finally:
			first.commit()
		self.assertTrue(second.finished.wait(WAIT))
		self.assertIsNone(second.error, second.error)
		self.assertEqual((second.value["status"], second.value["acted"]), ("Completed", False))
		frappe.db.commit()
		cancellation = self.cancelled["cancellation"]
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"recovery_id": self.recovery, "drawdown_state": "Reversed"}), 1)
		self.assertEqual(frappe.db.count("Reservation Cancellation Release", {"cancellation_id": cancellation}), 1)
		self.assertEqual([float(x) for x in world.planning_remaining(self.authorised["item_id"])], [100.0, 10_000_000.0])
