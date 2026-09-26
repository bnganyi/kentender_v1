# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tenders rows for the shared My Work queue — the TPR-CHG-001 v0.12 §5.11
hand-off register (plan D26). Core collects providers through the
`kt_my_work_providers` hook; core never imports this app.

- **assigned**: every open register item the user holds — the named holder,
  or any current holder of the item's Site-wide responsibility — with the
  same segregation rule the decision command applies (read-offer parity);
- **waiting**: the sender's "Waiting for …" item while the hand-off is open;
- the corrected-successor row (§5.11 "Corrected Requisition successor
  authorised") is derived at read time: it exists exactly while a stopped
  Tender has an authorised, unconsumed successor handoff.

Every item clears on its business transition (the task closes), never on
reading. Technical readers get nothing (core skips providers for them).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_core.services import next_step as ns
from kentender_procurement.tenders.services import handoffs, lifecycle
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.services.tender_roles import ROLE_PROCUREMENT_OFFICER

PAGE = "tenders"
TASK_FIELDS = ["name", "tender", "tender_version", "task_type", "business_role", "holder", "sender", "comment", "subject_type", "subject_id", "task_token", "creation"]


def _segregation_ok(task, user: str) -> bool:
	if task.task_type not in (handoffs.HOPF_APPROVAL, handoffs.AO_AUTHORISATION) or not task.tender_version:
		return True
	version = frappe.get_doc("Tender Version", task.tender_version)
	columns = ("prepared_by", "submitted_by") if task.task_type == handoffs.HOPF_APPROVAL else ("prepared_by", "submitted_by", "approved_by")
	try:
		lifecycle.require_segregation(version, user, blocked_columns=columns)
		return True
	except TendersError:
		return False


def _row(task, root, *, title: str, status: str, route: list[str], action_label: str, holder: dict[str, Any] | None = None) -> dict[str, Any]:
	row = {
		"task_id": task.name, "task_type": f"tenders.{cstr(task.task_type).lower().replace(' ', '_')}", "title": title, "reference": root.tender_reference,
		"module": "Tenders", "stage": _(cstr(task.task_type)), "fiscal_year": cstr(root.fiscal_year), "organisation_unit": cstr(root.lead_org_unit),
		"assignment": _(cstr(task.business_role)), "status": _(status), "received_at": cstr(task.creation), "due_at": "", "action_label": _(action_label),
		"route": route, "route_options": {}, "concurrency_token": cstr(task.task_token), "can_claim": False, "can_open": True,
		"comment": cstr(task.comment), "since": ns.since(task.creation, _since_label(task.creation)),
	}
	if holder:
		row["holder"] = holder
	return row


def _since_label(value) -> str:
	from kentender_procurement.tenders.services import serializer

	return serializer.fmt_datetime_short(value) if value else ""


def _successor_rows(user: str) -> list[dict[str, Any]]:
	from kentender_procurement.tenders.services import correction, handoff_gateway

	if not authz.has_site_role(ROLE_PROCUREMENT_OFFICER, user):
		return []
	rows = []
	for root in frappe.get_all("Tender", filters={"overall_status": correction.CORRECTION_REQUESTED}, fields=["name", "tender_reference", "fiscal_year", "lead_org_unit", "plan_item_id", "modified"], limit_page_length=0):
		if not handoff_gateway.successors(plan_item_id=cstr(root.plan_item_id), user=user):
			continue
		task = frappe._dict({"name": f"{root.name}:successor", "task_type": "Start corrected Tender Version", "business_role": ROLE_PROCUREMENT_OFFICER, "comment": "", "task_token": "", "creation": root.modified})
		rows.append(_row(task, root, title=f"Start corrected Tender Version for {root.tender_reference}", status="Assigned", route=[PAGE, root.tender_reference], action_label="Start corrected Tender Version"))
	return rows


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	if not user or user == "Guest":
		return {"assigned": [], "claimable": [], "waiting": []}
	assigned: list[dict[str, Any]] = []
	waiting: list[dict[str, Any]] = []
	roots: dict[str, Any] = {}
	for task in frappe.get_all("Tender Task", filters={"status": "Open"}, fields=TASK_FIELDS, order_by="creation asc", limit_page_length=0):
		if task.task_type not in handoffs.REGISTER:
			continue
		root = roots.get(task.tender) or frappe.db.get_value("Tender", task.tender, ["name", "tender_reference", "fiscal_year", "lead_org_unit", "fixture_namespace"], as_dict=True)
		if not root:
			continue
		roots[task.tender] = root
		holders = handoffs.holders_of(task)
		if user in holders and _segregation_ok(task, user):
			assigned.append(_row(task, root, title=handoffs.title_for(root, task), status="Assigned", route=handoffs.route_for(root, task), action_label=handoffs.REGISTER[task.task_type][3]))
		elif cstr(task.sender) == user:
			title = handoffs.waiting_title_for(root, task)
			if title:
				holder = ns.holder(cstr(task.business_role), [handoffs.full_name(u) for u in holders])
				waiting.append(_row(task, root, title=title, status="Waiting", route=[PAGE, root.tender_reference], action_label="View", holder=holder))
	assigned += _successor_rows(user)
	return {"assigned": assigned, "claimable": [], "waiting": waiting}
