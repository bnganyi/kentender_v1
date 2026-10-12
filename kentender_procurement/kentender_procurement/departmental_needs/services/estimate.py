# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.17 §4.3, §4.9 — the Need's estimated total cost.

One exact positive decimal amount in the Budget currency of the Need's Fiscal
Year. The only Budget interaction is the read-only currency and precision
lookup in `kentender_procurement.services.budget_currency`; nothing is funded,
checked or reserved. Excess precision is rejected, never rounded.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from frappe.utils import cstr

from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.services.budget_currency import BudgetCurrencyUnavailable, CurrencyBasis, currency_basis

MAX_INTEGRAL_DIGITS = 18
_PLAIN = re.compile(r"-?\d+(\.\d+)?")


def _decimal(value) -> Decimal | None:
	if value is None or isinstance(value, bool):
		return None
	if isinstance(value, Decimal):
		return value
	if isinstance(value, int):
		return Decimal(value)
	if isinstance(value, float):
		# a stored Currency comes back as a float; repr() is the shortest round-tripping text
		return Decimal(repr(value))
	text = cstr(value).strip().replace(",", "")
	if not text:
		return None
	if not _PLAIN.fullmatch(text):
		# a plain decimal only: no exponent, sign other than a leading minus, or NaN/Infinity text
		raise InvalidOperation(text)
	try:
		return Decimal(text)
	except (InvalidOperation, ValueError):
		raise


def basis_for(fiscal_year: str) -> CurrencyBasis:
	try:
		return currency_basis(fiscal_year)
	except BudgetCurrencyUnavailable:
		fail(
			"NDS_ESTIMATE_CURRENCY_UNAVAILABLE",
			"We cannot check the currency for this financial year right now. Try again, or ask your KenTender administrator to check the budget setting.",
		)


def blank(value) -> bool:
	return value is None or cstr(value).strip() == ""


def validated(value, fiscal_year: str) -> Decimal | None:
	"""The estimate as an exact `Decimal`, or None when blank (presence is a
	submission rule, NDS-BR-022). A supplied value must be positive, finite,
	inside the supported size and within the Budget currency's decimal places."""
	if blank(value):
		return None
	try:
		amount = _decimal(value)
	except (InvalidOperation, ValueError):
		amount = None
	if amount is None or not amount.is_finite():
		fail("NDS_ESTIMATE_PRECISION_INVALID", "Enter the estimated cost as a plain decimal amount.")
	if amount <= 0:
		fail("NDS_ESTIMATE_PRECISION_INVALID", "Enter an amount greater than zero.")
	if amount.adjusted() >= MAX_INTEGRAL_DIGITS:
		fail("NDS_ESTIMATE_PRECISION_INVALID", "The estimated cost is larger than the supported size.")
	basis = basis_for(fiscal_year)
	quantum = Decimal(1).scaleb(-basis.precision)
	if amount != amount.quantize(quantum):
		fail(
			"NDS_ESTIMATE_PRECISION_INVALID",
			f"Enter an amount using at most {basis.precision} decimal places for {basis.currency}.",
		)
	return amount.quantize(quantum)


def wire_text(value) -> str | None:
	"""The estimate as an exact plain-decimal string (no float, no exponent, no
	trailing zeros), or None for a revision without one (NDS-BR-025)."""
	try:
		amount = _decimal(value)
	except (InvalidOperation, ValueError):
		return None
	if amount is None or amount == 0:
		return None
	return format(amount.normalize(), "f")


def display_fields(value, fiscal_year: str) -> dict[str, Any]:
	"""Projection for the screens: the exact amount, its currency and the label
	('KES 80,000,000'). A revision without an estimate shows a null amount; the
	currency is read only when there is something to label."""
	text = wire_text(value)
	if text is None:
		return {"estimated_total_cost": None, "estimated_total_cost_currency": "", "estimated_total_cost_label": ""}
	try:
		basis = currency_basis(fiscal_year)
		currency, precision = basis.currency, basis.precision
	except BudgetCurrencyUnavailable:
		return {"estimated_total_cost": text, "estimated_total_cost_currency": "", "estimated_total_cost_label": text}
	amount = Decimal(text)
	label = f"{currency} {amount:,.{precision}f}"
	if precision and label.endswith("0" * precision) and amount == amount.to_integral_value():
		label = f"{currency} {amount:,.0f}"
	return {"estimated_total_cost": text, "estimated_total_cost_currency": currency, "estimated_total_cost_label": label}


def currency_of(fiscal_year: str) -> str:
	"""The Budget currency to label the estimate field with, or "" when it cannot
	be read. A display aid only: saving and submitting still go through
	`validated`, which refuses when the currency is unavailable."""
	if not fiscal_year:
		return ""
	try:
		return currency_basis(fiscal_year).currency
	except BudgetCurrencyUnavailable:
		return ""
