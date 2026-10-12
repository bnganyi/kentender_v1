# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Naming-series helper shared by the reference allocators (AUD-XC-130).

An allocator that keeps a never-reuse counter in Frappe's `tabSeries` first
raises the counter past the highest number already used, then asks
`make_autoname` for the next one. The raise used to be read, then insert or
update: under concurrency two requests both read "no row" and both inserted
(the second died on the primary key), and under REPEATABLE READ a plain read
could not see a counter another request had just committed. One atomic upsert
has neither problem: it takes the counter's row lock, waits for the request
that holds it, and never lowers the counter.

RG-21 — one lock order for every reference allocator. A locking read of a
reference that does not exist yet takes a gap lock (REPEATABLE READ). Two
creators of one table whose references fall in the same gap both hold it, and
each insert then waits for the other: MariaDB error 1213. So every allocator
first takes `allocation_lock(table)`, one row lock per table held to commit,
before it probes or counts; creators of one table never interleave, and the
gap locks of one are gone before the next probes. The order every allocator
follows: the case or parent row lock (Tender, Requisition, Budget versions...),
then `allocation_lock(table)`, then the probe, then the insert. Take the lock
of several tables in sorted name order (`allocation_lock_all`).
"""

from __future__ import annotations

import frappe

LOCK_WAIT_SECONDS = 10


class AllocationBusy(frappe.ValidationError):
	"""Another request holds the allocation lock and did not finish in time."""


def _busy(_table: str):
	raise AllocationBusy(frappe._("Reference generation is busy. Try again."))


def allocation_lock(table: str, *, busy=None) -> None:
	"""Take the table's allocation lock for the rest of this transaction.

	One `tabSeries` row per table, locked by an atomic upsert (an insert that finds the row takes
	its X lock directly, so two requests never deadlock on the mutex itself) and released by
	commit or rollback, so it cannot outlive the request or leak across a pooled connection.
	Calling it again in the same transaction is free. If another request holds it for longer than
	`LOCK_WAIT_SECONDS`, or the database picks this one as a deadlock victim, `busy(table)` is
	called (it must raise); the default raises `AllocationBusy`."""
	busy = busy or _busy
	key = f"kt:alloc:{table}"[:140]
	previous = frappe.db.sql("select @@session.innodb_lock_wait_timeout")[0][0]
	frappe.db.sql("set session innodb_lock_wait_timeout = %s", LOCK_WAIT_SECONDS)
	try:
		frappe.db.sql(
			"INSERT INTO `tabSeries` (`name`, `current`) VALUES (%s, 1) "
			"ON DUPLICATE KEY UPDATE `current` = `current` + 1",
			(key,),
		)
	except (frappe.QueryTimeoutError, frappe.QueryDeadlockError):
		busy(table)
	finally:
		frappe.db.sql("set session innodb_lock_wait_timeout = %s", int(previous))


def allocation_lock_all(*tables: str, busy=None) -> None:
	"""Take several tables' allocation locks in the one fixed order: sorted by name."""
	for table in sorted(set(tables)):
		allocation_lock(table, busy=busy)


def raise_series_to(prefix: str, minimum: int) -> None:
	"""Make the counter for `prefix` at least `minimum`, creating it if absent (RG-21: even at 0,
	so `make_autoname` finds the row and locks only that record; on an absent row it would read
	`for update`, take a gap lock and deadlock with another first allocation).
	MariaDB `ON DUPLICATE KEY UPDATE`; a counter already ahead is left alone."""
	minimum = max(int(minimum or 0), 0)
	frappe.db.sql(
		"INSERT INTO `tabSeries` (`name`, `current`) VALUES (%s, %s) "
		"ON DUPLICATE KEY UPDATE `current` = GREATEST(`current`, VALUES(`current`))",
		(prefix, minimum),
	)


def next_free_reference(doctype: str, field: str, prefix: str, highest_seen: int, width: int, *, busy=None) -> str:
	"""The next `{prefix}{number}` that is free as of the latest committed rows.

	For allocators that number from the highest reference in use (so a purged
	range is reused) and serialise on a named lock. MariaDB runs at REPEATABLE
	READ: a plain read after waiting for that lock returns the transaction's
	older snapshot, so a reference another request had just committed is
	invisible and a plain `max + 1` takes the same number (AUD-XC-130). The
	caller passes the highest number its own snapshot shows; this then probes
	each candidate with a locking read, which sees the committed row, and moves
	on while the candidate is taken. The probe of a candidate that is free takes
	a gap lock, so it runs only under the table's `allocation_lock` (RG-21).
	"""
	allocation_lock(doctype, busy=busy)
	number = int(highest_seen or 0) + 1
	while True:
		candidate = f"{prefix}{number:0{int(width)}d}"
		if not frappe.db.sql(f"select 1 from `tab{doctype}` where `{field}`=%s for update", (candidate,)):
			return candidate
		number += 1
