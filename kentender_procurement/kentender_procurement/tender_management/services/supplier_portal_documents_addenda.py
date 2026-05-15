# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §18.4 — supplier portal documents & addenda (bundle, attachments, addenda list).

Reuses active STD binding and access-rule reads from
:mod:`kentender_procurement.tender_management.services.tm2_workbench_tender_detail`.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, cstr, get_url

from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	_active_access_rule,
	_active_binding,
)

_SUPPLIER_HIDDEN_ADDENDUM_STATUSES: frozenset[str] = frozenset(
	{"Cancelled", "Withdrawn", "Superseded"},
)

_BUNDLE_DOWNLOAD_STATUSES: frozenset[str] = frozenset(
	{
		"Published",
		"Addendum Pending",
		"Suspended Pending Addendum",
		"Opening Ready",
		"Opening Completed",
		"Evaluation Ready",
		"Evaluation In Progress",
		"Awarded",
		"Contract Handoff Completed",
		"Closed",
		"Closed - No Valid Submissions",
	},
)


def _addendum_row_test_suffix(code_or_fallback: str) -> str:
	s = cstr(code_or_fallback or "").strip().lower()
	out_ch: list[str] = []
	for ch in s:
		if ch.isalnum() or ch in "-_":
			out_ch.append(ch)
		else:
			out_ch.append("-")
	val = "".join(out_ch).strip("-")
	return val or "row"


def _participation_supplier_code(tm2_name: str, supplier: str) -> str:
	row = frappe.db.get_value(
		"TM2 Supplier Participation",
		{"tm2_tender": tm2_name, "supplier": supplier},
		"supplier_code",
	)
	return cstr(row or "").strip() or cstr(supplier or "").strip()


def _bundle_download_allowed(
	tender_status: str,
	bundle_code: str,
	rule: dict[str, Any] | None,
) -> tuple[bool, str]:
	bc = cstr(bundle_code or "").strip()
	if not bc:
		return False, str(_("No publication bundle is bound for this tender yet."))
	st = cstr(tender_status or "").strip()
	if st not in _BUNDLE_DOWNLOAD_STATUSES:
		return False, str(_("Bundle download is available after the tender is published."))
	if rule and int(rule.get("requires_supplier_login_for_documents") or 0):
		# Portal user is authenticated; login requirement is satisfied for this surface.
		pass
	return True, ""


def _public_attachment_rows(tm2_name: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "TM2 Tender",
			"attached_to_name": tm2_name,
			"is_folder": 0,
		},
		fields=["file_name", "file_url", "is_private"],
		order_by="creation asc",
		limit=100,
	)
	out: list[dict[str, Any]] = []
	for r in rows or []:
		if cint(r.get("is_private")):
			continue
		fn = cstr(r.get("file_name") or "").strip()
		url = cstr(r.get("file_url") or "").strip()
		if not fn and not url:
			continue
		full = get_url(url) if url else ""
		out.append(
			{
				"file_name": fn,
				"file_url": full or url,
				"file_label": fn or url,
			}
		)
	return out


def _addenda_rows(tm2_name: str, supplier: str, sup_code: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"TM2 Addendum",
		filters={"tm2_tender": tm2_name},
		fields=[
			"name",
			"addendum_code",
			"addendum_number",
			"title",
			"status",
			"requires_supplier_acknowledgement",
		],
		order_by="addendum_number asc, modified asc",
	)
	out: list[dict[str, Any]] = []
	for add in rows or []:
		st = cstr(add.get("status") or "").strip()
		if st in _SUPPLIER_HIDDEN_ADDENDUM_STATUSES:
			continue
		ad_name = cstr(add.get("name") or "").strip()
		acode = cstr(add.get("addendum_code") or "").strip()
		anum = int(add.get("addendum_number") or 0)
		title = cstr(add.get("title") or "").strip()
		req_ack = bool(int(add.get("requires_supplier_acknowledgement") or 0))
		ack_row = None
		if ad_name and supplier:
			ack_row = frappe.db.get_value(
				"TM2 Addendum Acknowledgement",
				{"tm2_addendum": ad_name, "supplier": supplier},
				["acknowledged", "required", "acknowledged_at"],
				as_dict=True,
			)
		acked = bool(int(ack_row.get("acknowledged") or 0)) if ack_row else False
		ack_required = req_ack and st == "Issued"
		summary_parts: list[str] = [
			str(_("Addendum {0}: {1}")).format(f"{anum:02d}", st),
		]
		if req_ack and st == "Issued":
			summary_parts.append(str(_("Acknowledgement required")))
			if acked:
				summary_parts.append(str(_("Acknowledged by {0}")).format(sup_code or supplier))
			else:
				summary_parts.append(str(_("Acknowledgement pending")))
		elif req_ack:
			summary_parts.append(str(_("Acknowledgement may be required when issued")))
		summary_line = " · ".join(summary_parts)
		out.append(
			{
				"addendum_code": acode,
				"addendum_number": anum,
				"title": title,
				"status": st,
				"requires_acknowledgement": req_ack,
				"acknowledgement_required": ack_required,
				"acknowledged": acked if ack_row else None,
				"summary_line": summary_line,
				"row_test_suffix": _addendum_row_test_suffix(acode or ad_name),
			}
		)
	return out


def build_supplier_portal_documents_addenda(
	tm2_name: str,
	supplier: str,
	_tender_code: str,
	tender_status: str,
) -> dict[str, Any]:
	"""Return §18.4 payload (bundle, download control, public attachments, addenda)."""
	bind = _active_binding(tm2_name)
	rule = _active_access_rule(tm2_name)
	sup_code = _participation_supplier_code(tm2_name, supplier)
	bundle_code = cstr(bind.get("bundle_output_code") or "").strip() if bind else ""
	version_code = cstr(bind.get("std_template_version_code") or "").strip() if bind else ""
	template_code = cstr(bind.get("std_template_code") or "").strip() if bind else ""
	pub_snap = cstr(bind.get("publication_snapshot_code") or "").strip() if bind else ""
	dl_ok, dl_reason = _bundle_download_allowed(tender_status, bundle_code, rule)
	current_display = ""
	if bundle_code:
		current_display = str(_("Current Bundle: {0}")).format(bundle_code)
	return {
		"bundle": {
			"bundle_output_code": bundle_code,
			"std_template_version_code": version_code,
			"std_template_code": template_code,
			"publication_snapshot_code": pub_snap,
			"current_bundle_display": current_display,
			"download_allowed": dl_ok,
			"download_denial_reason": dl_reason,
		},
		"attachments": _public_attachment_rows(tm2_name),
		"addenda": _addenda_rows(tm2_name, supplier, sup_code),
	}


def buildSupplierPortalDocumentsAddenda(
	tm2_name: str,
	supplier: str,
	_tender_code: str,
	tender_status: str,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`build_supplier_portal_documents_addenda`."""
	return build_supplier_portal_documents_addenda(tm2_name, supplier, _tender_code, tender_status)
