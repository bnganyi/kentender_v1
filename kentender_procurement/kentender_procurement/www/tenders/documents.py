# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A3 Tender Documents & Addenda — Website at /tenders/<publication_ref>/documents."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
	get_tender_documents_addenda,
	portal_documents_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	if not publication_ref:
		raise frappe.DoesNotExistError(_("Published tender not found."))

	documents_path = portal_documents_url(publication_ref)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(documents_path, safe="")
		raise frappe.Redirect

	try:
		docs = get_tender_documents_addenda(publication_ref)
	except frappe.PermissionError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Published tender not found."))

	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "my_bids"
	context.active_ws = "prepare"
	# Sidebar include expects `checklist` shell fields (shared with A2).
	context.checklist = docs
	context.docs = docs
	context.copyright_year = str(getdate().year)
	context.title = _("Tender Documents & Addenda")
	return context
