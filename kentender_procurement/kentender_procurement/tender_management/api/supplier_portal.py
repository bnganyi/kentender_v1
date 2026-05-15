# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Supplier portal whitelisted APIs (doc 9 §18)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_management.services.supplier_portal_submit_bid import (
	submit_supplier_portal_bid as submit_supplier_portal_bid_service,
)

from kentender_procurement.tender_management.services.supplier_portal_tender_detail import (
	get_supplier_portal_tender_detail as get_supplier_portal_tender_detail_service,
)
from kentender_procurement.tender_management.services.supplier_portal_tender_list import (
	list_supplier_portal_tenders as list_supplier_portal_tenders_service,
)


@frappe.whitelist()
def list_supplier_portal_tenders() -> dict[str, Any]:
	"""P10-02 — doc 9 §18.2 tender list for the current portal user (allowed tenders only)."""
	return list_supplier_portal_tenders_service(frappe.session.user)


@frappe.whitelist()
def get_supplier_portal_tender_detail(tender_code: str | None = None) -> dict[str, Any]:
	"""P10-03 … P10-08 — doc 9 §18.3–§18.8 tender detail (metadata, deadlines, bundle, addenda, checklist, Works BOQ, submit panel, late submission notice)."""
	return get_supplier_portal_tender_detail_service(frappe.session.user, tender_code or "")


def _parse_bid_payload_arg(raw: Any) -> dict[str, Any]:
	if raw is None:
		return {}
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			p = frappe.parse_json(raw)
			return p if isinstance(p, dict) else {}
		except Exception:
			return {}
	return {}


@frappe.whitelist()
def submit_supplier_portal_bid(tender_code: str | None = None, bid_payload: Any = None) -> dict[str, Any]:
	"""P10-07 — doc 9 §18.7 sealed bid submission for the logged-in portal supplier."""
	tc = cstr(tender_code or "").strip()
	payload = _parse_bid_payload_arg(bid_payload)
	return submit_supplier_portal_bid_service(frappe.session.user, tc, payload)
