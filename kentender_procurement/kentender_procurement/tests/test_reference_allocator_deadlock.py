# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-21 — the reference allocators do not deadlock under two connections.

An allocator probes each candidate reference with `select ... for update`. A
probe of a reference that does not exist yet takes a gap lock (MariaDB
REPEATABLE READ). Two creators whose prefixes differ — two Plan Items — probe
into the same gap, both hold it, and each insert then waits for the other:
error 1213, one request rolled back. Every allocator now takes one named
allocation lock per table, held to commit (`kentender_core.utils.series`),
so two creators of one table never interleave.

The tests run the real allocators on two real connections and interleave them
so that both have allocated before either inserts.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tests.two_connections import Conn, WAIT

ITEM_A, ITEM_B = "9001", "9002"


def _fiscal_year() -> str:
	return frappe.db.get_value("Fiscal Year", {}, "name", order_by="year_start_date asc")


def _pe() -> str:
	from kentender_procurement.procurement_requisitions.services import references

	return references.pe_code()


class TestAllocatorsDoNotDeadlock(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.fy = _fiscal_year()
		self.inserted: list[tuple[str, str, str]] = []
		frappe.db.commit()
		self.addCleanup(self.purge)

	def purge(self):
		frappe.db.rollback()
		for doctype, field, value in self.inserted:
			frappe.db.delete(doctype, {field: value})
		frappe.db.commit()

	def _race(self, doctype: str, field: str, allocate):
		"""Two connections allocate for two different Plan Items, meet, then insert."""
		gate = threading.Barrier(2)

		def run(item: str):
			def go():
				reference = allocate(item)
				try:
					gate.wait(2)  # both have allocated before either inserts; with a lock the second is still waiting
				except threading.BrokenBarrierError:
					pass
				frappe.db.sql(
					f"insert into `tab{doctype}` (`name`, `owner`, `modified_by`, `creation`, `modified`, `docstatus`, `idx`, `{field}`) "
					"values (%s, 'Administrator', 'Administrator', now(), now(), 0, 0, %s)",
					(f"RG21-{reference}", reference),
				)
				return reference

			return go

		first, second = Conn("Administrator", run(ITEM_A)), Conn("Administrator", run(ITEM_B))
		self.assertTrue(first.finished.wait(WAIT) and second.finished.wait(WAIT), "a connection hung")
		for conn in (first, second):
			if conn.value:
				self.inserted.append((doctype, field, conn.value))
		self.assertIsNone(first.error, f"first connection: {first.error!r}")
		self.assertIsNone(second.error, f"second connection: {second.error!r}")
		self.assertNotEqual(first.value, second.value)

	def test_requisition_references_for_two_plan_items(self):
		from kentender_procurement.procurement_requisitions.services import references

		self._race(
			"Procurement Requisition", "requisition_reference",
			lambda item: references.requisition_reference(fiscal_year=self.fy, plan_item_id_value=f"PPI-{_pe()}-2027-{item}"),
		)

	def test_tender_references_for_two_plan_items(self):
		from kentender_procurement.tenders.services import references

		self._race(
			"Tender", "tender_reference",
			lambda item: references.tender_reference(fiscal_year=self.fy, plan_item_id_value=f"PPI-{_pe()}-2027-{item}"),
		)

	def test_plan_source_allocation_ids_for_two_plan_items(self):
		from kentender_procurement.procurement_planning.services import references

		self._race(
			"Plan Source Allocation", "allocation_id",
			lambda item: references.allocation_id(f"PPI-{_pe()}-2027-{item}"),
		)

	def test_departmental_plan_references_for_two_units(self):
		from kentender_procurement.procurement_planning.services import references

		units = frappe.get_all("Organisation Unit", pluck="name", limit=2, order_by="name asc")
		self.assertEqual(len(units), 2, "the test site needs two Organisation Units")
		order = {ITEM_A: units[0], ITEM_B: units[1]}
		self._race("Departmental Plan", "dpp_reference", lambda item: references.dpp_reference(order[item], self.fy))

	def test_per_case_sequence_numbers_for_two_cases(self):
		"""The first record of two cases: both counts probe the same empty range of the case index."""
		from kentender_procurement.services import sequence

		gate = threading.Barrier(2)
		cases = {ITEM_A: "RG21-CASE-A", ITEM_B: "RG21-CASE-B"}
		self.inserted += [("Bid Receipt", "tender", case) for case in cases.values()]

		def run(item: str):
			def go():
				number = sequence.next_count("Bid Receipt", {"tender": cases[item]})
				try:
					gate.wait(2)
				except threading.BrokenBarrierError:
					pass
				frappe.db.sql(
					"insert into `tabBid Receipt` (`name`, `owner`, `modified_by`, `creation`, `modified`, `docstatus`, `idx`, `tender`) "
					"values (%s, 'Administrator', 'Administrator', now(), now(), 0, 0, %s)",
					(f"RG21-RCPT-{item}", cases[item]),
				)
				return number

			return go

		first, second = Conn("Administrator", run(ITEM_A)), Conn("Administrator", run(ITEM_B))
		self.assertTrue(first.finished.wait(WAIT) and second.finished.wait(WAIT), "a connection hung")
		self.assertIsNone(first.error, f"first connection: {first.error!r}")
		self.assertIsNone(second.error, f"second connection: {second.error!r}")


LOCK_ROW = "kt:alloc:{}"


def _lock_count(table: str) -> int:
	row = frappe.db.sql("select `current` from `tabSeries` where `name`=%s", (LOCK_ROW.format(table),))
	return int(row[0][0]) if row else 0


class TestOneLockOrderForEveryAllocator(IntegrationTestCase):
	"""Every allocator takes its table's allocation lock; none uses a prefix-named advisory lock."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.fy = _fiscal_year()
		self.addCleanup(frappe.db.rollback)

	def _takes_lock(self, table: str, allocate):
		before = _lock_count(table)
		allocate()
		self.assertGreater(_lock_count(table), before, f"the allocator did not take the {table} allocation lock")

	def test_every_allocator_takes_the_allocation_lock_of_its_table(self):
		from kentender_procurement.bid_submission.services import references as bid_refs
		from kentender_procurement.departmental_needs.services import lifecycle
		from kentender_procurement.procurement_planning.services import references as pln
		from kentender_procurement.procurement_requisitions.services import references as req
		from kentender_procurement.services import sequence
		from kentender_procurement.tenders.services import references as tnd

		pe, fy = _pe(), self.fy
		item = f"PPI-{pe}-2027-9100"
		unit = frappe.get_all("Organisation Unit", pluck="name", limit=1)[0]
		self._takes_lock("Procurement Requisition", lambda: req.requisition_reference(fiscal_year=fy, plan_item_id_value=item))
		self._takes_lock("Tender", lambda: tnd.tender_reference(fiscal_year=fy, plan_item_id_value=item))
		self._takes_lock("Departmental Need", lambda: lifecycle._next_reference(fy))
		self._takes_lock("Departmental Plan", lambda: pln.dpp_reference(unit, fy))
		self._takes_lock("Departmental Plan Entry", lambda: pln.entry_id("DPP-X-X-2027-001"))
		self._takes_lock("Annual Plan", lambda: pln.plan_reference(fy))
		self._takes_lock("Annual Plan Item", lambda: pln.plan_item_id(fy))
		self._takes_lock("Plan Source Allocation", lambda: pln.allocation_id(item))
		self._takes_lock("Plan Finance Task", lambda: pln.finance_task_reference("PLN-X-2027-9100"))
		self._takes_lock("Bid Receipt", lambda: sequence.next_count("Bid Receipt", {"tender": "RG21-NONE"}))
		self._takes_lock("Bid Receipt", lambda: sequence.next_after("Bid Receipt", {"tender": "RG21-NONE"}, "version_number"))
		self._takes_lock("Bid Receipt", lambda: bid_refs.receipt_reference("RG21-NONE", "TND-X-2027-1"))
		self._takes_lock("Bid Submission Attempt", lambda: bid_refs.correlation_id("RG21-NONE", "TND-X-2027-1"))
		self._takes_lock("Bidder Arrangement", lambda: bid_refs.next_number("RG21-NONE"))

	def test_no_module_takes_its_own_advisory_lock_for_numbering(self):
		offenders = []
		for app in ("kentender_core", "kentender_strategy", "kentender_budget", "kentender_procurement"):
			root = Path(frappe.get_app_path(app))
			for path in root.rglob("*.py"):
				if "tests" in path.parts or path.name == "series.py":
					continue
				for number, line in enumerate(path.read_text().splitlines(), 1):
					if re.search(r"get_lock\(|release_lock\(", line):
						offenders.append(f"{path.relative_to(root.parent)}:{number}")
		self.assertEqual(offenders, [], "use kentender_core.utils.series.allocation_lock, not a prefix-named lock released before commit")

	def test_the_lock_is_held_to_commit_and_a_second_request_waits_for_it(self):
		from kentender_core.utils import series

		holder = Conn("Administrator", lambda: series.allocation_lock("RG21 Table"), hold=True)
		self.assertTrue(holder.ran.wait(WAIT))
		waiter = Conn("Administrator", lambda: series.allocation_lock("RG21 Table"))
		self.assertFalse(waiter.finished.wait(1.5), "the second request must wait for the first to commit")
		holder.commit()
		self.assertTrue(waiter.finished.wait(WAIT))
		self.assertIsNone(waiter.error, repr(waiter.error))
		frappe.db.delete("Series", {"name": LOCK_ROW.format("RG21 Table")})
		frappe.db.commit()

	def test_a_request_that_waits_too_long_gets_the_callers_typed_error(self):
		from kentender_core.utils import series

		class Busy(Exception):
			pass

		def busy(table):
			raise Busy(table)

		holder = Conn("Administrator", lambda: series.allocation_lock("RG21 Table"), hold=True)
		self.assertTrue(holder.ran.wait(WAIT))
		original, series.LOCK_WAIT_SECONDS = series.LOCK_WAIT_SECONDS, 1
		try:
			waiter = Conn("Administrator", lambda: series.allocation_lock("RG21 Table", busy=busy))
			self.assertTrue(waiter.finished.wait(WAIT))
		finally:
			series.LOCK_WAIT_SECONDS = original
		holder.commit()
		self.assertIsInstance(waiter.error, Busy)
		frappe.db.delete("Series", {"name": LOCK_ROW.format("RG21 Table")})
		frappe.db.commit()

	def test_several_tables_are_locked_in_sorted_order(self):
		from kentender_core.utils import series

		taken = []
		original = series.allocation_lock
		series.allocation_lock = lambda table, busy=None: taken.append(table)
		try:
			series.allocation_lock_all("Tender", "Annual Plan", "Bid Receipt", "Tender")
		finally:
			series.allocation_lock = original
		self.assertEqual(taken, ["Annual Plan", "Bid Receipt", "Tender"])
