# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Submission Receipt — Final Submission Stitch 05."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.tender_configurations.services.final_submission import (
	get_submission_receipt,
	portal_submission_receipt_url,
	portal_workspace_url,
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
	redirect_guest(portal_submission_receipt_url(publication_ref))
	try:
		receipt = get_submission_receipt(publication_ref)
	except frappe.PermissionError:
		raise
	except frappe.ValidationError:
		frappe.local.flags.redirect_location = portal_workspace_url(publication_ref)
		raise frappe.Redirect
	except Exception:
		raise frappe.DoesNotExistError(_("Submission receipt is not available."))

	from kentender_procurement.tender_configurations.services.final_submission import (
		get_bid_submission_readiness,
	)

	ready = get_bid_submission_readiness(publication_ref)
	apply_shell_context(context, active_ws="submit", title=_("Submission Receipt"))
	context.checklist = checklist_shell_for_readiness(ready)
	context.receipt = receipt
	return context
