# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Technical Proposal overview — /tenders/<publication_ref>/sections/technical_proposal_and_implementation_plan."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.technical_proposal_and_implementation_plan import (
	get_technical_proposal,
	portal_technical_proposal_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	if not publication_ref:
		raise frappe.DoesNotExistError(_("Technical Proposal and Implementation Plan not found."))

	path = portal_technical_proposal_url(publication_ref)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(path, safe="")
		raise frappe.Redirect

	try:
		sec = get_technical_proposal(publication_ref)
	except frappe.PermissionError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Technical Proposal and Implementation Plan not found."))

	pub = cstr(sec.get("published_tender_ref") or publication_ref)
	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	context.checklist = {
		"published_tender_ref": pub,
		"tender_title": cstr(sec.get("tender_title") or ""),
		"workspace_url": sec.get("workspace_url"),
		"bid_id": sec.get("bid_id"),
		"overview_url": f"/tenders/{quote(pub, safe='')}",
	}
	context.sec = sec
	context.copyright_year = str(getdate().year)
	context.title = sec.get("section_title") or _("Technical Proposal and Implementation Plan")
	return context
