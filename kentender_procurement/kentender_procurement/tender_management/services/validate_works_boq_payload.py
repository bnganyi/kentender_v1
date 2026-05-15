# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §11.4 — ``validate_works_boq_payload`` (Works BOQ supplier rate surface).

Rules (doc 9 §11.4 + doc 8 §12 Works BOQ smoke):

1. Supplier may submit **unit rates only** — each line object may contain only
   ``item_number``, ``rate``, and optionally ``quantity`` (must match PE when present).
2. **Quantities** must match STD instance BOQ when supplied.
3. **No** bill/header reshaping or edits to descriptions, units, item types, or locked
   provisional amounts via the payload (extra keys denied).
4. **Missing** required rates block validation.
5. **Negative** rates block validation.
6. **Zero** rates are blocked unless DSM ``boq_rate_entry.allow_zero_supplier_rates`` is true.
7. **Submitted line amounts and total** are computed as ``quantity × rate`` for
   rate-required lines; locked provisional / fixed lines use PE ``fixed_amount`` /
   ``provisional_sum_amount`` as the line value (no supplier arithmetic correction).
8. **No arithmetic correction** — payload must not include correction / corrected-total keys;
   responses always set ``correction_applied`` to false.

**``boq_payload`` shape**

Either a **list** of line dicts, or ``{"lines": [ ... ]}``. Top-level ``bills`` / ``header`` /
similar PE-structure keys are rejected.

**Alpha success contract** (doc 9 §11.4)::

    ok, submitted_total_price (int), correction_applied (false), currency

Tests: ``tender_management.tests.test_p6_04_validate_works_boq_payload``;
``tender_management.tests.test_o05_tm2_smoke_works_001_supplier_cannot_edit_boq_quantities`` (doc 8 TM2-SMOKE-WORKS-001 / O-05);
``tender_management.tests.test_p10_06_supplier_portal_works_boq`` (``test_EX_06_validate_works_boq_payload_rejects_quantity_tamper``, ``test_EX_18_*`` for doc 9 §25 **EX-18**);
``tender_management.tests.tm2_works_boq_supplier_fixture`` (shared published Works BOQ fixture).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	resolve_supplier_for_tm2_participation,
	resolve_tm2_tender_document,
)
from kentender_procurement.tender_management.services.supplier_management_adapter import (
	evaluate_supplier_eligibility_for_tender,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import get_current_dsm
from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance

_ALLOWED_LINE_KEYS: frozenset[str] = frozenset({"item_number", "rate", "quantity"})
_FORBIDDEN_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
	{
		"correction_applied",
		"arithmetic_correction",
		"arithmetic_corrections",
		"boq_arithmetic_correction",
		"corrected_total_price",
		"corrected_evaluated_price",
		"evaluated_price",
	}
)


def _deny(denial_code: str, message: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": False, "denial_code": denial_code, "message": message}
	if extra:
		out.update(extra)
	return out


def _active_std_instance(tm2_name: str) -> str | None:
	return frappe.db.get_value(
		"TM2 Tender STD Binding",
		{"tm2_tender": tm2_name, "is_active": 1},
		"tender_std_instance",
	)


def _parse_content_json(raw: Any) -> dict[str, Any] | None:
	if raw is None:
		return None
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str):
		s = raw.strip()
		if not s:
			return None
		try:
			parsed = json.loads(s)
		except json.JSONDecodeError:
			return None
		return parsed if isinstance(parsed, dict) else None
	return None


def _normalize_supplier_lines(boq_payload: Any) -> tuple[list[dict[str, Any]] | None, str | None]:
	"""Return line dicts or (None, error_token)."""
	if boq_payload is None:
		return None, "empty"
	if isinstance(boq_payload, list):
		return [row for row in boq_payload if isinstance(row, dict)], None
	if not isinstance(boq_payload, dict):
		return None, "type"
	for fk in ("bills", "header", "boq_bills", "boq_items", "format"):
		if fk in boq_payload:
			return None, "pe_structure_forbidden"
	for bad in _FORBIDDEN_TOP_LEVEL_KEYS:
		if bad in boq_payload:
			return None, "arithmetic_or_correction_forbidden"
	lines = boq_payload.get("lines")
	if not isinstance(lines, list):
		return None, "no_lines"
	return [row for row in lines if isinstance(row, dict)], None


def _allow_zero_rates(bqe: Any) -> bool:
	if not isinstance(bqe, dict):
		return False
	return bool(bqe.get("allow_zero_supplier_rates"))


def validate_works_boq_payload(
	tender_code: str,
	supplier_code: str,
	boq_payload: Any,
) -> dict[str, Any]:
	"""Doc 9 §11.4 — validate Works supplier BOQ lines and compute submitted total (no correction)."""
	tc_in = cstr(tender_code or "").strip()
	tm2 = resolve_tm2_tender_document(tc_in)
	if not tm2:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format(tc_in),
		)
	tc = cstr(tm2.tender_code or "").strip() or tm2.name

	supplier = resolve_supplier_for_tm2_participation(tm2.name, tc, supplier_code)
	if not supplier:
		return _deny(DenialCode.AUTH_CONTEXT_DENIED.value, _("Supplier could not be resolved for this tender."))

	if not frappe.db.exists("TM2 Supplier Participation", {"tm2_tender": tm2.name, "supplier": supplier}):
		return _deny(
			DenialCode.AUTH_SUPPLIER_INELIGIBLE.value,
			_("This supplier is not registered as a participant on this tender."),
		)

	elig = evaluate_supplier_eligibility_for_tender(
		tm2_tender=tm2.name,
		tender_code=tc,
		supplier=supplier,
		context={},
	)
	if not bool(elig.get("eligible")):
		return _deny(
			DenialCode.AUTH_SUPPLIER_INELIGIBLE.value,
			cstr(elig.get("message") or _("Supplier is not eligible for this tender.")).strip()
			or _("Supplier is not eligible for this tender."),
			extra={"eligibility": elig},
		)

	si = _active_std_instance(tm2.name)
	if not si:
		return _deny(
			DenialCode.AUTH_STD_NOT_READY.value,
			_("No active Tender STD binding is available for this tender."),
		)

	pc = cstr(frappe.db.get_value("Tender STD Instance", si, "procurement_category") or "").strip().upper()
	if pc != "WORKS":
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Works BOQ validation applies only when the STD instance procurement category is Works."),
			extra={"procurement_category": pc or None},
		)

	dsm_meta = get_current_dsm(si)
	if not dsm_meta.get("ok"):
		return _deny(
			DenialCode.AUTH_DSM_MISSING_OR_STALE.value,
			cstr(dsm_meta.get("message") or _("Current DSM output is missing or not consumable.")).strip()
			or _("Current DSM output is missing or not consumable."),
			extra={
				"dsm_reason": dsm_meta.get("reason"),
				"dsm_missing": dsm_meta.get("missing"),
				"dsm_stale_or_invalid": dsm_meta.get("stale_or_invalid"),
			},
		)
	dsm_output_name = cstr(dsm_meta.get("output_code") or "").strip()
	if not dsm_output_name:
		return _deny(
			DenialCode.AUTH_DSM_MISSING_OR_STALE.value,
			_("Current DSM output code is not available."),
		)

	go = frappe.get_doc("Tender STD Generated Output", dsm_output_name)
	dsm_json = _parse_content_json(go.get("content_json"))
	if not dsm_json:
		return _deny(
			DenialCode.AUTH_DSM_MISSING_OR_STALE.value,
			_("Current DSM content is missing or not valid JSON."),
		)
	bqe = dsm_json.get("boq_rate_entry")
	if not isinstance(bqe, dict) or not bqe.get("enabled"):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("BOQ rate entry is not enabled for this tender's DSM."),
		)
	allow_zero = _allow_zero_rates(bqe)

	boq_doc = get_boq_for_instance(si)
	if not boq_doc:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("No Tender STD Instance BOQ is available for this tender."),
		)
	currency = cstr(boq_doc.get("currency") or "").strip() or "KES"

	lines, err_tok = _normalize_supplier_lines(boq_payload)
	if lines is None:
		if err_tok == "pe_structure_forbidden":
			return _deny(
				DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value,
				_("Supplier BOQ payload must not include bills, header, or other PE-only structure."),
			)
		if err_tok == "arithmetic_or_correction_forbidden":
			return _deny(
				DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value,
				_("Arithmetic correction fields must not appear on the supplier BOQ payload."),
			)
		if err_tok == "empty":
			return _deny(
				DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value,
				_("BOQ payload is required."),
			)
		return _deny(
			DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value,
			_("BOQ payload must be a list of lines or an object with a ``lines`` array."),
		)

	by_item: dict[str, dict[str, Any]] = {}
	for raw in lines:
		num = cstr(raw.get("item_number") or "").strip()
		if not num:
			return _deny(
				DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value,
				_("Each BOQ line must include item_number."),
			)
		for k in raw.keys():
			if k not in _ALLOWED_LINE_KEYS:
				return _deny(
					DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value,
					_("Only unit rates (and optional quantity echo) are allowed; unexpected key {0}.").format(k),
					extra={"unexpected_key": k, "item_number": num},
				)
		by_item[num] = raw

	expected_numbers: list[str] = []
	total_amount = 0.0
	line_amounts: dict[str, float] = {}

	for row in boq_doc.get("boq_items") or []:
		st = cstr(getattr(row, "status", None) or "").strip()
		if st and st not in ("Published", "Current"):
			continue
		item_number = cstr(getattr(row, "item_number", None) or "").strip()
		if not item_number:
			continue
		expected_numbers.append(item_number)
		pe_qty = flt(getattr(row, "quantity", None))
		rate_req = cint(getattr(row, "rate_required_from_supplier", 0))
		item_type = cstr(getattr(row, "item_type", None) or "").strip()
		sup_mode = cstr(getattr(row, "supplier_input_mode", None) or "").strip()
		fixed_amount = flt(getattr(row, "fixed_amount", None))
		ps_amt = flt(getattr(row, "provisional_sum_amount", None))

		bid_row = by_item.get(item_number)

		if rate_req:
			if not bid_row:
				return _deny(
					DenialCode.REQUIRED_BOQ_RATE_MISSING.value,
					_("Missing supplier rate for BOQ item {0}.").format(item_number),
					extra={"boq_item_numbers": [item_number]},
				)
			if bid_row.get("rate") is None:
				return _deny(
					DenialCode.REQUIRED_BOQ_RATE_MISSING.value,
					_("Missing supplier rate for BOQ item {0}.").format(item_number),
					extra={"boq_item_numbers": [item_number]},
				)
			rate = flt(bid_row.get("rate"))
			if rate < 0:
				return _deny(
					DenialCode.INVALID_BOQ_RATE_NEGATIVE.value,
					_("Negative rates are not allowed (item {0}).").format(item_number),
					extra={"boq_item_numbers": [item_number]},
				)
			if rate == 0 and not allow_zero:
				return _deny(
					DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value,
					_("Zero rates are not permitted for item {0} unless DSM allows them.").format(item_number),
					extra={"boq_item_numbers": [item_number]},
				)
			if bid_row.get("quantity") is not None:
				bq = flt(bid_row.get("quantity"))
				if abs(bq - pe_qty) > 1e-6:
					return _deny(
						DenialCode.BOQ_QUANTITY_LOCKED.value,
						_("BOQ quantity for item {0} must match the published schedule.").format(item_number),
						extra={"boq_item_numbers": [item_number]},
					)
			line_amount = pe_qty * rate
		else:
			locked_ps = item_type == "Provisional Sum" or sup_mode in ("Fixed Amount", "None")
			lock_val = fixed_amount or ps_amt
			if bid_row is not None and bid_row.get("quantity") is not None:
				bq = flt(bid_row.get("quantity"))
				if abs(bq - pe_qty) > 1e-6:
					return _deny(
						DenialCode.BOQ_QUANTITY_LOCKED.value,
						_("BOQ quantity for item {0} must match the published schedule.").format(item_number),
						extra={"boq_item_numbers": [item_number]},
					)
			if locked_ps and bid_row is not None and bid_row.get("rate") is not None:
				br = flt(bid_row.get("rate"))
				if lock_val:
					if abs(br - flt(lock_val)) > 1e-6:
						return _deny(
							DenialCode.BOQ_FIXED_AMOUNT_LOCKED.value,
							_("Provisional / fixed BOQ line {0} is locked to the published amount.").format(item_number),
							extra={"boq_item_numbers": [item_number]},
						)
				elif abs(br) > 1e-9:
					return _deny(
						DenialCode.BOQ_FIXED_AMOUNT_LOCKED.value,
						_("BOQ item {0} does not accept supplier rate entry.").format(item_number),
						extra={"boq_item_numbers": [item_number]},
					)
			if lock_val:
				line_amount = flt(lock_val)
			else:
				line_amount = 0.0

		line_amounts[item_number] = line_amount
		total_amount += line_amount

	for num, _row in by_item.items():
		if num not in expected_numbers:
			return _deny(
				DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value,
				_("Unknown BOQ item_number {0}.").format(num),
				extra={"unknown_boq_item_numbers": [num]},
			)

	return {
		"ok": True,
		"message": _("Works BOQ payload is valid."),
		"submitted_total_price": int(round(total_amount)),
		"correction_applied": False,
		"currency": currency,
		"tender_code": tc,
		"tm2_tender": tm2.name,
		"supplier": supplier,
		"tender_std_instance_code": si,
		"dsm_output_code": dsm_output_name,
		"line_amounts": line_amounts,
	}


def validateWorksBoqPayload(
	tender_code: str,
	supplier_code: str,
	boq_payload: Any,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`validate_works_boq_payload`."""
	return validate_works_boq_payload(tender_code, supplier_code, boq_payload)
