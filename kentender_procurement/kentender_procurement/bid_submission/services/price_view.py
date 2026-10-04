# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What BDS-DES-10 shows (BDS-CHG-001 v0.8 §10.11; plan Phase 11, slice
11.10): one row per published price line with its quantity and unit, the
bid's unit price and tax inputs, and the calculated line amount; then the
subtotal, tax and bid total — calculated here (`price.calculate`), never
entered. Nothing here saves anything."""

from __future__ import annotations

from typing import Any

from kentender_procurement.bid_submission.services import labels, price

TITLE = "Price"
DESCRIPTION = "Enter your price for the published quantity. Totals are calculated automatically."
NOTE = "The Form of Tender uses this Bid total. You do not enter the total again."
BADGE_TONES = {"Complete": "live", "Needs attention": "attention"}


def view(ctx, tasks, task_view: dict[str, Any], *, at) -> dict[str, Any]:
	ws = ctx.workspace
	fields = {f["handle"]: f for g in task_view["groups"] for f in g["fields"]}
	handle_of = {f.response_id: f.handle for g in ctx.model.groups_of("price") for f in g.fields}
	calc = price.calculate(ctx)
	currency = calc["currency"]

	def money(value) -> str:
		return labels.money_label(value, currency) if value is not None else "—"

	rows = [r for r in ctx.model.price_rows if (r.get("calculation") or {}).get("calculation_id") == "CALC-LINE-TOTAL"]
	lines = []
	for row, line in zip(rows, calc["lines"]):
		inputs = row.get("input_response_ids") or {}
		lines.append({
			"line": line["line"], "description": line["description"], "quantity": line["quantity"], "unit": line["unit"],
			"unit_price": fields.get(handle_of.get(inputs.get("unit_price"))), "tax": fields.get(handle_of.get(inputs.get("tax_amount"))),
			"amount_before_tax": money(line["amount_before_tax"]),
		})
	status = tasks["price"].status
	return {
		"page": {"title": TITLE, "description": DESCRIPTION, "back_href": f"/tenders/{ws.tender_reference}/bid"},
		"badge": {"label": status, "tone": BADGE_TONES.get(status, "draft")},
		"terms": f"Currency {currency} · Fixed prices · Taxes shown separately." if currency else "",
		"lines": lines, "totals": {"subtotal": money(calc["subtotal"]), "tax": money(calc["tax"]), "total": money(calc["total"]), "complete": calc["complete"]},
		"note": NOTE, "footer": {"save_label": "Save and continue", "next_href": f"/tenders/{ws.tender_reference}/bid/review"},
	}
