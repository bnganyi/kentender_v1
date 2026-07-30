# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared Website context helpers for Final Submission screens."""

from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, getdate

from kentender_procurement.tender_configurations.services.final_submission import (
	portal_review_and_validate_url,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	get_submission_checklist,
	portal_workspace_url,
)


def require_publication_ref() -> str:
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	if not publication_ref:
		raise frappe.DoesNotExistError(_("Published tender not found."))
	return publication_ref


def redirect_guest(path: str) -> None:
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(path, safe="")
		raise frappe.Redirect


def checklist_shell_for_readiness(ready: dict) -> dict:
	"""Sidebar/nav fields from readiness (+ documents URL from checklist when available)."""
	pub = cstr(ready.get("published_tender_ref") or "")
	docs_url = ""
	try:
		cl = get_submission_checklist(pub)
		docs_url = cstr(cl.get("documents_url") or "")
	except Exception:
		docs_url = f"/tenders/{quote(pub, safe='')}/documents" if pub else ""
	return {
		"published_tender_ref": pub,
		"tender_title": ready.get("tender_title") or "",
		"workspace_url": ready.get("workspace_url") or portal_workspace_url(pub),
		"bid_id": ready.get("bid_id"),
		"overview_url": ready.get("overview_url") or f"/tenders/{quote(pub, safe='')}",
		"documents_url": docs_url,
		"review_nav_enabled": ready.get("review_nav_enabled") or 0,
		"review_nav_url": ready.get("review_and_validate_url")
		or portal_review_and_validate_url(pub),
		"submit_nav_enabled": ready.get("submit_nav_enabled") or 0,
		"submit_nav_url": ready.get("submit_bid_url")
		if ready.get("overall_state") != "Submitted"
		else ready.get("submission_receipt_url"),
		"evidence_url": f"/tenders/{quote(pub, safe='')}/evidence" if pub else "#",
		"issues_url": f"/tenders/{quote(pub, safe='')}/issues" if pub else "#",
	}


def apply_shell_context(context, *, active_ws: str, title: str) -> None:
	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.no_header = True
	context.no_footer = True
	context.active_nav = "my_bids"
	context.active_ws = active_ws
	context.copyright_year = str(getdate().year)
	context.title = title
