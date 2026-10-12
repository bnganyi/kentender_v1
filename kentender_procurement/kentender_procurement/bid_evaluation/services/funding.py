# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Funding beside the comparison (EVL-CHG-001 v0.4 §4.4; plan D9, C11;
boards D03-FUNDING, D07-FUNDING).

Funding is separate from evaluation: an authoritative budget comparison can
report a shortfall, but it cannot make a responsive bid fail, alter the
ranking or cause cancellation. The report names the highest-ranked
responsive bid and the funding issue; it authorises no expenditure. The
available amount is the remaining amount of the Tender's own budget
reservations, read through Budget's published funding read
(`kentender_budget.services.budget_funding_read`), which does not depend on
the session user's Budget roles. When that read is unavailable the report
carries a typed Unavailable funding fact and a qualification; nothing is
guessed and the absence is never silent (AUD-EVL-014)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import clock


UNAVAILABLE = "Unavailable"
UNAVAILABLE_QUALIFICATION = "Funding could not be confirmed: Budget's reservation read was unavailable. Confirm the funding before award."


def _unavailable(reason: str) -> dict[str, Any]:
	return {"status": UNAVAILABLE, "available": None, "reservations": [], "as_at": clock.now(), "source": "Budget confirmation", "reason": reason}


def available(tender: str) -> dict[str, Any] | None:
	"""The remaining amount of the Tender's reservations, read through Budget's published
	funding read (not as the session user). A read that cannot be completed is returned as a
	typed `Unavailable` fact, never as an absent one (AUD-EVL-014)."""
	from kentender_procurement.tenders.services import evaluation_seam as tenders

	reservations = tenders.funding_reservations(tender)["reservation_ids"]
	if not reservations:
		return None
	try:
		from kentender_budget.services.budget_funding_read import read_reservation_funding

		read = read_reservation_funding(reservations)
	except Exception:
		frappe.log_error(title="Bid Evaluation funding read unavailable")
		return _unavailable("Budget did not answer.")
	if not read["known"]:
		return _unavailable("Budget could not confirm every reservation of this tender.")
	total = sum((Decimal(cstr(row.get("remaining_amount") or 0)) for row in read["rows"]), Decimal("0"))
	return {"available": total.quantize(Decimal("0.01")), "reservations": [cstr(row.get("code")) for row in read["rows"]], "as_at": clock.now(),
		"source": "Budget confirmation"}


def compare(tender: str, evaluated_total: Decimal | None) -> dict[str, Any] | None:
	"""Available funding and any shortfall against the recommended evaluated total."""
	if evaluated_total is None:
		return None
	funds = available(tender)
	if funds is None:
		return None
	if funds.get("status") == UNAVAILABLE:
		return {**funds, "shortfall": None, "qualification": UNAVAILABLE_QUALIFICATION}
	shortfall = evaluated_total - funds["available"]
	return {**funds, "shortfall": shortfall.quantize(Decimal("0.01")) if shortfall > 0 else Decimal("0.00"), "qualification":
		"Funding needs resolution before award." if shortfall > 0 else ""}
