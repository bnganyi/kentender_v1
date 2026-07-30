# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Technical Proposal subsection detail —
/tenders/<publication_ref>/sections/technical_proposal_and_implementation_plan/<subsection_key>."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.technical_proposal_and_implementation_plan import (
	get_technical_proposal_subsection,
	portal_technical_proposal_subsection_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	subsection_key = cstr(frappe.form_dict.get("subsection_key") or "").strip()
	if not publication_ref or not subsection_key:
		raise frappe.DoesNotExistError(_("Technical proposal subsection not found."))

	path = portal_technical_proposal_subsection_url(publication_ref, subsection_key)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(path, safe="")
		raise frappe.Redirect

	try:
		sub = get_technical_proposal_subsection(publication_ref, subsection_key)
	except frappe.PermissionError:
		raise
	except frappe.ValidationError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Technical proposal subsection not found."))

	pub = cstr(sub.get("published_tender_ref") or publication_ref)
	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	context.checklist = {
		"published_tender_ref": pub,
		"tender_title": cstr(sub.get("tender_title") or ""),
		"workspace_url": sub.get("workspace_url"),
		"bid_id": sub.get("bid_id"),
		"overview_url": f"/tenders/{quote(pub, safe='')}",
	}
	context.sub = sub
	context.copyright_year = str(getdate().year)
	context.title = sub.get("title") or _("Technical proposal subsection")
	return context
