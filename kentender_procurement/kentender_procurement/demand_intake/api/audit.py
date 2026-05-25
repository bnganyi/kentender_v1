# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DIA Audit tab payload — workflow timeline and downstream usage."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, format_datetime


def _user_label(user_id: str | None) -> str:
	if not user_id:
		return ""
	full_name = frappe.db.get_value("User", user_id, "full_name")
	return (full_name or user_id or "").strip()


def _append_event(timeline: list, *, label: str, detail: str | None, at, note: str | None = None) -> None:
	if not at:
		return
	timeline.append({"label": label, "detail": detail, "at": at, "note": note})


def _build_timeline(doc) -> list[dict]:
	timeline: list[dict] = []
	_append_event(
		timeline,
		label=_("Draft created"),
		detail=_user_label(doc.created_by or doc.owner),
		at=doc.creation,
	)
	_append_event(
		timeline,
		label=_("Submitted for approval"),
		detail=_user_label(doc.submitted_by),
		at=doc.submitted_at,
	)
	_append_event(
		timeline,
		label=_("HoD approved"),
		detail=_user_label(doc.hod_approved_by),
		at=doc.hod_approved_at,
	)
	_append_event(
		timeline,
		label=_("Finance approved"),
		detail=_user_label(doc.finance_approved_by),
		at=doc.finance_approved_at,
	)
	if doc.returned_at:
		_append_event(
			timeline,
			label=_("Returned for correction"),
			detail=_user_label(doc.returned_by),
			at=doc.returned_at,
			note=(doc.return_reason or "").strip() or None,
		)
	if doc.rejected_at:
		_append_event(
			timeline,
			label=_("Rejected"),
			detail=_user_label(doc.rejected_by),
			at=doc.rejected_at,
			note=(doc.rejection_reason or "").strip() or None,
		)
	if doc.cancelled_at:
		_append_event(
			timeline,
			label=_("Cancelled"),
			detail=_user_label(doc.cancelled_by),
			at=doc.cancelled_at,
			note=(doc.cancellation_reason or "").strip() or None,
		)
	if (doc.status or "") == "Planning Ready":
		_append_event(
			timeline,
			label=_("Marked planning ready"),
			detail=None,
			at=doc.modified,
		)
	return timeline


def _build_downstream(doc) -> dict:
	downstream: dict = {
		"reservation_status": (doc.reservation_status or "None").strip(),
		"reservation_reference": (doc.reservation_reference or "").strip() or None,
		"planning_status": (doc.planning_status or "").strip() or None,
		"linked_packages": 0,
		"linked_journeys": 0,
		"procurement_available": True,
	}
	demand_id = (doc.demand_id or "").strip()
	if demand_id and frappe.db.exists("DocType", "Procurement Package Line"):
		downstream["linked_packages"] = frappe.db.count(
			"Procurement Package Line",
			{"demand_id": demand_id, "docstatus": ["<", 2]},
		)
	if demand_id and frappe.db.exists("DocType", "Procurement Journey"):
		downstream["linked_journeys"] = frappe.db.count(
			"Procurement Journey",
			{"demand_ref": demand_id},
		)
	try:
		from kentender_procurement.procurement_lifecycle.api.journey_api import get_demand_planning_status

		planning = get_demand_planning_status(doc.name)
		if planning.get("ok"):
			downstream["planning_handoff"] = {
				"journey_code": (planning.get("journey") or {}).get("journey_code"),
				"demand_approval_certificate": bool(planning.get("demand_approval_certificate")),
				"planning_inclusion": bool(planning.get("planning_inclusion")),
			}
	except Exception:
		downstream["procurement_available"] = False
	return downstream


@frappe.whitelist()
def get_demand_audit_data(demand_name: str | None = None):
	"""Return workflow timeline (non-empty events only) and downstream usage."""
	if not demand_name:
		frappe.throw(_("Demand is required."))
	if not frappe.has_permission("Demand", "read", demand_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("Demand", demand_name)
	timeline = _build_timeline(doc)
	return {
		"demand_name": doc.name,
		"demand_id": doc.demand_id,
		"title": doc.title,
		"status": doc.status,
		"total_amount": flt(doc.total_amount),
		"timeline": [
			{
				"label": row["label"],
				"detail": row.get("detail"),
				"at": format_datetime(row["at"]) if row.get("at") else None,
				"note": row.get("note"),
			}
			for row in timeline
		],
		"downstream": _build_downstream(doc),
	}
