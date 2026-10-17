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

import frappe

from kentender_procurement.procurement_requisitions.services import authorise as authorise_service
from kentender_procurement.procurement_requisitions.services import cancellation_recovery as recovery_service
from kentender_procurement.procurement_requisitions.services import recovery_sweep
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import cancellation_world as world
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx
from kentender_procurement.procurement_requisitions.tests.test_cancellation_recovery_integration import WorldCase
from kentender_procurement.tenders.tests import fixtures as tnd_fx
from kentender_procurement.tenders.tests.test_open_period import OpenPeriodCase
from kentender_procurement.tests.two_connections import WAIT, Conn

#: Tender, Award case, Requisition root, handoff, recovery, Version; Budget; Planning — a table never appears after one below it.
RECOVERY_DOCTYPE = recovery_service.DOCTYPE
LOCK_ORDER = (
	"Tender", "Award Case", "Procurement Requisition", "Authorised Requisition Handoff", "Cancellation Resource Recovery", "Requisition Version",
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
