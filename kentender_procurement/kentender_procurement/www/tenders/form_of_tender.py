# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Form of Tender — Website at /tenders/<publication_ref>/sections/form_of_tender."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.form_of_tender import (
	get_form_of_tender,
	portal_fot_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	if not publication_ref:
		raise frappe.DoesNotExistError(_("Form of Tender not found."))

	fot_path = portal_fot_url(publication_ref)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(fot_path, safe="")
		raise frappe.Redirect

	try:
		fot = get_form_of_tender(publication_ref)
	except frappe.PermissionError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Form of Tender not found."))

	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	# Sidebar include expects checklist-shaped fields for tender chrome.
	context.checklist = {
		"published_tender_ref": fot.get("published_tender_ref"),
		"tender_title": (fot.get("tender_owned_values") or {}).get("tender_name_and_identification")
		or "",
		"workspace_url": fot.get("workspace_url"),
		"bid_id": fot.get("bid_id"),
	}
	context.fot = fot
	context.copyright_year = str(getdate().year)
	context.title = fot.get("section_title") or _("Form of Tender")
	return context
