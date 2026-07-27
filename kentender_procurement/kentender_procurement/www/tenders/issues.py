# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""X100 Issues Register — Website at /tenders/<publication_ref>/issues."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.bid_evidence import portal_evidence_url
from kentender_procurement.tender_configurations.services.bid_issues import (
	get_issue_register,
	portal_issues_url,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	portal_workspace_url,
)
from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
	portal_documents_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	if not publication_ref:
		raise frappe.DoesNotExistError(_("Published tender not found."))

	issues_path = portal_issues_url(publication_ref)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(issues_path, safe="")
		raise frappe.Redirect

	try:
		register = get_issue_register(publication_ref)
	except frappe.PermissionError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Published tender not found."))

	shell = {
		"published_tender_ref": register.get("published_tender_ref"),
		"tender_title": register.get("tender_title"),
		"workspace_url": register.get("workspace_url") or portal_workspace_url(publication_ref),
		"documents_url": register.get("documents_url") or portal_documents_url(publication_ref),
		"overview_url": register.get("overview_url") or f"/tenders/{quote(publication_ref, safe='')}",
		"evidence_url": register.get("evidence_url") or portal_evidence_url(publication_ref),
		"issues_url": register.get("issues_url") or issues_path,
	}

	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	context.checklist = shell
	context.register = register
	context.copyright_year = str(getdate().year)
	context.title = _("Issues")
	return context
