# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 §7 — the Departmental Needs owner's feed to Home (owner key `needs`).

Registered on the `kt_home_providers` hook; core never imports this app. One
function, `entries(*, user, region)`, answers for one actor (never the session
user) and only reads: it never calls `workspace.get_workspace` (that persists the
working context) and no task is opened, closed or touched.

Every action text is the owner's own next-step wording (`guidance.need_guidance`, the
same answer the Need's page shows the same person), so the row and the page cannot say
different things.

- **my_work** — the Head of User Department's open review tasks (initial acceptance, an
  update to an accepted requirement, a withdrawal request) and the author's returned
  Needs. Who may decide a task is the owner's `permissions.in_scope` plus maker-checker
  (NDS-AC-042). An author's row is blocked only where the owner's answer for them is
  "Your turn, blocked" (submissions closed).
- **waiting** — what the author handed on and someone else holds: the Need under review,
  its update under review, its withdrawal request.
- **oversight** — NOT an owner concept: Needs has no "outstanding" list. This is a
  read-only summary Home derives from owner state for the people who may read a Need as
  its department's Head, an Auditor, or the Accounting Officer / Head of Procurement
  Function (only the states `OVERSIGHT_READ_STATES` allow): a Need awaiting review, awaiting
  its author's correction, with a withdrawal request open, or with an update submitted for
  review or returned. It uses the same `action_id` as the My work row for the same matter.
- **coming_up** — none in v1 (the needs-submission `closes_at` is a Fiscal Year flag, not
  a deadline recorded for an author; whether it belongs on an author's Coming up is an
  owner policy question).
- **completed** — the actor's own `Departmental Need Decision` rows of the last 30 days.

Returns None where the region does not apply to the actor, [] where it applies and there
is nothing to show; a failed read raises.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services import next_step as ns
from kentender_core.services.authorization import PURPOSE_READ, authorise_record, is_technical, permitted_ou_scopes
from kentender_procurement.departmental_needs import constants as c
from kentender_procurement.departmental_needs.services.context import INTAKE_OPEN, needs_submission_state
from kentender_procurement.departmental_needs.services.guidance import (
	STAGE_ACCEPTED,
	STAGE_PREPARATION,
	STAGE_REVIEW,
	_last_decision,
	_open_withdrawal,
	need_guidance,
)
from kentender_procurement.departmental_needs.services.permissions import can_view, in_scope

OWNER = "needs"
PAGE = "departmental-needs"
NEED_FIELDS = ["name", "need_reference", "owner", "organisation_unit", "financial_year", "current_state", "current_revision", "current_accepted_revision"]
REVIEW_KINDS = {c.TASK_INITIAL_ACCEPTANCE: "review", c.TASK_SUCCESSOR_ACCEPTANCE: "review", c.TASK_WITHDRAWAL: "withdrawal"}

#: Recently completed actions: Departmental Need Decision action → (the action label, what "You …" says). Saving a draft, creating
#: a Need or a successor, saving or cancelling a successor are not completed business actions and are not here.
COMPLETED: dict[str, tuple[str, str]] = {
	c.ACTION_SUBMIT: ("Submitted requirement for review", "submitted this requirement for review"),
	c.ACTION_RESUBMIT: ("Resubmitted requirement for review", "resubmitted this requirement for review"),
	c.ACTION_RETURN: ("Returned requirement for correction", "returned this requirement for correction"),
	c.ACTION_ACCEPT: ("Accepted requirement for planning", "accepted this requirement for planning"),
	c.ACTION_DECLINE: ("Did not take requirement forward", "decided not to take this requirement forward"),
	c.ACTION_WITHDRAW: ("Withdrew requirement", "withdrew this requirement"),
	c.ACTION_SUBMIT_SUCCESSOR: ("Submitted update for review", "submitted an update to this requirement for review"),
	c.ACTION_RETURN_SUCCESSOR: ("Returned update for correction", "returned an update to this requirement for correction"),
	c.ACTION_ACCEPT_SUCCESSOR: ("Accepted update", "accepted an update to this requirement"),
	c.ACTION_DECLINE_SUCCESSOR: ("Declined update", "declined an update to this requirement"),
	c.ACTION_REQUEST_WITHDRAWAL: ("Requested withdrawal", "asked to withdraw this requirement"),
	c.ACTION_EVALUATE_WITHDRAWAL: ("Evaluated withdrawal request", "evaluated the request to withdraw this requirement"),
	c.ACTION_REEVALUATE_WITHDRAWAL: ("Re-evaluated withdrawal request", "re-evaluated the request to withdraw this requirement"),
	c.ACTION_APPROVE_WITHDRAWAL: ("Approved withdrawal", "approved the withdrawal of this requirement"),
	c.ACTION_DECLINE_WITHDRAWAL: ("Declined withdrawal", "declined the request to withdraw this requirement"),
}
#: Decisions after which the Need waits on a Head of User Department, and what the clause calls that wait.
AWAITING_REVIEW = {c.ACTION_SUBMIT: ("review", STAGE_REVIEW), c.ACTION_RESUBMIT: ("review", STAGE_REVIEW), c.ACTION_SUBMIT_SUCCESSOR: ("review", STAGE_REVIEW), c.ACTION_REQUEST_WITHDRAWAL: ("the withdrawal decision", STAGE_ACCEPTED)}
AWAITING_CORRECTION = {c.ACTION_RETURN: [c.ACTION_RETURN], c.ACTION_RETURN_SUCCESSOR: [c.ACTION_RETURN_SUCCESSOR]}


# --------------------------------------------------------------------------
# facts read once per Home read
# --------------------------------------------------------------------------


def _people(names: list[str], role: str) -> str:
	"""The holders as a display: up to two names, otherwise the responsibility (never an invented person)."""
	return " or ".join(names) if names and len(names) <= 2 else cstr(role)


def _scopes(user: str) -> dict[str, bool]:
	"""Which Needs responsibilities the actor holds (AUTH assignments, read at the real clock as the resolver does)."""

	def site(role: str) -> bool:
		return authorise_record(user=user, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed

	return {
		"author": bool(permitted_ou_scopes(user, c.ROLE_DEPARTMENTAL_AUTHOR)),
		"hod": bool(permitted_ou_scopes(user, c.ROLE_HEAD_OF_USER_DEPARTMENT)),
		"planner": site(c.ROLE_PROCUREMENT_PLANNER),
		"auditor": site(c.ROLE_AUDITOR),
		"office": any(site(role) for role in c.OVERSIGHT_READ_ROLES),
	}


def _holds(user: str) -> dict[str, bool]:
	"""What the actor's responsibilities give Home: work (My work, Waiting, Completed), oversight, and whether they review as a Head of User Department."""

	def build() -> dict[str, bool]:
		if not user or user == "Guest" or is_technical(user):
			return {"work": False, "oversight": False, "hod": False}
		scopes = _scopes(user)
		return {
			"hod": scopes["hod"],
			# a Needs responsibility with work of its own; the Accounting Officer's and Head of Procurement Function's read grant is not one
			"work": scopes["author"] or scopes["hod"] or scopes["planner"] or scopes["auditor"],
			"oversight": scopes["hod"] or scopes["auditor"] or scopes["office"],
		}

	return home_support.memo("needs.holds", build, user=user)


class _Facts:
	"""What one actor's Home read needs more than once: the Need roots, their titles, the read verdict, the intake state per year
	and the owner's next-step answer per Need."""

	def __init__(self, user: str):
		self.user = user
		self._needs: dict[str, Any] = {}
		self._titles: dict[str, str] = {}
		self._steps: dict[tuple, dict[str, Any]] = {}
		self._views: dict[str, tuple[bool, str]] = {}
		self._intake: dict[str, bool] = {}

	def load(self, names: set[str]) -> None:
		missing = {name for name in names if name and name not in self._needs}
		if missing:
			for row in frappe.get_all("Departmental Need", filters={"name": ("in", sorted(missing))}, fields=NEED_FIELDS, limit_page_length=0):
				self._needs[row.name] = row

	def add(self, rows) -> None:
		for row in rows:
			self._needs.setdefault(row.name, row)

	def need(self, name: str):
		self.load({name})
		return self._needs.get(name)

	def titles(self, revisions: set[str]) -> None:
		missing = {name for name in revisions if name and name not in self._titles}
		if missing:
			for row in frappe.get_all("Departmental Need Revision", filters={"name": ("in", sorted(missing))}, fields=["name", "title"], limit_page_length=0):
				self._titles[row.name] = cstr(row.title).strip()

	def title(self, need, revision: str = "") -> str:
		"""The requirement's own title (on its Revision); the reference only when a Revision has none."""
		revision = revision or cstr(need.current_revision)
		self.titles({revision})
		return self._titles.get(revision) or cstr(need.need_reference)

	def update_state(self, need) -> str:
		"""Where an accepted Need's update stands: "submitted" (awaiting review), "returned" (the Head returned it; the author holds a
		Draft copy made from the returned revision, so the current revision is that Draft) or "" (no update, or the author's own Draft)."""
		revision = cstr(need.current_revision)
		if need.current_state != c.STATE_ACCEPTED or not revision or revision == cstr(need.current_accepted_revision):
			return ""
		row = frappe.db.get_value("Departmental Need Revision", revision, ["revision_status", "based_on_revision"], as_dict=True)
		if not row:
			return ""
		if row.revision_status == c.REVISION_SUBMITTED:
			return "submitted"
		based = cstr(frappe.db.get_value("Departmental Need Revision", row.based_on_revision, "revision_status")) if row.based_on_revision else ""
		return "returned" if row.revision_status == c.REVISION_DRAFT and based == c.REVISION_RETURNED else ""

	def view(self, need) -> tuple[bool, str]:
		"""The owner's one read predicate: (may read, profile)."""
		if need.name not in self._views:
			self._views[need.name] = can_view(need, self.user)
		return self._views[need.name]

	def intake_open(self, financial_year: str) -> bool:
		if financial_year not in self._intake:
			self._intake[financial_year] = needs_submission_state(financial_year)["state"] == INTAKE_OPEN
		return self._intake[financial_year]

	def step(self, need, codes: tuple[str, ...] = (), *, intake_open: bool | None = None) -> dict[str, Any]:
		"""The owner's `next_step` for the actor on this Need (read-only); `codes` are the page actions the actor has on it."""
		open_now = self.intake_open(need.financial_year) if intake_open is None else intake_open
		key = (need.name, codes, open_now)
		if key not in self._steps:
			self._steps[key] = need_guidance(need, principal=self.user, actions=[{"code": code} for code in codes], intake_open=open_now)["next_step"]
		return self._steps[key]

	def last_decision(self, need: str, actions: list[str]):
		return _last_decision(need, actions)


def _facts(user: str) -> _Facts:
	"""One set of facts per Home read, shared by every region (the owner's guidance runs once per Need and viewpoint)."""
	return home_support.memo("needs.facts", lambda: _Facts(user), user=user)


def _since(step: dict[str, Any]):
	at = (step.get("since") or {}).get("at")
	return get_datetime(at) if at else None


def _skipped(need, why: str) -> None:
	frappe.logger("kentender_home").info(f"Needs Home: {need.name} not listed, {why}")


# --------------------------------------------------------------------------
# My work and Waiting
# --------------------------------------------------------------------------


def _review_rows(facts: _Facts) -> list[dict[str, Any]]:
	"""The Head of User Department's open review tasks the actor may decide."""
	tasks = frappe.get_all(
		"Departmental Need Review Task", filters={"status": c.TASK_OPEN},
		fields=["name", "departmental_need", "need_revision", "task_type", "organisation_unit", "decision_token", "opened_at"], order_by="opened_at asc", limit_page_length=0,
	)
	facts.load({task.departmental_need for task in tasks})
	facts.titles({task.need_revision for task in tasks})
	entries: list[dict[str, Any]] = []
	for task in tasks:
		need = facts.need(task.departmental_need)
		if not need or cstr(need.owner) == facts.user:  # NDS-AC-042: the author never decides their own Need
			continue
		if not in_scope(facts.user, business_role=c.ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=task.organisation_unit):
			continue
		kind = REVIEW_KINDS.get(cstr(task.task_type))
		step = facts.step(need, (kind,)) if kind else {}
		if step.get("kind") != ns.KIND_YOUR_TURN or not cstr(step.get("headline")).strip():
			continue  # the owner's own answer for this person is not "your turn"
		route = ["departmental-needs", "review", task.name, *(["withdrawal"] if kind == "withdrawal" else [])]
		entries.append(he.make(
			region=he.MY_WORK, owner=OWNER, root=need.name, action_id=task.name, title=facts.title(need, cstr(task.need_revision)), reference=need.need_reference,
			action=step["headline"], destination={"route": route}, entered_at=task.opened_at,
			entered_verb="Received" if kind == "withdrawal" else "Submitted", source_revision=cstr(task.decision_token),
		))
	return entries


def _correction_rows(facts: _Facts, needs: list[Any]) -> list[dict[str, Any]]:
	"""The author's returned Needs (and Accepted Needs whose update was returned), worded and blocked by the owner's own answer."""
	entries: list[dict[str, Any]] = []
	for need in needs:
		returned = need.current_state == c.STATE_RETURNED
		if not (returned or facts.update_state(need) == "returned"):
			continue
		if facts.view(need)[1] != "owner":
			continue  # the page offers "Correct" only to an author who can still read it
		codes = ("edit",) if returned else ()
		step = facts.step(need, codes)
		if step.get("kind") not in ns.TURN_KINDS or not cstr(step.get("headline")).strip():
			continue
		blocked = step["kind"] == ns.KIND_BLOCKED
		# the action stays what the author does; the owner's blocked headline ("New submissions are closed") is the reason
		action = facts.step(need, codes, intake_open=True)["headline"] if blocked else step["headline"]
		decision = facts.last_decision(need.name, [c.ACTION_RETURN if returned else c.ACTION_RETURN_SUCCESSOR])
		if not decision:
			_skipped(need, "no return decision is recorded")
			continue
		entries.append(he.make(
			region=he.MY_WORK, owner=OWNER, root=need.name, action_id=f"{need.name}:correct", title=facts.title(need), reference=need.need_reference, action=action,
			destination={"route": ["departmental-needs", need.need_reference, "edit"]}, entered_at=decision.occurred_at, entered_verb="Received",
			blocked=blocked, reason=cstr(step["headline"]) if blocked else "",
		))
	return entries


def _waiting_rows(facts: _Facts, needs: list[Any]) -> list[dict[str, Any]]:
	"""What the author handed on and someone else holds. An answer with no recorded instant is not listed (and logged)."""
	entries: list[dict[str, Any]] = []
	for need in needs:
		if need.current_state not in (c.STATE_SUBMITTED, c.STATE_ACCEPTED) or not facts.view(need)[0]:
			continue
		step = facts.step(need)
		if step.get("kind") != ns.KIND_WAITING or not step.get("holder"):
			continue
		if step.get("stage") == STAGE_REVIEW:
			pass
		elif step.get("stage") == STAGE_ACCEPTED and _open_withdrawal(need.name):
			pass
		else:
			continue  # a draft update the author still holds, or Planning's position: not a hand-off
		since = _since(step)
		if not since:
			_skipped(need, "the wait has no recorded start")
			continue
		entries.append(he.make(
			region=he.WAITING, owner=OWNER, root=need.name, action_id=f"{need.name}:waiting", title=facts.title(need), reference=need.need_reference,
			action=step["headline"], destination={"route": ["departmental-needs", need.need_reference]}, holder=step["holder"], since=since,
		))
	return entries


def _own_needs(user: str) -> list[Any]:
	return frappe.get_all(
		"Departmental Need", filters={"owner": user, "current_state": ("in", [c.STATE_RETURNED, c.STATE_SUBMITTED, c.STATE_ACCEPTED])},
		fields=NEED_FIELDS, order_by="modified asc", limit_page_length=0,
	)


# --------------------------------------------------------------------------
# Records you oversee (derived from owner state; not an owner concept)
# --------------------------------------------------------------------------


def _oversight_needs(facts: _Facts) -> list[Any]:
	"""Needs in a state somebody has to move: awaiting review or correction, with a withdrawal request open, or an update
	submitted for review or returned."""
	needs = {row.name: row for row in frappe.get_all("Departmental Need", filters={"current_state": ("in", [c.STATE_SUBMITTED, c.STATE_RETURNED])}, fields=NEED_FIELDS, limit_page_length=0)}
	withdrawing = set(frappe.get_all("Need Withdrawal Request", filters={"status": ("in", sorted(c.OPEN_WITHDRAWAL_STATUSES))}, pluck="departmental_need", limit_page_length=0))
	for row in frappe.get_all("Departmental Need", filters={"current_state": c.STATE_ACCEPTED}, fields=NEED_FIELDS, limit_page_length=0):
		if row.name in withdrawing or (cstr(row.current_revision) != cstr(row.current_accepted_revision) and facts.update_state(row)):
			needs[row.name] = row
	return list(needs.values())


def _matter(facts: _Facts, need) -> str:
	"""Which of the owner's turns the Need is waiting on, in the owner's own precedence (withdrawal, update, then the Need)."""
	if need.current_state == c.STATE_SUBMITTED:
		return "review"
	if need.current_state == c.STATE_RETURNED:
		return "correct"
	if _open_withdrawal(need.name):
		return "withdrawal"
	return {"submitted": "review", "returned": "correct"}.get(facts.update_state(need), "")


def _oversight(facts: _Facts) -> list[dict[str, Any]]:
	candidates = _oversight_needs(facts)
	facts.add(candidates)
	tasks: dict[tuple[str, str], str] = {}
	for task in frappe.get_all("Departmental Need Review Task", filters={"status": c.TASK_OPEN}, fields=["name", "departmental_need", "task_type"], order_by="opened_at asc", limit_page_length=0):
		tasks.setdefault((task.departmental_need, REVIEW_KINDS.get(cstr(task.task_type), "")), task.name)
	entries: list[dict[str, Any]] = []
	for need in candidates:
		allowed, profile = facts.view(need)
		if not allowed or profile not in ("department", "oversight"):
			continue  # the author has the matter in My work and Waiting; a Planner or an outsider is not an overseer
		matter = _matter(facts, need)
		step = facts.step(need)
		if not matter or step.get("kind") != ns.KIND_WAITING or not step.get("holder") or not cstr(step.get("headline")).strip():
			continue  # the actor's own turn is their My work row; nothing else is a wait on someone
		since = _since(step)
		if not since and matter == "correct":
			decision = facts.last_decision(need.name, [c.ACTION_RETURN, c.ACTION_RETURN_SUCCESSOR])
			since = decision.occurred_at if decision else None
		if not since:
			_skipped(need, "the matter has no recorded start")
			continue
		entries.append(he.make(
			region=he.OVERSIGHT, owner=OWNER, root=need.name, action_id=f"{need.name}:correct" if matter == "correct" else tasks.get((need.name, matter)) or f"{need.name}:{matter}",
			title=facts.title(need), reference=need.need_reference, action=step["headline"], destination={"route": ["departmental-needs", need.need_reference]},
			holder=step["holder"], since=since, outstanding=True,
		))
	return entries


# --------------------------------------------------------------------------
# Recently completed actions
# --------------------------------------------------------------------------


def _awaiting(facts: _Facts, need, row) -> str:
	""""It is awaiting review by Peter Kimani." — only while the owner's answer for the actor is a wait that this very decision began
	(FU-HOME-24), held by the people the answer names."""
	step = facts.step(need)
	holder = step.get("holder") or {}
	names, role = list(holder.get("people") or []), cstr(holder.get("role"))
	if step.get("kind") != ns.KIND_WAITING or not names:
		return ""
	if row.action in AWAITING_REVIEW:
		phrase, stage = AWAITING_REVIEW[row.action]
		return home_time.awaiting(phrase, _people(names, role)) if step.get("stage") == stage and role == c.ROLE_HEAD_OF_USER_DEPARTMENT and _since(step) == get_datetime(row.occurred_at) else ""
	if row.action in AWAITING_CORRECTION and step.get("stage") == STAGE_PREPARATION and role == c.ROLE_DEPARTMENTAL_AUTHOR:
		latest = facts.last_decision(need.name, AWAITING_CORRECTION[row.action])
		return home_time.awaiting("correction", _people(names, role)) if latest and get_datetime(latest.occurred_at) == get_datetime(row.occurred_at) else ""
	return ""


def _completed(user: str) -> list[dict[str, Any]]:
	facts = _facts(user)
	at = home_time.now()
	cutoff = datetime.combine((at - timedelta(days=home_time.COMPLETED_DAYS)).date(), time.min)
	rows = frappe.get_all(
		"Departmental Need Decision", filters={"actor": user, "occurred_at": (">=", cutoff), "action": ("in", sorted(COMPLETED))},
		fields=["name", "departmental_need", "need_revision", "action", "occurred_at"], order_by="occurred_at desc", limit_page_length=0,
	)
	facts.load({row.departmental_need for row in rows})
	facts.titles({row.need_revision for row in rows})
	entries: list[dict[str, Any]] = []
	for row in rows:
		need = facts.need(row.departmental_need)
		if not need or not facts.view(need)[0]:
			continue
		label, did = COMPLETED[cstr(row.action)]
		entries.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=need.name, action_id=row.name, title=facts.title(need, cstr(row.need_revision)), reference=need.need_reference, action=label,
			destination={"route": ["departmental-needs", need.need_reference]}, completed_at=row.occurred_at,
			sentence=home_time.completed_sentence(did, row.occurred_at, follow=_awaiting(facts, need, row)),
		))
	return entries


# --------------------------------------------------------------------------
# the provider
# --------------------------------------------------------------------------


def _register(user: str) -> dict[str, Any]:
	"""One scan for one Home read: {"my_work", "waiting", "oversight"} (a list only where the actor's responsibilities give the region)."""
	facts = _facts(user)
	holds = _holds(user)
	out: dict[str, Any] = {"my_work": None, "waiting": None, "oversight": None}
	if holds["work"]:
		own = _own_needs(user)
		facts.add(own)
		out["my_work"] = (_review_rows(facts) if holds["hod"] else []) + _correction_rows(facts, own)
		out["waiting"] = _waiting_rows(facts, own)
	if holds["oversight"]:
		out["oversight"] = _oversight(facts)
	return out


def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	if region not in he.REGIONS:
		raise ValueError(f"unknown Home region {region!r}")
	if not user or user == "Guest" or region == he.COMING_UP:
		return None
	holds = _holds(user)
	if not (holds["oversight"] if region == he.OVERSIGHT else holds["work"]):
		return None
	if region == he.COMPLETED:
		return home_support.memo("needs.completed", lambda: _completed(user), user=user)
	return home_support.memo("needs.register", lambda: _register(user), user=user)[region]
