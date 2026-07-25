# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Section routes — FoT has a dedicated page; matrix for requirements_compliance; placeholders otherwise."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
	SECTION_KEY as CBQ_KEY,
	portal_cbq_url,
)
from kentender_procurement.tender_configurations.services.form_of_tender import SECTION_KEY as FOT_KEY
from kentender_procurement.tender_configurations.services.form_of_tender import portal_fot_url
from kentender_procurement.tender_configurations.services.requirement_matrix import (
	get_requirement_matrix,
	portal_section_url,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	portal_workspace_url,
)

no_cache = 1

MATRIX_KEYS = frozenset({"requirements_compliance", "technical_compliance_matrix"})


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	section_key = cstr(frappe.form_dict.get("section_key") or "").strip()
	if not publication_ref or not section_key:
		raise frappe.DoesNotExistError(_("Section not found."))

	section_path = portal_section_url(publication_ref, section_key)
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(section_path, safe="")
		raise frappe.Redirect

	if section_key == FOT_KEY:
		frappe.local.flags.redirect_location = portal_fot_url(publication_ref)
		raise frappe.Redirect

	if section_key == CBQ_KEY:
		frappe.local.flags.redirect_location = portal_cbq_url(publication_ref)
		raise frappe.Redirect

	if section_key in MATRIX_KEYS:
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
		context.checklist = matrix
		context.matrix = matrix
		context.copyright_year = str(getdate().year)
		context.title = matrix.get("section_title") or _("Requirement Matrix")
		return context

	# Lean slice placeholder for sections not yet implemented.
	workspace = portal_workspace_url(publication_ref)
	placeholder = {
		"section_key": section_key,
		"section_title": section_key.replace("_", " ").title(),
		"message": _(
			"This section route is reserved for the published electronic STD template. "
			"Editable completion is not implemented in the Form of Tender lean slice."
		),
		"workspace_url": workspace,
		"published_tender_ref": publication_ref,
	}
	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "my_bids"
	context.active_ws = "checklist"
	context.checklist = placeholder
	context.matrix = None
	context.section_placeholder = placeholder
	context.copyright_year = str(getdate().year)
	context.title = placeholder["section_title"]
	return context
