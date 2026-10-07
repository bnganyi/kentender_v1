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
