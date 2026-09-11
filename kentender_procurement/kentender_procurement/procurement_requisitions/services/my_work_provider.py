# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Requisitions rows for the shared My Work queue (§10.1).

Core collects providers through the `kt_my_work_providers` hook; core never
imports this app (same pattern as `procurement_planning`'s own provider).
Eligibility mirrors the decision commands exactly — a row appears only for
an actor the command layer would accept for that exact task (read-offer
parity), never a second, independently-derived rule.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.draft_commands import _contributing_units
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.services.requisition_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION


def _can(fn, *args, **kwargs) -> bool:
	try:
		fn(*args, **kwargs)
		return True
	except (ProcurementRequisitionsError, frappe.DoesNotExistError, frappe.PermissionError):
		return False


def _row(*, task, task_type: str, title: str, reference: str, stage: str, organisation_unit: str, assignment: str, action_label: str, route: list[str]) -> dict[str, Any]:
	return {
		"task_id": task.name,
		"task_type": task_type,
		"title": title,
		"reference": reference,
		"module": "Procurement Requisitions",
		"stage": stage,
		"fiscal_year": "",
		"organisation_unit": cstr(organisation_unit),
		"assignment": _(assignment),
		"status": _("Assigned"),
		"received_at": cstr(task.creation),
		"due_at": "",
		"action_label": action_label,
		"route": route,
		"route_options": {},
		"concurrency_token": cstr(task.task_token),
		"can_claim": False,
		"can_open": True,
	}


def _department_approval_rows(user: str) -> list[dict[str, Any]]:
	rows = []
	for task in frappe.get_all(
		"Requisition Task", filters={"status": "Open", "business_role": "Head of User Department"},
		fields=["name", "requisition", "requisition_version", "organisation_unit", "task_token", "creation"],
		order_by="creation asc", limit_page_length=0,
	):
		root = frappe.get_doc("Procurement Requisition", task.requisition)
		if not _can(authz.require_hod_for_any, _contributing_units(root), user, masked=False):
			continue
		rows.append(
			_row(
				task=task, task_type="requisitions.department_approval",
				title=_("Approve Requisition — {0}").format(root.requisition_reference), reference=root.requisition_reference,
				stage=_("Department approval"), organisation_unit=root.lead_org_unit, assignment="Head of User Department",
				action_label=_("Open department task"), route=["procurement-requisitions", "department-task", task.name],
			)
		)
	return rows


def _procurement_authorisation_rows(user: str) -> list[dict[str, Any]]:
	if not authz.can_read_site(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, user):
		return []
	rows = []
	for task in frappe.get_all(
		"Requisition Task", filters={"status": "Open", "business_role": ROLE_HEAD_OF_PROCUREMENT_FUNCTION},
		fields=["name", "requisition", "requisition_version", "task_token", "creation"],
		order_by="creation asc", limit_page_length=0,
	):
		root = frappe.get_doc("Procurement Requisition", task.requisition)
		rows.append(
			_row(
				task=task, task_type="requisitions.procurement_authorisation",
				title=_("Authorise Requisition — {0}").format(root.requisition_reference), reference=root.requisition_reference,
				stage=_("Procurement authorisation"), organisation_unit=root.lead_org_unit, assignment=ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
				action_label=_("Open procurement task"), route=["procurement-requisitions", "procurement-task", task.name],
			)
		)
	return rows


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	"""`kt_my_work_providers` entry: the caller's open Requisition decisions."""
	if not user or user == "Guest":
		return {"assigned": [], "claimable": [], "waiting": []}
	return {
		"assigned": _department_approval_rows(user) + _procurement_authorisation_rows(user),
		"claimable": [],
		"waiting": [],
	}
