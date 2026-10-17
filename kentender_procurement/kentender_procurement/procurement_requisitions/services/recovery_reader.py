# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.20 §10.3 — the read Budget uses (through `kentender_core.services.cancellation_recovery_contract`, because Budget sits
upstream of Requisitions) to show that a held reservation's Tender was cancelled and where its recovery stands. It returns only the status,
its label and explanation (Budget's own words, BUD-CHG-001 v1.17 §8.9) and the owner's reason, for reservations whose recovery is not complete;
no department rows and no totals, so it reveals nothing the Budget reader could not already see."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.services import cancellation_recovery, recovery_view


class Reader:
	def for_reservations(self, reservations: list[str]) -> dict[str, dict[str, Any]]:
		names = [cstr(r) for r in reservations if cstr(r)]
		if not names:
			return {}
		rows = frappe.db.sql(
			f"select s.reservation_id, p.name as recovery, p.status, p.reason_detail from `tabCancellation Recovery Source` s join `tab{cancellation_recovery.DOCTYPE}` p on p.name = s.parent "
			"where s.parenttype = %s and s.reservation_id in %s and p.status != %s",
			(cancellation_recovery.DOCTYPE, tuple(names), cancellation_recovery.COMPLETED), as_dict=True,
		)
		out = {}
		for row in rows:
			label, explanation = recovery_view.COPY["Budget"][row.status]
			out[row.reservation_id] = {"status": row.status, "label": label, "explanation": explanation, "reason": cstr(row.reason_detail), "recovery": row.recovery}
		return out


def reader() -> Reader:
	return Reader()
