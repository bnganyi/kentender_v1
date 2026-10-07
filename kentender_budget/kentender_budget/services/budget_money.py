# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD v1.12 §4.8 (AUD-XC-116, AUD-XC-117, AUD-XC-133) — Budget's one exact
money boundary and currency basis.

The rule being implemented: "at least 18 integral digits plus supported
fractional digits; exact decimal addition/subtraction/comparison throughout
persistence, services, fixtures and owner boundaries; no `flt()`, epsilon
equality or silent rounding. Overflow fails before mutation" and "Missing or
unsupported precision blocks monetary writes and positive decisions; it is
not defaulted."

* Inputs cross the boundary through `parse_money`: a decimal string, an int or
  a `Decimal` at the currency's scale. A JSON number (a float) is accepted only
  when its shortest text is a plain decimal of at most 15 significant digits
  (so the browser editor's typed `1250000.5` keeps its meaning); NaN/Infinity,
  exponent notation, excess scale, overflow, bool and blank are refused with
  `BUDGET_MONEY_PRECISION_INVALID` and nothing is rounded.
* Stored `Currency` values (decimal(21,9), read back as float by Frappe) enter
  arithmetic only through `stored`, and sums are read from the database as
  exact text (`cast(sum(..) as char)`), never as a float.
* Decisions (equality, floors, Needs Attention, availability) compare
  `Decimal`s exactly. `as_float` exists only for display read models.
* The scale comes from `currency_basis`, read from the native Currency record
  (`fraction_units`); a missing/disabled currency or a fraction that is not a
  power of ten raises `BUDGET_CURRENCY_PRECISION_UNSUPPORTED` instead of
  falling back to a constant.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

import frappe
from frappe import _

MAX_INTEGRAL_DIGITS = 18
# Frappe `Currency` is decimal(21,9) = 12 integral digits, and a stored value is
# read back as a binary float (AUD-XC-129). Until the owner chooses an exact
# storage type, an amount that the column cannot hold fails here, typed and
# before any write, instead of as a database error.
STORAGE_INTEGRAL_DIGITS = 12
MONEY_ERROR = "BUDGET_MONEY_PRECISION_INVALID"
CURRENCY_ERROR = "BUDGET_CURRENCY_PRECISION_UNSUPPORTED"
PRECISION_VERSION = "native-currency-1"
_MAX_FLOAT_SIGNIFICANT_DIGITS = 15
_PLAIN_DECIMAL = re.compile(r"^-?\d+(\.\d+)?$")


def currency_basis(currency: str | None) -> dict[str, Any]:
	"""CurrencyBasis (§4.8): `currency`, `fraction_digits`, `precision_version`,
	`source_metadata_reference`, read from the native Currency record."""
	name = (currency or "").strip()
	if not name:
		frappe.throw(_("A currency is required for a monetary write."), frappe.ValidationError, title=CURRENCY_ERROR)
	row = frappe.db.get_value("Currency", name, ["enabled", "fraction_units"], as_dict=True)
	if not row or not row.enabled:
		frappe.throw(_("Currency {0} is not an enabled currency on this site.").format(name), frappe.ValidationError, title=CURRENCY_ERROR)
	units = int(row.fraction_units or 0)
	digits_text = str(units)
	digits = len(digits_text) - 1 if digits_text.startswith("1") and set(digits_text[1:]) <= {"0"} else None
	if digits is None or digits > 6:
		frappe.throw(_("Currency {0} has no supported number of decimal places.").format(name), frappe.ValidationError, title=CURRENCY_ERROR)
	return {"currency": name, "fraction_digits": digits, "precision_version": PRECISION_VERSION, "source_metadata_reference": f"Currency:{name}"}


def scale_for(currency: str | None) -> int:
	return currency_basis(currency)["fraction_digits"]


def quantum(scale: int) -> Decimal:
	return Decimal(1).scaleb(-scale)


class MoneyInputError(ValueError):
	"""An amount that is not an exact amount at the currency's scale."""


def _refuse(value, message: str | None = None):
	raise MoneyInputError(message or _("Amount {0} is not an exact amount in currency units at the supported number of decimal places").format(repr(value)))


def _parse(value, scale: int, allow_zero: bool, allow_negative: bool) -> Decimal:
	if value is None or isinstance(value, bool):
		_refuse(value)
	if isinstance(value, Decimal):
		amount = value
	elif isinstance(value, int):
		amount = Decimal(value)
	elif isinstance(value, float):
		if value != value or value in (float("inf"), float("-inf")):
			_refuse(value)
		text_value = repr(value)
		if not _PLAIN_DECIMAL.match(text_value) or len(text_value.replace("-", "").replace(".", "").lstrip("0") or "0") > _MAX_FLOAT_SIGNIFICANT_DIGITS:
			_refuse(value)
		amount = Decimal(text_value)
	else:
		text_value = str(value).strip()
		if not _PLAIN_DECIMAL.match(text_value):
			_refuse(value)
		try:
			amount = Decimal(text_value)
		except InvalidOperation:
			_refuse(value)
	if not amount.is_finite():
		_refuse(value)
	q = quantum(scale)
	if amount != amount.quantize(q):
		_refuse(value)
	amount = amount.quantize(q)
	if len(str(int(abs(amount)))) > min(MAX_INTEGRAL_DIGITS, STORAGE_INTEGRAL_DIGITS):
		_refuse(value, _("Amount {0} is larger than the supported maximum").format(repr(value)))
	if amount < 0 and not allow_negative:
		_refuse(value, _("Amount {0} cannot be negative").format(repr(value)))
	if amount == 0 and not allow_zero and not allow_negative:
		_refuse(value, _("Amount must be greater than zero"))
	return amount


def parse_money(value, *, scale: int = 2, field: str | None = None, allow_zero: bool = False, allow_negative: bool = False) -> Decimal:
	"""One exact amount, or `BUDGET_MONEY_PRECISION_INVALID` (nothing rounded)."""
	try:
		return _parse(value, scale, allow_zero, allow_negative)
	except MoneyInputError as exc:
		frappe.throw(str(exc), frappe.ValidationError, title=MONEY_ERROR)


def check_money(value, *, scale: int = 2, allow_zero: bool = False, allow_negative: bool = False) -> tuple[Decimal | None, str]:
	"""Non-throwing `parse_money` for a validator that collects every error:
	`(amount, "")` or `(None, message)`."""
	try:
		return _parse(value, scale, allow_zero, allow_negative), ""
	except MoneyInputError as exc:
		return None, str(exc)


def stored(value, *, scale: int = 2) -> Decimal:
	"""A value read back from `Currency` storage (float/Decimal/str/None) as an
	exact `Decimal`. Float noise is removed by taking the shortest text of the
	float (`repr`), and the result is normalised to the currency scale when
	that loses nothing; a stored value that really has more places than the
	scale (legacy data) keeps them, so it is never silently rounded."""
	if value is None or value == "":
		return Decimal(0).quantize(quantum(scale))
	if isinstance(value, Decimal):
		amount = value
	elif isinstance(value, float):
		amount = Decimal(repr(value))
	else:
		amount = Decimal(str(value))
	at_scale = amount.quantize(quantum(scale))
	return at_scale if at_scale == amount else amount


def as_float(amount: Decimal | None) -> float:
	"""Display read models only; never an input to a decision."""
	return float(amount) if amount is not None else 0.0


def text(amount: Decimal, *, scale: int = 2) -> str:
	return f"{amount.quantize(quantum(scale)):f}"
