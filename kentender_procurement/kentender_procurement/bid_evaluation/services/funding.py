# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Funding beside the comparison (EVL-CHG-001 v0.4 §4.4; plan D9, C11;
boards D03-FUNDING, D07-FUNDING).

Funding is separate from evaluation: an authoritative budget comparison can
report a shortfall, but it cannot make a responsive bid fail, alter the
ranking or cause cancellation. The report names the highest-ranked
responsive bid and the funding issue; it authorises no expenditure. The
available amount is the remaining amount of the Tender's own budget
reservations, read through Budget's published lineage contract. When that
read is unavailable no funding fact is shown; nothing is guessed. A
published evaluation-funding contract is owed by Budget (FU-EVL-06)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import clock


def available(tender: str) -> dict[str, Any] | None:
	from kentender_procurement.tenders.services import evaluation_seam as tenders

	reservations = tenders.funding_reservations(tender)["reservation_ids"]
	if not reservations:
		return None
	try:
		from kentender_budget.services.budget_downstream_contracts import get_funding_lineage

		total = Decimal("0")
		codes = []
		for reservation in reservations:
			for row in get_funding_lineage(reservation=reservation).get("rows") or []:
				total += Decimal(cstr(row["reservation"].get("remaining_amount") or 0))
				codes.append(cstr(row["reservation"].get("code")))
	except Exception:
		frappe.log_error(title="Bid Evaluation funding read unavailable")
		return None
	return {"available": total.quantize(Decimal("0.01")), "reservations": codes, "as_at": clock.now(), "source": "Budget confirmation"}


def compare(tender: str, evaluated_total: Decimal | None) -> dict[str, Any] | None:
	"""Available funding and any shortfall against the recommended evaluated total."""
	if evaluated_total is None:
		return None
	funds = available(tender)
	if funds is None:
		return None
	shortfall = evaluated_total - funds["available"]
	return {**funds, "shortfall": shortfall.quantize(Decimal("0.01")) if shortfall > 0 else Decimal("0.00"), "qualification":
		"Funding needs resolution before award." if shortfall > 0 else ""}
