# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-06 / **P9-23** — TM2 workbench tender list rows (doc 9 §14.8, **§19.1**; doc 6 §10).

Returns permission-scoped list rows keyed by business codes (no internal PK in UI fields).
**§19.1** adds top-level ``counts`` (queue bucket totals, snake_case keys) and per-row
``current_action_label`` aligned with the active ``queue`` filter.

Tests: ``tender_management.tests.test_p9_06_workbench_tender_list``,
``tender_management.tests.test_p9_23_workbench_list_api_section_19_1``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import add_to_date, cstr, format_datetime, get_datetime, now_datetime

from kentender_procurement.tender_management.services.tm2_workbench_kpis import (
	_CLAR_PENDING,
	get_workbench_kpi_counts as get_workbench_kpi_counts_service,
)
from kentender_procurement.tender_management.services.tm2_workbench_terminology import (
	business_label_for_queue_slug,
	business_label_for_readiness_status,
	business_label_for_tender_status,
	business_readiness_short_label,
)

_ACTIVE = {"is_active": 1}

_VALID_QUEUE_SLUGS = frozenset(
	{
		"draft",
		"std-incomplete",
		"ready-review",
		"returned",
		"approved",
		"published",
		"clarifications",
		"addenda",
		"closing-soon",
		"closed",
		"opening-ready",
		"evaluation-ready",
		"cancelled",
	}
)


def _tender_name_filters_for_queue(slug: str | None) -> dict[str, Any] | None:
	"""Restrict by ``name`` for queues that are not a single status filter."""
	if not slug or slug not in _VALID_QUEUE_SLUGS:
		return None

	if slug == "clarifications":
		parents = frappe.get_list(
			"TM2 Clarification Request",
			filters={"status": ["in", list(_CLAR_PENDING)]},
			pluck="tm2_tender",
			limit=10_000,
		) or []
		uniq = list(dict.fromkeys([p for p in parents if p]))
		if not uniq:
			return {"name": "__no_such_tm2__"}
		return {"name": ["in", uniq]}

	if slug == "closing-soon":
		published = frappe.get_list(
			"TM2 Tender",
			filters={**_ACTIVE, "status": "Published"},
			pluck="name",
			limit=10_000,
		) or []
		now = now_datetime()
		soon = add_to_date(now, days=7, as_datetime=True)
		if not published:
			return {"name": "__no_such_tm2__"}
		tl_rows = frappe.get_all(
			"TM2 Tender Timeline",
			filters={
				"tm2_tender": ["in", published],
				"submission_deadline_at": ["between", [now, soon]],
			},
			pluck="tm2_tender",
			limit=10_000,
		)
		uniq = list(dict.fromkeys(tl_rows or []))
		if not uniq:
			return {"name": "__no_such_tm2__"}
		return {"name": ["in", uniq]}

	if slug == "closed":
		names = frappe.get_list(
			"TM2 Tender",
			filters={"status": ["in", ["Closed", "Closed - No Valid Submissions"]]},
			pluck="name",
			limit=10_000,
		) or []
		if not names:
			return {"name": "__no_such_tm2__"}
		return {"name": ["in", names]}

	if slug == "cancelled":
		names = frappe.get_list("TM2 Tender", filters={"status": "Cancelled"}, pluck="name", limit=10_000) or []
		if not names:
			return {"name": "__no_such_tm2__"}
		return {"name": ["in", names]}

	return None


def _base_filters_for_queue(slug: str | None) -> dict[str, Any]:
	if not slug:
		return dict(_ACTIVE)
	if slug not in _VALID_QUEUE_SLUGS:
		return {"name": "__no_such_tm2__"}

	if slug == "draft":
		return {**_ACTIVE, "status": "Draft"}
	if slug == "std-incomplete":
		return {**_ACTIVE, "status": "STD Instance Incomplete"}
	if slug == "ready-review":
		return {**_ACTIVE, "status": "Ready for Publication Review"}
	if slug == "returned":
		return {**_ACTIVE, "status": "Returned for Correction"}
	if slug == "approved":
		return {**_ACTIVE, "status": "Approved for Publication"}
	if slug == "published":
		return {**_ACTIVE, "status": "Published"}
	if slug == "addenda":
		return {**_ACTIVE, "status": "Addendum Pending"}
	if slug == "opening-ready":
		return {**_ACTIVE, "status": "Opening Ready"}
	if slug == "evaluation-ready":
		return {**_ACTIVE, "status": "Evaluation Ready"}
	if slug in ("clarifications", "closing-soon", "closed", "cancelled"):
		return dict(_ACTIVE)
	return {**_ACTIVE}


def _merge_filters(base: dict[str, Any], name_filt: dict[str, Any] | None) -> dict[str, Any]:
	out = dict(base)
	if name_filt:
		out.update(name_filt)
	return out


def _search_or_filters(q: str) -> list[list[Any]]:
	like = f"%{q}%"
	return [
		["tender_code", "like", like],
		["tender_title", "like", like],
		["procurement_package_code", "like", like],
		["procuring_entity_code", "like", like],
	]


def _binding_version(tm2_name: str) -> str:
	rows = frappe.get_all(
		"TM2 Tender STD Binding",
		filters={"tm2_tender": tm2_name, "is_active": 1},
		fields=["std_template_version_code"],
		limit=1,
	)
	if not rows:
		return ""
	return cstr(rows[0].get("std_template_version_code") or "")


def _submission_deadline_iso(dt: Any) -> str | None:
	"""§19.1-style ISO-8601 ``…T…`` string (no colon in offset); falls back to DB string."""
	if dt is None:
		return None
	try:
		return get_datetime(dt).isoformat(sep="T", timespec="seconds")
	except Exception:
		s = cstr(dt).strip()
		return s or None


def _timeline_bits(tm2_name: str) -> tuple[str | None, str | None, str]:
	rows = frappe.get_all(
		"TM2 Tender Timeline",
		filters={"tm2_tender": tm2_name},
		fields=["submission_deadline_at", "timezone"],
		limit=1,
	)
	if not rows:
		return None, None, ""
	r = rows[0]
	dt = r.get("submission_deadline_at")
	tz = cstr(r.get("timezone") or "").strip() or None
	if not dt:
		return None, tz or "", ""
	label = format_datetime(dt)
	if tz:
		label = f"{label} {tz}"
	return _submission_deadline_iso(dt), tz or "", label


def queue_counts_to_section_19_1(queue_counts: dict[str, Any]) -> dict[str, int]:
	"""Map §14.7 URL slug keys to doc 9 §19.1 ``counts`` object (snake_case)."""
	out: dict[str, int] = {}
	for slug, raw in (queue_counts or {}).items():
		sk = cstr(slug or "").strip().replace("-", "_")
		if not sk:
			continue
		try:
			out[sk] = int(raw or 0)
		except (TypeError, ValueError):
			out[sk] = 0
	return out


def _current_action_label_for_list_queue(queue_slug: str | None) -> str:
	"""Short queue-context label for §19.1 ``current_action_label`` (empty when no queue)."""
	s = cstr(queue_slug or "").strip()
	if not s:
		return ""
	labels: dict[str, str] = {
		"draft": business_label_for_queue_slug("draft"),
		"std-incomplete": business_label_for_queue_slug("std-incomplete"),
		"ready-review": business_label_for_queue_slug("ready-review"),
		"returned": business_label_for_queue_slug("returned"),
		"approved": business_label_for_queue_slug("approved"),
		"published": business_label_for_queue_slug("published"),
		"clarifications": business_label_for_queue_slug("clarifications"),
		"addenda": business_label_for_queue_slug("addenda"),
		"closing-soon": business_label_for_queue_slug("closing-soon"),
		"closed": business_label_for_queue_slug("closed"),
		"opening-ready": business_label_for_queue_slug("opening-ready"),
		"evaluation-ready": business_label_for_queue_slug("evaluation-ready"),
		"cancelled": business_label_for_queue_slug("cancelled"),
	}
	return str(labels.get(s, "") or "")


def _issued_addendum_count(tm2_name: str) -> int:
	return int(
		frappe.db.count(
			"TM2 Addendum",
			{"tm2_tender": tm2_name, "status": "Issued"},
		)
	)


def _blocker_bits(row: dict[str, Any]) -> tuple[int, str]:
	st = cstr(row.get("status") or "")
	rs = cstr(row.get("std_readiness_status") or "")
	n = 0
	parts: list[str] = []
	if rs in ("Not Ready", "Blocked", "Not Assessed"):
		n += 1
		parts.append(_("Document readiness: {0}").format(business_label_for_readiness_status(rs)))
	if st == "Addendum Pending":
		n += 1
		parts.append(_("Addendum pending"))
	if st == "Suspended Pending Addendum":
		n += 1
		parts.append(_("Suspended pending addendum"))
	if not parts:
		return 0, ""
	return n, " · ".join(parts)


def _badges(row: dict[str, Any], issued_addenda: int) -> list[str]:
	st = cstr(row.get("status") or "")
	cat = cstr(row.get("procurement_category") or "")
	rs = cstr(row.get("std_readiness_status") or "")
	out: list[str] = []
	if st:
		out.append(business_label_for_tender_status(st))
	if cat:
		out.append(cat)
	if rs == "Ready":
		out.append(_("Document ready"))
	elif rs in ("Not Ready", "Blocked", "Ready With Warnings", "Not Assessed"):
		out.append(business_label_for_readiness_status(rs))
	if issued_addenda > 0:
		out.append(_("Addendum {0}").format(issued_addenda))
	return out


def list_workbench_tenders(
	_user: str | None,
	queue: str | None = None,
	search: str | None = None,
	limit: int = 50,
	*,
	_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Return doc 9 §19.1 payload: ``items`` list rows + ``counts`` queue bucket totals.

	``_filters`` is reserved for future §19.1 filter objects (ignored).
	"""
	lim = max(1, min(int(limit or 50), 200))
	qslug = (queue or "").strip() or None
	if qslug and qslug not in _VALID_QUEUE_SLUGS:
		kpi_e = get_workbench_kpi_counts_service(_user)
		qc_e = (kpi_e.get("queue_counts") or {}) if kpi_e.get("ok") else {}
		return {
			"ok": False,
			"message": _("Unknown queue."),
			"items": [],
			"counts": queue_counts_to_section_19_1(qc_e),
		}

	base = _base_filters_for_queue(qslug)
	name_filt = _tender_name_filters_for_queue(qslug)
	filters = _merge_filters(base, name_filt)

	fields = [
		"name",
		"tender_code",
		"tender_title",
		"procurement_package_code",
		"procuring_entity_code",
		"procurement_method",
		"procurement_category",
		"status",
		"std_readiness_status",
	]
	or_filters = _search_or_filters(search.strip()) if (search or "").strip() else None

	rows = frappe.get_list(
		"TM2 Tender",
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		order_by="modified desc",
		limit=lim,
	)

	kpi = get_workbench_kpi_counts_service(_user)
	qc = (kpi.get("queue_counts") or {}) if kpi.get("ok") else {}
	counts_19 = queue_counts_to_section_19_1(qc)
	action_lab = _current_action_label_for_list_queue(qslug)

	items: list[dict[str, Any]] = []
	for row in rows:
		tm2 = cstr(row.get("name") or "")
		if not tm2:
			continue
		tcode = cstr(row.get("tender_code") or "")
		ver = _binding_version(tm2)
		_iso, tz, deadline_label = _timeline_bits(tm2)
		ad_ct = _issued_addendum_count(tm2)
		bc, bsum = _blocker_bits(row)
		items.append(
			{
				"tender_code": tcode,
				"tender_title": cstr(row.get("tender_title") or ""),
				"package_code": cstr(row.get("procurement_package_code") or ""),
				"procuring_entity_code": cstr(row.get("procuring_entity_code") or ""),
				"procurement_method": cstr(row.get("procurement_method") or ""),
				"procurement_category": cstr(row.get("procurement_category") or ""),
				"status": cstr(row.get("status") or ""),
				"status_label": business_label_for_tender_status(cstr(row.get("status") or "")),
				"std_readiness_status": cstr(row.get("std_readiness_status") or ""),
				"readiness_short": business_readiness_short_label(cstr(row.get("std_readiness_status") or "")),
				"std_template_version_code": ver,
				"submission_deadline_at": _iso,
				"timezone": tz or "",
				"submission_deadline_label": deadline_label,
				"badges": _badges(row, ad_ct),
				"blocker_count": bc,
				"blocker_summary": bsum,
				"current_action_label": action_lab,
			}
		)

	return {"ok": True, "items": items, "counts": counts_19}
