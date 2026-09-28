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
	"heading": "You do not have access to Procurement Planning.",
	# U21-DENIED draws two separate paragraphs, not one run-together
	# sentence, and its own second sentence says "check your assignment",
	# not "assign one" (re-diffed 22 Sep 2026 against the real v1.24
	# artboard).
	"text": [
		f"This area needs one of these responsibilities: {FORBIDDEN_RESPONSIBILITIES}.",
		"Ask your KenTender administrator to check your assignment in System setup.",
	],
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
			fields=["indicative_amount", "not_proceeding_reason", "budget_line"],
			limit_page_length=0,
		)
		# Matches dpp_read.get_departmental_plan's own "complete" predicate — an
		# entry counts once it is either funded (budget line + a positive
		# amount) or explicitly excluded, never merely present.
		incomplete = sum(
			1 for e in entries
			if not cstr(e.not_proceeding_reason).strip() and not (e.budget_line and flt(e.indicative_amount) > 0)
		)
		status, kind = ROOT_STATUS.get(root.current_state, (root.current_state, "muted"))
		# §4.3 — the root's state follows its current Version, so a Draft here
		# is either a plan never submitted or an update open beside an
		# accepted Version. Only the former can miss the window.
		if root.current_state == "Draft" and root.current_accepted_version:
			status, kind = "Accepted · update in progress", "attention"
		elif root.current_state in ("Draft", "Withdrawn") and not window_open and not root.current_accepted_version:
			status, kind = "Not submitted — window closed", "critical"
		# Owner decision 26 Sep 2026 — an accepted plan missing Needs accepted
		# after it is not finished: only the department's update adds them.
		late = needs_intake.late_needs(root)
		if late:
			status, kind = f"Accepted · {len(late)} accepted need{'s' if len(late) != 1 else ''} not in plan", "attention"
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
				"incomplete": incomplete,
				"value": _money(sum(flt(e.indicative_amount) for e in entries if not cstr(e.not_proceeding_reason).strip())),
				"status": status,
				"status_kind": kind,
				"accepted_submission": accepted_number,
				"open_submission": open_number,
				"route": ["departmental-procurement-plan", root.dpp_reference] if can_open_dpp else None,
				"late_needs": needs_intake.need_list(late) if late else "",
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


def _affected_purchases(active_version, open_version) -> str:
	"""Which of the plan's purchases this update actually changes — added,
	removed, or moved in scope or value.

	Computed from the live rows rather than a stored summary, because a Draft
	successor is still being edited and any frozen description of it would be
	stale the moment it was written. Nothing changed yet is an honest empty
	result, not a guess."""
	if not (active_version and open_version):
		return ""

	#: What "the purchase changed" means here: what it is, how much of it, and
	#: what it costs. A schedule or method change is a change to how it will be
	#: procured, not to the purchase itself, and belongs to the update's own
	#: reason rather than to this list.
	fields = ("title", "description")

	def snapshot(version_name: str) -> dict[str, tuple]:
		rows: dict[str, tuple] = {}
		for item in frappe.get_all(
			"Annual Plan Item",
			filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")},
			fields=["name", "plan_item_id", *fields],
			limit_page_length=0,
		):
			totals = frappe.get_all(
				"Plan Source Allocation",
				filters={"plan_item": item.name, "allocation_state": ("!=", "Released")},
				fields=["quantity", "indicative_amount"],
				limit_page_length=0,
			)
			rows[cstr(item.plan_item_id)] = (
				tuple(cstr(item.get(field)) for field in fields),
				sum(flt(t.quantity) for t in totals),
				sum(flt(t.indicative_amount) for t in totals),
			)
		return rows

	before, after = snapshot(active_version.name), snapshot(open_version.name)
	changed = [row[0][0] for plan_item_id, row in after.items() if before.get(plan_item_id) != row]
	changed += [row[0][0] for plan_item_id, row in before.items() if plan_item_id not in after]
	return " · ".join(sorted(set(changed)))


def _actionable_heading(actionable: list[dict[str, Any]]) -> str:
	"""The "Your actions" heading names what the decisions are about: U01-HOD
	draws "1 departmental plan requires your decision"; an Accounting Officer
	or statutory approver is deciding on the annual plan, not a departmental
	one (found in the browser 25 Sep 2026)."""
	n = len(actionable)
	if not n:
		return ""
	departmental = {"departmental-procurement-plan", "dpp-review"}
	subjects = {
		"departmental plan" if (set(action.get("route") or []) & departmental) else "annual plan"
		for action in actionable
	}
	subject = subjects.pop() if len(subjects) == 1 else "item"
	return f"{n} {subject}{'' if n == 1 else 's'} require{'s' if n == 1 else ''} your decision"


def _narrative(answer: dict[str, Any] | None) -> dict[str, str] | None:
	"""PLN v1.27 §10.3 — a workspace carries no tracker; the plan task row
	states the next-step answer instead, when it is blocked or waiting."""
	kind = (answer or {}).get("kind")
	if kind == "your_turn_blocked":
		# a declined budget revision is said here too, not only on the plan
		decline = next(
			(b["figures"]["budget_revision"] for b in answer.get("blockers") or [] if (b.get("figures") or {}).get("budget_revision")),
			None,
		)
		detail = ""
		if decline:
			detail = f"Budget revision declined by {decline['by']}" + (f": {decline['reason']}" if decline.get("reason") else "")
		return {"tone": "blocked", "headline": cstr(answer.get("headline")), "since": "", "detail": detail}
	if kind == "waiting":
		return {"tone": "waiting", "headline": cstr(answer.get("headline")), "since": cstr((answer.get("since") or {}).get("display"))}
	return None


def _plan_answer(plan, open_version, actor: str) -> dict[str, Any] | None:
	"""The open (not yet in force) Version's §5.7 answer for this reader —
	the same one U07 draws, so the workspace never words it differently."""
	if not (plan and open_version) or open_version.name == plan.active_version:
		return None
	from kentender_procurement.procurement_planning.services import plan_read

	version = frappe.get_doc("Annual Plan Version", open_version.name)
	return plan_read._guidance_for(version, frappe.get_doc("Annual Plan", plan.name), actor)["next_step"]


def _plan_rows(plan, active_version, open_version, *, is_planner: bool, answer: dict[str, Any] | None = None) -> list[dict[str, Any]]:
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
		narrative = None
		if active_version:
			facts = [
				("Work", "Plan update — Draft" if open_version.version_status == "Draft" else open_version.version_status),
				("Version", str(open_version.version_number)),
				("Proposed value", _money(value)),
			]
			# PLN v1.27 §10.3 U01-CURRENT-UPDATE-OVER-BUDGET / -WAITING-BUDGET:
			# a blocked or waiting update states that answer in place of what
			# it changes; otherwise it names the purchase it affects, which is
			# what tells the reader whether it concerns them (U01-CURRENT-UPDATE).
			narrative = _narrative(answer)
			if not narrative:
				affected = _affected_purchases(active_version, open_version)
				if affected:
					facts.append(("Affected purchase", affected))
				change = cstr(open_version.get("change_reason"))
				if change:
					facts.append(("Change", change))
			if narrative and narrative["tone"] == "waiting":
				action = "View update"
			else:
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
			if open_version.version_status == "Draft":
				note = "This plan is being prepared. It cannot yet be used to authorise procurement."
			else:
				# Submitted and beyond: say what it is and who holds it — never
				# "being prepared" (found in the browser 25 Sep 2026).
				note = f"{open_version.version_status}. It cannot yet be used to authorise procurement."
				narrative = _narrative(answer)
		rows.append(
			{
				"kind": "candidate" if active_version else "draft",
				"title": (
					"Continue plan update" if active_version
					else "Draft annual procurement plan" if open_version.version_status == "Draft"
					else "Annual procurement plan"
				),
				"facts": facts,
				"narrative": narrative,
				"note": note,
				"action": action,
				"action_kind": "primary" if action.startswith("Continue") else "secondary",
				"route": route,
			}
		)
	return rows


def _dominant_issue(answer: dict[str, Any], blockers: list[dict[str, Any]], plan_route: list[str]) -> dict[str, Any]:
	"""PLN v1.27 §10.3 (D2) — what stops the funding request, in the U01 BASE
	wording: the blocker's own headline, then when it must be resolved, with
	its one recovery route. A fix that is not a route (a command or a focus
	on the plan page) is reached by opening the plan, and says so."""
	if len(blockers) == 1:
		blocker = blockers[0]
		strong = f"{cstr(blocker.get('headline')).rstrip('.')}."
		fixes = blocker.get("fixes") or []
		primary = next((f for f in fixes if f.get("primary")), fixes[0] if fixes else None)
		method = bool(primary and primary.get("fix_id") == "choose_method")
		sentence = "Choose it before sending the plan to Finance." if method else "Resolve this before sending the plan to Finance."
	else:
		strong = f"{cstr(answer.get('headline')).rstrip('.')}."
		primary = None
		sentence = "Resolve them before sending the plan to Finance."
	routed = bool(primary and primary.get("kind") == "route" and primary.get("target"))
	return {
		"tone": "dominant",
		"text": f"{strong} {sentence}",
		"strong": strong,
		"action": primary["label"] if routed else "Open annual plan",
		"route": primary["target"] if routed else plan_route,
	}


def _issues(plan, open_version, answer: dict[str, Any] | None, rows: list[dict[str, Any]], *, is_planner: bool) -> list[dict[str, Any]]:
	"""The issues beneath the plan task row, in §10.3's order: first the one
	that stops the funding request (dominant), then the ones that stop only
	signature (quiet). Never four accounting values (PLN22-AC-006). An update
	row already states its blocked headline (`_narrative`), so it is not
	repeated here."""
	if not (plan and open_version and open_version.version_status == "Draft" and is_planner):
		return []
	from kentender_procurement.procurement_planning.services import readiness

	plan_route = ["annual-procurement-plan", plan.plan_reference]
	stated_in_row = any(row.get("narrative") for row in rows)
	issues: list[dict[str, Any]] = []
	if not stated_in_row and (answer or {}).get("kind") == "your_turn_blocked":
		# The accepted requirements still outside a purchase have their own,
		# richer sentence below (count, departments, value).
		blockers = [b for b in answer.get("blockers") or [] if b.get("reason_code") != "PLN_ENTRY_INCOMPLETE"]
		if blockers:
			issues.append(_dominant_issue(answer, blockers, plan_route))
	# Accepted departmental sources waiting to be formed into this same open
	# Draft: one issue on the plan, never a separate "N departmental plan
	# requires your decision" card leading to the identical Draft (found live
	# 22 Sep 2026).
	count, value, departments = _accepted_unallocated(plan.fiscal_year)
	if count and not stated_in_row:
		plural = "entry" if count == 1 else "entries"
		issues.append({
			"tone": "dominant",
			"text": f"{count} accepted departmental {plural} from {' · '.join(departments)} ({_money(value)}) are ready to consolidate into this plan.",
			"strong": "",
			"action": "Open Annual Plan",
			"route": plan_route,
		})
	allocations = readiness.reservation_allocations(open_version.name, plan.fiscal_year)
	if allocations.get("mandatory") and not allocations.get("met") and cstr(allocations.get("remaining")):
		amount = _money(flt(allocations.get("remaining")))
		# §10.3 v1.27 correction: the shortfall blocks signature (§5.5.3.1),
		# not the funding request.
		issues.append({
			"tone": "quiet",
			"text": f"Reserved procurement is below the required allocation by {amount}. Resolve this before the plan can be signed and submitted.",
			"strong": amount,
			"action": "Review reserved procurement",
			"route": plan_route,
		})
	return issues


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


def _own_departmental_section(dpp_rows, departmental_units, *, window_open: bool, financial_year_label: str) -> dict[str, Any] | None:
	"""U01-DEPARTMENT-AUTHOR / U01-HOD — "Your departmental plan".

	The spec's own fixture for this section is a single-department Author
	(§11 U01-DEPARTMENT-AUTHOR); there is no drawn multi-department variant.
	The prior code picked `departmental_units[0]` regardless, so an actor who
	authors two or more departments (the same dual-assignment shape NDS's own
	regression fixture exercises) got this section AND its own "Your
	actions" card pointing at the identical plan — two controls for one
	decision, the exact confusion §1.1's task-led redesign exists to remove
	(found live 22 Sep 2026). "Your actions" already lists every authored
	department individually and correctly; when there is more than one, this
	spotlight is redundant with it, not complementary, so it is omitted
	rather than arbitrarily picking one department to duplicate.
	"""
	if len(departmental_units) != 1:
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
		# §10.3 U01-DEPARTMENT-AUTHOR — which department, which year, what
		# state, in that order: the year is part of identifying the plan, not
		# a footnote after its status.
		"facts": [
			("Department", row["department"]),
			("Financial year", financial_year_label),
			("Status", row["status"]),
		],
		"action": (
			"Continue departmental plan" if row["state"] == "Draft"
			else "Create update" if row["late_needs"]
			else "View departmental plan"
		),
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
			# §10.3 U01-HOD — the Head of Department's own work on a draft is
			# not the Author's. They are not continuing to write it; they are
			# deciding whether to certify and submit it, so the card names
			# that outcome rather than the draft's size. That is only true
			# once there is a complete plan to decide on — `dpp_read_profile`
			# resolves "hod" for anyone who also holds Head of User Department
			# there, whether or not the Draft has a single requirement in it
			# yet, so an actor who is both Author and HOD (the same dual-
			# assignment shape NDS's own regression fixture exercises) was
			# told to "review and submit" an empty shell the instant they
			# opened it (found live 22 Sep 2026). Route them to "Continue"
			# instead until the plan is actually ready — at least one
			# requirement, every one of them funded or explicitly excluded.
			ready_to_review = row["requirements"] > 0 and not row["incomplete"]
			if ready_to_review and authz.dpp_read_profile(unit["id"], actor) == "hod":
				actionable.append(
					_action(
						"Review departmental plan",
						detail, "Review departmental plan", row["route"], "attention",
						facts=[
							("Departmental plan", f"{row['department']} {context.get('financial_year_label') or fy}"),
							("Outcome required", "Review and submit"),
						],
					)
				)
			else:
				actionable.append(
					_action(
						"Continue departmental plan", detail, "Continue", row["route"], "attention",
						facts=[("Submission", str(row["version"])), ("Requirements", str(row["requirements"])), ("Specified value", row["value"])],
					)
				)
		elif row["state"] == "Returned":
			returned = _returned_on(row["version_name"])
			actionable.append(_action("Correct and resubmit departmental plan", f"{detail} · returned {returned}" if returned else detail, "Correct", row["route"], "critical"))
		elif row["late_needs"]:
			# Owner decision 26 Sep 2026 — a Need accepted after this plan was
			# accepted: the department's own task, named for the need, leading
			# to the plan where Create update is the principal action.
			actionable.append(
				_action(
					f"Add {row['late_needs']} to the departmental plan",
					# One sentence, not facts joined by "·" (PLN-CHG-001 v1.28 §10.3).
					f"Accepted after {row['department']}'s departmental plan was accepted.",
					"Create update", row["route"], "attention",
				)
			)
		# A Submitted plan adds nothing here: §10.3's own rule is "waiting
		# work is status on its document, not a duplicate disabled task",
		# and the artboard's own U01 register ends at the plan count with no
		# further line — `departmental_table` (built from this same `row`,
		# below) already carries "Awaiting validation" as that department's
		# Status cell. This branch used to also push a plain, headerless
		# "Departmental plan awaiting validation · <department>" paragraph
		# to `waiting`, restating the exact same fact a second time with no
		# heading of its own (found live 22 Sep 2026).

	plan = frappe.db.get_value(
		"Annual Plan", {"fiscal_year": fy},
		# `fiscal_year` itself is read back here too — `_issues` keys
		# both its reservation-shortfall and accepted-entry checks off
		# `plan.fiscal_year`, and without it those checks silently no-op
		# (found live 22 Sep 2026, while fixing the duplicate-panel bug).
		["name", "plan_reference", "title", "active_version", "open_successor_version", "fiscal_year"], as_dict=True,
	)
	open_version = None
	if plan and (plan.open_successor_version or plan.active_version):
		open_version = frappe.db.get_value(
			"Annual Plan Version", plan.open_successor_version or plan.active_version,
			# §10.3 — `change_reason` is what the update row says it is *for*;
			# selecting it here is the difference between the row explaining
			# itself and the row being a version number.
			["name", "version_number", "version_status", "funding_state", "submitted_by_user", "submitted_at", "change_reason"],
			as_dict=True,
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
			# §7.1 — surfaced as this open Draft's own "one current issue"
			# (`_issues`, rendered directly under its task row) rather
			# than a second, separate card repeating the identical route
			# under a less accurate heading — this used to also be an
			# "actionable" entry, which put "N departmental plan requires
			# your decision" and "Annual plan work" on screen together for
			# the same plan (found live 22 Sep 2026).
			pass
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

	answer = _plan_answer(plan, open_version, actor)
	rows = _plan_rows(plan, active_version_doc, open_version, is_planner=is_planner, answer=answer)
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
		"issues": _issues(plan, open_version, answer, rows, is_planner=is_planner),
		"your_departmental_plan": _own_departmental_section(
			dpp_rows, departmental_units, window_open=window_open,
			financial_year_label=cstr(context.get("financial_year_label")) or cstr(fy),
		),
		# §9.1 — "Omit an empty Your actions section."
		"actionable": actionable,
		"actionable_heading": _actionable_heading(actionable),
		"waiting": waiting,
		"departmental_table": _departmental_table(dpp_rows),
		"departmental_plans": dpp_rows,
		"not_included": _not_included(fy, window_open),
	}
