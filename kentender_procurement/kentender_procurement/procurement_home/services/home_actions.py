# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — Requires Your Action aggregator."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import frappe
from frappe.utils import getdate

from kentender_procurement.procurement_home.services.pe_aliases import pe_aliases
from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	demand_doctype_available,
)

ACTION_LIMIT = 8
DUE_SOON_DAYS = 3
ALLOWED_ACTION_LABELS = frozenset(("Review", "Resolve", "Continue"))


def _roles(user: str) -> set[str]:
	return set(frappe.get_roles(user))


def _urgency(due: date | None, today: date) -> str:
	if due is None:
		return "Other"
	if due < today:
		return "Overdue"
	if due <= today + timedelta(days=DUE_SOON_DAYS):
		return "Due soon"
	return "Other"


def _sort_key(item: dict[str, Any], today: date) -> tuple:
	due = item.get("_due_date")
	urgency = item.get("urgency") or _urgency(due, today)
	rank = {"Overdue": 0, "Due soon": 1, "Other": 2, "Blocked": 0, "Returned": 1}.get(urgency, 3)
	if due is None:
		# Undated last among dated groups; oldest first via modified asc
		return (3, item.get("_modified") or datetime.min)
	return (rank, due)


def _fmt_due(due: date | None) -> str | None:
	if due is None:
		return None
	return due.strftime("%d %b %Y")


def _demand_actions(user: str, procuring_entity: str, today: date) -> list[dict[str, Any]]:
	_ = user, procuring_entity, today
	# Demands package retired; guard is permanently unreachable but kept explicit.
	if not demand_doctype_available():
		return []
	return []


def _package_actions(*_args, **_kwargs) -> list[dict[str, Any]]:
	"""PP2 Package actions retired."""
	return []

def _tender_actions(user: str, procuring_entity: str) -> list[dict[str, Any]]:
	roles = _roles(user)
	tm_roles = {"Tender Manager", "Procurement Officer", "System Manager"}
	if user != "Administrator" and not (roles & tm_roles):
		return []
	if not frappe.db.exists("DocType", "TM2 Tender"):
		return []
	filters: dict[str, Any] = {
		"status": ["in", ["Returned for Correction", "Ready for Publication Review", "STD Instance Incomplete"]],
	}
	if frappe.db.has_column("TM2 Tender", "procuring_entity_code"):
		filters["procuring_entity_code"] = ["in", pe_aliases(procuring_entity)]
	rows = frappe.get_all(
		"TM2 Tender",
		filters=filters,
		fields=["name", "tender_code", "tender_title", "status", "modified"],
		limit=20,
	)
	items: list[dict[str, Any]] = []
	for r in rows:
		status = r.get("status") or ""
		if status == "Returned for Correction":
			action_req, urgency, btn = "Returned for correction", "Returned", "Continue"
		elif status == "STD Instance Incomplete":
			action_req, urgency, btn = "Configuration blockers require correction", "Blocked", "Resolve"
		else:
			action_req, urgency, btn = "Publication approval required", "Overdue", "Review"
		items.append(
			{
				"title": r.get("tender_title") or r.get("tender_code") or r.name,
				"reference": r.get("tender_code") or r.name,
				"stage": "Tender Configuration" if "Incomplete" in status else "Publication",
				"action_required": action_req,
				"urgency": urgency,
				"due_date": None,
				"action_label": btn,
				"target_url": "/desk/publications" if "Publication" in action_req else "/desk/tender-management-v2",
				"_due_date": None,
				"_modified": r.get("modified"),
			}
		)
	return items


def get_home_actions(
	procuring_entity: str,
	fiscal_year: int | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Return permission-scoped action items (max 8). fiscal_year reserved for future demand FY filter."""
	_ = fiscal_year  # Demand has no fiscal_year field today
	user = (user or frappe.session.user or "").strip()
	today = getdate()
	raw = (
		_demand_actions(user, procuring_entity, today)
		+ _package_actions(user, procuring_entity)
		+ _tender_actions(user, procuring_entity)
	)
	# Deduplicate by reference+stage
	seen: set[str] = set()
	unique: list[dict[str, Any]] = []
	for item in raw:
		key = f"{item.get('stage')}:{item.get('reference')}"
		if key in seen:
			continue
		seen.add(key)
		if item.get("action_label") not in ALLOWED_ACTION_LABELS:
			item["action_label"] = "Review"
		unique.append(item)
	unique.sort(key=lambda i: _sort_key(i, today))
	capped = unique[:ACTION_LIMIT]
	for item in capped:
		due = item.get("_due_date")
		item["due_date"] = _fmt_due(due)
		item.pop("_due_date", None)
		item.pop("_modified", None)
	return {
		"ok": True,
		"items": capped,
		"pending_count": len(capped),
		"view_all_url": "/desk/departmental-needs",
		"empty": len(capped) == 0,
	}
