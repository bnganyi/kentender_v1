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
"""

from __future__ import annotations

import frappe


def raise_series_to(prefix: str, minimum: int) -> None:
	"""Make the counter for `prefix` at least `minimum`, creating it if absent.
	MariaDB `ON DUPLICATE KEY UPDATE`; a counter already ahead is left alone."""
	minimum = int(minimum or 0)
	if minimum <= 0:
		return
	frappe.db.sql(
		"INSERT INTO `tabSeries` (`name`, `current`) VALUES (%s, %s) "
		"ON DUPLICATE KEY UPDATE `current` = GREATEST(`current`, VALUES(`current`))",
		(prefix, minimum),
	)


def next_free_reference(doctype: str, field: str, prefix: str, highest_seen: int, width: int) -> str:
	"""The next `{prefix}{number}` that is free as of the latest committed rows.

	For allocators that number from the highest reference in use (so a purged
	range is reused) and serialise on a named lock. MariaDB runs at REPEATABLE
	READ: a plain read after waiting for that lock returns the transaction's
	older snapshot, so a reference another request had just committed is
	invisible and a plain `max + 1` takes the same number (AUD-XC-130). The
	caller passes the highest number its own snapshot shows; this then probes
	each candidate with a locking read, which sees the committed row, and moves
	on while the candidate is taken. A probe is a point lookup on an indexed
	field, so it never locks a range of unrelated rows.
	"""
	number = int(highest_seen or 0) + 1
	while True:
		candidate = f"{prefix}{number:0{int(width)}d}"
		if not frappe.db.sql(f"select 1 from `tab{doctype}` where `{field}`=%s for update", (candidate,)):
			return candidate
		number += 1
