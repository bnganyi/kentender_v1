# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §11.3 — ``validate_bid_submission_against_dsm``.

Validates a supplier **bid_payload** against the **current published DSM** for a TM2 tender
(no portal actor; ``supplier_code`` identifies the supplier account).

**Bid payload contract**

* ``dsm_output_code`` (str): must equal :func:`~kentender_procurement.tender_management.services.tm2_std_adapter.get_current_dsm` ``output_code``.
* ``tender_std_instance_code`` (str): must equal the active ``TM2 Tender STD Binding`` instance.
* ``supplier`` (str): must equal the resolved ``Supplier`` name for ``supplier_code``.
* ``requirements`` (dict): keys = DSM ``requirement_code``; values are dicts with optional
  ``value``, ``file_url`` / ``attachment_url``, or ``acknowledged`` (bool) for declarations / acknowledgements.
* ``addendum_acknowledgements`` (dict[str, Any]): DSM sheet mandatory addendum codes must map to truthy values.
* ``boq`` (list[dict]): rows with ``item_number``, optional ``quantity``, ``rate`` (PE quantities are locked).

Returns ``{"ok": True, ...}`` or ``{"ok": False, "denial_code", "message", ...}`` with optional
``missing_components`` (requirement codes), ``pending_addendum_codes``, ``boq_item_numbers``, etc.

Submission must **not** carry evaluation-stage arithmetic / correction fields (doc 8 **TM2-SMOKE-WORKS-004**;
doc 9 §25 **EX-07** — ``test_EX_07_*`` in ``test_p10_07_supplier_portal_submit_bid``;
aligns with :func:`~kentender_procurement.tender_management.services.validate_works_boq_payload.validate_works_boq_payload`).

Tests: ``tender_management.tests.test_p6_03_validate_bid_submission_against_dsm``;
``tender_management.tests.test_o06_tm2_smoke_works_005_no_arithmetic_correction_at_submission`` (O-06);
``tender_management.tests.test_p10_07_supplier_portal_submit_bid`` (``test_EX_07_*``).
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
from kentender_procurement.tender_management.services.tm2_addendum_acknowledgement_checks import (
	missing_required_addendum_acknowledgements,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import get_current_dsm
from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance

# Doc 8 TM2-SMOKE-WORKS-004 / validate_works_boq_payload — must not appear on bid submission payload.
_FORBIDDEN_BID_SUBMISSION_ARITHMETIC_KEYS: frozenset[str] = frozenset(
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

_BID_BOQ_LINE_ALLOWED_KEYS: frozenset[str] = frozenset({"item_number", "rate", "quantity"})


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


def _requirement_entry_satisfied(requirement_type: str, entry: Any) -> bool:
	if requirement_type == "System":
		return True
	if requirement_type == "BOQRateEntry":
		return True
	if entry is None:
		return False
	if isinstance(entry, str):
		return bool(entry.strip())
	if not isinstance(entry, dict):
		return bool(entry)
	if requirement_type in ("Declaration", "Acknowledgement"):
		if entry.get("acknowledged") is True:
			return True
		val = entry.get("value")
		if val is True:
			return True
		if isinstance(val, str) and val.strip().lower() in ("1", "true", "yes", "y"):
			return True
		return False
	fv = cstr(entry.get("file_url") or entry.get("attachment_url") or "").strip()
	if fv:
		return True
	val = entry.get("value")
	if val is None:
		return False
	if isinstance(val, (int, float)):
		return True
	if isinstance(val, str):
		return bool(val.strip())
	return bool(val)


def _missing_mandatory_requirement_codes(dsm: dict[str, Any], bid_req: dict[str, Any]) -> list[str]:
	missing: list[str] = []
	reqs = dsm.get("requirements")
	if not isinstance(reqs, list):
		return ["<invalid_dsm_requirements>"]
	for row in reqs:
		if not isinstance(row, dict):
			continue
		if not row.get("mandatory"):
			continue
		code = cstr(row.get("requirement_code") or "").strip()
		if not code:
			continue
		rt = cstr(row.get("requirement_type") or "").strip()
		if rt in ("System", "BOQRateEntry"):
			continue
		ent = bid_req.get(code)
		if not _requirement_entry_satisfied(rt, ent):
			missing.append(code)
	return sorted(missing)


def _missing_mandatory_dsm_addendum_acks(dsm: dict[str, Any], bid_acks: Any) -> list[str]:
	missing: list[str] = []
	if not isinstance(bid_acks, dict):
		bid_acks = {}
	rows = dsm.get("addendum_acknowledgements")
	if not isinstance(rows, list):
		return []
	for row in rows:
		if not isinstance(row, dict):
			continue
		if not row.get("mandatory"):
			continue
		code = cstr(row.get("addendum_code") or "").strip()
		if not code:
			continue
		if not bid_acks.get(code):
			missing.append(code)
	return sorted(missing)


def _validate_boq_against_instance(
	*,
	si: str,
	boq_enabled: bool,
	bid_boq: Any,
) -> dict[str, Any] | None:
	if not boq_enabled:
		return None
	if not isinstance(bid_boq, list):
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Bid BOQ payload must be a list when BOQ rate entry is enabled."),
		)
	for raw in bid_boq:
		if not isinstance(raw, dict):
			continue
		for k in raw.keys():
			if k not in _BID_BOQ_LINE_ALLOWED_KEYS:
				return _deny(
					DenialCode.BOQ_SUPPLIER_RATE_ENTRY_DENIED.value,
					_("Bid BOQ lines may only include item_number, rate, and optional quantity; unexpected key {0}.").format(
						k
					),
					extra={"unexpected_key": k},
				)
	boq_doc = get_boq_for_instance(si)
	if not boq_doc:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("DSM requires BOQ rates but this tender instance has no BOQ document."),
		)

	by_item: dict[str, dict[str, Any]] = {}
	for raw in bid_boq:
		if not isinstance(raw, dict):
			continue
		num = cstr(raw.get("item_number") or "").strip()
		if num:
			by_item[num] = raw

	expected_numbers: list[str] = []
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
			if rate == 0:
				return _deny(
					DenialCode.REQUIRED_BOQ_RATE_MISSING.value,
					_("A positive rate is required for BOQ item {0}.").format(item_number),
					extra={"boq_item_numbers": [item_number]},
				)
		if bid_row is not None and bid_row.get("quantity") is not None:
			bq = flt(bid_row.get("quantity"))
			if abs(bq - pe_qty) > 1e-6:
				return _deny(
					DenialCode.BOQ_QUANTITY_LOCKED.value,
					_("BOQ quantity for item {0} must match the published schedule.").format(item_number),
					extra={"boq_item_numbers": [item_number]},
				)

		locked_ps = item_type == "Provisional Sum" or sup_mode in ("Fixed Amount", "None")
		if locked_ps and not rate_req and bid_row is not None and bid_row.get("rate") is not None:
			br = flt(bid_row.get("rate"))
			lock_val = fixed_amount or ps_amt
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

	for num, _row in by_item.items():
		if num not in expected_numbers:
			return _deny(
				DenialCode.AUTH_CONTEXT_DENIED.value,
				_("Bid includes unknown BOQ item_number {0}.").format(num),
				extra={"unknown_boq_item_numbers": [num]},
			)

	return None


def validate_bid_submission_against_dsm(
	tender_code: str,
	supplier_code: str,
	bid_payload: dict[str, Any] | None,
) -> dict[str, Any]:
	"""Doc 9 §11.3 — structural validation of ``bid_payload`` vs current DSM."""
	payload: dict[str, Any] = dict(bid_payload or {})
	for fk in _FORBIDDEN_BID_SUBMISSION_ARITHMETIC_KEYS:
		if fk in payload:
			return _deny(
				DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value,
				_("Bid submission must not include arithmetic correction or corrected-total fields."),
				extra={"forbidden_key": fk},
			)
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

	payload_si = cstr(payload.get("tender_std_instance_code") or "").strip()
	if payload_si != si:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Bid tender_std_instance_code does not match the active binding."),
			extra={"expected_tender_std_instance_code": si, "got": payload_si or None},
		)
	payload_dsm = cstr(payload.get("dsm_output_code") or "").strip()
	if payload_dsm != dsm_output_name:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Bid dsm_output_code does not match the current published DSM."),
			extra={"expected_dsm_output_code": dsm_output_name, "got": payload_dsm or None},
		)
	payload_supplier = cstr(payload.get("supplier") or "").strip()
	if not payload_supplier:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Bid supplier is required and must match the resolved supplier."),
		)
	if payload_supplier != supplier:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Bid supplier does not match the resolved supplier for supplier_code."),
			extra={"expected_supplier": supplier, "got": payload_supplier},
		)

	go = frappe.get_doc("Tender STD Generated Output", dsm_output_name)
	dsm_json = _parse_content_json(go.get("content_json"))
	if not dsm_json:
		return _deny(
			DenialCode.AUTH_DSM_MISSING_OR_STALE.value,
			_("Current DSM content is missing or not valid JSON."),
		)

	pending_db = missing_required_addendum_acknowledgements(tm2.name, supplier)
	if pending_db:
		return _deny(
			DenialCode.AUTH_ADDENDUM_ACK_REQUIRED.value,
			_("Required addendum acknowledgement is missing for: {0}").format(", ".join(pending_db)),
			extra={"pending_addendum_codes": pending_db},
		)

	pending_sheet = _missing_mandatory_dsm_addendum_acks(dsm_json, payload.get("addendum_acknowledgements"))
	if pending_sheet:
		return _deny(
			DenialCode.AUTH_ADDENDUM_ACK_REQUIRED.value,
			_("Bid is missing required DSM addendum acknowledgement flags for: {0}").format(", ".join(pending_sheet)),
			extra={"missing_dsm_addendum_ack_codes": pending_sheet},
		)

	bid_req = payload.get("requirements")
	if not isinstance(bid_req, dict):
		bid_req = {}
	missing_req = _missing_mandatory_requirement_codes(dsm_json, bid_req)
	if missing_req:
		return _deny(
			DenialCode.AUTH_CONTEXT_DENIED.value,
			_("Bid is missing mandatory DSM requirement submissions."),
			extra={"missing_components": missing_req},
		)

	bqe = dsm_json.get("boq_rate_entry")
	boq_enabled = isinstance(bqe, dict) and bool(bqe.get("enabled"))
	boq_err = _validate_boq_against_instance(si=si, boq_enabled=boq_enabled, bid_boq=payload.get("boq"))
	if boq_err:
		return boq_err

	return {
		"ok": True,
		"message": _("Bid payload is consistent with the current DSM."),
		"tender_code": tc,
		"tm2_tender": tm2.name,
		"supplier": supplier,
		"tender_std_instance_code": si,
		"dsm_output_code": dsm_output_name,
	}


def validateBidSubmissionAgainstDsm(
	tender_code: str,
	supplier_code: str,
	bid_payload: dict[str, Any] | None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`validate_bid_submission_against_dsm`."""
	return validate_bid_submission_against_dsm(tender_code, supplier_code, bid_payload)
