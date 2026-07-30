# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Submit Bid — Final Submission Stitch 03/04."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.tender_configurations.services.final_submission import (
	get_submit_bid_page,
	portal_final_bid_review_url,
	portal_submission_receipt_url,
	portal_submit_bid_url,
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
	redirect_guest(portal_submit_bid_url(publication_ref))
	try:
		page = get_submit_bid_page(publication_ref)
	except frappe.PermissionError:
		raise
	except frappe.ValidationError as exc:
		msg = str(exc)
		if "already been submitted" in msg.lower():
			frappe.local.flags.redirect_location = portal_submission_receipt_url(publication_ref)
		else:
			frappe.local.flags.redirect_location = portal_final_bid_review_url(publication_ref)
		raise frappe.Redirect
	except Exception:
		raise frappe.DoesNotExistError(_("Submit Bid is not available."))

	from kentender_procurement.tender_configurations.services.final_submission import (
		get_bid_submission_readiness,
	)

	ready = get_bid_submission_readiness(publication_ref)
	apply_shell_context(context, active_ws="submit", title=_("Submit Bid"))
	context.checklist = checklist_shell_for_readiness(ready)
	context.page = page
	return context
