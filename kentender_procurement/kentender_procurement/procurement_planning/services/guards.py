# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.27 §5.7 / KT-STD-001 v1.8 §3B.1 — Planning's guards return
reasons, not booleans.

Each function answers one command's question for one actor — may this be
done now, and if not, every reason why with the figures behind it and each
way to clear it, naming the responsibility that can. The readiness rules
themselves stay where they are (`plan_read.plan_readiness`,
`readiness.item_blockers`); this module turns their blocker list into guard
results, so the command refusal, the screen's offer and the next-step answer
all come from the same evaluation (§3B.2 "single source").
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, fmt_money

from kentender_core.services import next_step as ns
from kentender_procurement.procurement_planning.errors import MESSAGES
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_PROCUREMENT_PLANNER,
)

ROLE_BUDGET_OFFICER = "Budget Officer"

FIX_REQUEST_BUDGET_REVISION = "request_budget_revision"
FIX_WAITING_BUDGET_REVISION = "waiting_budget_revision"
FIX_REQUEST_DEPARTMENTAL_UPDATE = "request_departmental_update"
FIX_REBUILD_FIRST = "rebuild_first"
FIX_WAITING_DEPARTMENTAL_UPDATE = "waiting_departmental_update"
FIX_CHOOSE_METHOD = "choose_method"
FIX_REVIEW_RESERVATION = "review_reservation"
FIX_EDIT_PURCHASE = "edit_purchase"
FIX_ADD_REQUIREMENTS = "add_requirements"
FIX_ASK_ADMINISTRATOR = "ask_administrator"
FIX_TRY_AGAIN = "try_again"

#: Focus targets a fix may move to on the same page (`fix.kind == "focus"`).
FOCUS_PURCHASES = "purchases"
FOCUS_RESERVATION = "reservation"
FOCUS_REQUIREMENTS = "requirements"


def money(amount: float) -> str:
	return f"KES {fmt_money(flt(amount), precision=0)}"


def people(role: str) -> list[str]:
	"""Full names of the current holders of a Site-wide responsibility."""
	return [
		cstr(frappe.db.get_value("User", user, "full_name") or user)
		for user in authz.users_with_site_role(role)
	]


def holder(role: str) -> dict[str, Any]:
	return ns.holder(role, people(role))


def person_or_role(role: str) -> str:
	names = people(role)
	return ", ".join(names) if names else role


# --------------------------------------------------------------------------
# Blocker → guard, with the fixes each blocker offers (§10.1A.5)
# --------------------------------------------------------------------------


def _purchases(n: int) -> str:
	return f"{n} purchase" if n == 1 else f"{n} purchases"


def _needs(n: int) -> str:
	return "needs" if n == 1 else "need"


def _item_route(plan_item_id: str) -> list[str]:
	return ["procurement-plan-item", plan_item_id]


def _budget_guards(
	blocker: dict[str, Any], *, open_requests: set[str], declined: dict[str, dict[str, Any]], departments: dict[str, list[dict[str, Any]]],
	rebuild_lines: set[str] = frozenset(),
) -> list[dict[str, Any]]:
	"""`PLN_PLAN_NOT_AFFORDABLE`: one guard per over-budget line (§10.1A.5).

	A purchase's cost is copied from the departments' accepted requirements
	and cannot be lowered in the plan (§4.6 "no source/quantity/value
	override"). Owner decision 26 Sep 2026 — the two recovery paths are
	**Request budget revision** (the Budget Officer) and **Request
	departmental plan update** (each department whose requirements make up
	the line decides whether to correct the estimate, change the requirement
	or mark it not proceeding). After Budget declines, its reason is shown
	and the departmental path leads; a fresh budget request is offered only
	on a new basis (the line's approved or planned amount has changed since
	the decline), never as an endless "ask again"."""
	out = []
	officer = person_or_role(ROLE_BUDGET_OFFICER)
	for line in blocker.get("lines") or []:
		budget_line = line["budget_line"]
		if budget_line in rebuild_lines:
			# A purchase on this line still draws on a departmental requirement
			# the department has since changed: its total is stale until that
			# purchase is rebuilt, so nothing is asked of anyone yet (found in
			# the named-user pass 26 Sep 2026: the department that had just
			# answered was offered again).
			facts = [("Requirements on this line", ", ".join(d["name"] for d in departments.get(budget_line) or []))] if departments.get(budget_line) else []
			out.append(ns.guard(
				False, reason_code="PLN_PLAN_NOT_AFFORDABLE", message=MESSAGES["PLN_PLAN_NOT_AFFORDABLE"],
				headline=f"Over budget by {money(line['over'])} on {line['title'] or line['reference']}",
				figures=dict(line), facts=facts,
				fixes=[ns.fix(
					"Rebuild the purchase first: the department's update changes this line's total",
					responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_TEXT, fix_id=FIX_REBUILD_FIRST,
				)],
			))
			continue
		waiting_on_budget = budget_line in open_requests
		decline = declined.get(budget_line) if not waiting_on_budget else None
		new_basis = not decline or (
			abs(flt(decline.get("planned")) - flt(line.get("planned"))) > 0.005
			or abs(flt(decline.get("approved")) - flt(line.get("approved"))) > 0.005
		)
		budget_fixes = []
		if waiting_on_budget:
			budget_fixes.append(ns.fix(
				f"Waiting for {officer} to revise this line", responsibility=ROLE_BUDGET_OFFICER, person=officer,
				kind=ns.FIX_TEXT, fix_id=FIX_WAITING_BUDGET_REVISION,
			))
		elif new_basis:
			budget_fixes.append(ns.fix(
				f"Request budget revision {'again ' if decline else ''}from {officer}",
				responsibility=ROLE_BUDGET_OFFICER, person=officer, kind=ns.FIX_COMMAND,
				fix_id=FIX_REQUEST_BUDGET_REVISION, target={"budget_line": budget_line}, primary=not decline,
			))
		department_fixes = []
		for department in departments.get(budget_line) or []:
			if department.get("requested"):
				department_fixes.append(ns.fix(
					f"Waiting for {department['name']} to update its departmental plan",
					responsibility=ROLE_DEPARTMENTAL_AUTHOR, person=department["name"], kind=ns.FIX_TEXT,
					fix_id=f"{FIX_WAITING_DEPARTMENTAL_UPDATE}:{department['unit']}",
				))
			else:
				department_fixes.append(ns.fix(
					f"Request departmental plan update from {department['name']}",
					responsibility=ROLE_DEPARTMENTAL_AUTHOR, person=department["name"], kind=ns.FIX_COMMAND,
					fix_id=FIX_REQUEST_DEPARTMENTAL_UPDATE, target={"budget_line": budget_line, "organisation_unit": department["unit"]},
					primary=bool(decline) and not any(f.get("primary") for f in department_fixes),
				))
		# after a decline the departmental path leads
		fixes = department_fixes + budget_fixes if decline else budget_fixes + department_fixes
		facts = []
		names = [d["name"] for d in departments.get(budget_line) or []]
		if names:
			facts.append(("Requirements on this line", ", ".join(names)))
		if decline:
			facts.append(("Budget revision", f"Declined by {decline['by']} on {decline['at']}" if decline["at"] else f"Declined by {decline['by']}"))
			if decline["reason"]:
				facts.append(("Reason", decline["reason"]))
		out.append(ns.guard(
			False,
			reason_code="PLN_PLAN_NOT_AFFORDABLE",
			message=MESSAGES["PLN_PLAN_NOT_AFFORDABLE"],
			headline=f"Over budget by {money(line['over'])} on {line['title'] or line['reference']}",
			figures={**line, **({"budget_revision": {"outcome": "Declined", **decline}} if decline else {})},
			fixes=fixes,
			facts=facts,
		))
	return out


def blocker_guards(
	blockers: list[dict[str, Any]], *, open_requests: set[str] | None = None, declined: dict[str, dict[str, Any]] | None = None,
	departments: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
	"""Every readiness blocker as a guard, grouped so one cause is stated once
	with the purchases it affects (§10.1A.5: headline figure only; the
	supporting figures stay in the working region)."""
	open_requests = open_requests or set()
	guards: list[dict[str, Any]] = []
	grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
	rebuild_lines = {line for b in blockers if b["code"] == "PLN_SOURCE_CORRECTION_REQUIRED" for line in b.get("budget_lines") or []}
	for blocker in blockers:
		code = blocker["code"]
		if code == "PLN_PLAN_NOT_AFFORDABLE":
			guards.extend(_budget_guards(blocker, open_requests=open_requests, declined=declined or {}, departments=departments or {}, rebuild_lines=rebuild_lines))
		elif code == "PLN_RESERVATION_SHORTFALL":
			guards.append(ns.guard(
				False, reason_code=code, message=MESSAGES[code],
				headline=f"Reserved procurement is below the required allocation by {money(blocker.get('shortfall'))}",
				figures={"shortfall": flt(blocker.get("shortfall"))},
				fixes=[ns.fix("Review reserved procurement", responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_FOCUS, fix_id=FIX_REVIEW_RESERVATION, target=FOCUS_RESERVATION)],
			))
		elif code == "PLN_REFERENCE_UNAVAILABLE" and blocker.get("field") == "budget_basis":
			guards.append(ns.guard(
				False, reason_code=code, message=cstr(blocker.get("message")),
				headline="The approved budget could not be read",
				fixes=[ns.fix("Try again shortly", responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_TEXT, fix_id=FIX_TRY_AGAIN)],
			))
		else:
			grouped.setdefault((code, cstr(blocker.get("field"))), []).append(blocker)
	for (code, field), rows in grouped.items():
		items = sorted({cstr(r.get("plan_item_id")) for r in rows if r.get("plan_item_id")})
		if code == "PLN_SOURCE_CORRECTION_REQUIRED":
			# The department's accepted update changed a requirement this
			# purchase draws on: the purchase is removed and re-formed from the
			# new accepted source (§7.1 correction, never an automatic move).
			titles = [cstr(r.get("title")) or cstr(r.get("plan_item_id")) for r in rows]
			headline = (
				f"Rebuild {titles[0]} from the department's updated plan" if len(rows) == 1
				else f"Rebuild {len(rows)} purchases from the departments' updated plans"
			)
			guards.append(ns.guard(
				False, reason_code=code, message=MESSAGES[code], headline=headline,
				figures={"plan_items": items, "field": field},
				fixes=[ns.fix("Edit purchase", responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_ROUTE, fix_id=FIX_EDIT_PURCHASE, target=_item_route(items[0]) if items else None, primary=True)],
			))
		elif code == "PLN_PLAN_CONTENTS_INCOMPLETE" and field == "procurement_method":
			guards.append(ns.guard(
				False, reason_code=code, message=MESSAGES[code],
				headline=f"{_purchases(len(items))} {_needs(len(items))} a procurement method",
				figures={"plan_items": items},
				fixes=[ns.fix("Choose a procurement method", responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_ROUTE, fix_id=FIX_CHOOSE_METHOD, target=_item_route(items[0]) if items else None, primary=True)],
			))
		elif code == "PLN_REFERENCE_UNAVAILABLE" and field in ("procurement_method", "method_profile_version", "schedule_profile_version", "reservation_category"):
			# A missing or unverified rule is a setting: Administrator or System
			# Manager completes it in System setup (§10.16; D3). The screen's
			# missing-setting content supplies the facts.
			label = "Schedule rule" if field == "schedule_profile_version" else ("Reservation rule" if field == "reservation_category" else "Procurement method rule")
			guards.append(ns.guard(
				False, reason_code=code, message=MESSAGES[code],
				headline=f"{label} is not set up",
				figures={"field": field, "plan_items": items},
				facts=[("Setting", label), ("Responsible role", "Administrator or System Manager")],
				fixes=[ns.fix("Ask your KenTender administrator to complete this setting.", responsibility="Administrator or System Manager", kind=ns.FIX_TEXT, fix_id=FIX_ASK_ADMINISTRATOR)],
			))
		else:
			from kentender_procurement.procurement_planning.services.plan_read import CURRENT_WORK

			work = CURRENT_WORK.get(code) or "Complete the purchase details"
			headline = f"{work} for {_purchases(len(items))}" if items else cstr(rows[0].get("message")) or MESSAGES.get(code, code)
			guards.append(ns.guard(
				False, reason_code=code, message=MESSAGES.get(code, ""),
				headline=headline,
				figures={"plan_items": items, "field": field},
				fixes=[ns.fix("Edit purchase", responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_ROUTE, fix_id=FIX_EDIT_PURCHASE, target=_item_route(items[0]) if items else None)],
			))
	return guards


# --------------------------------------------------------------------------
# Annual Plan guards (§7.2). Each has two halves: the plan's own readiness,
# which is the same whoever is looking and feeds the next-step answer, and
# the command guard, which adds the actor's responsibility and the state.
# --------------------------------------------------------------------------


def unallocated_guard(unallocated: list) -> dict[str, Any] | None:
	if not unallocated:
		return None
	return ns.guard(
		False, reason_code="PLN_ENTRY_INCOMPLETE",
		message="Add every accepted requirement to a purchase first.",
		headline="Add the accepted requirements to purchases",
		figures={"unallocated": len(unallocated)},
		fixes=[ns.fix("Add selected requirements", responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_FOCUS, fix_id=FIX_ADD_REQUIREMENTS, target=FOCUS_REQUIREMENTS)],
	)


def pre_finance(
	report: dict | None, *, unallocated: list, open_requests: set[str] | None = None, declined: dict[str, dict[str, Any]] | None = None,
	departments: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
	"""The plan's pre-Finance readiness as one guard (§5.6 item 4, D2)."""
	guards = blocker_guards((report or {}).get("blockers") or [], open_requests=open_requests, declined=declined, departments=departments)
	extra = unallocated_guard(unallocated)
	return ns.combine(*(guards + ([extra] if extra else [])))


def request_funding(version, *, actor: str, readiness_guard: dict[str, Any]) -> dict[str, Any]:
	"""RequestPlanFundingConfirmation for a Draft (§5.2.3)."""
	if not authz.has_site_role(ROLE_PROCUREMENT_PLANNER, actor):
		return ns.guard(False, reason_code="PLN_NO_CONTEXT", message=MESSAGES["PLN_NO_CONTEXT"])
	if version.version_status != "Draft" or version.funding_state not in ("Not requested", "Returned", "Stale", "Confirmed"):
		return ns.guard(False, reason_code="PLN_BASELINE_LOCKED", message=MESSAGES["PLN_BASELINE_LOCKED"])
	return readiness_guard


def submission(submission_report: dict | None, *, unallocated: list, funding_current: bool) -> dict[str, Any]:
	"""Every formal-submission gate together (§5.2.3, §6.1, §6.2)."""
	from kentender_procurement.procurement_planning.services import plan_governance

	guards = []
	if not funding_current:
		guards.append(ns.guard(
			False, reason_code="PLN_FINANCE_STALE", message=MESSAGES["PLN_FINANCE_STALE"],
			headline="Plan funding is not confirmed for the current plan",
			fixes=[ns.fix("The Procurement Planner requests a new funding check", responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_TEXT, fix_id="planner_requests_funding")],
		))
	if not plan_governance.statutory_route_configured():
		guards.append(setting_guard("PLN_STATUTORY_ROUTE_UNCONFIGURED", "Annual Plan approval authority", "Sign and submit Annual Plan"))
	extra = unallocated_guard(unallocated)
	if extra:
		guards.append(extra)
	guards.extend(blocker_guards((submission_report or {}).get("blockers") or []))
	return ns.combine(*guards)


def sign_and_submit(version, *, actor: str, submission_guard: dict[str, Any]) -> dict[str, Any]:
	"""SubmitConsolidatedPlan / SubmitCorrectedPlan (§5.2.3, §6.2)."""
	if not authz.has_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, actor):
		return ns.guard(False, reason_code="PLN_NO_CONTEXT", message=MESSAGES["PLN_NO_CONTEXT"])
	if version.version_status != "Draft":
		return ns.guard(False, reason_code="PLN_BASELINE_LOCKED", message=MESSAGES["PLN_BASELINE_LOCKED"])
	return submission_guard


def setting_guard(code: str, setting: str, affected_action: str) -> dict[str, Any]:
	"""A missing setting (§10.16, D3): its facts and the in-product route —
	the administrator completes it; there is no hand-off command."""
	return ns.guard(
		False, reason_code=code, message=MESSAGES[code],
		headline=f"{setting} is not set up",
		facts=[("Setting", setting), ("Affected action", affected_action), ("Responsible role", "Administrator or System Manager")],
		fixes=[ns.fix("Ask your KenTender administrator to complete this setting.", responsibility="Administrator or System Manager", kind=ns.FIX_TEXT, fix_id=FIX_ASK_ADMINISTRATOR)],
	)


def is_setup_only(guard_result: dict[str, Any]) -> bool:
	"""Every blocker is a setting only an administrator can complete, so no
	Planning work can clear it."""
	blockers = ns.blockers_of(guard_result)
	return bool(blockers) and all(
		any(f["fix_id"] == FIX_ASK_ADMINISTRATOR for f in b["fixes"]) for b in blockers
	)
