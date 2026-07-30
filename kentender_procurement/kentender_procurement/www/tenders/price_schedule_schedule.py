# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Price Schedule editor — Stitch 02/03."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
	get_price_schedule_editor,
	portal_price_schedule_schedule_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	schedule_key = cstr(frappe.form_dict.get("schedule_key") or "").strip()
	if not publication_ref or not schedule_key:
		raise frappe.DoesNotExistError(_("Price schedule not found."))

	path = portal_price_schedule_schedule_url(publication_ref, schedule_key)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(path, safe="")
		raise frappe.Redirect

	offer_id = cstr(frappe.form_dict.get("offer_id") or "").strip() or None
	lot_id = cstr(frappe.form_dict.get("lot_id") or "").strip() or None
	try:
		ed = get_price_schedule_editor(
			publication_ref, schedule_key, offer_id=offer_id, lot_id=lot_id
		)
	except frappe.PermissionError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Price schedule not found."))

	pub = cstr(ed.get("published_tender_ref") or publication_ref)
	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.no_header = True
	context.no_footer = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	context.checklist = {
		"published_tender_ref": pub,
		"tender_title": cstr(ed.get("tender_title") or ""),
		"workspace_url": ed.get("workspace_url"),
		"bid_id": ed.get("bid_id"),
		"overview_url": f"/tenders/{quote(pub, safe='')}",
	}
	context.ed = ed
	context.copyright_year = str(getdate().year)
	context.title = ed.get("schedule_title") or _("Price Schedule")
	return context
