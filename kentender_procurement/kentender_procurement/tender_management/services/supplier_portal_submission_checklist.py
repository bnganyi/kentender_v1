# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §18.5 — supplier portal submission checklist (DSM-driven only).

Rows are built from the active binding's **DSM** ``Tender STD Generated Output`` ``content_json``
(``requirements``, ``addendum_acknowledgements``, ``boq_rate_entry``). No generic upload slots
are invented.

Progress hints use the supplier's latest **TM2 Bid Submission** (by ``modified``) plus
``TM2 Bid Submission Component`` rows with ``submitted`` == 1, and the submission's
``addendum_acknowledgement_snapshot`` — consistent with
:func:`~kentender_procurement.tender_management.services.validate_bid_submission_against_dsm`.

Tests: ``tender_management.tests.test_p10_05_supplier_portal_submission_checklist`` (includes ``test_EX_05_*`` for doc 9 §25 **EX-05**);
``tender_management.tests.test_p10_06_supplier_portal_works_boq`` (``test_EX_18_*`` for doc 9 §25 **EX-18** — DSM + BOQ rates checklist + quantity locks on Works portal fixture).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, cstr

from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	_active_binding,
)
from kentender_procurement.tender_management.services.validate_bid_submission_against_dsm import (
	_missing_mandatory_dsm_addendum_acks,
	_missing_mandatory_requirement_codes,
	_requirement_entry_satisfied,
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


def _checklist_row_suffix(code_or_fallback: str) -> str:
	s = cstr(code_or_fallback or "").strip().lower()
	out: list[str] = []
	for ch in s:
		if ch.isalnum() or ch in "-_":
			out.append(ch)
		else:
			out.append("-")
	val = "".join(out).strip("-")
	return val or "row"


def _latest_bid_requirements_and_acks(
	tm2_name: str,
	supplier: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
	rows = frappe.get_all(
		"TM2 Bid Submission",
		filters={"tm2_tender": tm2_name, "supplier": supplier},
		fields=["name", "addendum_acknowledgement_snapshot"],
		order_by="modified desc",
		limit=1,
	)
	if not rows:
		return {}, {}
	bid_name = cstr(rows[0].get("name") or "").strip()
	if not bid_name:
		return {}, {}
	req_map: dict[str, Any] = {}
	for comp in frappe.get_all(
		"TM2 Bid Submission Component",
		filters={"tm2_bid_submission": bid_name, "submitted": 1},
		fields=["std_submission_requirement_code", "component_type"],
	):
		code = cstr(comp.get("std_submission_requirement_code") or "").strip()
		if not code:
			continue
		ct = cstr(comp.get("component_type") or "").strip()
		if ct in ("FILE_SET", "STRUCTURED_TEXT_AND_FILE"):
			req_map[code] = {"file_url": "/files/submitted"}
		else:
			req_map[code] = {"acknowledged": True}
	raw_ack = rows[0].get("addendum_acknowledgement_snapshot")
	ack_map: dict[str, Any] = {}
	if isinstance(raw_ack, dict):
		ack_map = raw_ack
	elif isinstance(raw_ack, str) and raw_ack.strip():
		try:
			p = json.loads(raw_ack)
			if isinstance(p, dict):
				ack_map = p
		except json.JSONDecodeError:
			pass
	return req_map, ack_map


def _any_rate_required_boq(si_name: str) -> bool:
	doc = get_boq_for_instance(si_name)
	if not doc:
		return False
	for row in doc.get("boq_items") or []:
		if cint(getattr(row, "rate_required_from_supplier", 0)):
			return True
	return False


def build_supplier_portal_submission_checklist(tm2_name: str, supplier: str) -> dict[str, Any]:
	"""Return §18.5 checklist rows from DSM + completion hints (no non-DSM rows)."""
	bind = _active_binding(tm2_name)
	dsm_code = cstr(bind.get("dsm_output_code") or "").strip() if bind else ""
	si_name = cstr(bind.get("tender_std_instance_code") or bind.get("tender_std_instance") or "").strip() if bind else ""

	if not dsm_code:
		return {
			"dsm_output_code": "",
			"has_dsm": False,
			"message": str(_("No DSM submission model is bound for this tender yet.")),
			"items": [],
			"all_mandatory_complete": False,
		}
	if not frappe.db.exists("Tender STD Generated Output", dsm_code):
		return {
			"dsm_output_code": dsm_code,
			"has_dsm": False,
			"message": str(_("DSM output document is not available.")),
			"items": [],
			"all_mandatory_complete": False,
		}
	dsm = _parse_dsm_content(dsm_code)
	if not dsm:
		return {
			"dsm_output_code": dsm_code,
			"has_dsm": False,
			"message": str(_("DSM content is empty or invalid.")),
			"items": [],
			"all_mandatory_complete": False,
		}

	bid_req, bid_acks = _latest_bid_requirements_and_acks(tm2_name, supplier)
	missing_req = set(_missing_mandatory_requirement_codes(dsm, bid_req))
	missing_ack = set(_missing_mandatory_dsm_addendum_acks(dsm, bid_acks))

	bqe = dsm.get("boq_rate_entry")
	bqe_on = isinstance(bqe, dict) and bool(int(bqe.get("enabled") or 0))
	boq_rates_required = bool(bqe_on and si_name and _any_rate_required_boq(si_name))

	items: list[dict[str, Any]] = []
	reqs = dsm.get("requirements")
	if isinstance(reqs, list):
		for row in reqs:
			if not isinstance(row, dict):
				continue
			rt = cstr(row.get("requirement_type") or "").strip()
			if rt == "System":
				continue
			if rt == "BOQRateEntry" and bqe_on:
				continue
			code = cstr(row.get("requirement_code") or "").strip()
			label = cstr(row.get("label") or "").strip() or code
			mandatory = bool(int(row.get("mandatory") or 0))
			ent = bid_req.get(code) if code else None
			satisfied = bool(_requirement_entry_satisfied(rt, ent)) if code else False
			if mandatory and code and code in missing_req:
				satisfied = False
			items.append(
				{
					"kind": "requirement",
					"requirement_code": code,
					"requirement_type": rt,
					"label": label,
					"mandatory": mandatory,
					"satisfied": satisfied,
					"row_test_suffix": _checklist_row_suffix(code or label),
				}
			)

	ack_rows = dsm.get("addendum_acknowledgements")
	if isinstance(ack_rows, list):
		for row in ack_rows:
			if not isinstance(row, dict):
				continue
			acode = cstr(row.get("addendum_code") or "").strip()
			if not acode:
				continue
			mandatory = bool(int(row.get("mandatory") or 0))
			ok = bool(bid_acks.get(acode)) if bid_acks else False
			if mandatory and acode in missing_ack:
				ok = False
			items.append(
				{
					"kind": "addendum_ack",
					"addendum_code": acode,
					"label": str(_("Acknowledgement of {0}")).format(acode),
					"mandatory": mandatory,
					"satisfied": ok,
					"row_test_suffix": _checklist_row_suffix(acode),
				}
			)

	if bqe_on:
		boq_ok = not boq_rates_required
		items.append(
			{
				"kind": "boq_rates",
				"requirement_code": "",
				"label": str(_("Priced Bills of Quantities")),
				"mandatory": boq_rates_required,
				"satisfied": boq_ok,
				"row_test_suffix": "boq-rates",
			}
		)

	all_ok = True
	for it in items:
		if not it.get("mandatory"):
			continue
		if not it.get("satisfied"):
			all_ok = False
			break

	return {
		"dsm_output_code": dsm_code,
		"has_dsm": True,
		"message": "",
		"items": items,
		"all_mandatory_complete": all_ok,
	}


def buildSupplierPortalSubmissionChecklist(tm2_name: str, supplier: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`build_supplier_portal_submission_checklist`."""
	return build_supplier_portal_submission_checklist(tm2_name, supplier)
