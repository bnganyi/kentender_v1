# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §18.3–§18.4 — supplier portal tender detail (metadata, deadlines, documents).

Uses the same **KTSM Supplier Profile** → ``Supplier`` resolution and
``check_supplier_tender_access`` gate as :mod:`supplier_portal_tender_list`.

Timeline labels reuse :func:`~kentender_procurement.tender_management.services.tm2_workbench_tender_detail._timeline_bits`.
§18.4 documents/addenda via :func:`~kentender_procurement.tender_management.services.supplier_portal_documents_addenda.build_supplier_portal_documents_addenda`.
§18.5 submission checklist via :func:`~kentender_procurement.tender_management.services.supplier_portal_submission_checklist.build_supplier_portal_submission_checklist`.

Canonical doc 9 §25 **EX-05** (checklist from DSM only): ``test_EX_05_*`` in
``kentender_procurement.tender_management.tests.test_p10_05_supplier_portal_submission_checklist``.
**EX-18** (DSM + BOQ locks on portal): ``test_EX_18_*`` in ``test_p10_06_supplier_portal_works_boq``.
§18.6 Works BOQ via :func:`~kentender_procurement.tender_management.services.supplier_portal_works_boq.build_supplier_portal_works_boq`.
§18.7–§18.8 Submit bid + late submission hints via :func:`~kentender_procurement.tender_management.services.supplier_portal_submit_bid_panel.build_supplier_portal_submit_bid_panel`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, format_datetime, get_datetime, now_datetime

from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	check_supplier_tender_access,
)
from kentender_procurement.tender_management.services.supplier_portal_tender_list import (
	resolve_erpnext_supplier_for_portal_user,
)
from kentender_procurement.tender_management.services.supplier_portal_documents_addenda import (
	build_supplier_portal_documents_addenda,
)
from kentender_procurement.tender_management.services.supplier_portal_submission_checklist import (
	build_supplier_portal_submission_checklist,
)
from kentender_procurement.tender_management.services.supplier_portal_works_boq import (
	build_supplier_portal_works_boq,
)
from kentender_procurement.tender_management.services.supplier_portal_submit_bid_panel import (
	build_supplier_portal_submit_bid_panel,
)
from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import _timeline_bits


def _format_time_remaining(deadline: datetime | None, *, now: datetime | None = None) -> str:
	if not deadline:
		return ""
	now_dt = now or now_datetime()
	dl = get_datetime(deadline) if not isinstance(deadline, datetime) else deadline
	if dl <= now_dt:
		return str(_("Deadline passed"))
	delta = dl - now_dt
	total = int(delta.total_seconds())
	if total <= 0:
		return str(_("Deadline passed"))
	days, rem = divmod(total, 86400)
	hours, rem = divmod(rem, 3600)
	mins = rem // 60
	if days:
		return str(_("{0}d {1}h {2}m").format(days, hours, mins))
	if hours:
		return str(_("{0}h {1}m").format(hours, mins))
	return str(_("{0}m").format(max(mins, 1)))


def _server_time_display(timezone: str) -> str:
	from frappe.utils.data import get_datetime_in_timezone, get_system_timezone

	tz = cstr(timezone or "").strip() or get_system_timezone()
	try:
		local_now = get_datetime_in_timezone(tz)
	except Exception:
		local_now = now_datetime()
	return f"{format_datetime(local_now)} {tz}"


def get_supplier_portal_tender_detail(actor: str, tender_code: str) -> dict[str, Any]:
	"""Return §18.3–§18.8 portal payload (header, documents, checklist, Works BOQ, submit + late notice) or ``ok`` false when denied."""
	tc = cstr(tender_code or "").strip()
	if not tc:
		return {"ok": False, "message": _("Tender code is required.")}

	supplier = resolve_erpnext_supplier_for_portal_user(actor)
	if not supplier:
		return {"ok": False, "message": _("No supplier profile is linked to this account.")}

	gate = check_supplier_tender_access(actor, tc, supplier, context={})
	if not gate.get("ok"):
		return {
			"ok": False,
			"message": cstr(gate.get("message") or "").strip() or _("This tender is not available."),
		}

	tm2_name = cstr(gate.get("tm2_tender") or "").strip()
	if not tm2_name:
		return {"ok": False, "message": _("This tender is not available.")}

	trow = frappe.db.get_value(
		"TM2 Tender",
		tm2_name,
		[
			"tender_code",
			"tender_title",
			"procuring_entity_code",
			"procurement_method",
			"procurement_category",
			"status",
		],
		as_dict=True,
	)
	if not trow:
		return {"ok": False, "message": _("This tender is not available.")}

	tcode = cstr(trow.get("tender_code") or tc).strip() or tc
	title = cstr(trow.get("tender_title") or "").strip()
	entity = cstr(trow.get("procuring_entity_code") or "").strip()
	method = cstr(trow.get("procurement_method") or "").strip()
	category = cstr(trow.get("procurement_category") or "").strip()
	status = cstr(trow.get("status") or "").strip()

	_deadline_at, tz, deadline_label = _timeline_bits(tm2_name)
	deadline_raw = frappe.db.get_value(
		"TM2 Tender Timeline",
		{"tm2_tender": tm2_name},
		"submission_deadline_at",
	)
	remaining = _format_time_remaining(deadline_raw)
	server_time = _server_time_display(tz)
	documents_addenda = build_supplier_portal_documents_addenda(
		tm2_name,
		supplier,
		tcode,
		status,
	)
	submission_checklist = build_supplier_portal_submission_checklist(tm2_name, supplier)
	works_boq = build_supplier_portal_works_boq(tm2_name, supplier, category)
	submit_bid_panel = build_supplier_portal_submit_bid_panel(
		tm2_name,
		supplier,
		tcode,
		submission_checklist,
		deadline_raw,
		server_time_display=server_time,
		submission_deadline_display=deadline_label or "",
	)

	return {
		"ok": True,
		"tender_code": tcode,
		"tender_title": title,
		"procuring_entity_code": entity,
		"procurement_method": method,
		"procurement_category": category,
		"tender_status": status,
		"header_line": f"{tcode} · {title}" if title else tcode,
		"subheader_line": " · ".join(p for p in (entity, method, category) if p),
		"server_time_display": server_time,
		"submission_deadline_display": deadline_label or "",
		"time_remaining_display": remaining,
		"timeline_timezone": tz,
		"submission_deadline_at": deadline_raw,
		"documents_addenda": documents_addenda,
		"submission_checklist": submission_checklist,
		"works_boq": works_boq,
		"submit_bid_panel": submit_bid_panel,
	}


def getSupplierPortalTenderDetail(actor: str, tender_code: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`get_supplier_portal_tender_detail`."""
	return get_supplier_portal_tender_detail(actor, tender_code)
