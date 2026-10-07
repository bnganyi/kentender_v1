# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget's published funding read for downstream modules that are not Budget
readers (Evaluation, Award; AUD-EVL-014).

`get_funding_lineage` authorises the *session user* against Budget's own read
roles, so a procurement officer who freezes an evaluation report, or whatever
account triggers a read, gets a permission error that the caller then has to
interpret. This read answers the one question those modules ask — how much of
the named reservations remains — as the Budget module itself, with no session
permission dependency. It is an in-process service call, never a web endpoint
(it is not whitelisted), moves no money and returns only each reservation's
code, status and amounts.

It never guesses: a reservation Budget cannot find is reported in `missing`
and `known` is False, so a caller fails closed instead of treating absence as
"not restricted"."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr


def read_reservation_funding(reservation_ids: list[str]) -> dict[str, Any]:
	"""{"known": bool, "rows": [{id, code, status, original_amount, remaining_amount}], "missing": [ids]}."""
	ids = [cstr(r).strip() for r in reservation_ids or [] if cstr(r).strip()]
	rows, missing = [], []
	for reservation in dict.fromkeys(ids):
		row = frappe.db.get_value("Funding Reservation", reservation, ["name", "generated_reference", "status", "original_amount", "remaining_amount"], as_dict=True)
		if not row:
			missing.append(reservation)
			continue
		rows.append({"id": row.name, "code": cstr(row.generated_reference), "status": cstr(row.status), "original_amount": row.original_amount,
			"remaining_amount": row.remaining_amount})
	return {"known": bool(ids) and not missing, "rows": rows, "missing": missing}
