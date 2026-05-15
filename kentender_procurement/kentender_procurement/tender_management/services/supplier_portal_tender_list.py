# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §18.2 — supplier portal tender list (allowed tenders only).

Resolves the logged-in **ERPNext Supplier** from **KTSM Supplier Profile** ``external_user``
when that DocType is installed; otherwise the portal cannot attribute a supplier identity
and returns an empty ``items`` list (no tender leakage).

Each candidate row comes from **TM2 Supplier Participation** for that supplier; tenders
that fail :func:`~kentender_procurement.tender_management.services.check_supplier_tender_access.check_supplier_tender_access`
are omitted.

Doc 9 §25 **EX-12** (doc 8 TM2-SMOKE-SEC-003): ``tender_management.tests.test_p10_02_supplier_portal_tender_list`` (``test_EX_12_*``).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, format_datetime

from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	check_supplier_tender_access,
)


def resolve_erpnext_supplier_for_portal_user(user: str) -> str | None:
	"""Return ``Supplier`` name for ``user`` when linked from KTSM Supplier Profile."""
	u = cstr(user or "").strip()
	if not u or u == "Guest":
		return None
	if not frappe.db.exists("DocType", "KTSM Supplier Profile"):
		return None
	rows = frappe.get_all(
		"KTSM Supplier Profile",
		filters={"external_user": u},
		fields=["erpnext_supplier"],
		limit=1,
	)
	if not rows:
		return None
	sup = cstr(rows[0].get("erpnext_supplier") or "").strip()
	if sup and frappe.db.exists("Supplier", sup):
		return sup
	return None


def _access_requirement_label(rule: dict[str, Any] | None) -> str:
	if not rule:
		return ""
	vis = cstr(rule.get("visibility") or "").strip()
	parts: list[str] = []
	if vis:
		parts.append(vis)
	if int(rule.get("requires_invitation") or 0):
		parts.append(_("Invitation required"))
	if int(rule.get("requires_supplier_login_for_documents") or 0):
		parts.append(_("Login required for documents"))
	if int(rule.get("eligibility_service_required") or 0):
		parts.append(_("Eligibility check required"))
	return " · ".join(parts) if parts else vis


def list_supplier_portal_tenders(actor: str) -> dict[str, Any]:
	"""Return §18.2 row DTOs for tenders this supplier may access (participation + §11.1 gate)."""
	supplier = resolve_erpnext_supplier_for_portal_user(actor)
	if not supplier:
		return {
			"ok": True,
			"items": [],
			"supplier": None,
			"message": _("No supplier profile is linked to this account."),
		}

	parts = frappe.get_all(
		"TM2 Supplier Participation",
		filters={"supplier": supplier},
		fields=["tender_code", "tm2_tender"],
		order_by="modified desc",
		limit=500,
	)
	ordered_codes: list[str] = []
	seen: set[str] = set()
	for p in parts or []:
		tc = cstr(p.get("tender_code") or "").strip()
		if not tc or tc in seen:
			continue
		seen.add(tc)
		ordered_codes.append(tc)

	items: list[dict[str, Any]] = []
	for tc in ordered_codes:
		gate = check_supplier_tender_access(actor, tc, supplier, context={})
		if not gate.get("ok"):
			continue
		tm2_name = cstr(gate.get("tm2_tender") or "").strip()
		if not tm2_name:
			continue
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
			continue
		rule = frappe.db.get_value(
			"TM2 Tender Access Rule",
			{"tm2_tender": tm2_name},
			[
				"visibility",
				"requires_invitation",
				"requires_supplier_login_for_documents",
				"eligibility_service_required",
			],
			as_dict=True,
		)
		deadline = frappe.db.get_value(
			"TM2 Tender Timeline",
			{"tender_code": tc},
			"submission_deadline_at",
		)
		deadline_disp = format_datetime(deadline) if deadline else ""
		items.append(
			{
				"tender_code": cstr(trow.get("tender_code") or tc).strip() or tc,
				"tender_title": cstr(trow.get("tender_title") or "").strip(),
				"procuring_entity_code": cstr(trow.get("procuring_entity_code") or "").strip(),
				"procurement_method": cstr(trow.get("procurement_method") or "").strip(),
				"procurement_category": cstr(trow.get("procurement_category") or "").strip(),
				"tender_status": cstr(trow.get("status") or "").strip(),
				"submission_deadline_at": deadline,
				"submission_deadline_display": deadline_disp,
				"access_requirement": _access_requirement_label(rule or {}),
			}
		)

	return {"ok": True, "items": items, "supplier": supplier, "message": None}


def listSupplierPortalTenders(actor: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`list_supplier_portal_tenders`."""
	return list_supplier_portal_tenders(actor)
