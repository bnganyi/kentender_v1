# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Planning rows for the shared My Work queue (§10).

Planning has exactly one navigation entry; actionable decisions reach their
actors through the workspace, this My Work projection and notifications —
never a sidebar work-queue entry (PLN-AC-059). Core collects providers
through the `kt_my_work_providers` hook; core never imports this app.

Eligibility mirrors the decision commands exactly (read-offer parity, the
NDS-807/911 classes): a row appears only for an actor the command layer
would accept — the same resolver, the same §6.1 segregation check.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PROCUREMENT_PLANNER,
)


def _row(*, task, task_type: str, title: str, reference: str, stage: str, fiscal_year: str, organisation_unit: str, assignment: str, action_label: str, route: list[str]) -> dict[str, Any]:
	return {
		"task_id": task.name,
		"task_type": task_type,
		"title": title,
		"reference": reference,
		"module": "Procurement Planning",
		"stage": stage,
		"fiscal_year": cstr(fiscal_year),
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


def _validation_rows(user: str) -> list[dict[str, Any]]:
	if not authz.has_site_role(ROLE_PROCUREMENT_PLANNER, user):
		return []
	rows = []
	for task in frappe.get_all(
		"Departmental Plan Validation Task",
		filters={"status": "Open"},
		fields=["name", "task_reference", "submission", "organisation_unit", "fiscal_year", "task_token", "creation"],
		order_by="creation asc",
		limit_page_length=0,
	):
		if authz.is_segregated(user, authz.ACTION_DPP_VALIDATE, submission=task.submission):
			continue
		department = cstr(frappe.db.get_value("Organisation Unit", task.organisation_unit, "unit_name") or task.organisation_unit)
		rows.append(
			_row(
				task=task, task_type="planning.dpp_validation",
				title=_("Validate {0} departmental plan").format(department), reference=cstr(task.task_reference),
				stage=_("Departmental plan validation"), fiscal_year=task.fiscal_year, organisation_unit=task.organisation_unit,
				assignment=ROLE_PROCUREMENT_PLANNER, action_label=_("Review departmental plan"),
				route=["procurement-planning", "dpp-review", task.name],
			)
		)
	return rows


def _plan_title(plan_version: str) -> tuple[str, str]:
	row = frappe.db.get_value("Annual Plan Version", plan_version, ["annual_plan", "version_reference"], as_dict=True)
	if not row:
		return "", ""
	plan = frappe.db.get_value("Annual Plan", row.annual_plan, ["title", "fiscal_year"], as_dict=True) or {}
	return cstr(plan.get("title")), cstr(plan.get("fiscal_year"))


def _finance_rows(user: str) -> list[dict[str, Any]]:
	if not authz.has_site_role(ROLE_FINANCE_CONFIRMATION_OFFICER, user):
		return []
	rows = []
	for task in frappe.get_all(
		"Plan Finance Task", filters={"status": "Open"},
		fields=["name", "task_reference", "plan_version", "task_token", "creation"], order_by="creation asc",
	):
		if authz.is_segregated(user, authz.ACTION_FINANCE_DECIDE, plan_version=task.plan_version):
			continue
		title, fy = _plan_title(task.plan_version)
		rows.append(
			_row(
				task=task, task_type="planning.finance", title=_("Confirm plan funding — {0}").format(title),
				reference=cstr(task.task_reference), stage=_("Plan funding confirmation"), fiscal_year=fy,
				organisation_unit="", assignment=ROLE_FINANCE_CONFIRMATION_OFFICER,
				action_label=_("Open Finance task"), route=["procurement-planning", "finance", task.name],
			)
		)
	return rows


def _governance_rows(user: str) -> list[dict[str, Any]]:
	rows = []
	for stage, role, action, label in (
		("Accounting Officer adoption", ROLE_ACCOUNTING_OFFICER, authz.ACTION_AO_DECIDE, _("Adopt Annual Procurement Plan — {0}")),
		("Statutory approval", ROLE_PLAN_STATUTORY_APPROVER, authz.ACTION_STATUTORY_DECIDE, _("Approve Annual Procurement Plan — {0}")),
	):
		if not authz.has_site_role(role, user):
			continue
		for task in frappe.get_all(
			"Plan Governance Task", filters={"status": "Open", "stage": stage},
			fields=["name", "task_reference", "plan_version", "task_token", "creation"], order_by="creation asc",
		):
			if authz.is_segregated(user, action, plan_version=task.plan_version):
				continue
			title, fy = _plan_title(task.plan_version)
			rows.append(
				_row(
					task=task, task_type="planning.governance", title=label.format(title),
					reference=cstr(task.task_reference), stage=_(stage), fiscal_year=fy, organisation_unit="",
					assignment=role, action_label=_("Open decision"), route=["procurement-planning", "review", task.name],
				)
			)
	return rows


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	"""`kt_my_work_providers` entry: the caller's open Planning decisions."""
	if not user or user == "Guest":
		return {"assigned": [], "claimable": [], "waiting": []}
	return {
		"assigned": _validation_rows(user) + _finance_rows(user) + _governance_rows(user),
		"claimable": [],
		"waiting": [],
	}
