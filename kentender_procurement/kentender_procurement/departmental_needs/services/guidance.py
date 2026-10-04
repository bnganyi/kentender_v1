# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.15 §5.5 — Departmental Needs' next-step answer and journey
tracker (KT-STD-001 v1.9 §2.9, §3B).

For the signed-in actor this answers, from the same facts that decide the
page's actions (`workspace._actions` and the owner actions of §12.4): where
the Need stands, whose turn it is, and — when nothing can move — why not and
who can. The shape is kentender_core's (`kentender_core.services.next_step`);
the stages, holders and wording are this module's §5.5. Screens draw the
answer unchanged; nothing here writes anything.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services import next_step as ns
from kentender_core.services.authorization import is_technical
from kentender_core.utils.display import display_datetime
from kentender_procurement.departmental_needs.constants import (
	ACTION_ACCEPT,
	ACTION_ACCEPT_SUCCESSOR,
	ACTION_REQUEST_WITHDRAWAL,
	ACTION_RESUBMIT,
	ACTION_SUBMIT,
	ACTION_SUBMIT_SUCCESSOR,
	REVISION_SUBMITTED,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_NOT_TAKEN_FORWARD,
	STATE_RETURNED,
	STATE_SUBMITTED,
	STATE_WITHDRAWN,
	WITHDRAWAL_AWAITING_CLEARANCE,
	WITHDRAWAL_AWAITING_REVIEW,
)
from kentender_procurement.departmental_needs.services.permissions import in_scope, is_owner

STAGE_PREPARATION = "preparation"
STAGE_REVIEW = "review"
STAGE_ACCEPTED = "accepted"
STAGES = [
	(STAGE_PREPARATION, "Preparation"),
	(STAGE_REVIEW, "Head of Department review"),
	(STAGE_ACCEPTED, "Accepted for planning"),
]

TECHNICAL_OPERATOR = "Administrator or System Manager"


def _name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name") or user) if user else ""


def _since(value) -> dict[str, Any] | None:
	return ns.since(value, display_datetime(value)) if value else None


def _last_decision(need: str, actions: list[str]):
	return frappe.db.get_value(
		"Departmental Need Decision",
		{"departmental_need": need, "action": ("in", actions)},
		["actor", "occurred_at"],
		order_by="occurred_at desc",
		as_dict=True,
	)


def _people(need, role: str, *, exclude: tuple[str, ...] = ()) -> list[str]:
	"""Named holders of an Organisation-Unit responsibility covering the Need
	(the same resolver the notifications and review queue use)."""
	users = frappe.get_all("Has Role", filters={"role": role, "parenttype": "User"}, pluck="parent")
	enabled = frappe.get_all("User", filters={"name": ("in", sorted(set(users)) or [""]), "enabled": 1}, pluck="name")
	names = []
	for user in sorted(enabled):
		if user in exclude or is_technical(user):
			continue
		if in_scope(user, business_role=role, organisation_unit=need.organisation_unit):
			names.append(_name(user))
	return names


def _reviewers(need, *, maker: str = "") -> dict[str, Any]:
	return ns.holder(ROLE_HEAD_OF_USER_DEPARTMENT, _people(need, ROLE_HEAD_OF_USER_DEPARTMENT, exclude=(maker,) if maker else ()))


def _author(need) -> dict[str, Any]:
	return ns.holder(ROLE_DEPARTMENTAL_AUTHOR, [_name(need.owner)])


def _department(need) -> dict[str, Any]:
	people = _people(need, ROLE_DEPARTMENTAL_AUTHOR) + _people(need, ROLE_HEAD_OF_USER_DEPARTMENT)
	return ns.holder("Departmental Author or Head of User Department", list(dict.fromkeys(people)))


def _planners() -> dict[str, Any]:
	users = frappe.get_all("Has Role", filters={"role": ROLE_PROCUREMENT_PLANNER, "parenttype": "User"}, pluck="parent")
	enabled = frappe.get_all("User", filters={"name": ("in", sorted(set(users)) or [""]), "enabled": 1}, pluck="name")
	names = [
		_name(user) for user in sorted(enabled)
		if not is_technical(user) and in_scope(user, business_role=ROLE_PROCUREMENT_PLANNER, organisation_unit="")
	]
	return ns.holder(ROLE_PROCUREMENT_PLANNER, names)


def _is_planner(principal: str) -> bool:
	return not is_technical(principal) and in_scope(principal, business_role=ROLE_PROCUREMENT_PLANNER, organisation_unit="")


def _department_name(need) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", need.organisation_unit, "unit_name") or need.organisation_unit)


def _waiting(headline: str, *, stage: str, holder: dict[str, Any], since=None, sentence: str = "") -> dict[str, Any]:
	return ns.answer(ns.KIND_WAITING, headline=headline, sentence=sentence, stage=stage, holder=holder, since=_since(since))


def _result(mine: dict[str, Any] | None, others: dict[str, Any], journey: dict[str, Any] | None, *, technical: bool) -> dict[str, Any]:
	if technical:
		answer = ns.for_viewer(others, technical=True, reader=others)
	else:
		answer = mine or others
	return {"next_step": answer, "journey": journey}


def _open_withdrawal(need: str):
	return frappe.db.get_value(
		"Need Withdrawal Request",
		{"departmental_need": need, "status": ("in", [WITHDRAWAL_AWAITING_REVIEW, WITHDRAWAL_AWAITING_CLEARANCE])},
		["name", "status", "requested_by", "creation"],
		as_dict=True,
	)


def need_guidance(
	doc,
	*,
	principal: str,
	actions: list[dict[str, Any]],
	intake_open: bool,
	planning_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""`{"next_step", "journey"}` for one Need (NDS-UI-04/05/07).

	`actions` is the page's own server-computed action list for this viewer
	(`workspace._actions`); a turn is offered only where it offers the
	matching action, so the answer and the buttons cannot disagree."""
	technical = is_technical(principal)
	codes = {cstr(a.get("code")) for a in actions or []}
	owner = is_owner(doc, principal) and not technical
	state = doc.current_state

	if state in (STATE_NOT_TAKEN_FORWARD, STATE_WITHDRAWN):
		# A terminal Need is off the forward path: no tracker (§5.5). Who
		# decided and when stay in the page's own NDS-DES-TERMINAL rows.
		headline = (
			"Not taken forward. Nothing further happens to this need." if state == STATE_NOT_TAKEN_FORWARD
			else "Withdrawn. Nothing further happens to this need."
		)
		return _result(None, ns.answer(ns.KIND_DONE, headline=headline), None, technical=technical)

	if state in (STATE_DRAFT, STATE_RETURNED):
		returned = state == STATE_RETURNED
		journey = ns.journey(STAGES, current=STAGE_PREPARATION, blocked=not intake_open, holder_display=_author(doc)["display"])
		others = _waiting(
			f"Waiting for {_name(doc.owner)} to correct and resubmit the requirement" if returned
			else f"Waiting for {_name(doc.owner)} to submit the requirement",
			stage=STAGE_PREPARATION, holder=_author(doc),
		)
		mine = None
		if "edit" in codes:
			if intake_open:
				mine = ns.answer(
					ns.KIND_YOUR_TURN,
					headline="Make the requested changes and resubmit" if returned else "Complete this requirement and submit it for review",
					stage=STAGE_PREPARATION, primary_action="edit",
				)
			else:
				# NDS-BR-003 — closed intake blocks submission, never the draft.
				blocker = ns.blocker(ns.guard(
					False, reason_code="NDS_INTAKE_NOT_OPEN", headline="New submissions are closed",
					fixes=[ns.fix(
						"Ask your KenTender administrator to reopen needs submissions.",
						responsibility=TECHNICAL_OPERATOR, kind=ns.FIX_TEXT, fix_id="ask_administrator",
					)],
				))
				mine = ns.answer(
					ns.KIND_BLOCKED, headline="New submissions are closed",
					sentence=(
						"You can keep editing this correction and resubmit it if submissions reopen." if returned
						else "You can keep editing this draft and submit it if submissions reopen."
					),
					stage=STAGE_PREPARATION, blockers=[blocker],
				)
		return _result(mine, others, journey, technical=technical)

	if state == STATE_SUBMITTED:
		submitted = _last_decision(doc.name, [ACTION_SUBMIT, ACTION_RESUBMIT])
		maker = cstr(submitted.actor) if submitted else cstr(doc.owner)
		reviewers = _reviewers(doc, maker=maker)
		journey = ns.journey(STAGES, current=STAGE_REVIEW, holder_display=reviewers["display"])
		others = _waiting(
			f"Waiting for {reviewers['display']} to review the requirement",
			stage=STAGE_REVIEW, holder=reviewers, since=submitted.occurred_at if submitted else None,
		)
		mine = None
		if "review" in codes:
			mine = ns.answer(
				ns.KIND_YOUR_TURN, headline="Decide whether this requirement is available to Procurement Planning",
				stage=STAGE_REVIEW, primary_action="review",
			)
		elif principal == maker and in_scope(principal, business_role=ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=doc.organisation_unit):
			mine = _waiting(
				"Waiting for another Head of User Department to review this requirement",
				sentence="You submitted this revision, so it must be decided by another Head of User Department.",
				stage=STAGE_REVIEW, holder=reviewers, since=submitted.occurred_at if submitted else None,
			)
		return _result(mine, others, journey, technical=technical)

	if state != STATE_ACCEPTED:
		return {"next_step": ns.not_involved(), "journey": None}

	# Accepted for planning: an open withdrawal, then an open update, then
	# Planning's position, then done (§5.5 precedence).
	withdrawal = _open_withdrawal(doc.name)
	if withdrawal:
		requested = _last_decision(doc.name, [ACTION_REQUEST_WITHDRAWAL])
		reviewers = _reviewers(doc, maker=cstr(withdrawal.requested_by))
		journey = ns.journey(STAGES, complete=True)
		clearance = withdrawal.status == WITHDRAWAL_AWAITING_CLEARANCE
		if clearance:
			others = _waiting(
				"Waiting for a Planning change",
				sentence="The annual plan has not yet been updated. Withdrawal cannot be approved while this requirement remains included.",
				stage=STAGE_ACCEPTED, holder=_planners(), since=requested.occurred_at if requested else withdrawal.creation,
			)
		else:
			others = _waiting(
				f"Waiting for {reviewers['display']} to decide the withdrawal request",
				stage=STAGE_ACCEPTED, holder=reviewers, since=requested.occurred_at if requested else withdrawal.creation,
			)
		mine = None
		if clearance and _is_planner(principal):
			# The wait is on Procurement Planning; its Planner is never told to
			# wait for themselves (KT-STD-001 §3B.7 rule 5, found by the matrix).
			item = cstr(frappe.db.get_value("Need Planning Usage Projection", cstr(doc.current_accepted_revision), "active_plan_item"))
			mine = ns.answer(
				ns.KIND_YOUR_TURN, headline="Decide whether the annual plan keeps this need",
				sentence="The department has asked to withdraw it. Withdrawal cannot be approved while it remains in the annual plan.",
				stage=STAGE_ACCEPTED,
				fixes=[ns.fix("View annual plan item", responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_ROUTE,
					fix_id="view_annual_plan_item", target=["procurement-plan-item", item])] if item else [],
			)
			if not item:
				mine = None
		if "withdrawal" in codes:
			mine = ns.answer(
				ns.KIND_YOUR_TURN,
				headline="Decline the withdrawal, or wait for the annual plan to change" if clearance else "Decide the withdrawal request",
				sentence="Withdrawal cannot be approved while this need is in the current annual plan." if clearance else "",
				stage=STAGE_ACCEPTED, primary_action="withdrawal",
			)
		return _result(mine, others, journey, technical=technical)

	if cstr(doc.current_revision) and cstr(doc.current_revision) != cstr(doc.current_accepted_revision):
		successor_status = cstr(frappe.db.get_value("Departmental Need Revision", doc.current_revision, "revision_status"))
		if successor_status == REVISION_SUBMITTED:
			submitted = _last_decision(doc.name, [ACTION_SUBMIT_SUCCESSOR])
			reviewers = _reviewers(doc, maker=cstr(submitted.actor) if submitted else cstr(doc.owner))
			journey = ns.journey(STAGES, current=STAGE_REVIEW, holder_display=reviewers["display"])
			others = _waiting(
				f"Waiting for {reviewers['display']} to review the proposed changes",
				stage=STAGE_REVIEW, holder=reviewers, since=submitted.occurred_at if submitted else None,
			)
			mine = None
			if "review" in codes:
				mine = ns.answer(
					ns.KIND_YOUR_TURN, headline="Decide whether the proposed changes replace the accepted requirement",
					stage=STAGE_REVIEW, primary_action="review",
				)
			return _result(mine, others, journey, technical=technical)
		journey = ns.journey(STAGES, current=STAGE_PREPARATION, holder_display=_author(doc)["display"])
		others = _waiting(f"Waiting for {_name(doc.owner)} to finish the proposed update", stage=STAGE_PREPARATION, holder=_author(doc))
		mine = None
		if owner:
			mine = ns.answer(
				ns.KIND_YOUR_TURN, headline="Continue the update and submit it for review",
				sentence="An update is already in progress. Complete or cancel it before requesting withdrawal.",
				stage=STAGE_PREPARATION,
				fixes=[ns.fix("Continue update", responsibility=ROLE_DEPARTMENTAL_AUTHOR, kind=ns.FIX_ROUTE, fix_id="continue_update",
					target=["departmental-needs", doc.name, "edit"])],
			)
		return _result(mine, others, journey, technical=technical)

	journey = ns.journey(STAGES, complete=True)
	accepted = _last_decision(doc.name, [ACTION_ACCEPT, ACTION_ACCEPT_SUCCESSOR])
	accepted_at = accepted.occurred_at if accepted else None
	position = planning_intake or {}
	department = _department_name(doc)
	if position.get("position") == "Update required":
		carried = int(position.get("carried_revision_number") or 0)
		revision = int(position.get("revision_number") or 0)
		headline = (
			f"Update {department}'s departmental plan to revision {revision} of this need" if carried
			else f"Add this need to {department}'s departmental plan"
		)
		sentence = (
			f"The plan still has revision {carried}. Create an update of the plan to bring in the accepted changes." if carried
			else "The plan was accepted before this need. Create an update of the plan, fund the need and resubmit."
		)
		others = _waiting(
			(f"Waiting for {department} to update its departmental plan to revision {revision}" if carried
			 else f"Waiting for {department} to add this need to its departmental plan"),
			stage=STAGE_ACCEPTED, holder=_department(doc), since=accepted_at,
		)
		mine = None
		if position.get("can_update") and position.get("departmental_plan"):
			mine = ns.answer(
				ns.KIND_YOUR_TURN, headline=headline, sentence=sentence, stage=STAGE_ACCEPTED,
				fixes=[ns.fix("Update departmental plan", responsibility="Departmental Author or Head of User Department",
					kind=ns.FIX_ROUTE, fix_id="update_departmental_plan",
					target=["departmental-procurement-plan", cstr(position["departmental_plan"])])],
			)
		return _result(mine, others, journey, technical=technical)
	if position.get("position") == "After current submission":
		others = _waiting(
			f"Waiting for Procurement to finish reviewing {department}'s departmental plan",
			sentence="This need goes into the plan's next update.",
			stage=STAGE_ACCEPTED, holder=_planners(), since=accepted_at,
		)
		mine = None
		if position.get("departmental_plan") and _is_planner(principal):
			# The Planner is Procurement: the review is theirs, on the plan.
			mine = ns.answer(
				ns.KIND_YOUR_TURN, headline=f"Finish reviewing {department}'s departmental plan",
				sentence="This need goes into the plan's next update.", stage=STAGE_ACCEPTED,
				fixes=[ns.fix("Open departmental plan", responsibility=ROLE_PROCUREMENT_PLANNER, kind=ns.FIX_ROUTE,
					fix_id="open_departmental_plan", target=["departmental-procurement-plan", cstr(position["departmental_plan"])])],
			)
		return _result(mine, others, journey, technical=technical)

	who = _name(accepted.actor) if accepted else ""
	headline = f"Accepted for planning by {who} on {display_datetime(accepted_at)}" if accepted else "Accepted for planning"
	return _result(None, ns.answer(ns.KIND_DONE, headline=headline, stage=STAGE_ACCEPTED), journey, technical=technical)
