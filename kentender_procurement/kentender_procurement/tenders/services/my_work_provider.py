# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tenders rows for the shared My Work queue (§9 "Tasks link to the Tender
record with the exact record/task identity"). Core collects providers
through the `kt_my_work_providers` hook; core never imports this app.
Eligibility mirrors the decision commands exactly (read-offer parity)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.tenders.services import lifecycle
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.services.tender_roles import ROLE_ACCOUNTING_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER

PAGE = "tenders"
TASK_ROUTES: dict[str, tuple[str, str, str, str]] = {
	# task_type -> (role, stage label, action label, route segment)
	"HOPF approval": (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "Procurement approval", "Review Tender package", ""),
	"AO publication authorisation": (ROLE_ACCOUNTING_OFFICER, "Publication authorisation", "Review publication", ""),
	"HOPF channel confirmation": (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "Publication confirmation", "Complete confirmations", "publication"),
	"HOPF addendum issue": (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "Addendum issue", "Review addendum", "addenda"),
	"Inquiry response": (ROLE_PROCUREMENT_OFFICER, "Addendum inquiry", "Respond to inquiry", "inquiries"),
}


def _row(task, root, *, stage: str, assignment: str, action_label: str, route: list[str]) -> dict[str, Any]:
	return {
		"task_id": task.name, "task_type": f"tenders.{task.task_type.lower().replace(' ', '_')}", "title": _("{0} — {1}").format(stage, root.tender_reference), "reference": root.tender_reference,
		"module": "Tenders", "stage": _(stage), "fiscal_year": cstr(root.fiscal_year), "organisation_unit": cstr(root.lead_org_unit), "assignment": _(assignment), "status": _("Assigned"),
		"received_at": cstr(task.creation), "due_at": "", "action_label": _(action_label), "route": route, "route_options": {}, "concurrency_token": cstr(task.task_token), "can_claim": False, "can_open": True,
	}


def _segregation_ok(task, root, user: str) -> bool:
	if task.task_type not in ("HOPF approval", "AO publication authorisation") or not task.tender_version:
		return True
	version = frappe.get_doc("Tender Version", task.tender_version)
	columns = ("prepared_by", "submitted_by") if task.task_type == "HOPF approval" else ("prepared_by", "submitted_by", "approved_by")
	try:
		lifecycle.require_segregation(version, user, blocked_columns=columns)
		return True
	except TendersError:
		return False


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	if not user or user == "Guest":
		return {"assigned": [], "claimable": [], "waiting": []}
	assigned: list[dict[str, Any]] = []
	for task in frappe.get_all("Tender Task", filters={"status": "Open"}, fields=["name", "tender", "tender_version", "task_type", "business_role", "subject_type", "subject_id", "task_token", "creation"], order_by="creation asc", limit_page_length=0):
		spec = TASK_ROUTES.get(task.task_type)
		if not spec:
			continue
		role, stage, action_label, segment = spec
		holders = (ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION) if task.task_type == "Inquiry response" else (role,)
		if not any(authz.has_site_role(r, user) for r in holders):
			continue
		root = frappe.db.get_value("Tender", task.tender, ["name", "tender_reference", "fiscal_year", "lead_org_unit"], as_dict=True)
		if not root or not _segregation_ok(task, root, user):
			continue
		route = [PAGE, root.tender_reference] + ([segment] if segment else []) + ([task.subject_id] if segment in ("addenda", "inquiries") and task.subject_id else [])
		assigned.append(_row(task, root, stage=stage, assignment=role, action_label=action_label, route=route))
	return {"assigned": assigned, "claimable": [], "waiting": []}
