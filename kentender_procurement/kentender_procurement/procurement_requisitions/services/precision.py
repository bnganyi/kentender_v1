# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §5.14 — exact Money and Quantity.

Money is a plain decimal string in currency units at KES scale 2, with up to
18 integral digits (BUD v1.10 CurrencyBasis). Quantity for this product is a
positive whole number of `Each`. Both are stored as canonical strings and
computed as `Decimal`; nothing here rounds, uses an epsilon or accepts a
binary float. A malformed value fails with `REQ_MONEY_PRECISION_INVALID` /
`REQ_QUANTITY_PRECISION_INVALID`, naming the field.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from kentender_procurement.procurement_requisitions.services.errors import fail

MONEY_SCALE = 2
MAX_INTEGRAL_DIGITS = 18
CURRENCY = "KES"
UNIT = "Each"

_QUANTUM = Decimal(1).scaleb(-MONEY_SCALE)
_MONEY_TEXT = re.compile(r"^\d{1,%d}(\.\d{1,%d})?$" % (MAX_INTEGRAL_DIGITS, MONEY_SCALE))
_WHOLE_TEXT = re.compile(r"^\d{1,%d}$" % MAX_INTEGRAL_DIGITS)


def _money_failure(field: str, value) -> None:
	fail("REQ_MONEY_PRECISION_INVALID", f"{field} must be an exact amount in KES with at most 2 decimal places.", {"field": field, "offered": repr(value)})


def _quantity_failure(field: str, value) -> None:
	fail("REQ_QUANTITY_PRECISION_INVALID", f"{field} must be a whole number of Each.", {"field": field, "offered": repr(value)})


def parse_money(value, *, field: str = "amount", allow_zero: bool = False) -> Decimal:
	"""Exact KES amount. Accepts a decimal string, an int or a Decimal."""
	if isinstance(value, (bool, float)) or value is None:
		_money_failure(field, value)
	if isinstance(value, int):
		amount = Decimal(value)
	elif isinstance(value, Decimal):
		amount = value
	else:
		text = str(value).strip()
		if not _MONEY_TEXT.match(text):
			_money_failure(field, value)
		try:
			amount = Decimal(text)
		except InvalidOperation:
			_money_failure(field, value)
	if not amount.is_finite() or amount != amount.quantize(_QUANTUM) or len(str(int(abs(amount)))) > MAX_INTEGRAL_DIGITS:
		_money_failure(field, value)
	if amount < 0 or (amount == 0 and not allow_zero):
		_money_failure(field, value)
	return amount.quantize(_QUANTUM)


def parse_quantity(value, *, field: str = "quantity", allow_zero: bool = False) -> Decimal:
	"""Positive whole number of Each. Accepts a digit string, an int or an
	integral Decimal; a fractional or float value is refused."""
	if isinstance(value, (bool, float)) or value is None:
		_quantity_failure(field, value)
	if isinstance(value, int):
		quantity = Decimal(value)
	elif isinstance(value, Decimal):
		quantity = value
	else:
		text = str(value).strip()
		if not _WHOLE_TEXT.match(text):
			_quantity_failure(field, value)
		quantity = Decimal(text)
	if not quantity.is_finite() or quantity != quantity.to_integral_value():
		_quantity_failure(field, value)
	if quantity < 0 or (quantity == 0 and not allow_zero):
		_quantity_failure(field, value)
	return quantity.to_integral_value()


def stored_money(value) -> Decimal:
	"""A canonical money string read back from REQ's own storage."""
	return parse_money(value or "0", allow_zero=True)


def stored_quantity(value) -> Decimal:
	return parse_quantity(value or "0", allow_zero=True)


def planning_quantity(value) -> Decimal:
	"""Planning's exact quantity string (its own boundary may carry a
	decimal UOM). This product accepts only a whole number (§5.14)."""
	try:
		quantity = Decimal(str(value).strip())
	except (InvalidOperation, ValueError):
		_quantity_failure("approved quantity", value)
	if quantity != quantity.to_integral_value():
		_quantity_failure("approved quantity", value)
	return quantity.to_integral_value()


def money_text(amount) -> str:
	return f"{Decimal(amount).quantize(_QUANTUM):f}"


def quantity_text(quantity) -> str:
	return f"{Decimal(quantity).to_integral_value():f}"


def display_money(amount) -> str:
	"""`KES 50,000,000.00` — the §13 display form."""
	return f"{CURRENCY} {Decimal(amount).quantize(_QUANTUM):,.2f}"


def display_quantity(quantity) -> str:
	return f"{Decimal(quantity).to_integral_value():,f} {UNIT}"
