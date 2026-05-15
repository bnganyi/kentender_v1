# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Website controller for doc 9 §18.1 supplier tender routes (P10-01) + §18.2 list (P10-02) + §18.3 detail (P10-03) + §18.7 submit modal (P10-07) + §18.8 late submission (P10-08)."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.tender_management.services.supplier_portal_tender_detail import (
	get_supplier_portal_tender_detail,
)
from kentender_procurement.tender_management.services.supplier_portal_tender_list import (
	list_supplier_portal_tenders,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	if frappe.session.user == "Guest":
		req = getattr(frappe.local, "request", None)
		raw = getattr(req, "path", None) if req else None
		if not raw:
			raw = "/supplier/tenders"
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(raw, safe="")
		raise frappe.Redirect

	tender_code = cstr(frappe.form_dict.get("tender_code") or "").strip()
	context.tm2_supplier_tender_code = tender_code
	context.title = _("Supplier tenders") if not tender_code else _("Tender {0}").format(tender_code)
	if not tender_code:
		lst = list_supplier_portal_tenders(frappe.session.user)
		context.tm2_supplier_tender_rows = lst.get("items") or []
		context.tm2_supplier_portal_message = lst.get("message")
		context.tm2_supplier_detail = None
	else:
		context.tm2_supplier_tender_rows = []
		context.tm2_supplier_portal_message = None
		detail = get_supplier_portal_tender_detail(frappe.session.user, tender_code)
		context.tm2_supplier_detail = detail
		if detail.get("ok"):
			context.title = cstr(detail.get("header_line") or tender_code)
	return context
