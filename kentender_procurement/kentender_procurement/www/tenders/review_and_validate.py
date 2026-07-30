# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Review & Validate — Final Submission Stitch 01."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.tender_configurations.services.final_submission import (
	get_bid_submission_readiness,
	portal_review_and_validate_url,
)
from kentender_procurement.www.tenders._final_submission_context import (
	apply_shell_context,
	checklist_shell_for_readiness,
	redirect_guest,
	require_publication_ref,
)

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = require_publication_ref()
	redirect_guest(portal_review_and_validate_url(publication_ref))
	try:
		ready = get_bid_submission_readiness(publication_ref)
	except frappe.PermissionError:
		raise
	except Exception:
		raise frappe.DoesNotExistError(_("Review & Validate is not available."))

	apply_shell_context(context, active_ws="review", title=_("Review & Validate"))
	context.checklist = checklist_shell_for_readiness(ready)
	context.ready = ready
	return context
