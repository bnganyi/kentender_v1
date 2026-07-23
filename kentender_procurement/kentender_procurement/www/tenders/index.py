# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A0 Available Tenders — public Website landing at /tenders."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, cstr, getdate

from kentender_procurement.tender_configurations.services.available_tenders import (
	build_filter_query,
	list_available_tenders,
)

no_cache = 1

STATUS_BUTTONS = [
	{"value": "Open", "label": "Open"},
	{"value": "Closing Soon", "label": "Closing Soon"},
	{"value": "Clarification Period Closed", "label": "Clarification Closed"},
	{"value": "Closed", "label": "Closed"},
	{"value": "Cancelled", "label": "Cancelled"},
]


def get_context(context):
	frappe.local.no_cache = 1
	form = frappe.form_dict or {}
	filters = {
		"q": cstr(form.get("q") or ""),
		"procuring_entity": cstr(form.get("procuring_entity") or ""),
		"category": cstr(form.get("category") or ""),
		"std": cstr(form.get("std") or ""),
		"method": cstr(form.get("method") or ""),
		"status": cstr(form.get("status") or ""),
		"deadline": cstr(form.get("deadline") or ""),
	}
	page = max(1, cint(form.get("page") or 1))
	payload = list_available_tenders(filters, user=frappe.session.user, page=page)
	active_filters = payload["filters"]

	status_buttons = []
	for btn in STATUS_BUTTONS:
		f = dict(active_filters)
		f["status"] = btn["value"]
		status_buttons.append(
			{
				"value": btn["value"],
				"label": _(btn["label"]),
				"url": "/tenders" + build_filter_query(f),
				"active": cstr(active_filters.get("status") or "") == btn["value"]
				or (not active_filters.get("status") and btn["value"] == "Open"),
			}
		)

	context.no_cache = 1
	context.title = _("Available Tenders")
	context.show_sidebar = False
	context.full_width = True
	context.active_nav = "tenders"
	context.filters = active_filters
	context.tenders = payload["tenders"]
	context.counts = payload["counts"]
	context.pagination = payload["pagination"]
	context.is_guest = payload["is_guest"]
	context.login_url = payload["login_url"]
	context.filter_query = build_filter_query(active_filters)
	context.prev_url = (
		"/tenders" + build_filter_query(active_filters, page=page - 1) if payload["pagination"]["has_prev"] else ""
	)
	context.next_url = (
		"/tenders" + build_filter_query(active_filters, page=page + 1) if payload["pagination"]["has_next"] else ""
	)
	context.status_buttons = status_buttons
	context.copyright_year = str(getdate().year)
	return context
