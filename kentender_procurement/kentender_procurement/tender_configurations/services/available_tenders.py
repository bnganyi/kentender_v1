# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A0 — Available Tenders public list (Website /tenders)."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlencode

import frappe
from frappe.utils import cstr, get_datetime, now_datetime

from kentender_procurement.tender_configurations.services.configuration_home import (
	build_configuration_context,
)
from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_DRAFT,
	STATUS_SEALED,
)
from kentender_procurement.tender_configurations.services.f1_publication_handoff import (
	PUBLICATION_DOCTYPE,
	PUBLICATION_STATUS_PUBLISHED,
	package_summary_dto,
)
from kentender_procurement.tender_configurations.services.publication_setup import (
	_activate_flag,
	_visibility,
	ensure_publication_ref,
)

CLOSING_SOON_HOURS = 72

STATUS_OPEN = "Open"
STATUS_CLOSING_SOON = "Closing Soon"
STATUS_CLARIFICATION_CLOSED = "Clarification Period Closed"
STATUS_CLOSED = "Closed"
STATUS_CANCELLED = "Cancelled"

ACTION_VIEW_TENDER = "View Tender"
ACTION_CONTINUE = "Continue Bid"
ACTION_VIEW_SUBMITTED = "View Submitted Bid"
ACTION_VIEW_NOTICE = "View Notice"

DEFAULT_PAGE_SIZE = 20


def _as_dt(value: Any):
	if not value:
		return None
	try:
		return get_datetime(value)
	except Exception:
		return None


def compute_public_status(
	*,
	publication_status: str,
	submission_deadline: Any,
	clarification_deadline: Any,
	now=None,
	closing_soon_hours: int = CLOSING_SOON_HOURS,
) -> str:
	"""Map internal publication + deadlines to bidder-facing public status."""
	status = cstr(publication_status or "").strip()
	if status in ("Cancelled", "Returned"):
		return STATUS_CANCELLED
	if status != PUBLICATION_STATUS_PUBLISHED:
		return STATUS_CANCELLED

	now = now or now_datetime()
	sub_dt = _as_dt(submission_deadline)
	clar_dt = _as_dt(clarification_deadline)

	if sub_dt and now > sub_dt:
		return STATUS_CLOSED

	if sub_dt:
		hours_left = (sub_dt - now).total_seconds() / 3600.0
		if 0 < hours_left <= float(closing_soon_hours):
			return STATUS_CLOSING_SOON

	if clar_dt and now > clar_dt and (not sub_dt or now <= sub_dt):
		return STATUS_CLARIFICATION_CLOSED

	return STATUS_OPEN


def format_time_remaining(submission_deadline: Any, now=None) -> str:
	now = now or now_datetime()
	sub_dt = _as_dt(submission_deadline)
	if not sub_dt:
		return "—"
	delta = sub_dt - now
	secs = int(delta.total_seconds())
	if secs <= 0:
		return "0d 00h 00m 00s"
	days, rem = divmod(secs, 86400)
	hours, rem = divmod(rem, 3600)
	mins, secs = divmod(rem, 60)
	return f"{days:02d}d {hours:02d}h {mins:02d}m {secs:02d}s"


def _bid_flags_for_user(configuration_id: str, user: str) -> dict[str, Any]:
	if not user or user == "Guest" or not configuration_id:
		return {"has_draft": False, "has_sealed": False, "bid_id": None}
	# PoC electronic bids are not yet org-scoped; match by configuration for the session.
	draft = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": configuration_id, "status": STATUS_DRAFT},
		"name",
	)
	sealed = frappe.db.get_value(
		"Electronic Bid Submission",
		{"configuration": configuration_id, "status": STATUS_SEALED},
		"name",
		order_by="sealed_at desc",
	)
	return {
		"has_draft": bool(draft),
		"has_sealed": bool(sealed),
		"bid_id": sealed or draft,
	}


def resolve_primary_action(
	*,
	public_status: str,
	is_guest: bool,
	has_draft: bool,
	has_sealed: bool,
) -> str:
	if public_status == STATUS_CANCELLED:
		return ACTION_VIEW_NOTICE
	if is_guest:
		return ACTION_VIEW_TENDER
	if has_sealed:
		return ACTION_VIEW_SUBMITTED
	if has_draft and public_status in (
		STATUS_OPEN,
		STATUS_CLOSING_SOON,
		STATUS_CLARIFICATION_CLOSED,
	):
		return ACTION_CONTINUE
	return ACTION_VIEW_TENDER


def _overview_url(publication_ref: str) -> str:
	"""Bidder-facing Published Tender Overview on the public Website portal."""
	return f"/tenders/{quote(publication_ref, safe='')}"


def _workspace_url(publication_ref: str) -> str:
	"""Bidder workspace home (A2 Submission Checklist) on the public Website portal."""
	return f"/tenders/{quote(publication_ref, safe='')}/workspace"


def _pdf_url(configuration_id: str) -> str:
	return (
		"/api/method/kentender_procurement.tender_configurations"
		".download_tender_configuration_document_preview_pdf"
		f"?configuration_id={quote(configuration_id, safe='')}"
	)


def _format_user_dt(value: Any) -> str:
	if not value:
		return "—"
	try:
		return frappe.utils.format_datetime(value)
	except Exception:
		return cstr(value)


def list_available_tenders(
	filters: dict[str, Any] | None = None,
	*,
	user: str | None = None,
	page: int = 1,
	page_size: int = DEFAULT_PAGE_SIZE,
) -> dict[str, Any]:
	"""Return public Available Tenders list DTO for Website /tenders."""
	filters = filters or {}
	user = user if user is not None else frappe.session.user
	is_guest = not user or user == "Guest"
	now = now_datetime()
	page = max(1, int(page or 1))
	page_size = max(1, min(100, int(page_size or DEFAULT_PAGE_SIZE)))

	q = cstr(filters.get("q") or "").strip().lower()
	status_filter = cstr(filters.get("status") or "").strip()
	entity_filter = cstr(filters.get("procuring_entity") or "").strip().lower()
	category_filter = cstr(filters.get("category") or "").strip().lower()
	std_filter = cstr(filters.get("std") or "").strip().lower()
	method_filter = cstr(filters.get("method") or "").strip().lower()

	rows = frappe.get_all(
		PUBLICATION_DOCTYPE,
		filters={"status": PUBLICATION_STATUS_PUBLISHED},
		fields=[
			"name",
			"publication_ref",
			"configuration",
			"configuration_ref",
			"confirmed_package",
			"status",
			"tender_notice",
			"clarification_deadline",
			"submission_deadline",
			"opening_datetime",
			"publication_datetime",
			"published_at",
			"activate_bidder_workspace",
			"bidder_workspace_activation",
			"bidder_visibility",
			"supplier_visibility",
		],
		order_by="published_at desc",
		limit=500,
	)

	# One public card per configuration — newest published record wins.
	seen_configs: set[str] = set()
	deduped = []
	for row in rows:
		cfg_key = cstr(row.configuration or "").strip()
		if not cfg_key or cfg_key in seen_configs:
			continue
		seen_configs.add(cfg_key)
		deduped.append(row)
	rows = deduped
	rows.sort(key=lambda r: cstr(r.submission_deadline or "9999"))

	tenders: list[dict[str, Any]] = []
	closing_soon_count = 0
	draft_bids = 0
	submitted_bids = 0

	for row in rows:
		if not _activate_flag(row):
			continue
		visibility = _visibility(row)
		# Bidder-visible: empty or registered/invited audiences (exclude explicit Off).
		if visibility and visibility.lower() in ("hidden", "none", "off", "internal only"):
			continue

		cfg_id = cstr(row.configuration or "").strip()
		if not cfg_id or not frappe.db.exists("Tender Configuration", cfg_id):
			continue
		cfg = frappe.get_doc("Tender Configuration", cfg_id)
		ctx = build_configuration_context(cfg)
		pub_ref = cstr(row.publication_ref or "").strip() or ensure_publication_ref(
			frappe.get_doc(PUBLICATION_DOCTYPE, row.name)
		)

		public_status = compute_public_status(
			publication_status=cstr(row.status),
			submission_deadline=row.submission_deadline,
			clarification_deadline=row.clarification_deadline,
			now=now,
		)
		if public_status == STATUS_CLOSING_SOON:
			closing_soon_count += 1

		# Default list excludes closed/cancelled unless filtered.
		if not status_filter:
			if public_status in (STATUS_CLOSED, STATUS_CANCELLED):
				continue
		elif status_filter.lower() != public_status.lower() and status_filter != public_status:
			# Allow short aliases from UI
			aliases = {
				"clarification closed": STATUS_CLARIFICATION_CLOSED,
				"clarification period closed": STATUS_CLARIFICATION_CLOSED,
			}
			wanted = aliases.get(status_filter.lower(), status_filter)
			if wanted != public_status:
				continue

		title = cstr(ctx.get("procurement_title") or cfg.tender_title or "")
		entity = cstr(ctx.get("procuring_entity_name") or "")
		method = cstr(ctx.get("procurement_method_label") or "")
		category = cstr(ctx.get("std_family_label") or getattr(cfg, "std_family_label", None) or "")
		std_label = cstr(
			ctx.get("standard_tender_document_label") or getattr(cfg, "std_document_label", None) or ""
		)
		scope = cstr(getattr(cfg, "short_scope_summary", None) or row.tender_notice or "")

		if q:
			hay = " ".join([title, pub_ref, entity, category, scope]).lower()
			if q not in hay:
				continue
		if entity_filter and entity_filter not in entity.lower():
			continue
		if category_filter and category_filter not in category.lower():
			continue
		if std_filter and std_filter not in std_label.lower():
			continue
		if method_filter and method_filter not in method.lower():
			continue

		bid = _bid_flags_for_user(cfg_id, user) if not is_guest else {
			"has_draft": False,
			"has_sealed": False,
			"bid_id": None,
		}
		if bid["has_draft"]:
			draft_bids += 1
		if bid["has_sealed"]:
			submitted_bids += 1

		primary = resolve_primary_action(
			public_status=public_status,
			is_guest=is_guest,
			has_draft=bool(bid["has_draft"]),
			has_sealed=bool(bid["has_sealed"]),
		)
		if primary == ACTION_CONTINUE:
			primary_url = _workspace_url(pub_ref)
		elif primary == ACTION_VIEW_SUBMITTED:
			primary_url = _workspace_url(pub_ref)
		else:
			primary_url = _overview_url(pub_ref)

		pkg = package_summary_dto(cstr(row.confirmed_package or "") or None)
		has_pdf = bool(pkg.get("has_pdf"))

		tenders.append(
			{
				"title": title,
				"tender_reference": pub_ref,
				"publication_id": row.name,
				"configuration_id": cfg_id,
				"procuring_entity": entity,
				"procurement_method": method,
				"procurement_category": category,
				"standard_tender_document": std_label,
				"published_datetime": _format_user_dt(row.published_at or row.publication_datetime),
				"clarification_deadline": _format_user_dt(row.clarification_deadline),
				"submission_deadline": _format_user_dt(row.submission_deadline),
				"submission_deadline_raw": cstr(row.submission_deadline or ""),
				"time_remaining_label": format_time_remaining(row.submission_deadline, now=now),
				"public_status": public_status,
				"scope_summary": scope,
				"primary_action_label": primary,
				"primary_action_url": primary_url,
				"view_document_url": _pdf_url(cfg_id) if has_pdf else "",
				"download_document_url": _pdf_url(cfg_id) if has_pdf else "",
				"clarifications_url": _overview_url(pub_ref) + "#clarifications",
				"has_document": 1 if has_pdf else 0,
			}
		)

	total = len(tenders)
	start = (page - 1) * page_size
	page_rows = tenders[start : start + page_size]
	total_pages = max(1, (total + page_size - 1) // page_size)

	return {
		"filters": {
			"q": cstr(filters.get("q") or ""),
			"procuring_entity": cstr(filters.get("procuring_entity") or ""),
			"category": cstr(filters.get("category") or ""),
			"std": cstr(filters.get("std") or ""),
			"method": cstr(filters.get("method") or ""),
			"status": status_filter,
			"deadline": cstr(filters.get("deadline") or ""),
			"page": page,
		},
		"tenders": page_rows,
		"counts": {
			"draft_bids": 0 if is_guest else draft_bids,
			"submitted_bids": 0 if is_guest else submitted_bids,
			"closing_soon": closing_soon_count,
			"result_total": total,
		},
		"pagination": {
			"page": page,
			"page_size": page_size,
			"total": total,
			"total_pages": total_pages,
			"has_prev": page > 1,
			"has_next": page < total_pages,
		},
		"is_guest": 1 if is_guest else 0,
		"login_url": "/login?redirect-to=/tenders",
	}


def build_filter_query(filters: dict[str, Any], *, page: int | None = None) -> str:
	params = {}
	for key in ("q", "procuring_entity", "category", "std", "method", "status", "deadline"):
		val = cstr(filters.get(key) or "").strip()
		if val:
			params[key] = val
	if page and page > 1:
		params["page"] = str(page)
	return ("?" + urlencode(params)) if params else ""
