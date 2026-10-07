# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-130 — a reference allocator that seeds its never-reuse counter past
the highest number in use does it atomically: two requests allocating at once
on a prefix with no counter yet both succeed and take different numbers.

REAL two-connection test (each request on its own MariaDB connection and
transaction); the counter rows are committed and purged afterwards.

    bench --site kentender-test.local run-tests --app kentender_core \
        --module kentender_core.tests.test_series_race
"""

from __future__ import annotations

import threading

import frappe
from frappe.model.naming import make_autoname
from frappe.tests import IntegrationTestCase

from kentender_budget.services.budget_reference import _sync_series
from kentender_core.utils.series import raise_series_to

PREFIX = "ZZRACE-REF-"
_WAIT = 30
_BLOCKED_FOR = 1.5


def _allocate(highest_in_use: int) -> str:
	"""What Budget's allocators do: seed the counter past the highest number in
	use, then take the next one."""
	_sync_series(PREFIX, highest_in_use)
	return make_autoname(f"{PREFIX}.####")


class _Conn:
	def __init__(self, fn, *, hold=False):
		self.fn, self.hold = fn, hold
		self.site, self.sites_path = frappe.local.site, frappe.local.sites_path
		self.value = self.error = None
		self.ran, self.commit_gate, self.finished = threading.Event(), threading.Event(), threading.Event()
		threading.Thread(target=self._run, daemon=True).start()

	def _run(self):
		try:
			frappe.init(site=self.site, sites_path=self.sites_path)
			frappe.connect()
			frappe.set_user("Administrator")
			try:
				self.value = self.fn()
			except BaseException as exc:  # noqa: BLE001 - handed to the test thread
				self.error = exc
			self.ran.set()
			if self.hold:
				self.commit_gate.wait(_WAIT)
			frappe.db.rollback() if self.error else frappe.db.commit()
		finally:
			try:
				frappe.db.close()
			except Exception:  # noqa: BLE001
				pass
			self.finished.set()

	def commit(self):
		self.commit_gate.set()
		assert self.finished.wait(_WAIT)


def _purge():
	frappe.db.sql("delete from `tabSeries` where `name` = %s", (PREFIX,))
	frappe.db.commit()


class TestSeriesRace(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		_purge()
		cls.addClassCleanup(_purge)

	def setUp(self):
		_purge()

	def test_two_allocators_on_a_prefix_with_no_counter_take_different_numbers(self):
		conn_a = _Conn(lambda: _allocate(7), hold=True)
		self.assertTrue(conn_a.ran.wait(_WAIT))
		self.assertIsNone(conn_a.error, repr(conn_a.error))
		conn_b = _Conn(lambda: _allocate(7))
		self.assertFalse(conn_b.finished.wait(_BLOCKED_FOR), "the second allocator must wait for the first")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(_WAIT))
		self.assertIsNone(conn_b.error, repr(conn_b.error))
		self.assertEqual(sorted([conn_a.value, conn_b.value]), [f"{PREFIX}0008", f"{PREFIX}0009"])

	def test_the_counter_is_never_lowered(self):
		raise_series_to(PREFIX, 12)
		raise_series_to(PREFIX, 3)
		self.assertEqual(make_autoname(f"{PREFIX}.####"), f"{PREFIX}0013")

	def test_a_prefix_with_nothing_in_use_still_gets_its_counter_row(self):
		"""RG-21: without the row, make_autoname reads an absent key `for update` (a gap lock) and two first
		allocations of different prefixes deadlock on their inserts."""
		frappe.db.delete("Series", {"name": PREFIX})
		raise_series_to(PREFIX, 0)
		self.assertEqual(frappe.db.sql("select `current` from `tabSeries` where `name`=%s", (PREFIX,)), ((0,),))
		self.assertEqual(make_autoname(f"{PREFIX}.####"), f"{PREFIX}0001")
