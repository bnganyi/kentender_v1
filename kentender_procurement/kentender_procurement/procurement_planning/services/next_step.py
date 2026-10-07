# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.27 §5.7 — Planning's next-step answers and journey
trackers (KT-STD-001 v1.8 §3B.2, §2.9.2).

For the signed-in actor this answers, from the same guards that enable the
commands (`guards.py`): what stage the record is at, whose turn it is, and —
when nothing can move — every reason why and who can fix it. The shape is
kentender_core's (`kentender_core.services.next_step`); the states, stages,
holders and wording are Planning's (§5.7, §10.1A and the per-screen
paragraphs of §10). Screens draw the answer unchanged.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_core.services import next_step as ns
from kentender_core.services.authorization import is_technical
from kentender_procurement.procurement_planning.services import guards, needs_intake
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PROCUREMENT_PLANNER,
)

TECHNICAL_OPERATOR = "Administrator or System Manager"

STAGE_PREPARATION = "preparation"
STAGE_FUNDING = "funding"
STAGE_SIGNATURE = "signature"
STAGE_AO = "ao"
STAGE_STATUTORY = "statutory"
STAGE_PUBLICATION = "publication"
STAGE_IN_FORCE = "in_force"

#: The Plan-lifecycle responsibilities: each of them sees "Waiting" on a stage
#: they do not hold (§5.7 "everyone else"). An Auditor or any other reader is
#: Not involved (§10.1A.6).
PLAN_PARTICIPANTS = (
	ROLE_PROCUREMENT_PLANNER,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
)


def plan_stages() -> list[tuple[str, str]]:
	"""§10.1A.1 — seven formal stages; budget fit is a condition, not a stage."""
	from kentender_procurement.procurement_planning.services import plan_governance

	return [
		(STAGE_PREPARATION, "Preparation"),
		(STAGE_FUNDING, "Funding confirmation"),
		(STAGE_SIGNATURE, "Signature"),
		(STAGE_AO, "AO adoption"),
		(STAGE_STATUTORY, plan_governance.statutory_stage_label()),
		(STAGE_PUBLICATION, "Publication"),
		(STAGE_IN_FORCE, "In force"),
	]


def _eat(value) -> str:
	from kentender_procurement.procurement_planning.services.plan_read import _eat as eat

	return eat(value)


def _since(value) -> dict[str, Any] | None:
	return ns.since(value, _eat(value)) if value else None


def _statutory_holder() -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	label = plan_governance.STATUTORY_HOLDER_LABEL.get(plan_governance.statutory_route(), "Statutory authority")
	return ns.holder(label, guards.people(ROLE_PLAN_STATUTORY_APPROVER))


def _waiting(headline: str, *, stage: str, holder: dict[str, Any], since=None) -> dict[str, Any]:
	return ns.answer(ns.KIND_WAITING, headline=headline, stage=stage, holder=holder, since=_since(since))


def _open_task_created(doctype: str, filters: dict[str, Any]):
	row = frappe.db.get_value(doctype, {**filters, "status": "Open"}, ["name", "creation"], as_dict=True)
	return row


# --------------------------------------------------------------------------
# Budget revision requests (§4.7) — the Planner's waiting state
# --------------------------------------------------------------------------


def open_budget_revision_requests(plan_version: str) -> dict[str, Any]:
	"""Open requests for this Draft Version, keyed by Budget Line."""
	rows = frappe.get_all(
		"Plan Budget Revision Request",
		filters={"plan_version": plan_version, "status": "Open"},
		fields=["name", "budget_line", "requested_at", "over_amount"],
		order_by="requested_at asc",
		limit_page_length=0,
	)
	return {row.budget_line: row for row in rows}


def line_departments(plan_version: str) -> dict[str, list[dict[str, Any]]]:
	"""Each budget line's departments — where the line's cost comes from —
	and whether each has an Open request to update its departmental plan."""
	from kentender_procurement.procurement_planning.services import departmental_update

	requested = departmental_update.open_requests(plan_version)
	return {
		line: [
			{"unit": unit, "name": departmental_update.unit_name(unit), "requested": (line, unit) in requested}
			for unit in units
		]
		for line, units in departmental_update.line_units(plan_version).items()
	}


def declined_budget_revision_requests(plan_version: str) -> dict[str, dict[str, Any]]:
	"""Budget lines of this Version whose latest answered request was
	Declined — who declined it, when (Nairobi display) and why — so the
	Planner is told, not returned silently to the state before asking."""
	rows = frappe.get_all(
		"Plan Budget Revision Request",
		filters={"plan_version": plan_version, "status": ("in", ("Revised", "Declined", "Withdrawn"))},
		fields=["budget_line", "status", "outcome_by", "outcome_at", "outcome_reason", "approved_amount", "planned_amount"],
		order_by="outcome_at desc, requested_at desc",
		limit_page_length=0,
	)
	out: dict[str, dict[str, Any]] = {}
	seen: set[str] = set()
	for row in rows:
		if row.budget_line in seen:
			continue
		seen.add(row.budget_line)
		if row.status == "Declined":
			since = _since(row.outcome_at)
			out[row.budget_line] = {
				"by": cstr(row.outcome_by) or guards.ROLE_BUDGET_OFFICER,
				"at": since["display"] if since else "",
				"reason": cstr(row.outcome_reason),
				# the basis Budget declined: a fresh request needs a new one
				"approved": flt(row.approved_amount),
				"planned": flt(row.planned_amount),
			}
	return out


# --------------------------------------------------------------------------
# Annual Plan (§5.7 first table)
# --------------------------------------------------------------------------


def plan_guidance(
	version,
	plan,
	*,
	actor: str,
	report: dict | None = None,
	submission_report: dict | None = None,
	unallocated: list | None = None,
	accepted_entries: int = 0,
	reduced: bool = False,
) -> dict[str, Any]:
	"""`{"next_step", "journey", "guards"}` for one Plan Version and viewer."""
	unallocated = unallocated or []
	technical = is_technical(actor)
	roles = {role: authz.has_site_role(role, actor) for role in PLAN_PARTICIPANTS}
	participant = any(roles.values())
	status = version.version_status
	state = _plan_state(version, plan, actor=actor, roles=roles, report=report, submission_report=submission_report, unallocated=unallocated)

	journey = None
	if state.get("stage"):
		journey = ns.journey(
			plan_stages(),
			current=state["stage"] if not state.get("complete") else "",
			blocked=bool(state.get("blocked")),
			holder_display=state.get("stage_holder", ""),
			complete=bool(state.get("complete")),
			reduced=reduced,
			upstream=(
				ns.link(f"{accepted_entries} departmental requirement{'s' if accepted_entries != 1 else ''} included", kind=ns.FIX_FOCUS, target=guards.FOCUS_REQUIREMENTS)
				if accepted_entries and status == "Draft" else None
			),
			downstream=_requisitions_link(version) if state.get("complete") else None,
		)

	answer = state["mine"] or state["others"]
	# O4 — the one named exception: the authorised technical operator holds
	# publication recovery although they hold no Planning responsibility.
	technical_turn = bool(technical and state.get("technical_turn") and state.get("mine"))
	if not participant and not technical_turn and state.get("others", {}).get("kind") != ns.KIND_DONE:
		# §10.1A.6 — an Auditor or other reader is Not involved; the tracker
		# still shows the exact Version's markers.
		answer = ns.not_involved(state.get("stage", ""))
	answer = ns.for_viewer(
		answer, technical=technical, reader=state["others"],
		allow_technical_turn=bool(state.get("technical_turn")),
	)
	if technical and not state.get("technical_turn"):
		# §3B.6 — a technical reader sees where the record stands: the line any
		# participant who does not hold it would see.
		answer = ns.for_viewer(state["others"], technical=True, reader=state["others"])
	return {"next_step": answer, "journey": journey, "guards": state.get("guards", {})}


def _plan_state(version, plan, *, actor, roles, report, submission_report, unallocated) -> dict[str, Any]:
	status = version.version_status
	if status == "Draft":
		return _draft_state(version, plan, actor=actor, roles=roles, report=report, submission_report=submission_report, unallocated=unallocated)
	if status == "Awaiting Accounting Officer":
		return _governance_state(version, actor=actor, roles=roles, stage=STAGE_AO)
	if status == "Awaiting statutory approval":
		return _governance_state(version, actor=actor, roles=roles, stage=STAGE_STATUTORY)
	if status in ("Approved — publication pending", "Publication failed"):
		return _publication_state(version, actor=actor, roles=roles)
	if status == "Published — activation held":
		planner = guards.holder(ROLE_PROCUREMENT_PLANNER)
		others = _waiting(f"Waiting for {planner['display']} to prepare a corrected plan", stage=STAGE_PUBLICATION, holder=planner)
		mine = None
		if roles[ROLE_PROCUREMENT_PLANNER] and not plan.open_successor_version:
			mine = ns.answer(
				ns.KIND_BLOCKED, headline="Prepare a corrected plan", stage=STAGE_PUBLICATION,
				blockers=[ns.blocker(ns.guard(False, reason_code="PLN_ACTIVATION_HELD", headline="The published plan could not be activated",
					fixes=[ns.fix("Prepare a corrected plan", responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_COMMAND, fix_id="prepare_corrected_plan", primary=True)]))],
			)
		return {"stage": STAGE_PUBLICATION, "blocked": True, "stage_holder": _names(planner), "mine": mine, "others": others}
	if status == "Withdrawn for correction":
		planner = guards.holder(ROLE_PROCUREMENT_PLANNER)
		mine = ns.answer(ns.KIND_YOUR_TURN, headline="Continue the correction", stage=STAGE_PREPARATION, primary_action="open_correction") if roles[ROLE_PROCUREMENT_PLANNER] else None
		others = _waiting(f"Waiting for {planner['display']} to prepare the correction", stage=STAGE_PREPARATION, holder=planner)
		return {"stage": STAGE_PREPARATION, "stage_holder": _names(planner), "mine": mine, "others": others}
	if status == "Active":
		done = ns.answer(ns.KIND_DONE, headline=f"In force since {_eat(version.activated_at)}" if version.activated_at else "In force", stage=STAGE_IN_FORCE)
		return {"stage": STAGE_IN_FORCE, "complete": True, "mine": None, "others": done}
	# Returned, Superseded, Cancelled: historical — no tracker, Not involved.
	return {"stage": "", "mine": None, "others": ns.not_involved()}


def preparer(version) -> dict[str, Any]:
	"""The Planner preparing this Version: whoever created it, while they
	still hold the responsibility (§10.1A.1 "Procurement Planner — Mercy
	Kilonzo"); every current holder otherwise (§6.5)."""
	owner = cstr(version.owner)
	if owner and authz.has_site_role(ROLE_PROCUREMENT_PLANNER, owner):
		return ns.holder(ROLE_PROCUREMENT_PLANNER, [cstr(frappe.db.get_value("User", owner, "full_name") or owner)])
	return guards.holder(ROLE_PROCUREMENT_PLANNER)


def _draft_state(version, plan, *, actor, roles, report, submission_report, unallocated) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance

	planner = preparer(version)
	funding = version.funding_state
	is_update = bool(version.based_on_version)

	if funding == "Awaiting confirmation":
		fco = guards.holder(ROLE_FINANCE_CONFIRMATION_OFFICER)
		task = _open_task_created("Plan Finance Task", {"plan_version": version.name})
		others = _waiting(f"Waiting for {fco['display']} to confirm plan funding", stage=STAGE_FUNDING, holder=fco, since=task.creation if task else None)
		mine = None
		if roles[ROLE_FINANCE_CONFIRMATION_OFFICER] and task and not authz.is_segregated(actor, authz.ACTION_FINANCE_DECIDE, plan_version=version.name):
			mine = ns.answer(ns.KIND_YOUR_TURN, headline="Confirm plan funding or return the plan to the planner", stage=STAGE_FUNDING, primary_action="open_finance_task")
		return {"stage": STAGE_FUNDING, "stage_holder": _names(fco), "mine": mine, "others": others}

	funding_current = plan_finance.funding_is_current(version) if funding == "Confirmed" else False
	if funding_current:
		hopf = guards.holder(ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
		sub = guards.submission(submission_report, unallocated=unallocated, funding_current=True)
		# The confirmation this Version relies on — its own, or (after a
		# return) the one carried forward from the returned Version (§5.2).
		confirmed = plan_finance._confirmed_decision(version.name)
		decided = confirmed.decided_at if confirmed else None
		sign = guards.sign_and_submit(version, actor=actor, submission_guard=sub)
		if sub["allowed"]:
			others = _waiting(f"Waiting for {hopf['display']} to sign and submit", stage=STAGE_SIGNATURE, holder=hopf, since=decided)
			mine = ns.answer(ns.KIND_YOUR_TURN, headline="Sign and submit the annual plan", stage=STAGE_SIGNATURE, primary_action="sign_and_submit") if roles[ROLE_HEAD_OF_PROCUREMENT_FUNCTION] else None
			return {"stage": STAGE_SIGNATURE, "stage_holder": _names(hopf), "mine": mine, "others": others, "guards": {"sign_and_submit": sign}}
		blockers = ns.blockers_of(sub)
		setup_only = guards.is_setup_only(sub)
		headline = _count_headline(blockers, "stop this plan being signed and submitted")
		blocked = ns.answer(ns.KIND_BLOCKED, headline=headline, stage=STAGE_SIGNATURE, blockers=blockers)
		# §5.7: the Planner holds a Planning fix; a setup fix is the
		# administrator's, stated to the signer who is blocked by it.
		holder_role = ROLE_HEAD_OF_PROCUREMENT_FUNCTION if setup_only else ROLE_PROCUREMENT_PLANNER
		holding = hopf if setup_only else planner
		others = _waiting(f"Waiting for {holding['display']}: {blockers[0]['headline']}", stage=STAGE_SIGNATURE, holder=holding, since=decided)
		mine = blocked if roles[holder_role] else None
		return {"stage": STAGE_SIGNATURE, "blocked": True, "stage_holder": _names(holding), "mine": mine, "others": others, "guards": {"sign_and_submit": sign}}

	# Preparation: Not requested, Returned, Stale, or a confirmation the
	# current plan no longer matches.
	requests = open_budget_revision_requests(version.name)
	readiness = guards.pre_finance(
		report, unallocated=unallocated, open_requests=set(requests),
		declined=declined_budget_revision_requests(version.name), departments=line_departments(version.name),
	)
	request = guards.request_funding(version, actor=actor, readiness_guard=readiness)
	result = {"stage": STAGE_PREPARATION, "stage_holder": _names(planner), "guards": {"request_funding": request, "pre_finance": readiness}}
	others = _waiting(f"Waiting for {planner['display']} to prepare the {'update' if is_update else 'plan'}", stage=STAGE_PREPARATION, holder=planner)
	result["others"] = others
	if readiness["allowed"]:
		result["mine"] = ns.answer(
			ns.KIND_YOUR_TURN,
			headline=f"Send the {'update' if is_update else 'plan'} to Finance for funding review",
			stage=STAGE_PREPARATION, primary_action="request_funding",
		) if roles[ROLE_PROCUREMENT_PLANNER] else None
		return result

	blockers = ns.blockers_of(readiness)
	only_unallocated = all(b["reason_code"] == "PLN_ENTRY_INCOMPLETE" and b["figures"].get("unallocated") for b in blockers)
	if only_unallocated:
		# U07-UNALLOCATED: the work is on this page — Your turn, not blocked.
		result["mine"] = ns.answer(ns.KIND_YOUR_TURN, headline="Add the accepted requirements to purchases", stage=STAGE_PREPARATION, primary_action="add_requirements") if roles[ROLE_PROCUREMENT_PLANNER] else None
		return result

	result["blocked"] = True
	from kentender_procurement.procurement_planning.services import departmental_update

	asked_departments = departmental_update.open_requests(version.name)
	asked_lines = {line for line, _unit in asked_departments}
	waiting_on_budget = [b for b in blockers if b["reason_code"] == "PLN_PLAN_NOT_AFFORDABLE" and b["figures"].get("budget_line") in requests]
	in_hand = [b for b in blockers if b["reason_code"] == "PLN_PLAN_NOT_AFFORDABLE" and (b["figures"].get("budget_line") in requests or b["figures"].get("budget_line") in asked_lines)]
	if in_hand and len(in_hand) == len(blockers) and not waiting_on_budget:
		# Every remaining over-budget line is with a department the Planner
		# asked to update its plan (owner decision 26 Sep 2026): the Planner
		# waits on that department, named, since the request.
		first = min((row for key, row in asked_departments.items()), key=lambda row: row.requested_at)
		department = departmental_update.unit_name(first.organisation_unit)
		people = ou_holders("Departmental Author", first.organisation_unit)["people"] + [
			name for name in ou_holders("Head of User Department", first.organisation_unit)["people"]
		]
		holder = ns.holder(department, list(dict.fromkeys(people)))
		waiting = ns.answer(
			ns.KIND_WAITING, headline=f"Waiting for {department} to update its departmental plan",
			stage=STAGE_PREPARATION, holder=holder, since=_since(first.requested_at),
		)
		result["others"] = waiting
		result["stage_holder"] = department
		result["mine"] = waiting if roles[ROLE_PROCUREMENT_PLANNER] else None
		return result
	if waiting_on_budget and len(in_hand) == len(blockers):
		# §5.7: every remaining blocker is a line the Budget Officer has been
		# asked to revise — the Planner waits (Draft editing stays
		# available as ordinary Draft editing).
		officer = guards.holder(guards.ROLE_BUDGET_OFFICER)
		first = requests[waiting_on_budget[0]["figures"]["budget_line"]]
		waiting = ns.answer(
			ns.KIND_WAITING, headline=f"Waiting for {officer['display']} to revise the budget line",
			stage=STAGE_PREPARATION, holder=officer, since=_since(first.requested_at),
		)
		# Every reader, not only the Planner, is told it is with the Budget
		# Officer — not "waiting for the Planner to prepare" (found live) —
		# and the tracker names the same holder as the line.
		result["others"] = waiting
		result["stage_holder"] = _names(officer)
		result["mine"] = waiting if roles[ROLE_PROCUREMENT_PLANNER] else None
		if authz.has_site_role(guards.ROLE_BUDGET_OFFICER, actor):
			# A Budget Officer who can read the plan (found live 25 Sep 2026:
			# Josphat Mwangi also confirms funding) holds this step: the turn
			# is theirs, decided in Budget (§5.7 "Budget Officer: Your turn in
			# BUD"), never "waiting for" themselves.
			line = waiting_on_budget[0]["figures"]
			result["mine"] = ns.answer(
				ns.KIND_YOUR_TURN,
				headline=f"Revise {line.get('title') or line.get('reference')} for the plan update",
				stage=STAGE_PREPARATION,
				fixes=[ns.fix(
					"Open the request in Budget & Funding", responsibility=guards.ROLE_BUDGET_OFFICER,
					kind=ns.FIX_ROUTE, fix_id="open_budget_revision_request",
					target=["budget-funding", {"fiscal_year": plan.fiscal_year}],
				)],
			)
		return result

	result["mine"] = ns.answer(
		ns.KIND_BLOCKED,
		headline=_count_headline(blockers, "stop this plan going to Finance"),
		sentence=_pre_finance_sentence(blockers),
		stage=STAGE_PREPARATION,
		blockers=blockers,
	) if roles[ROLE_PROCUREMENT_PLANNER] else None
	return result


def _count_headline(blockers: list[dict[str, Any]], what: str) -> str:
	"""§10.1A.5 D1 — name one blocker; count two or more."""
	if len(blockers) == 1:
		return blockers[0]["headline"]
	return f"{len(blockers)} things {what}"


def _pre_finance_sentence(blockers: list[dict[str, Any]]) -> str:
	if len(blockers) > 1:
		return "You can request the funding check once all of these are resolved."
	code = blockers[0]["reason_code"]
	if code == "PLN_PLAN_NOT_AFFORDABLE":
		return (
			"Purchase costs come from the departments' accepted requirements and cannot be lowered in the plan. "
			"You can request the funding check once the line's approved amount covers them."
		)
	if code == "PLN_PLAN_CONTENTS_INCOMPLETE" and "procurement method" in blockers[0]["headline"]:
		return "You can request the funding check once a method is chosen."
	return "You can request the funding check once this is resolved."


def _governance_state(version, *, actor, roles, stage: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance, plan_governance

	stage_name = plan_governance.STAGE_AO if stage == STAGE_AO else plan_governance.STAGE_STATUTORY
	task = _open_task_created("Plan Governance Task", {"plan_version": version.name, "stage": stage_name})
	if stage == STAGE_AO:
		holding = guards.holder(ROLE_ACCOUNTING_OFFICER)
		role, action = ROLE_ACCOUNTING_OFFICER, authz.ACTION_AO_DECIDE
		verb, turn = "adopt or return the plan", "Adopt and submit the plan, or return it for correction"
	else:
		holding = _statutory_holder()
		role, action = ROLE_PLAN_STATUTORY_APPROVER, authz.ACTION_STATUTORY_DECIDE
		verb, turn = "approve or return the plan", "Approve the annual plan, or return it for correction"
	others = _waiting(f"Waiting for {holding['display']} to {verb}", stage=stage, holder=holding, since=task.creation if task else None)
	result = {"stage": stage, "stage_holder": ", ".join(holding["people"]) or holding["role"], "others": others, "mine": None}
	if roles[role] and task and not authz.is_segregated(actor, action, plan_version=version.name):
		if stage == STAGE_AO and not plan_governance.statutory_route_configured():
			# §10.16 C01-ROUTE-MISSING: adoption creates the statutory task, so
			# the missing approval authority is the AO's blocker (D3 fix).
			result["blocked"] = True
			setting = ns.blocker(guards.setting_guard("PLN_STATUTORY_ROUTE_UNCONFIGURED", "Annual Plan approval authority", "Adopt and submit"))
			result["mine"] = ns.answer(ns.KIND_BLOCKED, headline=setting["headline"], stage=stage, blockers=[setting])
		elif not plan_finance.funding_is_current(version):
			# U11-STALE-EVIDENCE: the positive decision is blocked; Return stays.
			result["blocked"] = True
			result["mine"] = ns.answer(ns.KIND_YOUR_TURN, headline="Return the plan for a new funding check", stage=stage, primary_action="return_for_correction")
		else:
			result["mine"] = ns.answer(ns.KIND_YOUR_TURN, headline=turn, stage=stage, primary_action="decide")
	return result


def _publication_state(version, *, actor, roles) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import treasury as treasury_service

	ao = guards.holder(ROLE_ACCOUNTING_OFFICER)
	statutory = _statutory_holder()
	publication = frappe.db.get_value(
		"Plan Publication", {"plan_version": version.name}, ["name", "publication_state"], as_dict=True, order_by="creation desc",
	)
	attempt = frappe.db.get_value(
		"Publication Attempt", {"publication": publication.name}, ["attempted_at", "result"], as_dict=True, order_by="attempt_number desc",
	) if publication else None
	hold = frappe.db.get_value("Plan Publication Hold", {"plan_version": version.name, "hold_state": "Active"}, ["hold_kind", "raised_at"], as_dict=True)
	withdrawal_task = frappe.db.get_value("Plan Governance Task", {"plan_version": version.name, "task_reference": f"SAT-WD-{version.name}", "status": "Open"}, "name")
	treasury = frappe.db.get_value("Treasury Submission Evidence", {"plan_version": version.name, "evidence_state": "Current"}, ["recorded_at"], as_dict=True)
	base = {"stage": STAGE_PUBLICATION, "mine": None}

	if withdrawal_task:
		others = _waiting(f"Waiting for {statutory['display']} to decide the withdrawal", stage=STAGE_PUBLICATION, holder=statutory, since=hold.raised_at if hold else None)
		mine = ns.answer(ns.KIND_YOUR_TURN, headline="Withdraw the plan for correction", stage=STAGE_PUBLICATION, primary_action="decide_withdrawal") if roles[ROLE_PLAN_STATUTORY_APPROVER] else None
		return {**base, "blocked": True, "stage_holder": ", ".join(statutory["people"]) or statutory["role"], "others": others, "mine": mine}
	if hold and treasury_service._confirmed_unpublished(version):
		others = _waiting(f"Waiting for {ao['display']} to request withdrawal for correction", stage=STAGE_PUBLICATION, holder=ao, since=hold.raised_at)
		mine = ns.answer(ns.KIND_YOUR_TURN, headline="Request withdrawal for correction", stage=STAGE_PUBLICATION, primary_action="request_withdrawal") if roles[ROLE_ACCOUNTING_OFFICER] else None
		return {**base, "blocked": True, "stage_holder": ", ".join(ao["people"]) or ao["role"], "others": others, "mine": mine}
	state = cstr(publication.publication_state) if publication else ""
	if version.version_status == "Publication failed" or state in ("Failed", "Indeterminate"):
		unknown = state == "Indeterminate"
		operator = ns.holder(TECHNICAL_OPERATOR)
		verb = "check the publication result" if unknown else "retry publication"
		others = _waiting(f"Waiting for an authorised technical operator to {verb}", stage=STAGE_PUBLICATION, holder=operator, since=attempt.attempted_at if attempt else None)
		# O4 — the one named exception to KT-STD-001 v1.8 §3B.6: the
		# authorised technical operator's turn, on this screen only.
		mine = ns.answer(ns.KIND_YOUR_TURN, headline="Check the publication result" if unknown else "Retry publication", stage=STAGE_PUBLICATION, primary_action="reconcile" if unknown else "retry") if is_technical(actor) else None
		return {**base, "blocked": True, "stage_holder": TECHNICAL_OPERATOR, "others": others, "mine": mine, "technical_turn": True}
	if not treasury:
		others = _waiting(f"Waiting for {ao['display']} to record the Treasury submission", stage=STAGE_PUBLICATION, holder=ao, since=version.modified)
		mine = ns.answer(ns.KIND_YOUR_TURN, headline="Record the Treasury submission", stage=STAGE_PUBLICATION, primary_action="record_treasury") if roles[ROLE_ACCOUNTING_OFFICER] else None
		return {**base, "stage_holder": ", ".join(ao["people"]) or ao["role"], "others": others, "mine": mine}
	# RG-01 (owner decision 7 Oct 2026): Treasury evidence is in and nothing is held, so the
	# Head of Procurement Function presses Publish
	hopf = guards.holder(ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
	others = _waiting(f"Waiting for {hopf['display']} to publish the plan", stage=STAGE_PUBLICATION, holder=hopf, since=treasury.recorded_at)
	mine = ns.answer(ns.KIND_YOUR_TURN, headline="Publish the annual plan", stage=STAGE_PUBLICATION, primary_action="publish") if roles[ROLE_HEAD_OF_PROCUREMENT_FUNCTION] else None
	return {**base, "stage_holder": ", ".join(hopf["people"]) or hopf["role"], "others": others, "mine": mine}


def _requisitions_link(version) -> dict[str, Any] | None:
	"""§10.1A.1 — the downstream count at In force, from the owner evidence
	(Planning's drawdown references record each authorised requisition)."""
	items = frappe.get_all("Annual Plan Item", filters={"plan_version": version.name}, pluck="name")
	if not items:
		return None
	count = len({
		cstr(r) for r in frappe.get_all(
			"Plan Drawdown Reference", filters={"plan_item": ("in", items)}, pluck="requisition_reference",
		) if r
	})
	return ns.link(f"{count} requisition{'s' if count != 1 else ''} raised", kind=ns.FIX_ROUTE, target=["annual-procurement-plan", frappe.db.get_value("Annual Plan", version.annual_plan, "plan_reference"), "progress"])


# --------------------------------------------------------------------------
# Departmental plan (§5.7 second table, §10.1A.2)
# --------------------------------------------------------------------------

DPP_PREPARATION = "preparation"
DPP_CERTIFICATION = "certification"
DPP_REVIEW = "review"
DPP_ACCEPTED = "accepted"
DPP_STAGES = [
	(DPP_PREPARATION, "Preparation"),
	(DPP_CERTIFICATION, "Certification"),
	(DPP_REVIEW, "Procurement review"),
	(DPP_ACCEPTED, "Accepted"),
]


def ou_holders(role: str, organisation_unit: str) -> dict[str, Any]:
	"""Who currently holds an Organisation-Unit responsibility covering this
	unit (an assignment covers its unit and every descendant)."""
	from frappe.utils import getdate, nowdate

	from kentender_core.services.authorization import descendants_of

	today = getdate(nowdate())
	names = []
	for row in frappe.get_all(
		"User Responsibility Assignment",
		# "is set", not `not in ("", None)`: SQL `x NOT IN ('', NULL)` is never
		# true, so that filter matched no one and every department step named
		# the role alone (found in the named-user pass 26 Sep 2026).
		filters={"business_role": role, "status": "Enabled", "organisation_unit": ("is", "set")},
		fields=["user", "organisation_unit", "effective_from", "effective_to"],
		limit_page_length=0,
	):
		if row.effective_from and getdate(row.effective_from) > today:
			continue
		if row.effective_to and getdate(row.effective_to) < today:
			continue
		if organisation_unit in descendants_of({row.organisation_unit}):
			name = cstr(frappe.db.get_value("User", row.user, "full_name") or row.user)
			if name not in names:
				names.append(name)
	return ns.holder(role, names)


def _names(holder: dict[str, Any]) -> str:
	return ", ".join(holder["people"]) or holder["role"]


def dpp_guidance(
	root,
	version,
	*,
	actor: str,
	access: str,
	ready: bool,
	incomplete: int,
	entry_count: int,
	window_closed: bool,
	is_correction: bool,
	update_in_progress: bool,
	reduced: bool = False,
	update_requested_at=None,
	late_needs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
	"""`{"next_step", "journey"}` for a departmental plan (U02–U05).

	`access` is `dpp_read_profile`'s answer for the viewer: hod, author,
	planner or oversight (a technical reader or Auditor). `late_needs` are
	`needs_intake.late_needs(root)`: accepted Needs an accepted plan with no
	open candidate does not carry."""
	from kentender_procurement.procurement_planning.services.planning_roles import (
		ROLE_DEPARTMENTAL_AUTHOR,
		ROLE_HEAD_OF_USER_DEPARTMENT,
	)

	technical = is_technical(actor)
	department = access in ("hod", "author")
	hod = ou_holders(ROLE_HEAD_OF_USER_DEPARTMENT, root.organisation_unit)
	authors = ou_holders(ROLE_DEPARTMENTAL_AUTHOR, root.organisation_unit)
	status = version.version_status if version else ""

	if status == "Draft":
		if window_closed and not is_correction and not update_in_progress:
			# U02-CLOSED — the initial window is a System setup setting (D3).
			blocker = ns.blocker(ns.guard(
				False, reason_code="PLN_WINDOW_CLOSED", headline="Initial submissions are closed",
				fixes=[ns.fix("Ask your KenTender administrator to complete this setting.", responsibility=TECHNICAL_OPERATOR, kind=ns.FIX_TEXT, fix_id=guards.FIX_ASK_ADMINISTRATOR)],
			))
			mine = ns.answer(ns.KIND_BLOCKED, headline="Initial submissions are closed", sentence="You can keep editing this draft, but it cannot be submitted now.", stage=DPP_PREPARATION, blockers=[blocker]) if department else None
			others = _waiting(f"Waiting for the department to prepare its plan", stage=DPP_PREPARATION, holder=authors)
			return _dpp_result(mine, others, stage=DPP_PREPARATION, blocked=True, holder=_names(authors), technical=technical, department=department or access == "planner", reduced=reduced)
		if is_correction:
			mine = ns.answer(ns.KIND_YOUR_TURN, headline="Correct and resubmit the departmental plan", stage=DPP_PREPARATION, primary_action="resubmit") if department else None
			others = _waiting("Waiting for the department to correct its plan", stage=DPP_PREPARATION, holder=hod)
			return _dpp_result(mine, others, stage=DPP_PREPARATION, holder=_names(hod), technical=technical, department=department or access == "planner", reduced=reduced)
		if ready:
			# U05-HOD — complete content is the Head of Department's to certify.
			mine = None
			if access == "hod":
				mine = ns.answer(ns.KIND_YOUR_TURN, headline="Certify and submit the departmental plan", stage=DPP_CERTIFICATION, primary_action="submit")
			others = _waiting(f"Waiting for {hod['display']} to certify and submit the departmental plan", stage=DPP_CERTIFICATION, holder=hod)
			return _dpp_result(mine, others, stage=DPP_CERTIFICATION, holder=_names(hod), technical=technical, department=department or access == "planner", reduced=reduced)
		if update_in_progress:
			headline = "Continue the departmental update"
		elif entry_count and incomplete:
			headline = f"Enter funding details for {incomplete} requirement{'s' if incomplete != 1 else ''}"
		else:
			headline = "Add the department's requirements to the plan"
		mine = ns.answer(ns.KIND_YOUR_TURN, headline=headline, stage=DPP_PREPARATION, primary_action="continue") if department else None
		others = _waiting("Waiting for the department to prepare its plan", stage=DPP_PREPARATION, holder=authors)
		return _dpp_result(mine, others, stage=DPP_PREPARATION, holder=_names(authors), technical=technical, department=department or access == "planner", reduced=reduced)

	if status == "Submitted":
		planner = guards.holder(ROLE_PROCUREMENT_PLANNER)
		submitted_at = frappe.db.get_value("Departmental Plan Submission", {"dpp_version": version.name}, "submitted_at")
		others = _waiting(f"Waiting for {planner['display']} to review the submission", stage=DPP_REVIEW, holder=planner, since=submitted_at)
		mine = None
		if access == "planner":
			task = frappe.db.get_value("Departmental Plan Validation Task", {"dpp_version": version.name, "status": "Open"}, ["name", "submission"], as_dict=True)
			if task and not authz.is_segregated(actor, authz.ACTION_DPP_VALIDATE, submission=task.submission):
				mine = ns.answer(ns.KIND_YOUR_TURN, headline="Classify every included requirement, then accept or return the submission", stage=DPP_REVIEW, primary_action="review")
			else:
				# §10.5 U06-SEGREGATION: the other Planners by name, or the
				# role alone where none resolves (§6.5) — never the certifier.
				me = cstr(frappe.db.get_value("User", actor, "full_name") or actor)
				others_named = [name for name in guards.people(ROLE_PROCUREMENT_PLANNER) if name != me]
				mine = _waiting("Waiting for Procurement review by another Procurement Planner", stage=DPP_REVIEW, holder=ns.holder(ROLE_PROCUREMENT_PLANNER, others_named), since=submitted_at)
		return _dpp_result(mine, others, stage=DPP_REVIEW, holder=_names(planner), technical=technical, department=department or access == "planner", reduced=reduced)

	if root.current_state == "Accepted" and root.current_accepted_version:
		holders = ns.holder("Departmental Author or Head of User Department", list(dict.fromkeys(authors["people"] + hod["people"])))
		late = late_needs or []
		# Owner instruction 28 Sep 2026 — an update the department still has to
		# make starts the next round at Preparation, so the tracker and the
		# next step agree instead of "every stage Done" beside "Your turn".
		pending = bool(update_requested_at or late)
		journey = (
			ns.journey(DPP_STAGES, current=DPP_PREPARATION, holder_display=_names(holders), reduced=reduced) if pending
			else ns.journey(DPP_STAGES, complete=True, reduced=reduced)
		)
		if update_requested_at:
			# Procurement asked the department to update its accepted plan
			# (owner decision 26 Sep 2026): the department's turn, everyone
			# else waits on the department.
			others = _waiting("Waiting for the department to update its plan", stage=DPP_PREPARATION, holder=holders, since=update_requested_at)
			also = f"The update also adds {needs_intake.need_list(late)}, accepted after this plan." if late else ""
			mine = ns.answer(ns.KIND_YOUR_TURN, headline="Update this plan as Procurement asked", sentence=also, stage=DPP_PREPARATION, primary_action="create_update") if department else None
			answer = others if technical or not mine else mine
			return {"next_step": answer, "journey": journey}
		if late:
			# Owner decision 26 Sep 2026 — a Need accepted after this plan was
			# accepted is in no plan until the department creates an update;
			# "Done" here left it stranded with no one told to act.
			names = needs_intake.need_list(late)
			one = len(late) == 1
			sentence = (
				f"{'It was' if one else 'They were'} accepted after this plan was accepted. "
				f"Create an update to add {'it' if one else 'them'}, then fund {'it' if one else 'them'} and resubmit."
			)
			mine = ns.answer(ns.KIND_YOUR_TURN, headline=f"Add {names} to this plan", sentence=sentence, stage=DPP_PREPARATION, primary_action="create_update") if department else None
			others = _waiting(f"Waiting for the department to add {names} to its plan", stage=DPP_PREPARATION, holder=holders, since=needs_intake.late_needs_since(late))
			if technical:
				answer = ns.for_viewer(others, technical=True, reader=others)
			elif mine:
				answer = mine
			elif access == "planner":
				answer = others
			else:
				# §10.1A.6 — an Auditor or other reader is Not involved.
				answer = ns.not_involved(DPP_PREPARATION)
			return {"next_step": answer, "journey": journey}
		done = ns.answer(ns.KIND_DONE, headline=accepted_line(root.current_accepted_version), stage=DPP_ACCEPTED)
		return {"next_step": done, "journey": journey}
	return {"next_step": ns.not_involved(), "journey": None}


def accepted_line(dpp_version: str) -> str:
	"""U06-ACCEPTED-CLASSIFICATION — "Accepted by {actor} on {instant}"."""
	submission = frappe.db.get_value("Departmental Plan Submission", {"dpp_version": dpp_version}, "name")
	task = frappe.db.get_value("Departmental Plan Validation Task", {"submission": submission}, "decision") if submission else None
	decision = frappe.db.get_value("Departmental Plan Validation Decision", task, ["actor", "decided_at"], as_dict=True) if task else None
	if not decision:
		return "Accepted"
	who = cstr(frappe.db.get_value("User", decision.actor, "full_name") or decision.actor)
	return f"Accepted by {who} on {_eat(decision.decided_at)}"


def _dpp_result(mine, others, *, stage: str, holder: str, technical: bool, department: bool, reduced: bool, blocked: bool = False) -> dict[str, Any]:
	journey = ns.journey(DPP_STAGES, current=stage, blocked=blocked, holder_display=holder, reduced=reduced)
	if technical:
		answer = ns.for_viewer(others, technical=True, reader=others)
	elif mine:
		answer = mine
	elif department:
		answer = others
	else:
		# §10.1A.6 — an Auditor or other reader is Not involved.
		answer = ns.not_involved(stage)
	return {"next_step": answer, "journey": journey}
