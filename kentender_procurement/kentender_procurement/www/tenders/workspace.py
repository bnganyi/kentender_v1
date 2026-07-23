# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A2 Submission Checklist — Website workspace home at /tenders/<publication_ref>/workspace."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.submission_checklist import (
	get_submission_checklist,
	portal_workspace_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	if not publication_ref:
		raise frappe.DoesNotExistError(_("Published tender not found."))

	workspace_path = portal_workspace_url(publication_ref)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(workspace_path, safe="")
		raise frappe.Redirect

	try:
		checklist = get_submission_checklist(publication_ref)
	except frappe.PermissionError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Published tender not found."))

	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	context.checklist = checklist
	context.copyright_year = str(getdate().year)
	context.title = _("Submission Checklist")
	return context
