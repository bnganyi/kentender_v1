# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A4 Requirement Matrix — Website at /tenders/<publication_ref>/sections/<section_key>."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.requirement_matrix import (
	get_requirement_matrix,
	portal_section_url,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	section_key = cstr(frappe.form_dict.get("section_key") or "").strip()
	if not publication_ref or not section_key:
		raise frappe.DoesNotExistError(_("Requirement matrix section not found."))

	section_path = portal_section_url(publication_ref, section_key)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(section_path, safe="")
		raise frappe.Redirect

	try:
		matrix = get_requirement_matrix(publication_ref, section_key)
	except frappe.PermissionError:
		raise
	except frappe.DoesNotExistError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Requirement matrix section not found."))

	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	# Shared sidebar include expects checklist-shaped shell fields.
	context.checklist = matrix
	context.matrix = matrix
	context.copyright_year = str(getdate().year)
	context.title = matrix.get("section_title") or _("Requirement Matrix")
	return context
