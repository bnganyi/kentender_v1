# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — upcoming deadlines from explicit stored dates only."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime, now_datetime

from kentender_procurement.procurement_home.services.pe_aliases import pe_aliases

DEADLINE_LIMIT = 5


def _time_remaining(dt) -> str:
	now = now_datetime()
	delta = get_datetime(dt) - now
	secs = int(delta.total_seconds())
	if secs < 0:
		over = -secs
		days = over // 86400
		if days >= 1:
			return f"{days} day{'s' if days != 1 else ''} overdue"
		hours = over // 3600
		return f"{hours} hour{'s' if hours != 1 else ''} overdue"
	days = secs // 86400
	if days >= 2:
		return f"{days} days remaining"
	if days == 1:
		return "1 day remaining"
	hours = max(1, secs // 3600)
	return f"{hours} hour{'s' if hours != 1 else ''} remaining"


def _timeline_for_tender(tender_name: str, tender_code: str) -> dict[str, Any]:
	if not frappe.db.exists("DocType", "TM2 Tender Timeline"):
		return {}
	row = frappe.db.get_value(
		"TM2 Tender Timeline",
		{"tm2_tender": tender_name},
		["submission_deadline_at", "clarification_deadline_at", "planned_publication_at"],
		as_dict=True,
	)
	if row:
		return row
	if tender_code:
		row = frappe.db.get_value(
			"TM2 Tender Timeline",
			{"tender_code": tender_code},
			["submission_deadline_at", "clarification_deadline_at", "planned_publication_at"],
			as_dict=True,
		)
	return row or {}


def get_home_deadlines(
	procuring_entity: str,
	fiscal_year: int | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	_ = fiscal_year, user
	items: list[dict[str, Any]] = []
	if not frappe.db.exists("DocType", "TM2 Tender"):
		return {"ok": True, "items": [], "empty": True}

	filters: dict[str, Any] = {
		"status": ["in", ["Published", "Approved for Publication", "Ready for Publication Review"]],
	}
	if frappe.db.has_column("TM2 Tender", "procuring_entity_code"):
		filters["procuring_entity_code"] = ["in", pe_aliases(procuring_entity)]
	tenders = frappe.get_all(
		"TM2 Tender",
		filters=filters,
		fields=["name", "tender_code", "tender_title", "status"],
		limit=100,
	)
	now = now_datetime()
	for t in tenders:
		code = t.get("tender_code") or t.name
		tl = _timeline_for_tender(t.name, code)
		# Stitch action icons: open_in_new / visibility / rate_review
		candidates = [
			("Bid submission deadline", tl.get("submission_deadline_at"), "View tender", "open_in_new"),
			("Clarification deadline", tl.get("clarification_deadline_at"), "View tender", "open_in_new"),
			("Scheduled publication date", tl.get("planned_publication_at"), "View", "visibility"),
		]
		for event, raw_dt, action, action_icon in candidates:
			if not raw_dt:
				continue
			try:
				dt = get_datetime(raw_dt)
			except Exception:
				continue
			if dt < now and t.get("status") not in ("Published", "Ready for Publication Review"):
				continue
			items.append(
				{
					"event": event,
					"title": t.get("tender_title") or code,
					"reference": code,
					"datetime": dt.isoformat(),
					"display_date": dt.strftime("%b"),
					"display_day": str(int(dt.strftime("%d"))),
					"time_remaining": _time_remaining(dt),
					"action_label": action,
					"action_icon": action_icon,
					"target_url": "/desk/tender-management-v2",
					"_dt": dt,
					"_overdue": dt < now,
				}
			)

	items.sort(key=lambda i: (0 if i["_overdue"] else 1, i["_dt"]))
	capped = items[:DEADLINE_LIMIT]
	for i in capped:
		i.pop("_dt", None)
		i.pop("_overdue", None)
	return {"ok": True, "items": capped, "empty": len(capped) == 0}
