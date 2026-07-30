# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Requirements Compliance workspace (Stitch 01 / 02)."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.requirement_matrix import (
	SECTION_KEY_RC,
	get_requirement_matrix,
	portal_requirements_compliance_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	if not publication_ref:
		raise frappe.DoesNotExistError(_("Tender not found."))

	path = portal_requirements_compliance_url(publication_ref)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(path, safe="")
		raise frappe.Redirect

	group = cstr(frappe.form_dict.get("group") or "").strip() or None
	q = cstr(frappe.form_dict.get("q") or "").strip() or None
	requirement_id = cstr(frappe.form_dict.get("requirement_id") or "").strip()
	matrix = get_requirement_matrix(
		publication_ref,
		SECTION_KEY_RC,
		group=group,
		q=q,
		page_size=50,
	)
	pub = cstr(matrix.get("published_tender_ref") or publication_ref)
	context.matrix = matrix
	context.open_requirement_id = requirement_id
	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.no_header = True
	context.no_footer = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	context.checklist = {
		"published_tender_ref": pub,
		"tender_title": cstr(matrix.get("tender_title") or ""),
		"workspace_url": matrix.get("workspace_url"),
		"bid_id": matrix.get("bid_id"),
		"overview_url": f"/tenders/{quote(pub, safe='')}",
	}
	context.copyright_year = str(getdate().year)
	context.title = matrix.get("section_title") or "Requirements Compliance"
	return context
