# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A command on its own database connection and thread, for tests that must
prove behaviour under real concurrency (MariaDB REPEATABLE READ): the
competing commands do not share a transaction, so a stale snapshot, a missing
lock or a racing journal insert shows up as it does in production.

Fixtures the other connection must see have to be committed first, and the
test must purge them afterwards. See `kentender_budget`'s
`test_budget_locking_races.py` for the two shapes used here:

* snapshot race — `snapshot_first=True`: B opens its snapshot, A commits, then
  B runs (`start_gate`). Only a locking read after B's lock sees A's effect.
* lock-wait race — `hold=True`: A holds its uncommitted effect while B starts;
  B must block until `commit()` and then decide from A's committed state.
"""

from __future__ import annotations

import threading
from typing import Callable

import frappe

WAIT = 30
BLOCKED_FOR = 1.5


class Conn:
	def __init__(self, user: str, fn: Callable, *, hold: bool = False, snapshot_first: bool = False, setup: Callable | None = None):
		self.user, self.fn, self.hold, self.snapshot_first, self.setup = user, fn, hold, snapshot_first, setup
		self.site, self.sites_path = frappe.local.site, frappe.local.sites_path
		self.value = self.error = None
		self.snapshot_open = threading.Event()
		self.start_gate = threading.Event()
		self.ran = threading.Event()
		self.commit_gate = threading.Event()
		self.finished = threading.Event()
		if not snapshot_first:
			self.start_gate.set()
		self.thread = threading.Thread(target=self._run, daemon=True)
		self.thread.start()

	def _run(self):
		try:
			frappe.init(site=self.site, sites_path=self.sites_path)
			frappe.connect()
			frappe.set_user(self.user)
			if self.setup:
				self.setup()  # thread-local flags (fixture namespace, injected clock)
			if self.snapshot_first:
				frappe.db.sql("select count(*) from `tabUser`")
				self.snapshot_open.set()
				self.start_gate.wait(WAIT)
			try:
				self.value = self.fn()
			except BaseException as exc:  # noqa: BLE001 - handed to the test thread
				self.error = exc
			self.ran.set()
			if self.hold:
				self.commit_gate.wait(WAIT)
			if self.error:
				frappe.db.rollback()
			else:
				frappe.db.commit()
		finally:
			try:
				frappe.db.close()
			except Exception:  # noqa: BLE001
				pass
			self.finished.set()

	def commit(self):
		self.commit_gate.set()
		assert self.finished.wait(WAIT), "connection did not finish"
