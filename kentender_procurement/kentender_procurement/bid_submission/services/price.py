# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Price (BDS-CHG-001 v0.8 §5.6; STD-TPL-001 released calculations
`CALC-LINE-TOTAL` and `CALC-TENDER-TOTAL`).

Quantity, unit, description and currency are published facts. The bidder
enters only the published unit price and tax amount of each line. The
server calculates, in Decimal at the currency scale with half-up rounding:
each line's amount before tax (unit price × quantity), its line total (plus
the stated tax) and the bid total (the sum of line totals). No other
currency, alternative price, extra line or discount can be entered, because
the definition offers no input for one. A total exists only when every line
is priced."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from frappe.utils import cstr

from kentender_procurement.bid_submission.services import labels

CENT = Decimal("0.01")


def _money(value) -> Decimal | None:
	if value in (None, ""):
		return None
	return Decimal(cstr(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def calculate(ctx) -> dict[str, Any]:
	"""Lines, subtotal before tax, tax and bid total for the bid's current answers."""
	lines, currency = [], ""
	for row in ctx.model.price_rows:
		calc = row.get("calculation") or {}
		if calc.get("calculation_id") != "CALC-LINE-TOTAL":
			continue
		currency = cstr(row.get("currency")) or currency
		inputs = row.get("input_response_ids") or {}
		quantity = Decimal(cstr(row.get("quantity") or "0"))
		unit_price = _money(ctx.values.get(inputs.get("unit_price")))
		tax = _money(ctx.values.get(inputs.get("tax_amount")))
		before_tax = (unit_price * quantity).quantize(CENT, rounding=ROUND_HALF_UP) if unit_price is not None else None
		line_total = before_tax + tax if before_tax is not None and tax is not None else None
		lines.append({
			"line": cstr(row.get("line")), "description": cstr(row.get("description")), "quantity": cstr(row.get("quantity")), "unit": cstr(row.get("unit")),
			"unit_price": unit_price, "tax_amount": tax, "amount_before_tax": before_tax, "line_total": line_total,
		})
	complete = bool(lines) and all(line["line_total"] is not None for line in lines)
	subtotal = sum((line["amount_before_tax"] for line in lines), Decimal(0)) if complete else None
	tax = sum((line["tax_amount"] for line in lines), Decimal(0)) if complete else None
	total = sum((line["line_total"] for line in lines), Decimal(0)) if complete else None
	return {"currency": currency, "lines": lines, "complete": complete, "subtotal": subtotal, "tax": tax, "total": total}


def summary(ctx) -> dict[str, Any]:
	"""The read-only calculation the portal shows beside the price inputs."""
	calc = calculate(ctx)
	currency = calc["currency"]

	def label(value):
		return labels.money_label(value, currency) if value is not None else ""

	return {
		"currency": currency, "complete": calc["complete"],
		"lines": [{"line": l["line"], "description": l["description"], "quantity": l["quantity"], "unit": l["unit"], "amount_before_tax": label(l["amount_before_tax"]), "line_total": label(l["line_total"])} for l in calc["lines"]],
		"subtotal": label(calc["subtotal"]), "tax": label(calc["tax"]), "total": label(calc["total"]),
	}
