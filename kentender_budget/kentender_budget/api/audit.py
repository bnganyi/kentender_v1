# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""Budget audit tab payload — workflow history and downstream usage."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, format_datetime

from kentender_budget.api.builder import _get_builder_payload


def _user_label(user_id: str | None) -> str:
	if not user_id:
		return ""
	full_name = frappe.db.get_value("User", user_id, "full_name")
	return (full_name or user_id or "").strip()


@frappe.whitelist()
def get_budget_audit_data(budget_name: str | None = None):
	"""Return workflow timeline and aggregated downstream usage for Audit tab."""
	if not budget_name:
		frappe.throw(_("Budget is required."))
	if not frappe.has_permission("Budget", "read", budget_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	budget = frappe.get_doc("Budget", budget_name)
	review_payload = _get_builder_payload(budget_name, lines_filter="active")
	totals = review_payload.get("totals") or {}
	lines = review_payload.get("budget_lines") or []

	timeline = []
	timeline.append(
		{
			"label": _("Draft created"),
			"detail": _user_label(budget.owner or budget.created_by),
			"at": budget.creation,
		}
	)
	if budget.get("submitted_at"):
		timeline.append(
			{
				"label": _("Submitted for approval"),
				"detail": _user_label(budget.get("submitted_by")),
				"at": budget.get("submitted_at"),
			}
		)
	if budget.get("rejected_at"):
		timeline.append(
			{
				"label": _("Rejected"),
				"detail": _user_label(budget.get("rejected_by")),
				"at": budget.get("rejected_at"),
				"note": (budget.get("rejection_reason") or "").strip() or None,
			}
		)
	if budget.status == "Approved":
		timeline.append(
			{
				"label": _("Approved"),
				"detail": _user_label(budget.get("approved_by")),
				"at": budget.get("approved_at"),
			}
		)
		timeline.append({"label": _("Locked"), "detail": None, "at": budget.get("approved_at") or budget.modified})

	demand_ids: set[str] = set()
	package_ids: set[str] = set()
	journey_ids: set[str] = set()
	procurement_available = True

	for line in lines:
		line_name = line.get("name")
		if not line_name:
			continue
		try:
			from kentender_procurement.procurement_lifecycle.api.journey_api import (
				get_procurement_use_for_budget_line,
			)

			result = get_procurement_use_for_budget_line(budget_line_name=line_name)
		except Exception:
			procurement_available = False
			break
		if not result or not result.get("ok"):
			continue
		for row in result.get("demands") or []:
			key = row.get("demand_id") or row.get("name")
			if key:
				demand_ids.add(str(key))
		for row in result.get("packages") or []:
			key = row.get("code") or row.get("name")
			if key:
				package_ids.add(str(key))
		for row in result.get("journeys") or []:
			key = row.get("journey_code") or row.get("name")
			if key:
				journey_ids.add(str(key))

	downstream = {
		"reserved_sum": flt(totals.get("reserved_sum")),
		"available_sum": flt(totals.get("available_sum")),
		"linked_demands": len(demand_ids) if procurement_available else None,
		"linked_packages": len(package_ids) if procurement_available else None,
		"linked_journeys": len(journey_ids) if procurement_available else None,
		"procurement_available": procurement_available,
	}

	return {
		"budget_name": budget.name,
		"currency": budget.currency,
		"timeline": [
			{
				"label": row["label"],
				"detail": row.get("detail"),
				"at": format_datetime(row["at"]) if row.get("at") else None,
				"note": row.get("note"),
			}
			for row in timeline
		],
		"downstream": downstream,
	}
