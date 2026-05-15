# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §18.7–§18.8 — supplier portal **Submit bid** + **late submission** read-only hints.

Exposes TM2-level addendum acknowledgement completeness (§21.3 item 8), submission checklist
summary, deadline state, doc 9 §18.8 **late submission** copy (§21.3 item 9 — official server time),
and a **non-authoritative** ``bid_payload_template`` JSON object
that the portal page merges with live BOQ rate inputs before calling
:func:`~kentender_procurement.tender_management.services.submit_bid.submit_bid`.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_procurement.tender_management.services.tm2_addendum_acknowledgement_checks import (
	missing_required_addendum_acknowledgements,
)
from kentender_procurement.tender_management.services.tm2_std_adapter import get_current_dsm
from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import _active_binding
from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance


def _parse_dsm_json(dsm_output_name: str) -> dict[str, Any] | None:
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


def _fill_mandatory_requirements(content: dict[str, Any]) -> dict[str, dict[str, Any]]:
	out: dict[str, dict[str, Any]] = {}
	for row in content.get("requirements") or []:
		if not isinstance(row, dict) or not row.get("mandatory"):
			continue
		code = cstr(row.get("requirement_code") or "").strip()
		rt = cstr(row.get("requirement_type") or "").strip()
		if not code or rt in ("System", "BOQRateEntry"):
			continue
		if rt in ("Declaration", "Acknowledgement"):
			out[code] = {"acknowledged": True}
		else:
			out[code] = {"value": "portal-template"}
	return out


def _fill_mandatory_dsm_addendum_acks(content: dict[str, Any]) -> dict[str, bool]:
	flags: dict[str, bool] = {}
	for row in content.get("addendum_acknowledgements") or []:
		if not isinstance(row, dict):
			continue
		if row.get("mandatory"):
			ac = cstr(row.get("addendum_code") or "").strip()
			if ac:
				flags[ac] = True
	return flags


def _boq_template_lines(si: str, content: dict[str, Any]) -> list[dict[str, Any]]:
	bqe = content.get("boq_rate_entry")
	if not (isinstance(bqe, dict) and bqe.get("enabled")):
		return []
	boq_doc = get_boq_for_instance(si)
	if not boq_doc:
		return []
	lines: list[dict[str, Any]] = []
	for row in boq_doc.get("boq_items") or []:
		st = cstr(getattr(row, "status", None) or "").strip()
		if st and st not in ("Published", "Current"):
			continue
		item_number = cstr(getattr(row, "item_number", None) or "").strip()
		if not item_number:
			continue
		if int(getattr(row, "rate_required_from_supplier", 0) or 0):
			lines.append({"item_number": item_number, "rate": 0.0})
	return lines


def build_portal_bid_payload_template(tm2_name: str, supplier: str) -> dict[str, Any] | None:
	"""Return a merge-friendly bid JSON template (Declaration/Ack defaults + BOQ zero rates)."""
	bind = _active_binding(tm2_name)
	if not bind:
		return None
	si = cstr(bind.get("tender_std_instance_code") or bind.get("tender_std_instance") or "").strip()
	dsm_code = cstr(bind.get("dsm_output_code") or "").strip()
	if not si or not dsm_code:
		return None
	meta = get_current_dsm(si)
	if not meta.get("ok"):
		return None
	out_code = cstr(meta.get("output_code") or "").strip()
	if not out_code or out_code != dsm_code:
		return None
	content = _parse_dsm_json(dsm_code)
	if not content:
		return None
	reqs = _fill_mandatory_requirements(content)
	acks = _fill_mandatory_dsm_addendum_acks(content)
	boq = _boq_template_lines(si, content)
	return {
		"tender_std_instance_code": si,
		"dsm_output_code": out_code,
		"supplier": supplier,
		"requirements": reqs,
		"addendum_acknowledgements": acks,
		"boq": boq,
	}


def build_supplier_portal_submit_bid_panel(
	tm2_name: str,
	supplier: str,
	tender_code: str,
	submission_checklist: dict[str, Any],
	submission_deadline_at: Any,
	*,
	server_time_display: str = "",
	submission_deadline_display: str = "",
) -> dict[str, Any]:
	"""§18.7 modal fields + §18.8 late notice + §21.3 item 8 addendum gate flags."""
	pending = missing_required_addendum_acknowledgements(tm2_name, supplier)
	addendum_ack_complete = len(pending) == 0
	checklist_complete = bool(
		submission_checklist.get("has_dsm") and submission_checklist.get("all_mandatory_complete")
	)
	deadline_passed = False
	if submission_deadline_at:
		try:
			deadline_passed = get_datetime(now_datetime()) > get_datetime(submission_deadline_at)
		except Exception:
			deadline_passed = False

	supplier_display = cstr(frappe.db.get_value("Supplier", supplier, "supplier_name") or supplier).strip()

	tpl = build_portal_bid_payload_template(tm2_name, supplier)

	deadline_label = cstr(submission_deadline_display or "").strip() or "—"
	server_label = cstr(server_time_display or "").strip() or "—"
	late_notice = {
		"visible": deadline_passed,
		"lead_message": str(
			_(
				"Submission rejected. The tender deadline has passed according to the official server time."
			)
		),
		"deadline_label": deadline_label,
		"official_server_time_label": server_label,
	}

	return {
		"supplier_display": supplier_display,
		"tender_code": cstr(tender_code or "").strip(),
		"addendum_ack_complete": addendum_ack_complete,
		"pending_addendum_codes": pending,
		"checklist_all_mandatory_complete": checklist_complete,
		"deadline_passed": deadline_passed,
		"submit_disabled_by_addendum_ack": not addendum_ack_complete,
		"submit_disabled_by_deadline": deadline_passed,
		"late_submission_notice": late_notice,
		"bid_payload_template": tpl,
	}


def buildSupplierPortalSubmitBidPanel(
	tm2_name: str,
	supplier: str,
	tender_code: str,
	submission_checklist: dict[str, Any],
	submission_deadline_at: Any,
	*,
	server_time_display: str = "",
	submission_deadline_display: str = "",
) -> dict[str, Any]:
	"""CamelCase alias for :func:`build_supplier_portal_submit_bid_panel`."""
	return build_supplier_portal_submit_bid_panel(
		tm2_name,
		supplier,
		tender_code,
		submission_checklist,
		submission_deadline_at,
		server_time_display=server_time_display,
		submission_deadline_display=submission_deadline_display,
	)
