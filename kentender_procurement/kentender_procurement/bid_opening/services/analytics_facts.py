# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1 — Bid Opening's facts for Procurement Analytics (plan Phase 2C; FU-ANL-06).

One function, `facts_for(*, user, tender_names, at)`, called by the Tenders Analytics provider. It only reads: no case is
prepared, swept or advanced, and the stage summary is not called. It does not decide the audience (the Tenders provider
does), and it gives every actor the same facts, technical readers included: `stage_summary` shows a technical reader status
only, which is why it is not reused. Per Tender with an opening case it returns exactly:

- `opening_complete_at`: `Bid Opening Case.completed_at`, only for a completed opening whose outcome is "Bids opened"
  (T4 start). An empty opening has no transition, so it has none.
- `outcome`: "Bids opened" or "No bids" once the opening is complete, otherwise None. Never "No bids" for an opening that
  is not final (`evaluation_seam.final_outcome`), and None for an opening that was not held or ended by cancellation.
- `status`: the owner's own status text (`stage_summary.STATUS`: "Awaiting deadline", "In session", "Paused", "Complete" ...).

No bid count, no sealed content and no bidder identity leave the module. A completed "Bids opened" opening with no
completion instant is inconsistent and raises. A failed read raises."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_opening.services import records
from kentender_procurement.bid_opening.services.stage_summary import STATUS

COMPLETE, OPENED, NO_BIDS = "Opening complete", "Bids opened", "No bids"


def facts_for(*, user: str, tender_names: list[str], at: datetime) -> dict[str, dict[str, Any]]:
	"""Opening facts keyed by Tender name; a Tender with no opening case is omitted."""
	names = list(dict.fromkeys(name for name in tender_names or [] if name))
	if not names:
		return {}
	out: dict[str, dict[str, Any]] = {}
	for case in frappe.get_all(records.CASE, filters={"tender": ("in", names)}, fields=["tender", "state", "outcome", "completed_at", "name"], order_by="creation asc"):
		out.setdefault(case.tender, _facts(case))
	return out


def _facts(case) -> dict[str, Any]:
	outcome = (OPENED if case.outcome == OPENED else NO_BIDS) if case.state == COMPLETE else None
	complete_at = None
	if outcome == OPENED:
		if not case.completed_at:
			raise ValueError(f"opening case {case.name} is complete with bids opened but records no completion instant")
		complete_at = get_datetime(case.completed_at)
	return {"opening_complete_at": complete_at, "outcome": outcome, "status": STATUS.get(case.state, cstr(case.state))}
