# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD v1.12 §8.2A step 2 / BUD-BR-013 / BUD-BR-021 — the one lock order every
Budget path that creates or changes a funding position, or decides on a
Budget Version, takes.

Why this module exists (AUD-XC-101..104): MariaDB runs at REPEATABLE READ. A
plain SELECT reads the snapshot taken at the transaction's first consistent
read; `SELECT ... FOR UPDATE` reads the latest committed row. A path that took
a lock and then computed availability from plain reads re-read a position that
a competing transaction had already changed and committed, and reserve locked
Budget Line rows while approve/close locked Version rows, so the lock sets
never conflicted.

The rules, in one place:

1. Lock order is fixed: every Procurement Budget Version row of each affected
   Budget (Budgets in name order, Versions in name order), then each affected
   Procurement Budget Line row in name order, then the Funding Reservation or
   Procurement Commitment row being changed. Reserve, adjust, convert, release,
   approve, close, successor creation and the Finance decision's basis check
   all call `lock_budgets_of_lines` / `lock_budget` first.
2. After the lock, every read that decides the outcome (Active Version, the
   Line Version, status, reserved/committed sums, existing reservations) is a
   locking read, so it sees what the previous lock holder committed.
"""

from __future__ import annotations

from typing import Iterable

import frappe


def lock_budget(budget: str, *, lines: bool = True) -> None:
	"""Lock the Budget's Version rows, then (by default) all of its Budget
	Line rows — the whole Budget's guard for approve, close, successor creation
	and decision-time validation."""
	lock_budgets([budget])
	if lines:
		frappe.db.sql(
			"select name from `tabProcurement Budget Line` where budget = %s order by name for update",
			(budget,),
		)


def lock_budgets(budgets: Iterable[str]) -> None:
	for budget in sorted({b for b in budgets if b}):
		frappe.db.sql(
			"select name from `tabProcurement Budget Version` where budget = %s order by name for update",
			(budget,),
		)


def lock_budgets_of_lines(budget_lines: Iterable[str]) -> list[str]:
	"""Version rows of every Budget the lines belong to, then the line rows,
	each in name order. Returns the sorted line names that were locked."""
	names = sorted({n for n in budget_lines if n})
	if not names:
		return []
	budgets = {
		row[0]
		for row in frappe.db.sql(
			"select distinct budget from `tabProcurement Budget Line` where name in %s", (tuple(names),)
		)
	}
	lock_budgets(budgets)
	frappe.db.sql(
		"select name from `tabProcurement Budget Line` where name in %s order by name for update",
		(tuple(names),),
	)
	return names


def locked_doc(doctype: str, name: str):
	"""The document as last committed, with its row locked (a plain `reload`
	would return the transaction's snapshot)."""
	return frappe.get_doc(doctype, name, for_update=True)


def locked_value(doctype: str, filters, fieldname):
	"""`frappe.db.get_value` as a locking read."""
	return frappe.db.get_value(doctype, filters, fieldname, for_update=True)
