"""NDS-CHG-001 v1.16 §4.3 / §4.9 — the exact quantity rule (AUD-XC-118).

A quantity is an exact positive decimal, never rounded. Three limits apply and
a breach raises `NDS_QUANTITY_PRECISION_INVALID` naming the limit:

* a unit the native ERPNext `UOM` marks `must_be_whole_number` takes only whole
  quantities (the Each fixture rejects 1.5);
* at most `QUANTITY_DECIMALS` decimal places (the storage scale of the
  revision's quantity column; ERPNext's UOM carries no fractional-scale column,
  so this is the one supported scale until CFG publishes a per-unit one);
* at most `QUANTITY_INTEGRAL_DIGITS` integral digits (the storage range).

A value that is not an exact decimal (NaN, infinity, exponent text) fails the
same way. Positivity stays `NDS_FIELD_REQUIRED` (§4.3 required-ness).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import frappe

from kentender_procurement.departmental_needs.constants import QUANTITY_DECIMALS
from kentender_procurement.departmental_needs.errors import fail

# Frappe stores a Float as decimal(21,9): twelve integral digits remain.
QUANTITY_INTEGRAL_DIGITS = 12


def _exact(value) -> Decimal:
	if isinstance(value, bool):
		raise InvalidOperation
	if isinstance(value, float):
		# repr() is the shortest round-tripping text: 0.1 stays 0.1
		return Decimal(repr(value))
	if isinstance(value, Decimal):
		return value
	text = str(value).strip()
	if "e" in text.lower() or "," in text:
		raise InvalidOperation
	return Decimal(text)


def require_valid_quantity(value, unit: str | None = None) -> Decimal | None:
	"""Validate a supplied quantity against the unit; blank passes (presence is
	a submission rule). Returns the exact value."""
	if value in (None, ""):
		return None
	try:
		quantity = _exact(value)
	except (InvalidOperation, ValueError):
		fail("NDS_QUANTITY_PRECISION_INVALID", "Enter the quantity as a plain decimal number.")
	if not quantity.is_finite():
		fail("NDS_QUANTITY_PRECISION_INVALID", "Enter the quantity as a plain decimal number.")
	if quantity <= 0:
		fail("NDS_FIELD_REQUIRED", "Indicative quantity must be greater than zero.")
	if len(str(quantity.to_integral_value())) > QUANTITY_INTEGRAL_DIGITS:
		fail("NDS_QUANTITY_PRECISION_INVALID", f"The quantity can have at most {QUANTITY_INTEGRAL_DIGITS} digits before the decimal point.")
	if unit and frappe.db.get_value("UOM", unit, "must_be_whole_number"):
		if quantity != quantity.to_integral_value():
			fail("NDS_QUANTITY_PRECISION_INVALID", f"{unit} is counted in whole numbers; enter a quantity without decimals.")
	if quantity != quantity.quantize(Decimal(1).scaleb(-QUANTITY_DECIMALS)):
		fail("NDS_QUANTITY_PRECISION_INVALID", f"The quantity can have at most {QUANTITY_DECIMALS} decimal places.")
	return quantity


def wire_text(value) -> str:
	"""The quantity as an exact plain-decimal string for a published contract
	(NDS v1.16 §4.9 "exact Quantity strings"): no float, no exponent, no
	trailing zeros, so 10 -> "10" and 1.5 -> "1.5". Blank stays blank."""
	if value in (None, ""):
		return ""
	return format(_exact(value).normalize(), "f")


def normalise_wire_payload(body: dict) -> dict:
	"""Replay-side companion of `wire_text`: events appended before the
	decimal-string cutover carry `indicative_quantity` as a JSON number. Every
	consumer-facing replay passes the stored body through here so a consumer
	sees one type, whatever era the event is from. The stored row (and the
	content hash, which is over the stored column) are untouched."""
	if not isinstance(body, dict):
		return body
	if "indicative_quantity" in body and not isinstance(body["indicative_quantity"], str):
		body = {**body, "indicative_quantity": wire_text(body["indicative_quantity"])}
	nested = body.get("successor_accepted_payload")
	if isinstance(nested, dict):
		body = {**body, "successor_accepted_payload": normalise_wire_payload(nested)}
	return body
