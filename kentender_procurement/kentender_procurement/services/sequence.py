# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Per-record sequence numbers read from the latest committed rows (RG-19, AUD-XC-130).

A command that numbers a child record of a case (`APT-02`, a version, a run) first
takes the case's row lock and then asks how many already exist. MariaDB runs at
REPEATABLE READ: a plain `count()` after waiting for that lock still answers from
the transaction's older snapshot, so a record the previous command committed while
this one waited is invisible and both commands take the same number. The second
one then dies on a duplicate-name or unique-field error.

A locking read (`for update`) is a current read: it sees what the waited-for
command committed. Use these helpers for every `count + 1` and `max + 1` taken
under a case lock; `test_sequence_sweep` fails on a plain one in the case modules.
Each helper first takes the table's allocation lock (RG-21), after the case lock.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_core.utils.series import allocation_lock


def locked_names(doctype: str, filters: dict[str, Any]) -> list[str]:
	"""The names of the matching rows as last committed, locked for this transaction."""
	allocation_lock(doctype)  # RG-21: one lock order for every allocator (see `kentender_core.utils.series`)
	return frappe.db.get_values(doctype, filters, "name", pluck="name", for_update=True) or []


def next_count(doctype: str, filters: dict[str, Any]) -> int:
	"""How many rows match, plus one, as of the latest committed state."""
	return len(locked_names(doctype, filters)) + 1


def next_after(doctype: str, filters: dict[str, Any], field: str) -> int:
	"""The highest `field` among the matching rows, plus one, as of the latest committed state."""
	allocation_lock(doctype)
	values = frappe.db.get_values(doctype, filters, field, pluck=field, for_update=True) or []
	return (max((cint(v) for v in values), default=0)) + 1
