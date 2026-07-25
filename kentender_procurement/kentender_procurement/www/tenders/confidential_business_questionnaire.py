# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""S300 CBQ — Website at /tenders/<publication_ref>/sections/confidential_business_questionnaire."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
	get_confidential_business_questionnaire,
	portal_cbq_url,
)
from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
	portal_documents_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	if not publication_ref:
		raise frappe.DoesNotExistError(_("Confidential Business Questionnaire not found."))

	cbq_path = portal_cbq_url(publication_ref)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(cbq_path, safe="")
		raise frappe.Redirect

	try:
		cbq = get_confidential_business_questionnaire(publication_ref)
	except frappe.PermissionError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Confidential Business Questionnaire not found."))

	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	context.checklist = {
		"published_tender_ref": cbq.get("published_tender_ref"),
		"tender_title": cbq.get("tender_title") or "",
		"workspace_url": cbq.get("workspace_url"),
		"documents_url": portal_documents_url(publication_ref),
		"overview_url": f"/tenders/{quote(publication_ref, safe='')}",
		"bid_id": cbq.get("bid_id"),
	}
	context.cbq = cbq
	context.copyright_year = str(getdate().year)
	context.title = cbq.get("section_title") or _("Confidential Business Questionnaire")
	return context
