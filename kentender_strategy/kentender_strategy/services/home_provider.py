# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 §7 — the Strategy owner's feed to Home (owner key `strategy`).

Registered on the `kt_home_providers` hook; core never imports this app and this app imports
nothing from Procurement (Strategy is upstream of it). One function, `entries(*, user, region)`,
answers for one actor (never the session user) and only reads. Strategy has no earlier Home or
My Work provider: `strategy_ui_contracts._my_work_versions` reads the session user and is not
called here; the same questions are asked of the owner's own rules with the explicit `user`.

- **my_work** — a version awaiting approval that the actor may decide
  (`available_actions(version, user)` is not empty: Strategy Approver, not the submitter),
  worded "Review new plan" or "Review plan changes"; and a Draft the Strategy Approver returned,
  which the actor may correct and resubmit (`available_actions` holds "Submit for approval").
  The instant is the raw timestamp of the submission or return in the version's audit trail.
  A bare Draft has no hand-off instant, so it is not a row. The review row is blocked only where
  `strategy_readiness.get_version_approval_blockers` says the version cannot be approved yet,
  with the owner's own headline as the reason.
- **waiting** — the Strategy Author's own submitted version while a Strategy Approver holds it.
- **oversight** — a Home-side summary of owner state, not an existing Strategy concept: for an
  Auditor, the versions awaiting approval (since the submission, holder Strategy Approver). The
  Accounting Officer, the Head of Procurement Function and a Head of User Department read
  approved versions only, so for them nothing is outstanding and the region does not apply.
- **coming_up** — none: Strategy has no scheduled activation.
- **completed** — the actor's own submit, return and approve events of the last 30 days from
  the shared Audit Event trail.

Returns None where the region does not apply to the actor, [] where it applies and there is
nothing to show; a failed read raises.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services.authorization import PURPOSE_COMMAND, PURPOSE_READ, authorise_record, is_technical
from kentender_strategy.services.strategy_audit import list_events
from kentender_strategy.services.strategy_authorization import (
	APPROVED_STATUSES,
	ROLE_STRATEGY_APPROVER,
	STRATEGY_READ_ELIGIBLE_ROLES,
	read_scope,
)
from kentender_strategy.services.strategy_readiness import get_version_approval_blockers
from kentender_strategy.services.strategy_transitions import available_actions
from kentender_strategy.services.strategy_ui_contracts import approval_route, plan_route, version_route

OWNER = "strategy"
VERSION, PLAN = "Strategic Plan Version", "Strategic Plan"
SUBMITTED, DRAFT = "Submitted for approval", "Draft"
SUBMIT, RETURN, APPROVE = "Submit for approval", "Return", "Approve"
REVIEW, CORRECT = ":review", ":correct"

#: The owner's action wording, in one place (the plan title leads the row, so none of it carries the title).
REVIEW_NEW, REVIEW_CHANGES, CORRECT_ACTION = "Review new plan", "Review plan changes", "Correct and resubmit"
WAITING_REVIEW = "Waiting for {holder} to review the plan"

#: Recently completed actions: Audit Event action → (the action label, what "You …" says). Anything not here is not shown
#: ("Approve successor" is the system's own event on the superseded version, not the actor's).
COMPLETED: dict[str, tuple[str, str]] = {
	SUBMIT: ("Submitted plan version for approval", "submitted this plan version for approval"),
	RETURN: ("Returned plan version", "returned this plan version for correction"),
	APPROVE: ("Approved plan version", "approved this plan version"),
}


# --------------------------------------------------------------------------
# facts read once per Home read
# --------------------------------------------------------------------------


def _people(names: list[str], role: str) -> str:
	"""The holder as a display: up to two names, otherwise the responsibility (never an invented person)."""
	return " or ".join(names) if names and len(names) <= 2 else cstr(role)


def _someone(names: list[str], role: str) -> str:
	"""The holder as a sentence subject: "Amina Hassan", or "a Strategy Approver"."""
	if names and len(names) <= 2:
		return " or ".join(names)
	return f"{'an' if cstr(role)[:1] in 'AEIOU' else 'a'} {role}"


class _Facts:
	"""What one actor's Home read needs more than once: plans, audit trails and who holds the Approver responsibility."""

	def __init__(self, user: str):
		self.user = user
		self._plans: dict[str, Any] = {}
		self._events: dict[str, list[dict]] = {}
		self._holders: list[str] | None = None
		self.scope = read_scope(user)

	def plan(self, name: str):
		if name not in self._plans:
			self._plans[name] = frappe.db.get_value(PLAN, name, ["name", "plan_id", "title"], as_dict=True)
		return self._plans[name]

	def events(self, version: str) -> list[dict]:
		"""The version's audit trail, newest first."""
		if version not in self._events:
			self._events[version] = list_events(VERSION, version)
		return self._events[version]

	def last(self, version: str, action: str) -> dict | None:
		return next((event for event in self.events(version) if event.get("action") == action), None)

	def approver_names(self) -> list[str]:
		"""The people who hold Strategy Approver now, other than the actor (a holder the segregation rule removed is not their own wait)."""
		if self._holders is None:
			users = frappe.get_all("User Responsibility Assignment", filters={"business_role": ROLE_STRATEGY_APPROVER, "status": "Enabled"}, pluck="user", distinct=True)
			held = sorted(
				user for user in users
				if user != self.user and not is_technical(user)
				and authorise_record(user=user, business_role=ROLE_STRATEGY_APPROVER, organisation_unit="", purpose=PURPOSE_COMMAND).allowed
			)
			self._holders = [cstr(frappe.db.get_value("User", user, "full_name")) or user for user in held]
		return self._holders

	def readable(self, status: str) -> bool:
		"""The owner's read rule: everything for a full reader, approved versions only for the approved-only readers."""
		return self.scope == "full" or (self.scope == "approved" and status in APPROVED_STATUSES)


def _blocker(version) -> tuple[bool, str]:
	"""Blocked only where the owner says the version cannot be approved yet; its own headline is the reason."""
	answer = get_version_approval_blockers(version.name)
	if not answer["blocked"]:
		return False, ""
	future = answer.get("future_effective") or {}
	return True, cstr(future.get("headline")) or " ".join(cstr(failure["message"]) for failure in answer["failures"])


# --------------------------------------------------------------------------
# My work, Waiting, Records you oversee
# --------------------------------------------------------------------------


def _applies(user: str) -> bool:
	"""A Strategy responsibility that reads every version: Strategy Author, Strategy Approver or Auditor. The Accounting Officer,
	Head of Procurement Function and Head of User Department read approved versions only (OVS-CHG-001 §4.1)."""
	return home_support.memo(
		"strategy.applies",
		lambda: not is_technical(user) and any(authorise_record(user=user, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed for role in STRATEGY_READ_ELIGIBLE_ROLES),
		user=user,
	)


def _is_auditor(user: str) -> bool:
	return home_support.memo("strategy.auditor", lambda: authorise_record(user=user, business_role="Auditor", organisation_unit="", purpose=PURPOSE_READ).allowed, user=user)


def _register(user: str) -> dict[str, Any]:
	"""One scan of Strategy's open versions for one Home read: {"my_work", "waiting", "oversight"} (oversight None unless the actor is an Auditor)."""
	facts = _Facts(user)
	versions = frappe.get_all(
		VERSION, filters={"status": ("in", (SUBMITTED, DRAFT))},
		fields=["name", "plan_id", "plan_version_id", "version_number", "status", "return_reason"], order_by="modified asc", limit_page_length=0,
	)
	work: list[dict[str, Any]] = []
	waiting: list[dict[str, Any]] = []
	oversight: list[dict[str, Any]] | None = [] if _is_auditor(user) else None
	for version in versions:
		plan = facts.plan(version.plan_id)
		if not plan:
			continue
		if version.status == SUBMITTED:
			event = facts.last(version.name, SUBMIT)
			if not event or not event.get("timestamp"):
				frappe.logger("kentender.home").error("strategy version has no submission event | version=%s", version.name)
				continue
			since = event["timestamp"]
			if available_actions(version.name, user):
				blocked, reason = _blocker(version)
				work.append(he.make(
					region=he.MY_WORK, owner=OWNER, root=version.name, action_id=version.name + REVIEW, title=plan.title, reference=version.plan_version_id,
					action=REVIEW_NEW if int(version.version_number or 1) == 1 else REVIEW_CHANGES, destination={"route": approval_route(version.plan_version_id)},
					entered_at=since, entered_verb="Submitted", blocked=blocked, reason=reason,
				))
				continue
			names = facts.approver_names()
			line, holder = WAITING_REVIEW.format(holder=_someone(names, ROLE_STRATEGY_APPROVER)), _people(names, ROLE_STRATEGY_APPROVER)
			if cstr(event.get("performed_by")) == user:
				waiting.append(he.make(
					region=he.WAITING, owner=OWNER, root=version.name, action_id=version.name + REVIEW, title=plan.title, reference=version.plan_version_id, action=line,
					destination={"route": approval_route(version.plan_version_id)}, holder=holder, since=since,
				))
			elif oversight is not None and facts.readable(version.status):
				oversight.append(he.make(
					region=he.OVERSIGHT, owner=OWNER, root=version.name, action_id=version.name + REVIEW, title=plan.title, reference=version.plan_version_id, action=line,
					destination={"route": approval_route(version.plan_version_id)}, holder=holder, since=since, outstanding=True,
				))
		elif cstr(version.return_reason).strip() and "Submit for approval" in available_actions(version.name, user):
			event = facts.last(version.name, RETURN)
			if not event or not event.get("timestamp"):
				frappe.logger("kentender.home").error("returned strategy version has no return event | version=%s", version.name)
				continue
			work.append(he.make(
				region=he.MY_WORK, owner=OWNER, root=version.name, action_id=version.name + CORRECT, title=plan.title, reference=version.plan_version_id, action=CORRECT_ACTION,
				destination={"route": version_route(plan.plan_id, version.version_number, "structure")}, entered_at=event["timestamp"], entered_verb="Received",
			))
	return {"my_work": work, "waiting": waiting, "oversight": oversight}


# --------------------------------------------------------------------------
# Recently completed actions
# --------------------------------------------------------------------------


def _completed(user: str) -> list[dict[str, Any]]:
	facts = _Facts(user)
	at = home_time.now()
	cutoff = datetime.combine((at - timedelta(days=home_time.COMPLETED_DAYS)).date(), time.min)
	entries: list[dict[str, Any]] = []
	rows = frappe.get_all(
		"Audit Event",
		filters={"document_type": VERSION, "performed_by": user, "action": ("in", list(COMPLETED)), "timestamp": (">=", cutoff)},
		fields=["name", "action", "document_name", "timestamp"], order_by="timestamp desc", limit_page_length=0,
	)
	for row in rows:
		version = frappe.db.get_value(VERSION, row.document_name, ["name", "plan_id", "plan_version_id", "status"], as_dict=True)
		plan = facts.plan(version.plan_id) if version else None
		if not plan or not facts.readable(version.status):
			continue
		wording = COMPLETED[row.action]
		entries.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=version.name, action_id=row.name, title=plan.title, reference=version.plan_version_id, action=wording[0],
			destination={"route": plan_route(plan.plan_id)}, completed_at=row.timestamp, sentence=home_time.completed_sentence(wording[1], row.timestamp),
		))
	return entries


# --------------------------------------------------------------------------
# the provider
# --------------------------------------------------------------------------

def entries(*, user: str, region: str) -> list[dict[str, Any]] | None:
	if region not in he.REGIONS:
		raise ValueError(f"unknown Home region {region!r}")
	if not user or user == "Guest" or region == he.COMING_UP or not _applies(user):
		return None
	if region == he.COMPLETED:
		return home_support.memo("strategy.completed", lambda: _completed(user), user=user)
	return home_support.memo("strategy.register", lambda: _register(user), user=user)[region]
