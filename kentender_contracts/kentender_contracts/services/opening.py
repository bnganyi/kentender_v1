# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The opening position of a registered existing contract (CM-CHG-001 v0.8 section 5.13; board D21; plan Phase 5, tracker CM8-508).

An existing signed contract already has history: units accepted and perhaps paid for, units in custody, invoices, credits and cash. That history is **not** reposted. It is recorded once as the
opening position of the agreement the contract starts management from, and the rest of Contract Management reads it as a starting offset, never as new activity: accepted units count toward what is
accepted, invoiced quantity and amount count toward what has already been claimed, so new activity can never take a line or the contract above its entitlement.

`lines()` and the money totals are what the position and the claim matching add; `reconcile()` compares the source's figures with the native records the preparer linked, which is what Finance checks
before it confirms (D21). Unknown figures stay unknown (`None`), never zero."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, flt

from kentender_contracts.services import records

AGREEMENT = "Contract Agreement Version"
TOLERANCE = 0.005


def of(case: str) -> dict[str, Any]:
	"""The opening position of the agreement in force, or `{}` for a contract that began here."""
	raw = frappe.db.get_value(AGREEMENT, {"contract_case": case, "state": "Effective"}, "intake_json", order_by="version_no desc")
	return (records.loads(raw).get("opening") or {}) if raw else {}


def line(case: str, line_id: str) -> dict[str, int]:
	row = (of(case).get("lines") or {}).get(line_id) or {}
	return {"accepted": cint(row.get("accepted")), "in_custody": cint(row.get("in_custody")), "invoiced_quantity": cint(row.get("invoiced_quantity"))}


def invoiced(case: str) -> float:
	"""What has already been claimed on this contract before management started, net of credits."""
	opening = of(case)
	return flt(opening.get("invoiced")) - flt(opening.get("credits"))


def prior_activity(opening: dict[str, Any]) -> bool:
	if opening.get("prior_activity") == "Some":
		return True
	return any(flt(opening.get(k)) for k in ("invoiced", "credits", "cash_paid", "advance")) or any(cint(v.get("accepted")) or cint(v.get("in_custody")) for v in (opening.get("lines") or {}).values())


def _qty(doctype: str, name: str) -> float | None:
	if not name or not frappe.db.exists(doctype, name):
		return None
	child = f"{doctype} Item"
	return sum(flt(q) for q in frappe.get_all(child, filters={"parent": name}, pluck="qty"))


def reconcile(opening: dict[str, Any], units_in_custody: int) -> list[dict[str, Any]]:
	"""The source's figures against the linked native records: `{measure, source, native, match}`. A figure with no linked record and a source of zero matches; a nonzero figure without its record does not."""
	links = opening.get("links") or {}
	lines = (opening.get("lines") or {}).values()
	accepted, custody = sum(cint(l.get("accepted")) for l in lines), sum(cint(l.get("in_custody")) for l in lines)
	invoice = links.get("purchase_invoice")
	exists = bool(invoice) and frappe.db.exists("Purchase Invoice", invoice)
	payment = links.get("payment_entry")
	paid = flt(frappe.db.get_value("Payment Entry", payment, "paid_amount")) if payment and frappe.db.exists("Payment Entry", payment) else None
	rows = [
		{"measure": "Accepted units", "source": accepted, "native": _qty("Purchase Receipt", links.get("purchase_receipt")), "kind": "quantity"},
		{"measure": "In custody", "source": custody, "native": units_in_custody, "kind": "quantity"},
		{"measure": "Invoiced", "source": flt(opening.get("invoiced")), "native": flt(frappe.db.get_value("Purchase Invoice", invoice, "grand_total")) if exists else None, "kind": "money"},
		{"measure": "Cash paid", "source": flt(opening.get("cash_paid")), "native": paid, "kind": "money"},
		{"measure": "Outstanding", "source": flt(opening.get("outstanding")), "native": flt(frappe.db.get_value("Purchase Invoice", invoice, "outstanding_amount")) if exists else None, "kind": "money"},
		{"measure": "Advance", "source": flt(opening.get("advance")), "native": None, "kind": "money"},
	]
	for row in rows:
		zero_and_unlinked = row["native"] is None and not flt(row["source"])
		row["match"] = zero_and_unlinked or (row["native"] is not None and abs(flt(row["native"]) - flt(row["source"])) <= TOLERANCE)
	return rows
