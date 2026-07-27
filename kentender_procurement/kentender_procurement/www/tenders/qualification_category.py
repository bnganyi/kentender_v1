# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Qualification category detail — /tenders/<ref>/sections/qualification_and_capability/<category_key>."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.qualification_and_capability import (
	CATEGORY_KEYS,
	get_qualification_category,
	portal_qualification_category_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	category_key = cstr(frappe.form_dict.get("category_key") or "").strip()
	if not publication_ref or category_key not in CATEGORY_KEYS:
		raise frappe.DoesNotExistError(_("Qualification category not found."))

	path = portal_qualification_category_url(publication_ref, category_key)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(path, safe="")
		raise frappe.Redirect

	try:
		cat = get_qualification_category(publication_ref, category_key)
	except frappe.PermissionError:
		raise
	except frappe.ValidationError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Qualification category not found."))

	pub = cstr(cat.get("published_tender_ref") or publication_ref)
	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	context.checklist = {
		"published_tender_ref": pub,
		"tender_title": cstr(cat.get("tender_title") or ""),
		"workspace_url": cat.get("workspace_url"),
		"bid_id": cat.get("bid_id"),
		"overview_url": f"/tenders/{quote(pub, safe='')}",
	}
	context.cat = cat
	context.copyright_year = str(getdate().year)
	context.title = cat.get("label") or _("Qualification category")
	return context
