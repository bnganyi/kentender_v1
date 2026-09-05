# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §8.1 GetPlanningWorkspace / §12.1 PLN-UI-01 (PLN-DES-01).

One scope predicate feeds every row and count. The actionable area is one
card of headline-plus-button rows containing only work the actor may perform
now (the read-offer-vs-command parity rule); it is absent, not empty, when
nothing is actionable. The departmental-plans table beneath is supporting
detail for that card. Where an Active Plan Version exists in scope the
workspace shows one schedule-health count. Reads create nothing (invariant
1). The Forbidden verdict is resolved before anything else (PLN-AC-111).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, fmt_money

from kentender_core.services import site_configuration
from kentender_procurement.procurement_planning.services import needs_intake, schedule
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_context import resolve_planning_context
from kentender_procurement.procurement_planning.services.planning_roles import (
	FORBIDDEN_RESPONSIBILITIES,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_AUDITOR,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PROCUREMENT_PLANNER,
)

PAGE = "procurement-planning"

FORBIDDEN = {
	"heading": "You do not have access to Procurement Planning",
	"text": (
		f"This area needs one of these responsibilities: {FORBIDDEN_RESPONSIBILITIES}. "
		"Ask your KenTender administrator to assign one in System setup."
	),
}


def _money(amount: float) -> str:
	return f"KES {fmt_money(flt(amount), precision=0, currency=None).strip()}"


def _ou_label(ou: str) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)


ROOT_STATUS = {
	"Draft": ("Draft", "attention"),
	"Submitted": ("Awaiting validation", "attention"),
	"Returned": ("Returned", "critical"),
	"Accepted": ("Accepted", "live"),
	"Withdrawn": ("Withdrawn", "muted"),
}


def _dpp_rows(fiscal_year: str, permitted_units: set[str] | None, window_open: bool, can_open_dpp: bool) -> list[dict[str, Any]]:
	roots = frappe.get_all(
		"Departmental Plan",
		filters={"fiscal_year": fiscal_year},
		fields=["name", "dpp_reference", "organisation_unit", "current_state", "current_version", "current_accepted_version"],
		order_by="dpp_reference asc",
		limit_page_length=0,
	)
	rows = []
	for root in roots:
		if permitted_units is not None and root.organisation_unit not in permitted_units:
			continue
		version_name = root.current_version or root.current_accepted_version
		version_number = frappe.db.get_value("Departmental Plan Version", version_name, "version_number") if version_name else None
		entries = frappe.get_all(
			"Departmental Plan Entry",
			filters={"dpp_version": version_name or ""},
			fields=["indicative_amount", "not_proceeding_reason"],
			limit_page_length=0,
		)
		status, kind = ROOT_STATUS.get(root.current_state, (root.current_state, "muted"))
		if root.current_state in ("Draft", "Withdrawn") and not window_open:
			status, kind = "Not submitted — window closed", "critical"
		rows.append(
			{
				"dpp_reference": root.dpp_reference,
				"department": _ou_label(root.organisation_unit),
				"organisation_unit": root.organisation_unit,
				"version": version_number,
				"requirements": len(entries),
				"value": _money(sum(flt(e.indicative_amount) for e in entries if not cstr(e.not_proceeding_reason).strip())),
				"status": status,
				"status_kind": kind,
				"route": ["departmental-procurement-plan", root.dpp_reference] if can_open_dpp else None,
			}
		)
	return rows


def _accepted_unallocated(fiscal_year: str) -> tuple[int, float, list[str]]:
	"""§8.1 ListAcceptedDPPSources scope: current accepted entries (that
	proceed) not yet effectively allocated in the open Plan Version."""
	accepted_versions = frappe.get_all(
		"Departmental Plan", filters={"fiscal_year": fiscal_year, "current_accepted_version": ("!=", "")},
		fields=["current_accepted_version", "organisation_unit"],
	)
	if not accepted_versions:
		return 0, 0.0, []
	unit_by_version = {r.current_accepted_version: r.organisation_unit for r in accepted_versions}
	entries = frappe.get_all(
		"Departmental Plan Entry",
		filters={"dpp_version": ("in", list(unit_by_version)), "not_proceeding_reason": ("in", ("", None))},
		fields=["name", "indicative_amount", "dpp_version"],
		limit_page_length=0,
	)
	allocated = set(
		frappe.get_all(
			"Plan Source Allocation",
			filters={"dpp_entry": ("in", [e.name for e in entries] or ("",)), "allocation_state": ("in", ("Draft", "Active"))},
			pluck="dpp_entry",
		)
	)
	free = [e for e in entries if e.name not in allocated]
	departments = sorted({_ou_label(unit_by_version[e.dpp_version]) for e in free})
	return len(free), sum(flt(e.indicative_amount) for e in free), departments


def _not_included(fiscal_year: str, window_open: bool) -> dict[str, str] | None:
	"""§7.1 — accepted Needs stranded by a closed window stay visible."""
	if window_open:
		return None
	try:
		sources = needs_intake.current_accepted_sources(fiscal_year)
	except Exception:
		return None
	covered = set(
		frappe.get_all(
			"Departmental Plan",
			filters={"fiscal_year": fiscal_year, "current_state": ("in", ("Submitted", "Accepted", "Returned"))},
			pluck="organisation_unit",
		)
	)
	stranded = [s for s in sources if cstr(s.get("org_unit_id")) not in covered]
	if not stranded:
		return None
	count = len(stranded)
	departments = sorted({_ou_label(cstr(s.get("org_unit_id"))) for s in stranded})
	noun = "Need" if count == 1 else "Needs"
	verb = "is" if count == 1 else "are"
	return {
		"title": f"{count} accepted {noun} {verb} not included in any departmental plan",
		"text": (
			f"{count} accepted {noun} from {' and '.join(departments)} {'was' if count == 1 else 'were'} not included "
			"because the departmental-plan submission window closed before they were added. "
			"Ask the department to raise this with your KenTender administrator."
		),
	}


def _action(headline: str, supporting: str, button: str, route: list[str], kind: str = "live") -> dict[str, Any]:
	return {"headline": headline, "supporting": supporting, "action": button, "route": route, "kind": kind}


def get_planning_workspace(*, financial_year: str | None = None, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if not authz.holds_any_planning_responsibility(actor):
		return {"outcome": "FORBIDDEN", "forbidden": FORBIDDEN}
	context = resolve_planning_context(financial_year=financial_year, user=actor)
	fy = context.get("financial_year")
	if not fy:
		return {"outcome": "NO_CONTEXT", "context": context}

	window_open = bool(site_configuration.get_dpp_submission_state(fy).get("open"))
	permitted_units = authz.workspace_units(actor)
	departmental_units = authz.creation_units(actor)
	is_planner = authz.has_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	# §12.1 route table — only the actors `dpp_read` will actually admit get a
	# route; Site-wide oversight roles see the row without a dead-end link.
	can_open_dpp = (
		bool(departmental_units)
		or authz.is_technical(actor)
		or authz.can_read_site(ROLE_PROCUREMENT_PLANNER, actor)
		or authz.can_read_site(ROLE_AUDITOR, actor)
	)
	dpp_rows = _dpp_rows(fy, permitted_units, window_open, can_open_dpp)

	actionable: list[dict[str, Any]] = []
	waiting: list[dict[str, Any]] = []

	for unit in departmental_units:
		row = next((r for r in dpp_rows if r["organisation_unit"] == unit["id"]), None)
		if row is None:
			if window_open:
				actionable.append(_action("Open departmental plan", unit["name"], "Open departmental plan", [PAGE, "open", unit["id"]]))
			continue
		if row["status"] == "Draft":
			actionable.append(_action("Continue departmental plan", f"{row['department']} · {row['requirements']} requirements", "Open", row["route"], "attention"))
		elif row["status"] == "Returned":
			actionable.append(_action("Correct and resubmit departmental plan", row["department"], "Open", row["route"], "critical"))
		elif row["status"] == "Awaiting validation":
			waiting.append({"item": "Departmental plan awaiting validation", "scope": row["department"]})

	plan = frappe.db.get_value(
		"Annual Plan", {"fiscal_year": fy},
		["name", "plan_reference", "title", "active_version", "open_successor_version"], as_dict=True,
	)
	open_version = None
	if plan and (plan.open_successor_version or plan.active_version):
		open_version = frappe.db.get_value(
			"Annual Plan Version", plan.open_successor_version or plan.active_version,
			["name", "version_number", "version_status", "funding_state"], as_dict=True,
		)

	if is_planner:
		for task in frappe.get_all(
			"Departmental Plan Validation Task",
			filters={"fiscal_year": fy, "status": "Open"},
			fields=["name", "organisation_unit", "submission"],
			order_by="creation asc",
			limit_page_length=0,
		):
			if authz.is_segregated(actor, authz.ACTION_DPP_VALIDATE, submission=task.submission):
				waiting.append({"item": "Departmental plan awaiting validation by another Planner", "scope": _ou_label(task.organisation_unit)})
				continue
			actionable.append(_action("Validate departmental plan", _ou_label(task.organisation_unit), "Review", [PAGE, "dpp-review", task.name], "attention"))
		count, value, departments = _accepted_unallocated(fy)
		if count and plan and open_version and open_version.version_status == "Draft":
			plural = "entry" if count == 1 else "entries"
			actionable.append(
				_action(
					f"{count} accepted departmental {plural} ready to consolidate",
					f"{' · '.join(departments)} · {_money(value)}",
					"Open Annual Plan",
					["annual-procurement-plan", plan.plan_reference],
				)
			)
		elif count and plan and open_version and open_version.version_status != "Draft":
			waiting.append({"item": f"{count} accepted departmental {'entry' if count == 1 else 'entries'} pending addition to the next Draft", "scope": _money(value)})
		if plan and open_version and open_version.version_status == "Draft" and open_version.funding_state == "Returned":
			actionable.append(_action("Plan funding returned by Finance", plan.title, "Open Annual Plan", ["annual-procurement-plan", plan.plan_reference], "critical"))
		if plan and open_version and open_version.version_status in ("Awaiting Accounting Officer", "Awaiting statutory approval"):
			waiting.append({"item": f"Annual Plan {open_version.version_status.lower()}", "scope": plan.title})
		if plan and open_version and open_version.version_status == "Publication failed":
			waiting.append({"item": "Publication was not acknowledged; a technical retry is pending", "scope": plan.title})

	if plan and open_version and authz.has_site_role(ROLE_FINANCE_CONFIRMATION_OFFICER, actor):
		for task in frappe.get_all("Plan Finance Task", filters={"plan_version": open_version.name, "status": "Open"}, fields=["name"]):
			if authz.is_segregated(actor, authz.ACTION_FINANCE_DECIDE, plan_version=open_version.name):
				continue
			actionable.append(_action("Confirm plan funding", plan.title, "Open Finance task", [PAGE, "finance", task.name]))

	if plan and open_version:
		for stage, role, action in (
			("Accounting Officer adoption", ROLE_ACCOUNTING_OFFICER, authz.ACTION_AO_DECIDE),
			("Statutory approval", ROLE_PLAN_STATUTORY_APPROVER, authz.ACTION_STATUTORY_DECIDE),
		):
			if not authz.has_site_role(role, actor):
				continue
			for task in frappe.get_all(
				"Plan Governance Task", filters={"plan_version": open_version.name, "stage": stage, "status": "Open"}, fields=["name"]
			):
				if authz.is_segregated(actor, action, plan_version=open_version.name):
					continue
				headline = "Adopt the Annual Procurement Plan" if stage == "Accounting Officer adoption" else "Approve the Annual Procurement Plan"
				actionable.append(_action(headline, plan.title, "Open decision", [PAGE, "review", task.name]))

	health = None
	if plan and plan.active_version:
		health = schedule.schedule_health(plan.active_version)

	plan_summary = ""
	if open_version:
		plan_summary = f"Annual Plan · {open_version.version_status} Version {open_version.version_number}"
	count_label = f"{len(dpp_rows)} departmental plan{'s' if len(dpp_rows) != 1 else ''}"
	return {
		"outcome": "OK",
		"context": context,
		"window_open": window_open,
		"annual_plan": {"plan_reference": plan.plan_reference if plan else "", "summary": plan_summary},
		"actionable": actionable,
		"waiting": waiting,
		"schedule_health": health,
		"departmental_plans": dpp_rows,
		"departmental_plans_heading": "Departmental plans feeding this Annual Plan",
		"departmental_plans_lede": "These are the accepted and pending plans behind the entry above.",
		"count_label": count_label,
		"not_included": _not_included(fy, window_open),
	}
