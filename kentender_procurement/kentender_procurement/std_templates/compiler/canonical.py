# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-IMP-001 v1.0 §7 — canonical JSON and value formats.

Canonical JSON is UTF-8, sorted object keys, no insignificant whitespace and
no floating-point values. Decimals travel as plain decimal strings
(`"50000000.00"`), dates as ISO `YYYY-MM-DD`, date-times as ISO 8601 with an
explicit offset. A float, `Decimal`, `date` or any other non-JSON type is
refused rather than coerced, so two producers can never serialise the same
fact differently. Pure Python: no Frappe import.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from kentender_procurement.std_templates.compiler.errors import fail

_DECIMAL = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class CanonicalError(ValueError):
	pass


def _check(value: Any, path: str) -> None:
	if value is None or isinstance(value, (str, bool)):
		return
	if isinstance(value, int):
		return
	if isinstance(value, float):
		raise CanonicalError(f"floating-point value at {path}; use a decimal string")
	if isinstance(value, list):
		for index, item in enumerate(value):
			_check(item, f"{path}[{index}]")
		return
	if isinstance(value, dict):
		for key, item in value.items():
			if not isinstance(key, str):
				raise CanonicalError(f"non-string key at {path}")
			_check(item, f"{path}.{key}")
		return
	raise CanonicalError(f"unsupported type {type(value).__name__} at {path}")


def canonical_json(value: Any) -> str:
	_check(value, "$")
	return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def canonical_bytes(value: Any) -> bytes:
	return canonical_json(value).encode("utf-8")


def sha256_hex(value: Any) -> str:
	return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_bytes(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pretty_json(value: Any) -> str:
	"""The on-disk form of a controlled JSON asset: canonical key order and
	values, indented for review, one trailing newline."""
	_check(value, "$")
	return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def is_sha256(value: Any) -> bool:
	return isinstance(value, str) and bool(_SHA256.match(value))


# --------------------------------------------------------------------------
# typed scalar formats
# --------------------------------------------------------------------------


def decimal_string(value: Any, *, field: str, scale: int | None = None) -> str:
	"""A plain decimal string; never a float. `scale` bounds fractional digits."""
	if isinstance(value, bool) or not isinstance(value, (str, int)):
		fail("STD_INPUT_UNSUPPORTED", f"{field} must be a decimal string.", identity=field)
	text = str(value)
	if not _DECIMAL.match(text):
		fail("STD_INPUT_UNSUPPORTED", f"{field} is not a plain decimal: {text!r}.", identity=field)
	if scale is not None and "." in text and len(text.split(".", 1)[1]) > scale:
		fail("STD_INPUT_UNSUPPORTED", f"{field} has more than {scale} decimal places.", identity=field)
	return text


def to_decimal(value: str, *, field: str) -> Decimal:
	try:
		return Decimal(decimal_string(value, field=field))
	except InvalidOperation:  # pragma: no cover - regex already guards
		fail("STD_INPUT_UNSUPPORTED", f"{field} is not a decimal.", identity=field)
		raise


def decimal_text(number: Decimal) -> str:
	"""The canonical text of an exact decimal: no exponent, no trailing
	fractional zeros beyond those the value needs."""
	if number == number.to_integral_value():
		return str(number.quantize(Decimal(1)))
	return format(number.normalize(), "f")


def iso_date(value: Any, *, field: str) -> str:
	if not isinstance(value, str) or not _DATE.match(value):
		fail("STD_INPUT_UNSUPPORTED", f"{field} must be an ISO date (YYYY-MM-DD).", identity=field)
	try:
		date.fromisoformat(value)
	except ValueError:
		fail("STD_INPUT_UNSUPPORTED", f"{field} is not a valid date.", identity=field)
	return value


def iso_datetime(value: Any, *, field: str) -> str:
	if not isinstance(value, str):
		fail("STD_INPUT_UNSUPPORTED", f"{field} must be an ISO date-time with an offset.", identity=field)
	try:
		parsed = datetime.fromisoformat(value)
	except ValueError:
		fail("STD_INPUT_UNSUPPORTED", f"{field} is not a valid ISO date-time.", identity=field)
		raise
	if parsed.tzinfo is None:
		fail("STD_INPUT_UNSUPPORTED", f"{field} must carry an explicit UTC offset.", identity=field)
	return value


def short_hash(*parts: str, length: int = 24) -> str:
	"""First `length` lowercase hex of SHA-256 over the parts joined by NUL."""
	return hashlib.sha256("\u0000".join(parts).encode("utf-8")).hexdigest()[:length]
