# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Exact Decimal monetary helpers for BWMF persistence."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any, Iterable

MONEY_SCALE = Decimal("0.01")
MONEY_KEY_HINTS = frozenset(
	{
		"amount",
		"unit_price",
		"total",
		"grand_total",
		"line_total",
		"subtotal",
		"tax",
		"price",
	}
)


def exact_decimal_roundtrip(value: str | Decimal, *, scale: Decimal = MONEY_SCALE) -> Decimal:
	"""Parse and quantize money with banker's rounding; reject binary float inputs."""
	if isinstance(value, float):
		raise TypeError("float is not allowed for exact monetary values; use str or Decimal")
	try:
		dec = value if isinstance(value, Decimal) else Decimal(str(value))
	except (InvalidOperation, ValueError) as exc:
		raise ValueError(f"invalid monetary value: {value!r}") from exc
	return dec.quantize(scale, rounding=ROUND_HALF_EVEN)


def decimal_to_storage_str(value: Decimal | str, *, scale: Decimal = MONEY_SCALE) -> str:
	return format(exact_decimal_roundtrip(value, scale=scale), "f")


def sum_money(values: Iterable[str | Decimal], *, scale: Decimal = MONEY_SCALE) -> Decimal:
	total = Decimal("0")
	for value in values:
		total += exact_decimal_roundtrip(value, scale=scale)
	return exact_decimal_roundtrip(total, scale=scale)


def serialize_manifest_money(node: Any) -> Any:
	"""Recursively convert money-like leaves to decimal strings; reject float money."""
	if isinstance(node, float):
		raise TypeError("float is not allowed in canonical money serialization")
	if isinstance(node, Decimal):
		return decimal_to_storage_str(node)
	if isinstance(node, dict):
		out: dict[str, Any] = {}
		for key, value in node.items():
			if key in MONEY_KEY_HINTS or key.endswith("_amount") or key.endswith("_price"):
				if isinstance(value, float):
					raise TypeError(f"float is not allowed for money field {key}")
				if value is None or value == "":
					out[key] = value
				elif isinstance(value, (str, Decimal, int)):
					out[key] = decimal_to_storage_str(exact_decimal_roundtrip(value if not isinstance(value, int) else str(value)))
				else:
					out[key] = serialize_manifest_money(value)
			else:
				out[key] = serialize_manifest_money(value)
		return out
	if isinstance(node, list):
		return [serialize_manifest_money(item) for item in node]
	return node
