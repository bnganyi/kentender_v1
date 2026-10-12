# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The one command-write family of the Budget app (AUD-XC-006, AUD-XC-013).

Every Budget, Budget Version, Budget Line, Line Version, Funding Reservation,
Commitment, ledger event, submission attempt and revision request record
changes only inside `budget_write()`, opened by the Budget services around the
statements that write them; a Desk form, `/api/resource` or `frappe.client`
write is refused by the doctype controllers
(`kentender_core.services.command_write_guard`). Test and seed clean-up that
must write a record directly uses `maintenance_write(BUDGET_WRITE_FAMILY, ...)`
or `purge_doc` / `fixture_insert`.
"""

from __future__ import annotations

from kentender_core.services.command_write_guard import command_write

BUDGET_WRITE_FAMILY = "Budget"


def budget_write():
	"""Open the Budget write window (a context manager). Used only by the
	Budget services, after the command has checked permission, as narrowly as
	the writes it authorises."""
	return command_write(BUDGET_WRITE_FAMILY)
