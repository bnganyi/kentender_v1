# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Planning's one live integration point into Budget & Funding
for reservation release on Plan Item removal (`plan_item_finance.py`).

BUD-CHG-001 v1.2 §12.6: Planning's Finance confirmation flow calls
`check_funding`/`reserve_funding` directly (`api/budget_api.py`), not through
this module. This file's only remaining, genuinely-called function is
`release_reservation`, kept as a thin translating pass-through — Planning
supplies a simple `(reservation_id, reason)` pair; Budget's own
`release_reservation` contract needs a fuller downstream-event shape
(§9.1). Every other function this module used to expose
(`create_reservation`, `check_available_budget`, `get_budget_line_context`,
...) had no live caller and reimplemented logic that now belongs solely to
`budget_commitment_contracts.py` / `budget_check_reserve_contracts.py` —
removed outright, not preserved as dead parallel logic.
"""

from __future__ import annotations

import frappe


@frappe.whitelist()
def release_reservation(reservation_id: str | None = None, reason: str | None = None):
	from kentender_budget.services.budget_commitment_contracts import release_reservation as _release

	reservation_id = (reservation_id or "").strip()
	if not reservation_id:
		return {"ok": False, "message": "Reservation is required"}

	result = _release(
		reservation=reservation_id,
		amount=None,
		downstream_event_id=(reason or "").strip() or "Procurement Planning",
		downstream_event_type="Procurement Planning",
		idempotency_key=f"planning-release:{reservation_id}",
	)
	return {"ok": True, "skipped": False, "data": result, "message": ""}
