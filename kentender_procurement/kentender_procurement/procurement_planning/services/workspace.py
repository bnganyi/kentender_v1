# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §8.1 GetPlanningWorkspace / §12.1 PLN-UI-01.

One scope predicate feeds every row and count. The action queue offers only
work the actor may decide now (the NDS-807/NDS-911 read-offer-vs-command
class: whatever appears here must be accepted by the command layer, and every
open task an actor may decide must appear here). Reads create nothing
(invariant 1)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, fmt_money, get_datetime, now_datetime

from kentender_procurement.procurement_planning.services import needs_intake
from kentender_procurement.procurement_planning.services.planning_context import (
	resolve_planning_context,
)
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_BUDGET_OFFICER,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PLANNING_AUDITOR,
	ROLE_PROCUREMENT_PLANNER,
)

PAGE = "procurement-planning"


def _money(amount: float) -> str:
	return f"KES {fmt_money(flt(amount), precision=0, currency=None).strip()}"


def _ou_label(ou: str) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)


def _window_state(ctx: str) -> str:
	row = frappe.db.get_value(
		"Departmental Plan Submission Window",
		{"pe_fy_context": ctx},
		["opens_at", "closes_at"],
		as_dict=True,
	)
	if not row:
		return "None"
	now = now_datetime()
	if now < get_datetime(row.opens_at):
		return "Scheduled"
	if now > get_datetime(row.closes_at):
		return "Closed"
	return "Open"


ROOT_STATUS = {
	"Draft": ("Draft", "attention"),
	"Submitted": ("Awaiting validation", "attention"),
	"Returned": ("Returned", "critical"),
	"Accepted": ("Accepted", "live"),
	"Withdrawn": ("Withdrawn", "muted"),
}


def _dpp_rows(ctx: str, permitted_ous: set[str] | None, window_state: str) -> list[dict[str, Any]]:
	roots = frappe.get_all(
		"Departmental Plan",
		filters={"pe_fy_context": ctx},
		fields=[
			"name", "dpp_reference", "organisation_unit", "current_state",
			"current_version", "current_accepted_version",
		],
		order_by="dpp_reference asc",
		limit_page_length=0,
	)
	rows = []
	for root in roots:
		if permitted_ous is not None and root.organisation_unit not in permitted_ous:
			continue
		version_name = root.current_version or root.current_accepted_version
		version_number = (
			frappe.db.get_value("Departmental Plan Version", version_name, "version_number")
			if version_name
			else None
		)
		entries = frappe.get_all(
			"Departmental Plan Entry",
			filters={"dpp_version": version_name or ""},
			fields=["indicative_amount"],
			limit_page_length=0,
		)
		status, kind = ROOT_STATUS.get(root.current_state, (root.current_state, "muted"))
		if root.current_state in ("Draft", "Withdrawn") and window_state == "Closed":
			status, kind = "Not submitted — window closed", "critical"
		rows.append(
			{
				"dpp_reference": root.dpp_reference,
				"department": _ou_label(root.organisation_unit),
				"organisation_unit": root.organisation_unit,
				"version": version_number,
				"requirements": len(entries),
				"value": _money(sum(flt(e.indicative_amount) for e in entries)),
				"status": status,
				"status_kind": kind,
				"route": ["departmental-procurement-plan", root.dpp_reference],
			}
		)
	return rows


def _accepted_unallocated(ctx: str) -> tuple[int, float]:
	"""§8.1 ListAcceptedDPPSources scope: current accepted entries not yet
	effectively allocated in the open Plan Version."""
	accepted_versions = frappe.get_all(
		"Departmental Plan",
		filters={"pe_fy_context": ctx, "current_accepted_version": ("!=", "")},
		pluck="current_accepted_version",
	)
	if not accepted_versions:
		return 0, 0.0
	entries = frappe.get_all(
		"Departmental Plan Entry",
		filters={"dpp_version": ("in", accepted_versions)},
		fields=["name", "indicative_amount"],
		limit_page_length=0,
	)
	allocated = set(
		frappe.get_all(
			"Plan Source Allocation",
			filters={
				"dpp_entry": ("in", [e.name for e in entries] or ("",)),
				"allocation_state": ("in", ("Draft", "Active")),
			},
			pluck="dpp_entry",
		)
	)
	free = [e for e in entries if e.name not in allocated]
	return len(free), sum(flt(e.indicative_amount) for e in free)


def _not_included(ctx: str, pe: str, fy: str, window_state: str) -> str:
	"""§7.1 — accepted Needs stranded by a closed window stay visible."""
	if window_state != "Closed":
		return ""
	try:
		sources = needs_intake.current_accepted_sources(pe, fy)
	except Exception:
		return ""
	covered_ous = set(
		frappe.get_all(
			"Departmental Plan",
			filters={"pe_fy_context": ctx, "current_state": ("in", ("Submitted", "Accepted", "Returned"))},
			pluck="organisation_unit",
		)
	)
	stranded = [s for s in sources if cstr(s.get("org_unit_id")) not in covered_ous]
	if not stranded:
		return ""
	count = len(stranded)
	plural = "Need is" if count == 1 else "Needs are"
	return (
		f"{count} accepted {plural} not included because the departmental-plan "
		"submission window closed."
	)


def get_planning_workspace(
	*, procuring_entity: str | None = None, financial_year: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	context = resolve_planning_context(
		procuring_entity=procuring_entity, financial_year=financial_year, user=actor
	)
	if context.get("no_scope"):
		return {"outcome": "NO_SCOPE", "context": context}
	pe, fy = context.get("procuring_entity"), context.get("financial_year")
	if not pe or not fy:
		return {"outcome": "SELECTION_REQUIRED", "context": context}
	ctx_rows = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"procuring_entity": pe, "financial_year": fy},
		pluck="name",
		limit_page_length=2,
	)
	if len(ctx_rows) != 1:
		return {"outcome": "SELECTION_REQUIRED", "context": context}
	ctx = ctx_rows[0]

	roles = set(frappe.get_roles(actor))
	from kentender_procurement.procurement_planning.services.authority import (
		permitted_org_units,
	)

	departmental = bool(
		roles & {ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT}
	)
	oversight = bool(
		roles & {ROLE_PROCUREMENT_PLANNER, ROLE_PLANNING_AUDITOR, ROLE_ACCOUNTING_OFFICER,
		         ROLE_PLAN_STATUTORY_APPROVER, ROLE_BUDGET_OFFICER}
	)
	permitted_ous = None if oversight else (permitted_org_units(actor) or set())

	window_state = _window_state(ctx)
	dpp_rows = _dpp_rows(ctx, permitted_ous, window_state)
	your_work: list[dict[str, Any]] = []

	if departmental and permitted_ous is not None:
		for ou in sorted(permitted_ous):
			row = next((r for r in dpp_rows if r["organisation_unit"] == ou), None)
			if row is None:
				if window_state == "Open":
					your_work.append(
						{
							"item": "Open departmental plan",
							"scope": _ou_label(ou),
							"status": "Ready",
							"status_kind": "live",
							"action": "Open departmental plan",
							"route": [PAGE, "open", ou],
						}
					)
				continue
			if row["status"] in ("Draft",):
				your_work.append(
					{
						"item": "Continue departmental plan",
						"scope": f"{row['department']} · {row['requirements']} requirements",
						"status": "Draft",
						"status_kind": "attention",
						"action": "Open",
						"route": row["route"],
					}
				)
			elif row["status"] == "Returned":
				your_work.append(
					{
						"item": "Correct and resubmit departmental plan",
						"scope": row["department"],
						"status": "Returned",
						"status_kind": "critical",
						"action": "Open",
						"route": row["route"],
					}
				)

	if ROLE_PROCUREMENT_PLANNER in roles:
		open_tasks = frappe.get_all(
			"Departmental Plan Validation Task",
			filters={"procuring_entity": pe, "financial_year": fy, "status": "Open"},
			fields=["name", "task_reference", "organisation_unit"],
			order_by="creation asc",
			limit_page_length=0,
		)
		planner_ous = permitted_org_units(actor)
		for task in open_tasks:
			if planner_ous and task.organisation_unit not in planner_ous:
				continue
			your_work.append(
				{
					"item": "Validate departmental plan",
					"scope": _ou_label(task.organisation_unit),
					"status": "Awaiting validation",
					"status_kind": "attention",
					"action": "Review",
					"route": [PAGE, "dpp-review", task.name],
				}
			)
		count, value = _accepted_unallocated(ctx)
		if count:
			plural = "entry" if count == 1 else "entries"
			your_work.append(
				{
					"item": "Form Plan Items",
					"scope": f"{count} accepted departmental {plural} · {_money(value)}",
					"status": "Ready",
					"status_kind": "live",
					"action": "Open Annual Plan",
					"route": ["annual-procurement-plan"],
				}
			)

	plan = frappe.db.get_value(
		"Annual Plan",
		{"pe_fy_context": ctx},
		["plan_reference", "title", "active_version", "open_successor_version"],
		as_dict=True,
	)
	plan_summary = ""
	if plan:
		open_version = plan.open_successor_version or plan.active_version
		if open_version:
			row = frappe.db.get_value(
				"Annual Plan Version", open_version,
				["version_number", "version_status"],
				as_dict=True,
			)
			plan_summary = f"Annual Plan · {row.version_status} Version {row.version_number}"

	count_label = (
		f"{len(dpp_rows)} departmental plan{'s' if len(dpp_rows) != 1 else ''}"
	)
	return {
		"outcome": "OK",
		"context": context,
		"window_state": window_state,
		"annual_plan": {
			"plan_reference": plan.plan_reference if plan else "",
			"summary": plan_summary,
		},
		"your_work": your_work,
		"departmental_plans": dpp_rows,
		"count_label": count_label,
		"not_included_message": _not_included(ctx, pe, fy, window_state),
	}
