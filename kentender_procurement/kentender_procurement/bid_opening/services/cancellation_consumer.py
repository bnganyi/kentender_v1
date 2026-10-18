# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening as a consumer of the existing `TenderCancelled` event (TPR-CHG-001 v0.24 §7.6; BOP-CHG-001 v0.16 §7.2 ConsumeTenderCancellation /
CloseCancelledOpening). Registered under `kt_tender_cancellation_consumers`, so Tenders tracks and retries its delivery from the same event.

`deliver` is idempotent on the cancellation: before Start it records the terminal Not held, after Start the terminal partial closure, each once;
a replay returns the first outcome. Its receipt names the terminal state the case reached."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

NAME = "bid-opening"
LABEL = "Bid Opening"


def available() -> dict[str, Any]:
	"""Bid Opening can take a cancellation whenever its records are installed; a test environment can take it down to exercise the blocked route."""
	return {"available": True, "reason": ""}


def deliver(*, tender: str, cancellation: str, event_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import cancellation as after_start
	from kentender_procurement.bid_opening.services import not_held, records

	name = records.case_for(tender)
	if not name:
		return {"receipt": f"no-opening-case:{cancellation}"}
	not_held.consume_tender_cancellation(tender=tender)
	after_start.close_cancelled_opening(tender=tender, cancellation_reference=cancellation)
	return {"receipt": f"{cstr(frappe.db.get_value(records.CASE, name, 'state'))}:{cancellation}"}
