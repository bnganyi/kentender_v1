# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Preparation rows for the shared My Work queue: the Head of
Procurement Function's open approval tasks, and a Procurement Officer's
returned Drafts. Eligibility mirrors the command gates exactly (read-offer
parity); work queues are never sidebar entries."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.tender_preparation.services import tender_authorization as authz
from kentender_procurement.tender_preparation.services.tender_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER


def _row(*, task_id: str, task_type: str, title: str, reference: str, stage: str, assignment: str, action_label: str, route: list[str], received_at, token: str) -> dict[str, Any]:
	return {
		"task_id": task_id, "task_type": task_type, "title": title, "reference": reference, "module": "Tender Preparation", "stage": stage,
		"fiscal_year": "", "organisation_unit": "", "assignment": _(assignment), "status": _("Assigned"), "received_at": cstr(received_at), "due_at": "",
		"action_label": action_label, "route": route, "route_options": {}, "concurrency_token": cstr(token), "can_claim": False, "can_open": True,
	}


def _approval_rows(user: str) -> list[dict[str, Any]]:
	if not authz.has_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, user):
		return []
	rows = []
	for task in frappe.get_all("Tender Preparation Task", filters={"status": "Open", "business_role": ROLE_HEAD_OF_PROCUREMENT_FUNCTION}, fields=["name", "tender", "tender_version", "task_token", "creation"], order_by="creation asc"):
		root = frappe.db.get_value("Prepared Tender", task.tender, ["tender_reference", "requirement_title"], as_dict=True)
		rows.append(_row(task_id=task.name, task_type="tender_preparation.approval", title=_("Approve Tender — {0}").format(root.tender_reference), reference=root.tender_reference, stage=_("Tender approval"), assignment=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, action_label=_("Open approval task"), route=["tender-preparation", "task", task.name], received_at=task.creation, token=task.task_token))
	return rows


def _returned_draft_rows(user: str) -> list[dict[str, Any]]:
	if not authz.has_site_role(ROLE_PROCUREMENT_OFFICER, user):
		return []
	rows = []
	for version in frappe.get_all("Tender Preparation Version", filters={"version_status": "Draft", "based_on_version": ("is", "set")}, fields=["name", "tender", "based_on_version", "creation", "record_version"], order_by="creation asc"):
		root = frappe.db.get_value("Prepared Tender", version.tender, ["tender_reference", "current_version", "current_state"], as_dict=True)
		if not root or root.current_version != version.name or root.current_state != "Draft":
			continue
		based_on_status = frappe.db.get_value("Tender Preparation Version", version.based_on_version, "version_status")
		stage = _("Returned for correction") if based_on_status == "Returned" else _("Reopened before publication")
		rows.append(_row(task_id=version.name, task_type="tender_preparation.correction", title=_("Correct Tender — {0}").format(root.tender_reference), reference=root.tender_reference, stage=stage, assignment=ROLE_PROCUREMENT_OFFICER, action_label=_("Open Tender"), route=["tender-preparation", version.tender], received_at=version.creation, token=str(version.record_version)))
	return rows


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	return {"assigned": _approval_rows(user) + _returned_draft_rows(user), "available": []}
