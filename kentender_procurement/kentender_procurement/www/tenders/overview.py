# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A1 Published Tender Overview — public Website at /tenders/<publication_ref>."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, format_datetime, getdate

from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
	PUBLICATION_DOCTYPE,
	PUBLICATION_STATUS_PUBLISHED,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	_activate_flag,
	_visibility,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	get_published_tender_overview,
)

no_cache = 1


def _pdf_url(configuration_id: str) -> str:
	return (
		"/api/method/kentender_procurement.tender_configurations"
		".download_tender_configuration_document_preview_pdf"
		f"?configuration_id={quote(configuration_id, safe='')}"
	)


def _format_display_dt(value: Any) -> str:
	if not value:
		return "—"
	try:
		return format_datetime(value)
	except Exception:
		raw = cstr(value).strip()
		# Drop microsecond noise from raw ISO/DB strings.
		if "." in raw and " " in raw:
			raw = raw.split(".", 1)[0]
		return raw or "—"


def _publication_is_bidder_visible(publication_ref: str) -> bool:
	ref = cstr(publication_ref or "").strip()
	if not ref:
		return False
	name = frappe.db.get_value(PUBLICATION_DOCTYPE, {"publication_ref": ref}, "name")
	if not name and frappe.db.exists(PUBLICATION_DOCTYPE, ref):
		name = ref
	if not name:
		return False
	row = frappe.db.get_value(
		PUBLICATION_DOCTYPE,
		name,
		[
			"status",
			"activate_bidder_workspace",
			"bidder_workspace_activation",
			"bidder_visibility",
			"supplier_visibility",
		],
		as_dict=True,
	)
	if not row or cstr(row.status) != PUBLICATION_STATUS_PUBLISHED:
		return False
	if not _activate_flag(row):
		return False
	visibility = _visibility(row)
	if visibility and visibility.lower() in ("hidden", "none", "off", "internal only"):
		return False
	return True


def _documents_for_display(documents: list[dict[str, Any]], pdf_url: str) -> list[dict[str, Any]]:
	"""Prefer actionable package docs (design mock); fall back to full list if none."""
	enriched: list[dict[str, Any]] = []
	for doc in documents or []:
		row = dict(doc)
		if row.get("can_view") or row.get("can_download"):
			row["view_url"] = pdf_url
			row["download_url"] = pdf_url
		enriched.append(row)
	actionable = [d for d in enriched if d.get("can_view") or d.get("can_download")]
	return actionable or enriched


def get_context(context):
	frappe.local.no_cache = 1
	publication_ref = cstr(frappe.form_dict.get("publication_ref") or "").strip()
	if not publication_ref or not _publication_is_bidder_visible(publication_ref):
		raise frappe.DoesNotExistError(_("Published tender not found."))

	# Public portal may run as Guest — assemble the same DTO officers see on Desk A1.
	prev_ignore = getattr(frappe.flags, "ignore_permissions", False)
	frappe.flags.ignore_permissions = True
	try:
		overview = get_published_tender_overview(publication_ref)
	finally:
		frappe.flags.ignore_permissions = prev_ignore

	is_guest = frappe.session.user == "Guest"
	page_path = f"/tenders/{quote(overview['published_tender_ref'], safe='')}"
	login_url = "/login?redirect-to=" + quote(page_path, safe="")

	cfg_id = cstr(overview.get("configuration_id") or "")
	pdf_url = _pdf_url(cfg_id) if cfg_id else ""
	documents = _documents_for_display(overview.get("documents") or [], pdf_url)

	raw_dates = overview.get("dates") or {}
	dates_display = {
		"published_at": _format_display_dt(raw_dates.get("published_at")),
		"clarification_deadline": _format_display_dt(raw_dates.get("clarification_deadline")),
		"submission_deadline": _format_display_dt(raw_dates.get("submission_deadline")),
		"opening_datetime": _format_display_dt(raw_dates.get("opening_datetime")),
	}

	workspace_route = cstr(overview.get("bidder_workspace_route") or "")
	if workspace_route.startswith("/"):
		workspace_url = workspace_route
	elif workspace_route:
		workspace_url = f"/app/{workspace_route}"
	else:
		workspace_url = ""

	context.no_cache = 1
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "tenders"
	context.overview = overview
	context.documents = documents
	context.dates_display = dates_display
	context.is_guest = is_guest
	context.login_url = login_url
	context.page_path = page_path
	context.workspace_url = workspace_url
	context.pdf_url = pdf_url
	context.copyright_year = str(getdate().year)
	context.title = overview.get("tender_title") or _("Published Tender")
	return context
