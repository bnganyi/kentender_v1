# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Requirements Compliance review (Stitch 03)."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.requirement_matrix import (
	get_requirements_compliance_review,
	portal_requirements_compliance_review_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	if not publication_ref:
		raise frappe.DoesNotExistError(_("Tender not found."))

	path = portal_requirements_compliance_review_url(publication_ref)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(path, safe="")
		raise frappe.Redirect

	review = get_requirements_compliance_review(publication_ref)
	pub = cstr(review.get("published_tender_ref") or publication_ref)
	context.review = review
	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.no_header = True
	context.no_footer = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	context.checklist = {
		"published_tender_ref": pub,
		"tender_title": cstr(review.get("tender_title") or ""),
		"workspace_url": review.get("workspace_url"),
		"bid_id": review.get("bid_id"),
		"overview_url": f"/tenders/{quote(pub, safe='')}",
	}
	context.copyright_year = str(getdate().year)
	context.title = review.get("page_title") or "Review Requirements Compliance"
	return context
