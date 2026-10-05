# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""HOME-CHG-001 v0.6 §7 — the Budget & Funding owner's feed to Home (owner key `budget`).

Registered on the `kt_home_providers` hook; core never imports this app and this app imports
nothing from Procurement (Budget is upstream of it). One function, `entries(*, user, region)`,
answers for one actor (never the session user) and only reads.

- **my_work** — the two kinds of work `budget_my_work_provider` already publishes, with the
  owner's own eligibility called, not copied: a submitted version the actor may approve
  (`has_budget_version_capability(CAP_APPROVE)`, which also removes the actor's own
  submission) and each Open budget revision request the Budget Officer may answer
  (`open_requests_for_workspace`). Instants are the raw `submitted_at` / `requested_at`.
  Nothing Budget says blocks either row, so none is blocked.
- **waiting** — the Budget Officer's own submitted version while a Budget Approver holds it.
- **oversight** — a Home-side summary of owner state, not an existing Budget concept: for an
  actor with a Budget responsibility, the versions awaiting approval and the Open revision
  requests that are neither theirs to act on nor theirs to wait on, each confirmed with the
  owner's read check (`frappe.has_permission`). The Accounting Officer, the Head of
  Procurement Function and a Head of User Department read approved versions only, so for
  them nothing is outstanding and the region does not apply (None).
- **coming_up** — none: Budget has no deadline or window.
- **completed** — the actor's own `Budget Audit Event` rows of the last 30 days, on the
  owner's wording table below.

Returns None where the region does not apply to the actor, [] where it applies and there is
nothing to show; a failed read raises.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_budget.services import budget_audit_contracts as audit
from kentender_budget.services.budget_authorization import (
	BUDGET_READ_ROLES,
	CAP_APPROVE,
	ROLE_BUDGET_APPROVER,
	ROLE_BUDGET_OFFICER,
	has_budget_version_capability,
)
from kentender_budget.services.budget_revision_request_contracts import CLOSED_BUDGET_REASON, STATUS_OPEN, open_requests_for_workspace
from kentender_core.services import home_entries as he
from kentender_core.services import home_support, home_time
from kentender_core.services.authorization import PURPOSE_COMMAND, PURPOSE_READ, authorise_record, is_technical

OWNER = "budget"
PAGE = "budget-funding"
VERSION, BUDGET, REQUEST, LINE_VERSION = "Procurement Budget Version", "Procurement Budget", "Budget Revision Request", "Procurement Budget Line Version"
SUBMITTED = "Submitted for approval"

#: The owner's action wording, in one place (the budget title leads the row, so none of it carries the title).
APPROVE_ACTION = "Approve budget version"
REVISE_ACTION = "Revise {line} for the plan update"
WAITING_APPROVE = "Waiting for {holder} to approve the budget version"
WAITING_REVISE = "Waiting for {holder} to revise {line} for the plan update"

#: Recently completed actions: Budget Audit Event type → (the action label, what "You …" says). Anything not here is not shown
#: (funding events, creation and draft saves are not decisions; the system's and an integration's events are not the actor's).
COMPLETED: dict[str, tuple[str, str]] = {
	audit.EVENT_SUBMITTED: ("Submitted budget version for approval", "submitted this budget version for approval"),
	audit.EVENT_RETURNED: ("Returned budget version", "returned this budget version"),
	audit.EVENT_APPROVED: ("Approved budget version", "approved and activated this budget version"),
	audit.EVENT_REVISION_REQUEST_DECLINED: ("Declined budget revision request", "declined a budget revision request"),
	audit.EVENT_REVISION_REQUEST_WITHDRAWN: ("Withdrew budget revision request", "withdrew a budget revision request"),
	audit.EVENT_REVISION_REQUEST_REVISED: ("Answered budget revision request", "answered a budget revision request by approving this budget version"),
}


# --------------------------------------------------------------------------
# facts read once per Home read
# --------------------------------------------------------------------------


def _people(names: list[str], role: str) -> str:
	"""The holder as a display: up to two names, otherwise the responsibility (never an invented person)."""
	return " or ".join(names) if names and len(names) <= 2 else cstr(role)


def _someone(names: list[str], role: str) -> str:
	"""The holder as a sentence subject: "Amina Hassan", or "a Budget Approver"."""
	if names and len(names) <= 2:
		return " or ".join(names)
	return f"{'an' if cstr(role)[:1] in 'AEIOU' else 'a'} {role}"


class _Facts:
	"""What one actor's Home read needs more than once: Budget titles and who holds each responsibility."""

	def __init__(self, user: str):
		self.user = user
		self._budgets: dict[str, Any] = {}
		self._holders: dict[str, list[str]] = {}

	def budget(self, name: str):
		if name not in self._budgets:
			self._budgets[name] = frappe.db.get_value(BUDGET, name, ["name", "title", "fiscal_year", "generated_reference"], as_dict=True)
		return self._budgets[name]

	def holder_names(self, role: str) -> list[str]:
		"""The people who hold `role` now, other than the actor (a holder the segregation rule removed is not their own wait)."""
		if role not in self._holders:
			users = frappe.get_all("User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"}, pluck="user", distinct=True)
			held = sorted(
				user for user in users
				if user != self.user and not is_technical(user) and authorise_record(user=user, business_role=role, organisation_unit="", purpose=PURPOSE_COMMAND).allowed
			)
			self._holders[role] = [cstr(frappe.db.get_value("User", user, "full_name")) or user for user in held]
		return self._holders[role]

	def line_title(self, request) -> str:
		"""The line's title on the current budget version, as the owner's own request row words it."""
		active = frappe.db.get_value(VERSION, {"budget": request.budget, "status": "Active"}, "name")
		title = frappe.db.get_value(LINE_VERSION, {"budget_version": active, "budget_line": request.budget_line}, "title") if active else None
		return cstr(title) or cstr(request.budget_line)

	def submitted_at(self, version) -> Any:
		"""The hand-off instant: the version's own `submitted_at`, else the submission event's."""
		return version.submitted_at or frappe.db.get_value("Budget Audit Event", {"budget_version": version.name, "event_type": audit.EVENT_SUBMITTED}, "event_at", order_by="event_at asc")

	def can_read(self, doctype: str, name: str) -> bool:
		return bool(frappe.has_permission(doctype, "read", doc=name, user=self.user))


def _route_budget(budget) -> dict[str, Any]:
	return {"route": [PAGE, cstr(budget.generated_reference or budget.name)]}


def _route_review(version: str) -> dict[str, Any]:
	return {"route": [PAGE, "review", version]}


def _route_year(budget) -> dict[str, Any]:
	return {"route": [PAGE], "route_options": {"fiscal_year": cstr(budget.fiscal_year)}}


# --------------------------------------------------------------------------
# My work, Waiting, Records you oversee
# --------------------------------------------------------------------------


def _applies(user: str) -> bool:
	"""A Budget responsibility that reads submitted work: Budget Officer, Budget Approver, Finance Confirmation Officer or Auditor.
	The Accounting Officer, Head of Procurement Function and Head of User Department read approved versions only (OVS-CHG-001 §4.1)."""
	return home_support.memo(
		"budget.applies",
		lambda: not is_technical(user) and any(authorise_record(user=user, business_role=role, organisation_unit="", purpose=PURPOSE_READ).allowed for role in BUDGET_READ_ROLES),
		user=user,
	)


def _register(user: str) -> dict[str, Any]:
	"""One scan of Budget's open matters for one Home read: {"my_work", "waiting", "oversight"}."""
	facts = _Facts(user)
	versions = frappe.get_all(
		VERSION, filters={"status": SUBMITTED}, fields=["name", "generated_reference", "budget", "submitted_by", "submitted_at"], order_by="submitted_at asc, creation asc", limit_page_length=0,
	)
	requests = frappe.get_all(
		REQUEST, filters={"status": STATUS_OPEN}, fields=["name", "budget_revision_request_id", "budget", "budget_line", "requested_at"], order_by="requested_at asc", limit_page_length=0,
	)
	work: list[dict[str, Any]] = []
	waiting: list[dict[str, Any]] = []
	oversight: list[dict[str, Any]] = []
	held: set[str] = set()
	sent: set[str] = set()

	for version in versions:
		budget = facts.budget(version.budget)
		since = facts.submitted_at(version)
		if not budget or not since:
			frappe.logger("kentender.home").error("budget version has no submission instant | version=%s", version.name)
			continue
		if has_budget_version_capability(user, CAP_APPROVE, version.name):
			held.add(version.name)
			work.append(he.make(
				region=he.MY_WORK, owner=OWNER, root=version.name, action_id=version.name, title=budget.title, reference=version.generated_reference, action=APPROVE_ACTION,
				destination=_route_review(version.name), entered_at=since, entered_verb="Submitted",
			))
		elif cstr(version.submitted_by) == user:
			sent.add(version.name)
			names = facts.holder_names(ROLE_BUDGET_APPROVER)
			waiting.append(he.make(
				region=he.WAITING, owner=OWNER, root=version.name, action_id=version.name, title=budget.title, reference=version.generated_reference,
				action=WAITING_APPROVE.format(holder=_someone(names, ROLE_BUDGET_APPROVER)), destination=_route_review(version.name),
				holder=_people(names, ROLE_BUDGET_APPROVER), since=since,
			))

	# the Budget Officer's own answers, by the owner's eligibility
	by_id = {row.budget_revision_request_id: row for row in requests}
	for budget_name in sorted({row.budget for row in requests}):
		budget = facts.budget(budget_name)
		for answer in open_requests_for_workspace(budget_name, user):
			request = by_id.get(answer["budget_revision_request_id"])
			if not budget or not request or not request.requested_at:
				continue
			held.add(request.name)
			work.append(he.make(
				region=he.MY_WORK, owner=OWNER, root=request.name, action_id=request.name, title=budget.title, reference=request.budget_revision_request_id,
				action=REVISE_ACTION.format(line=answer["line_title"]), destination=_route_year(budget), entered_at=request.requested_at, entered_verb="Received",
			))

	# a summary of owner state for what is neither the actor's to act on nor theirs to wait on, each read-checked
	for version in versions:
		budget = facts.budget(version.budget)
		since = facts.submitted_at(version)
		if version.name in held or version.name in sent or not budget or not since or not facts.can_read(VERSION, version.name):
			continue
		names = facts.holder_names(ROLE_BUDGET_APPROVER)
		oversight.append(he.make(
			region=he.OVERSIGHT, owner=OWNER, root=version.name, action_id=version.name, title=budget.title, reference=version.generated_reference,
			action=WAITING_APPROVE.format(holder=_someone(names, ROLE_BUDGET_APPROVER)), destination=_route_review(version.name),
			holder=_people(names, ROLE_BUDGET_APPROVER), since=since, outstanding=True,
		))
	for request in requests:
		budget = facts.budget(request.budget)
		if request.name in held or not budget or not request.requested_at or not facts.can_read(REQUEST, request.name):
			continue
		names = facts.holder_names(ROLE_BUDGET_OFFICER)
		oversight.append(he.make(
			region=he.OVERSIGHT, owner=OWNER, root=request.name, action_id=request.name, title=budget.title, reference=request.budget_revision_request_id,
			action=WAITING_REVISE.format(holder=_someone(names, ROLE_BUDGET_OFFICER), line=facts.line_title(request)), destination=_route_year(budget),
			holder=_people(names, ROLE_BUDGET_OFFICER), since=request.requested_at, outstanding=True,
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
		"Budget Audit Event",
		filters={"actor": user, "actor_kind": "user", "event_type": ("in", list(COMPLETED)), "event_at": (">=", cutoff)},
		fields=["name", "event_type", "event_at", "budget", "budget_version", "reason"],
		order_by="event_at desc", limit_page_length=0,
	)
	for row in rows:
		wording = COMPLETED.get(cstr(row.event_type))
		budget = facts.budget(row.budget) if wording else None
		# closing a budget declines its open requests with the system's reason: the actor did not decide those
		if not budget or (row.event_type == audit.EVENT_REVISION_REQUEST_DECLINED and cstr(row.reason) == CLOSED_BUDGET_REASON):
			continue
		doctype, name = (VERSION, row.budget_version) if row.budget_version else (BUDGET, row.budget)
		if not facts.can_read(doctype, name):
			continue
		reference = frappe.db.get_value(VERSION, row.budget_version, "generated_reference") if row.budget_version else budget.generated_reference
		entries.append(he.make(
			region=he.COMPLETED, owner=OWNER, root=name, action_id=row.name, title=budget.title, reference=reference, action=wording[0],
			destination=_route_budget(budget), completed_at=row.event_at, sentence=home_time.completed_sentence(wording[1], row.event_at),
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
		return home_support.memo("budget.completed", lambda: _completed(user), user=user)
	return home_support.memo("budget.register", lambda: _register(user), user=user)[region]
