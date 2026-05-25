# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DIA Review tab payload — staged submission and planning readiness checks."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.demand_intake.services.readiness import (
	evaluate_approval_integrity,
	evaluate_draft_save,
	evaluate_planning_handoff_readiness,
	evaluate_planning_panel_checks,
	evaluate_planning_readiness,
	evaluate_review_action,
	evaluate_submission_readiness,
)


def _load_demand(demand_name: str | None):
	if not demand_name:
		frappe.throw(_("Demand is required."))
	if not frappe.has_permission("Demand", "read", demand_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return frappe.get_doc("Demand", demand_name)


def _resolve_review_view(status: str) -> str:
	st = (status or "Draft").strip()
	if st in ("Draft", "Rejected"):
		return "draft"
	if st in ("Pending HoD Approval", "Pending Finance Approval"):
		return "pending_review"
	if st in ("Approved", "Planning Ready"):
		return "approved_outcome"
	if st == "Cancelled":
		return "terminal"
	return "draft"


def _approval_outcome(doc) -> dict:
	return {
		"hod_approved_by": doc.hod_approved_by,
		"hod_approved_at": doc.hod_approved_at,
		"finance_approved_by": doc.finance_approved_by,
		"finance_approved_at": doc.finance_approved_at,
		"submitted_by": doc.submitted_by,
		"submitted_at": doc.submitted_at,
	}


@frappe.whitelist()
def get_demand_draft_readiness(demand_name: str | None = None):
	"""Return draft-save readiness checks (§24.1)."""
	doc = _load_demand(demand_name)
	return evaluate_draft_save(doc)


@frappe.whitelist()
def get_demand_submission_readiness(demand_name: str | None = None):
	"""Return submission readiness checks (§24.2)."""
	doc = _load_demand(demand_name)
	return evaluate_submission_readiness(doc)


@frappe.whitelist()
def get_demand_review_data(demand_name: str | None = None):
	"""Return state-aware review/planning payloads for workbench tabs (Phase L)."""
	doc = _load_demand(demand_name)
	status = (doc.status or "Draft").strip()
	review_view = _resolve_review_view(status)
	integrity = evaluate_approval_integrity(doc)
	panel = evaluate_planning_panel_checks(doc)

	payload: dict = {
		"demand_name": doc.name,
		"demand_id": doc.demand_id,
		"title": doc.title,
		"status": status,
		"review_view": review_view,
		"draft_readiness": evaluate_draft_save(doc),
		"integrity_blockers": integrity.get("blockers") or [],
		"integrity_blocked": bool(integrity.get("blocked")),
		"integrity_blocker_count": integrity.get("blocker_count") or 0,
		"planning_panel_checks": panel,
	}

	if review_view in ("draft",):
		payload["submission_readiness"] = evaluate_submission_readiness(doc)
		payload["review_action_readiness"] = None
		payload["approval_outcome"] = None
		payload["planning_handoff_guidance"] = None
	elif review_view == "pending_review":
		payload["submission_readiness"] = None
		action = "approve_hod" if status == "Pending HoD Approval" else "approve_finance"
		payload["review_action_readiness"] = evaluate_review_action(doc, action=action)
		payload["approval_outcome"] = None
		payload["planning_handoff_guidance"] = None
	elif review_view == "approved_outcome":
		payload["submission_readiness"] = evaluate_submission_readiness(doc)
		payload["review_action_readiness"] = None
		payload["approval_outcome"] = _approval_outcome(doc)
		payload["planning_handoff_guidance"] = {
			"message": _("Use the Planning tab to run readiness checks and confirm Planning Ready."),
			"planning_tab": True,
		}
	elif review_view == "terminal":
		payload["submission_readiness"] = None
		payload["review_action_readiness"] = None
		payload["approval_outcome"] = None
		payload["planning_handoff_guidance"] = None
	else:
		payload["submission_readiness"] = evaluate_submission_readiness(doc)
		payload["review_action_readiness"] = None
		payload["approval_outcome"] = None
		payload["planning_handoff_guidance"] = None

	if status in ("Approved", "Planning Ready"):
		payload["planning_handoff_readiness"] = evaluate_planning_handoff_readiness(doc)
		payload["planning_readiness"] = evaluate_planning_readiness(doc)
	else:
		payload["planning_handoff_readiness"] = None
		payload["planning_readiness"] = None

	return payload
