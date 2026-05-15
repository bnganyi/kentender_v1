# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §18.6 — supplier portal Works BOQ editor (read-only PE quantities; editable rates per DSM).

**EX-06** (doc 9 §25): quantities are PE-sourced only; regression tests ``test_EX_06_*`` in
``tender_management.tests.test_p10_06_supplier_portal_works_boq``.

Rows mirror **Tender STD Instance BOQ** ``boq_items`` (Published / Current only). Rate inputs are
offered only when the active DSM ``boq_rate_entry.enabled`` is true **and** the line requires a
supplier rate. Provisional / PE-fixed lines surface a locked amount instead of a rate field.

``submitted_total_from_bid`` reflects the supplier's latest **TM2 Bid Submission**
``total_submitted_price`` when present (per-line rate replay is P10-07+).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt, fmt_money

from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	_active_binding,
)
from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance


def _parse_dsm_content(dsm_output_name: str) -> dict[str, Any] | None:
	if not dsm_output_name or not frappe.db.exists("Tender STD Generated Output", dsm_output_name):
		return None
	doc = frappe.get_doc("Tender STD Generated Output", dsm_output_name)
	raw = doc.get("content_json")
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			p = json.loads(raw)
			return p if isinstance(p, dict) else None
		except json.JSONDecodeError:
			return None
	return None


def _row_slug(item_number: str) -> str:
	s = cstr(item_number or "").strip().lower()
	out: list[str] = []
	for ch in s:
		if ch.isalnum() or ch in "-_.":
			out.append(ch)
		else:
			out.append("-")
	val = "".join(out).strip("-")
	return val or "row"


def _latest_bid_submitted_total(tm2_name: str, supplier: str) -> float | None:
	rows = frappe.get_all(
		"TM2 Bid Submission",
		filters={"tm2_tender": tm2_name, "supplier": supplier},
		fields=["total_submitted_price"],
		order_by="modified desc",
		limit=1,
	)
	if not rows:
		return None
	v = rows[0].get("total_submitted_price")
	if v is None:
		return None
	f = flt(v)
	return f if f else None


def _is_works_category(procurement_category: str) -> bool:
	return cstr(procurement_category or "").strip().lower() == "works"


def build_supplier_portal_works_boq(
	tm2_name: str,
	supplier: str,
	procurement_category: str,
) -> dict[str, Any]:
	"""Return §18.6 BOQ table DTO for the supplier portal (empty ``rows`` when not applicable)."""
	if not _is_works_category(procurement_category):
		return {
			"show_panel": False,
			"message": str(_("Works BOQ entry applies to Works tenders only.")),
			"dsm_boq_rates_enabled": False,
			"currency": "",
			"rows": [],
			"submitted_total_from_bid": None,
			"submitted_total_display": "",
			"arithmetic_notice": "",
		}

	bind = _active_binding(tm2_name)
	si = cstr(bind.get("tender_std_instance_code") or bind.get("tender_std_instance") or "").strip() if bind else ""
	if not si:
		return {
			"show_panel": False,
			"message": str(_("No active STD binding is available for this tender.")),
			"dsm_boq_rates_enabled": False,
			"currency": "",
			"rows": [],
			"submitted_total_from_bid": None,
			"submitted_total_display": "",
			"arithmetic_notice": "",
		}

	boq_doc = get_boq_for_instance(si)
	if not boq_doc:
		return {
			"show_panel": False,
			"message": str(_("No Bill of Quantities is available for this tender.")),
			"dsm_boq_rates_enabled": False,
			"currency": "",
			"rows": [],
			"submitted_total_from_bid": None,
			"submitted_total_display": "",
			"arithmetic_notice": "",
		}

	dsm_code = cstr(bind.get("dsm_output_code") or "").strip() if bind else ""
	dsm = _parse_dsm_content(dsm_code) if dsm_code else None
	bqe = dsm.get("boq_rate_entry") if isinstance(dsm, dict) else None
	rates_globally_on = isinstance(bqe, dict) and bool(bqe.get("enabled"))

	currency = cstr(boq_doc.currency or "KES").strip() or "KES"
	rows_out: list[dict[str, Any]] = []

	for row in boq_doc.get("boq_items") or []:
		st = cstr(getattr(row, "status", None) or "").strip()
		if st and st not in ("Published", "Current"):
			continue
		num = cstr(getattr(row, "item_number", None) or "").strip()
		if not num:
			continue
		desc = cstr(getattr(row, "description", None) or "").strip()
		unit = cstr(getattr(row, "unit", None) or "").strip()
		qty = flt(getattr(row, "quantity", None))
		qd = f"{qty:g}"
		rate_req = cint(getattr(row, "rate_required_from_supplier", 0))
		item_type = cstr(getattr(row, "item_type", None) or "").strip()
		fixed_amount = flt(getattr(row, "fixed_amount", None))
		ps_amt = flt(getattr(row, "provisional_sum_amount", None))
		lock_val = fixed_amount or ps_amt
		rate_editable = bool(rates_globally_on and rate_req)
		line_amount = None
		line_amount_display = ""
		if not rate_editable and lock_val:
			line_amount = flt(lock_val)
			line_amount_display = fmt_money(line_amount, currency=currency)
		elif not rate_editable:
			line_amount = 0.0
			line_amount_display = fmt_money(0.0, currency=currency)

		rows_out.append(
			{
				"item_number": num,
				"description": desc,
				"unit": unit,
				"quantity": qty,
				"quantity_display": qd,
				"item_type": item_type,
				"rate_editable": rate_editable,
				"line_locked_amount": float(lock_val) if lock_val else 0.0,
				"line_amount": line_amount,
				"line_amount_display": line_amount_display,
				"row_test_suffix": _row_slug(num),
			}
		)

	prev_total = _latest_bid_submitted_total(tm2_name, supplier)
	prev_disp = fmt_money(prev_total, currency=currency) if prev_total is not None else ""

	return {
		"show_panel": True,
		"message": "",
		"dsm_boq_rates_enabled": rates_globally_on,
		"currency": currency,
		"rows": rows_out,
		"submitted_total_from_bid": prev_total,
		"submitted_total_display": prev_disp,
		"arithmetic_notice": str(
			_(
				"Quantities and descriptions are fixed by the Procuring Entity. "
				"Amounts update from your rates. Any arithmetic correction happens during Evaluation — "
				"not in this portal."
			)
		),
	}


def buildSupplierPortalWorksBoq(
	tm2_name: str,
	supplier: str,
	procurement_category: str,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`build_supplier_portal_works_boq`."""
	return build_supplier_portal_works_boq(tm2_name, supplier, procurement_category)
