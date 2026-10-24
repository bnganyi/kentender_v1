# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening as a consumer of the existing `TenderCancelled` event (TPR-CHG-001 v0.24 §7.6; BOP-CHG-001 v0.16 §7.2 ConsumeTenderCancellation /
CloseCancelledOpening; PRC-CHG-001 v0.14 §7.2). Registered under `kt_tender_cancellation_consumers`, so Tenders tracks and retries its delivery from the
same event.

`deliver` believes only an authoritative cancellation: the reference it is given must be the one the Tender itself carries, committed — never the event
alone, never a caller's assertion. Then, once and under any number of deliveries:

- before Start the case ends Not held, with the cancellation (`not_held.consume_tender_cancellation`);
- a case already Not held keeps that fact and gains the cancellation (`not_held.attach_tender_cancellation`);
- after Start the partial session closes, Cancelled after start (`cancellation.close_cancelled_opening`);
- a case with no opening yet, or an opening already complete, has nothing to close.

The receipt names the terminal state reached. The Accounting Officer's open item clears inside the same committed closure and nowhere else. A failure raises
and Tenders keeps the delivery row for retry; ceremony commands are already refused (`records.refuse_if_cancelled`) whatever this does."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

NAME = "bid-opening"
LABEL = "Bid Opening"


class NotAnAuthoritativeCancellation(Exception):
	pass


def available() -> dict[str, Any]:
	"""Bid Opening can take a cancellation whenever its records are installed; a test environment can take it down to exercise the blocked route."""
	from kentender_procurement.bid_opening.services import simulation

	if simulation.controls()["cancellation_integration_down"]:
		return {"available": False, "reason": "The opening records are not available."}
	return {"available": True, "reason": ""}


def deliver(*, tender: str, cancellation: str, event_id: str, payload: dict[str, Any]) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import cancellation as after_start
	from kentender_procurement.bid_opening.services import not_held, records
	from kentender_procurement.tenders.services import opening_seam

	reference = cstr(cancellation).strip()
	authoritative = opening_seam.authoritative_cancellation(tender)
	if not reference or authoritative is None or cstr(authoritative["reference"]) != reference:
		raise NotAnAuthoritativeCancellation(f"{reference or 'No reference'} is not the committed cancellation of this Tender.")
	name = records.case_for(tender)
	if not name:
		return {"receipt": f"no-opening-case:{reference}"}
	state = cstr(frappe.db.get_value(records.CASE, name, "state"))
	if state in not_held.NOT_STARTED:
		not_held.consume_tender_cancellation(tender=tender)
	elif state == "Not held":
		not_held.attach_tender_cancellation(tender=tender)
	elif state in after_start.STARTED:
		after_start.close_cancelled_opening(tender=tender, cancellation_reference=reference, source_at=authoritative["cancelled_at"])
	return {"receipt": f"{cstr(frappe.db.get_value(records.CASE, name, 'state'))}:{reference}"}
