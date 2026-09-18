# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §8.1 GetPlanningWorkspace / §12.1 PLN-UI-01 (PLN-DES-01).

One scope predicate feeds every row and count. The actionable area is one
card of headline-plus-button rows containing only work the actor may perform
now (the read-offer-vs-command parity rule); it is absent, not empty, when
nothing is actionable. The departmental-plans table beneath is supporting
detail for that card. Where an Active Plan Version exists in scope the
workspace creates nothing (invariant
1). The Forbidden verdict is resolved before anything else (PLN-AC-111).
"""

from __future__ import annotations

from typing import Any

import frappe
import json

from frappe.utils import cstr, flt, fmt_money, formatdate

from kentender_core.services import site_configuration
from kentender_procurement.procurement_planning.services import needs_intake
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


def _date(value) -> str:
	return formatdate(value, "d MMM yyyy") if value else ""


def _count(n: int, noun: str) -> str:
	return f"{n} {noun}{'' if n == 1 else 's'}"


def _returned_on(version_name: str) -> str:
	submission = frappe.db.get_value("Departmental Plan Version", version_name, "returned_from_submission")
	if not submission:
		return ""
	decided = frappe.db.get_value(
		"Departmental Plan Validation Decision", {"submission": submission, "decision": "Return to department"}, "decided_at"
	)
	return _date(decided)


def _validation_line(task) -> str:
	"""FU-15 — department · submission · requirements · value · submitted when, by whom."""
	submission = frappe.db.get_value(
		"Departmental Plan Submission", task.submission, ["submitted_by_user", "submitted_at", "entry_snapshots"], as_dict=True,
	) or {}
	snapshots = json.loads(submission.get("entry_snapshots") or "[]")
	value = sum(flt(r.get("indicative_amount")) for r in snapshots if not cstr(r.get("not_proceeding_reason")).strip())
	version_number = frappe.db.get_value("Departmental Plan Version", task.dpp_version, "version_number")
	by = cstr(frappe.db.get_value("User", submission.get("submitted_by_user"), "full_name") or submission.get("submitted_by_user"))
	return (
		f"{_ou_label(task.organisation_unit)} · Submission {version_number} · {_count(len(snapshots), 'requirement')} · "
		f"{_money(value)} · submitted {_date(submission.get('submitted_at'))} by {by}"
	)


def _plan_line(plan, version, value: float, requested_at) -> str:
	"""FU-15 — plan · version · items · value · requested when."""
	items = frappe.db.count("Annual Plan Item", {"plan_version": version.name, "item_state": ("!=", "Dissolved")})
	return f"{plan.title} · Version {version.version_number} · {_count(items, 'item')} · {_money(value)} · requested {_date(requested_at)}"


def _validation_facts(task) -> list[tuple[str, Any]]:
	"""U01-D's own labelled facts for a Validate departmental plan task."""
	submission = frappe.db.get_value(
		"Departmental Plan Submission", task.submission, ["submitted_by_user", "submitted_at", "entry_snapshots"], as_dict=True,
	) or {}
	snapshots = json.loads(submission.get("entry_snapshots") or "[]")
	value = sum(flt(r.get("indicative_amount")) for r in snapshots if not cstr(r.get("not_proceeding_reason")).strip())
	by = cstr(frappe.db.get_value("User", submission.get("submitted_by_user"), "full_name") or submission.get("submitted_by_user"))
	return [
		("Submitted by", by),
		("Submitted", _date(submission.get("submitted_at"))),
		("Requirements", str(len(snapshots))),
		("Value", _money(value)),
	]


def _governance_facts(version, value: float) -> list[tuple[str, Any]]:
	"""U01-F's own labelled facts for an Accounting Officer/statutory decision task."""
	items = frappe.db.count("Annual Plan Item", {"plan_version": version.name, "item_state": ("!=", "Dissolved")})
	by = cstr(frappe.db.get_value("User", version.get("submitted_by_user"), "full_name") or version.get("submitted_by_user"))
	return [
		("Version", str(version.version_number)),
		("Plan Items", str(items)),
		("Value", _money(value)),
		("Submitted by", by),
		("Submitted", _date(version.get("submitted_at"))),
	]


def _allocated_value(version_name: str) -> float:
	return sum(
		flt(r.indicative_amount)
		for r in frappe.get_all(
			"Plan Source Allocation", filters={"plan_version": version_name, "allocation_state": ("in", ("Draft", "Active"))}, fields=["indicative_amount"],
		)
	)


# PLN-CHG-001 v1.18 §9.6 (U01) — the Annual Plan card's own fact rows and, at
# most, one discretionary command button distinct from the "Your actions"
# queue: a Planner-exercisable command when this actor holds it, a plain
# "View" link for every other reader, and no button while the candidate
# awaits a decision someone else's own task already carries (U01-F/U01-D).
FUNDING_BADGE = {
	"Not requested": "Not requested", "Awaiting confirmation": "Awaiting confirmation",
	"Confirmed": "Confirmed", "Returned": "Returned", "Stale": "Stale",
}


def _plan_version_facts(version, *, route: list[str]) -> dict[str, Any]:
	return {
		"route": route,
		"version_number": version.version_number,
		"version_status": version.version_status,
		"funding_state": FUNDING_BADGE.get(version.funding_state, cstr(version.funding_state)),
		"plan_items": frappe.db.count("Annual Plan Item", {"plan_version": version.name, "item_state": ("!=", "Dissolved")}),
		"value_display": _money(_allocated_value(version.name)),
	}


def _annual_plan_card(plan, active_version, open_version, *, is_planner: bool) -> list[dict[str, Any]]:
	if not plan:
		return []
	route = ["annual-procurement-plan", plan.plan_reference]
	blocks: list[dict[str, Any]] = []
	has_distinct_candidate = bool(active_version and open_version and open_version.name != active_version.name)
	if active_version:
		block = {"kind": "active", **_plan_version_facts(active_version, route=route)}
		if has_distinct_candidate:
			block.update(action="View Active Plan", action_kind="secondary")
		elif is_planner:
			block.update(action="Prepare plan update", action_kind="primary")
		else:
			block.update(action="View Active Plan", action_kind="secondary")
		blocks.append(block)
	if open_version and (not active_version or has_distinct_candidate):
		block = {"kind": "candidate" if active_version else "current", **_plan_version_facts(open_version, route=route)}
		if not is_planner:
			block.update(action="View", action_kind="secondary")
		elif open_version.version_status == "Draft":
			block.update(action="Continue Plan" if not active_version else "Continue update", action_kind="primary")
		elif open_version.version_status == "Published — activation held":
			block.update(action="View published Plan", action_kind="secondary")
		else:
			# Awaiting Accounting Officer / Awaiting statutory approval /
			# Approved — publication pending / Publication failed / Withdrawn
			# for correction: the decision or recovery lives on that actor's
			# own task in "Your actions" (U01-F), never a second button here.
			block.update(action="", action_kind="")
		blocks.append(block)
	return blocks


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
		# §4.3 — the root's state follows its current Version, so a Draft here
		# is either a plan never submitted or an update open beside an
		# accepted Version. Only the former can miss the window.
		if root.current_state == "Draft" and root.current_accepted_version:
			status, kind = "Accepted · update in progress", "attention"
		elif root.current_state in ("Draft", "Withdrawn") and not window_open and not root.current_accepted_version:
			status, kind = "Not submitted — window closed", "critical"
		accepted_number = (
			frappe.db.get_value("Departmental Plan Version", root.current_accepted_version, "version_number")
			if root.current_accepted_version else None
		)
		open_number = version_number if root.current_accepted_version and version_name != root.current_accepted_version else None
		rows.append(
			{
				"dpp_reference": root.dpp_reference,
				"department": _ou_label(root.organisation_unit),
				"organisation_unit": root.organisation_unit,
				"version": version_number,
				"version_name": version_name,
				"state": root.current_state,
				"requirements": len(entries),
				"value": _money(sum(flt(e.indicative_amount) for e in entries if not cstr(e.not_proceeding_reason).strip())),
				"status": status,
				"status_kind": kind,
				"accepted_submission": accepted_number,
				"open_submission": open_number,
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
	from kentender_procurement.procurement_planning.services import plan_read

	# §7.1 — an allocation pinned to an earlier copy of an unchanged entry
	# claims the current copy too, so a DPP update does not re-offer sources
	# the Plan already carries.
	allocated = plan_read.allocated_current_entries(fiscal_year)
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
	# A department with an accepted Version is covered whatever its current
	# Version's state — an open update (§4.3) is not a missed window.
	roots = frappe.get_all(
		"Departmental Plan",
		filters={"fiscal_year": fiscal_year},
		fields=["organisation_unit", "current_state", "current_accepted_version"],
	)
	covered = {
		r.organisation_unit
		for r in roots
		if r.current_state in ("Submitted", "Accepted", "Returned") or r.current_accepted_version
	}
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


def _action(
	headline: str, supporting: str, button: str, route: list[str], kind: str = "live",
	*, facts: list[tuple[str, Any]] | None = None,
) -> dict[str, Any]:
	# U01-D/E/F's own "Your actions" cards show labelled facts, not one prose
	# line; only the three variants a frame actually specifies get `facts` —
	# every other actionable kind keeps its existing free-text `supporting`.
	return {
		"headline": headline, "supporting": supporting, "action": button, "route": route, "kind": kind,
		"facts": [{"label": label, "value": value} for label, value in (facts or [])],
	}



# --------------------------------------------------------------------------
# PLN-CHG-001 v1.23 §10.3 — the U01 composition
#
# The workspace leads with the governing or draft plan, then one current issue,
# then departmental plans. The reservation arithmetic that used to sit here in
# four numbers is now one plain sentence and one recovery action; the full
# calculation stays in the Plan check detail (PLN22-CHG-003).
# --------------------------------------------------------------------------

#: Header copy per actor. The Planner owns the annual plan; a departmental
#: actor's page is about their own department's requirements.
HEADER_PLANNER = {
	"title": "Annual procurement planning",
	"description": "Prepare departmental requirements, organise the annual plan and follow its approval.",
}
HEADER_DEPARTMENTAL = {
	"title": "Procurement planning",
	"description": "Prepare your department's procurement requirements and follow their review.",
}


def _plan_rows(plan, active_version, open_version, *, is_planner: bool) -> list[dict[str, Any]]:
	"""The Annual plan section: one labelled row per independently existing
	thing. §9.1 requires Active and candidate to stay separate rows, each
	saying what it represents, and a Current plan link to resolve the actual
	Active pointer rather than the highest version number."""
	if not plan:
		return []
	route = ["annual-procurement-plan", plan.plan_reference]
	rows: list[dict[str, Any]] = []
	distinct_candidate = bool(active_version and open_version and open_version.name != active_version.name)

	if active_version:
		value = _allocated_value(active_version.name)
		rows.append(
			{
				"kind": "current",
				"facts": [
					("Current plan", plan.title),
					("Version", str(active_version.version_number)),
					("Approved value", _money(value)),
					("Status", "Current plan"),
					("Plan reference", plan.plan_reference),
				],
				"note": "",
				"action": "View current plan",
				"action_kind": "secondary",
				"route": route,
				# §11.5 — what has actually been procured against the plan in
				# force is its own surface (U14), reached from the plan it is
				# about rather than from a separate menu entry.
				"secondary_action": "View procurement progress",
				"secondary_route": [*route, "progress"],
			}
		)

	if open_version and (not active_version or distinct_candidate):
		value = _allocated_value(open_version.name)
		items = frappe.db.count("Annual Plan Item", {"plan_version": open_version.name, "item_state": ("!=", "Dissolved")})
		if active_version:
			facts = [
				("Work", "Plan update — Draft" if open_version.version_status == "Draft" else open_version.version_status),
				("Version", str(open_version.version_number)),
				("Proposed value", _money(value)),
			]
			change = cstr(open_version.get("change_reason"))
			if change:
				facts.append(("Change", change))
			action = "Continue update" if (is_planner and open_version.version_status == "Draft") else "View plan update"
			note = ""
		else:
			facts = [
				("Current plan", "No current plan yet"),
				("Work", "Draft plan" if open_version.version_status == "Draft" else open_version.version_status),
				("Version", str(open_version.version_number)),
				("Purchases", str(items)),
				("Estimated cost", _money(value)),
				("Plan reference", plan.plan_reference),
			]
			action = "Continue plan" if (is_planner and open_version.version_status == "Draft") else "View plan"
			note = "This plan is being prepared. It cannot yet be used to authorise procurement."
		rows.append(
			{
				"kind": "candidate" if active_version else "draft",
				"facts": facts,
				"note": note,
				"action": action,
				"action_kind": "primary" if action.startswith("Continue") else "secondary",
				"route": route,
			}
		)
	return rows


def _current_issue(plan, open_version, *, is_planner: bool) -> dict[str, Any] | None:
	"""One plain sentence and one recovery action, placed immediately below the
	plan row. Never four accounting values (PLN22-AC-006)."""
	if not (plan and open_version and open_version.version_status == "Draft" and is_planner):
		return None
	from kentender_procurement.procurement_planning.services import readiness

	try:
		allocations = readiness.reservation_allocations(open_version.name, plan.fiscal_year)
	except Exception:
		return None
	if not allocations.get("mandatory") or allocations.get("met"):
		return None
	shortfall = cstr(allocations.get("shortfall"))
	if not shortfall:
		return None
	return {
		"text": f"Allocate {_money(flt(shortfall))} more to eligible reserved procurement before sending the plan to Finance.",
		"action": "Review reserved procurement",
		"route": ["annual-procurement-plan", plan.plan_reference],
	}


def _departmental_table(dpp_rows: list[dict[str, Any]]) -> dict[str, Any]:
	"""Department / Status / Requirements / Estimated cost / Action. Submission
	numbers are deliberately absent from this summary (§10.3)."""
	return {
		"heading": "Departmental plans",
		"columns": ["Department", "Status", "Requirements", "Estimated cost", "Action"],
		"rows": [
			{
				"department": row["department"],
				"status": row["status"],
				"status_kind": row["status_kind"],
				"requirements": row["requirements"],
				"value": row["value"],
				"action": "View departmental plan" if row["route"] else "",
				"route": row["route"],
			}
			for row in dpp_rows
		],
		"count_label": f"{len(dpp_rows)} departmental plan{'s' if len(dpp_rows) != 1 else ''}",
		"empty_text": "No departmental plans to display.",
	}


def _own_departmental_section(dpp_rows, departmental_units, *, window_open: bool) -> dict[str, Any] | None:
	"""U01-DEPARTMENT-AUTHOR / U01-HOD — "Your departmental plan"."""
	if not departmental_units:
		return None
	unit = departmental_units[0]
	row = next((r for r in dpp_rows if r["organisation_unit"] == unit["id"]), None)
	if row is None:
		if not window_open:
			return None
		return {
			"heading": "Your departmental plan",
			"empty": True,
			"empty_text": "No departmental plan yet",
			"action": "Start departmental plan",
			"organisation_unit": unit["id"],
		}
	return {
		"heading": "Your departmental plan",
		"empty": False,
		"facts": [("Department", row["department"]), ("Status", row["status"])],
		"action": "Continue departmental plan" if row["state"] == "Draft" else "View departmental plan",
		"route": row["route"],
	}


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
				# the §5.1 "Open departmental plan" command — labelled as what it
				# does for the user, never as "Open" beside a navigate button
				actionable.append(
					_action(
						f"No departmental plan yet for {context.get('financial_year_label') or fy}",
						unit["name"], "Start departmental plan", [PAGE, "open", unit["id"]],
					)
				)
			continue
		# FU-15 — every supporting line carries version, size and value
		detail = f"{row['department']} · Submission {row['version']} · {_count(row['requirements'], 'requirement')} · {row['value']}"
		if row["state"] == "Draft" and row["status_kind"] != "critical":
			actionable.append(
				_action(
					"Continue departmental plan", detail, "Continue", row["route"], "attention",
					facts=[("Submission", str(row["version"])), ("Requirements", str(row["requirements"])), ("Specified value", row["value"])],
				)
			)
		elif row["state"] == "Returned":
			returned = _returned_on(row["version_name"])
			actionable.append(_action("Correct and resubmit departmental plan", f"{detail} · returned {returned}" if returned else detail, "Correct", row["route"], "critical"))
		elif row["state"] == "Submitted":
			waiting.append({"item": "Departmental plan awaiting validation", "scope": row["department"]})

	plan = frappe.db.get_value(
		"Annual Plan", {"fiscal_year": fy},
		["name", "plan_reference", "title", "active_version", "open_successor_version"], as_dict=True,
	)
	open_version = None
	if plan and (plan.open_successor_version or plan.active_version):
		open_version = frappe.db.get_value(
			"Annual Plan Version", plan.open_successor_version or plan.active_version,
			["name", "version_number", "version_status", "funding_state", "submitted_by_user", "submitted_at"], as_dict=True,
		)
	active_version_doc = None
	if plan and plan.active_version:
		active_version_doc = (
			open_version if open_version and open_version.name == plan.active_version
			else frappe.db.get_value("Annual Plan Version", plan.active_version, ["name", "version_number", "version_status", "funding_state"], as_dict=True)
		)

	if is_planner:
		for task in frappe.get_all(
			"Departmental Plan Validation Task",
			filters={"fiscal_year": fy, "status": "Open"},
			fields=["name", "organisation_unit", "submission", "dpp_version"],
			order_by="creation asc",
			limit_page_length=0,
		):
			if authz.is_segregated(actor, authz.ACTION_DPP_VALIDATE, submission=task.submission):
				waiting.append({"item": "Departmental plan awaiting validation by another Planner", "scope": _ou_label(task.organisation_unit)})
				continue
			actionable.append(
				_action(
					"Validate departmental plan", _validation_line(task), "Review submission", [PAGE, "dpp-review", task.name], "attention",
					facts=_validation_facts(task),
				)
			)
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
		elif count and plan and open_version and open_version.version_status == "Active" and not plan.open_successor_version:
			# §5 "Active; no successor → Begin plan update": the Planner holds
			# the command, so the workspace offers it rather than a waiting line
			plural = "entry" if count == 1 else "entries"
			actionable.append(
				_action(
					f"{count} accepted departmental {plural} not yet in the Active plan",
					f"{' · '.join(departments)} · {_money(value)}",
					"Prepare plan update",
					["annual-procurement-plan", plan.plan_reference],
					"attention",
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
		for task in frappe.get_all("Plan Finance Task", filters={"plan_version": open_version.name, "status": "Open"}, fields=["name", "plan_value", "creation"]):
			if authz.is_segregated(actor, authz.ACTION_FINANCE_DECIDE, plan_version=open_version.name):
				continue
			actionable.append(_action("Confirm plan funding", _plan_line(plan, open_version, flt(task.plan_value), task.creation), "Open Finance task", [PAGE, "finance", task.name]))

	if plan and open_version:
		for stage, role, action in (
			("Accounting Officer adoption", ROLE_ACCOUNTING_OFFICER, authz.ACTION_AO_DECIDE),
			("Statutory approval", ROLE_PLAN_STATUTORY_APPROVER, authz.ACTION_STATUTORY_DECIDE),
		):
			if not authz.has_site_role(role, actor):
				continue
			for task in frappe.get_all(
				"Plan Governance Task", filters={"plan_version": open_version.name, "stage": stage, "status": "Open"}, fields=["name", "creation"]
			):
				if authz.is_segregated(actor, action, plan_version=open_version.name):
					continue
				headline = "Adopt the Annual Procurement Plan" if stage == "Accounting Officer adoption" else "Approve the Annual Procurement Plan"
				value = _allocated_value(open_version.name)
				actionable.append(
					_action(
						headline, _plan_line(plan, open_version, value, task.creation), "Open decision", [PAGE, "review", task.name],
						facts=_governance_facts(open_version, value),
					)
				)

	rows = _plan_rows(plan, active_version_doc, open_version, is_planner=is_planner)
	# §10.3 U01-CURRENT: the Planner may start an update only while no candidate
	# exists; U01-CURRENT-UPDATE removes the control rather than disabling it.
	can_prepare_update = bool(
		is_planner and plan and active_version_doc
		and not (open_version and open_version.name != active_version_doc.name)
	)
	return {
		"outcome": "OK",
		"context": context,
		"window_open": window_open,
		# §9.1 — a departmental actor's page is about their own requirements.
		"header": HEADER_DEPARTMENTAL if (departmental_units and not is_planner) else HEADER_PLANNER,
		"annual_plan": {
			"heading": "Annual plan",
			"plan_reference": plan.plan_reference if plan else "",
			"title": plan.title if plan else "",
			"rows": rows,
			"can_prepare_update": can_prepare_update,
			"prepare_update_action": "Prepare plan update",
			# §10.3 U01-CURRENT-UPDATE
			"update_note": (
				"The current plan remains in force while this update is reviewed."
				if len(rows) > 1 else ""
			),
			# §10.3 U01-NO-PLAN — an empty state, never a create action.
			"empty_title": "No annual plan yet",
			"empty_text": "The draft annual plan will appear after Procurement accepts a departmental plan.",
			# A departmental actor reads the annual plan; they never act on it.
			"read_only": not is_planner,
		},
		"current_issue": _current_issue(plan, open_version, is_planner=is_planner),
		"your_departmental_plan": _own_departmental_section(dpp_rows, departmental_units, window_open=window_open),
		# §9.1 — "Omit an empty Your actions section."
		"actionable": actionable,
		"waiting": waiting,
		"departmental_table": _departmental_table(dpp_rows),
		"departmental_plans": dpp_rows,
		"not_included": _not_included(fy, window_open),
	}
