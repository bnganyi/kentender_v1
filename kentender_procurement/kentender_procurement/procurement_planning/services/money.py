# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §4.1 Money / Quantity (plan D3) — the exact-decimal boundary.

Services compute in `Decimal`; the API accepts and returns decimal strings;
storage stays Frappe `Currency`/`Float`, which is why every value crossing the
boundary is normalised here. Excess precision is **rejected**, never rounded
(`PLN_MONEY_PRECISION_INVALID`). Currency precision is supplied by the caller
from the Budget currency contract (KES: 2 in the fixture); a missing or
unsupported precision blocks the write rather than guessing.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from kentender_procurement.procurement_planning.errors import fail

DEFAULT_MONEY_PRECISION = 2
DEFAULT_QUANTITY_PRECISION = 3
SUPPORTED_PRECISIONS = (0, 1, 2, 3, 4, 5, 6)
MAX_INTEGRAL_DIGITS = 18


def _to_decimal(value) -> Decimal | None:
	if value is None or value == "":
		return None
	if isinstance(value, Decimal):
		return value
	if isinstance(value, bool):
		return None
	if isinstance(value, int):
		return Decimal(value)
	if isinstance(value, float):
		# a stored Currency/Float comes back as float; repr() is the shortest
		# round-tripping text, so 0.1 stays 0.1 rather than 0.1000000000000000055…
		return Decimal(repr(value))
	try:
		return Decimal(str(value).strip().replace(",", ""))
	except (InvalidOperation, ValueError):
		return None


def parse_money(value, *, precision: int | None = DEFAULT_MONEY_PRECISION, field: str = "amount", allow_zero: bool = False, allow_blank: bool = False) -> Decimal | None:
	"""Exact positive decimal currency-unit value at the currency's precision."""
	if precision is None or precision not in SUPPORTED_PRECISIONS:
		fail("PLN_MONEY_PRECISION_INVALID", "The currency precision for this amount is not configured.", {"field": field, "precision": precision})
	amount = _to_decimal(value)
	if amount is None:
		if allow_blank and (value is None or value == ""):
			return None
		fail("PLN_MONEY_PRECISION_INVALID", detail={"field": field, "offered": "" if value is None else str(value)})
	if not amount.is_finite():
		fail("PLN_MONEY_PRECISION_INVALID", detail={"field": field, "offered": str(value)})
	quantum = Decimal(1).scaleb(-precision)
	if amount != amount.quantize(quantum):
		fail("PLN_MONEY_PRECISION_INVALID", detail={"field": field, "precision": precision, "offered": str(value)})
	amount = amount.quantize(quantum)
	if len(str(abs(amount.to_integral_value()))) > MAX_INTEGRAL_DIGITS:
		fail("PLN_MONEY_PRECISION_INVALID", "The amount exceeds the supported magnitude.", {"field": field, "offered": str(value)})
	if amount < 0 or (amount == 0 and not allow_zero):
		fail("PLN_MONEY_PRECISION_INVALID", "Enter a positive amount.", {"field": field, "offered": str(value)})
	return amount


def parse_quantity(value, *, precision: int = DEFAULT_QUANTITY_PRECISION, field: str = "quantity", allow_zero: bool = False) -> Decimal:
	"""Exact positive decimal quantity at the governed UOM precision (§4.1)."""
	quantity = _to_decimal(value)
	if quantity is None or not quantity.is_finite():
		fail("PLN_ENTRY_INCOMPLETE", "Enter the quantity as a decimal number.", {"field": field, "offered": "" if value is None else str(value)})
	quantum = Decimal(1).scaleb(-precision)
	if quantity != quantity.quantize(quantum):
		fail("PLN_ENTRY_INCOMPLETE", f"The quantity supports at most {precision} decimal places.", {"field": field, "precision": precision, "offered": str(value)})
	quantity = quantity.quantize(quantum)
	if quantity < 0 or (quantity == 0 and not allow_zero):
		fail("PLN_ENTRY_INCOMPLETE", "Enter a positive quantity.", {"field": field, "offered": str(value)})
	return quantity


def money_text(value, *, precision: int = DEFAULT_MONEY_PRECISION) -> str:
	"""Canonical decimal string for the API/JSON boundary (never a float)."""
	amount = _to_decimal(value)
	if amount is None:
		return ""
	return f"{amount.quantize(Decimal(1).scaleb(-precision)):f}"


def quantity_text(value, *, precision: int = DEFAULT_QUANTITY_PRECISION) -> str:
	quantity = _to_decimal(value)
	if quantity is None:
		return ""
	text = f"{quantity.quantize(Decimal(1).scaleb(-precision)):f}"
	return text.rstrip("0").rstrip(".") if "." in text else text


def sum_money(values, *, precision: int = DEFAULT_MONEY_PRECISION) -> Decimal:
	total = Decimal(0)
	for value in values:
		amount = _to_decimal(value)
		if amount is not None:
			total += amount
	return total.quantize(Decimal(1).scaleb(-precision))
