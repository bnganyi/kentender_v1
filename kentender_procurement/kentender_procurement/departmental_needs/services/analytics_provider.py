# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §4, §4A.2, §7.1 — the Departmental Needs owner's feed to Procurement Analytics (fact kind `needs`).

Registered on the `kt_analytics_providers` hook; core never imports this app. Two functions answer for one actor (never the
session user) and only read: `facts` never calls `workspace.get_workspace` (that persists the working-context preference), opens
no task and writes nothing. Each Need is classified once, by its current owner disposition.

One record per permitted Need root in Submitted, Returned, Accepted for planning or Not taken forward:

- **state / state_key** — the owner's disposition label and a stable key (`submitted`, `returned`, `accepted`, `not_taken_forward`).
- **accepted_at** — the FIRST acceptance of the root: the earliest `Departmental Need Decision` of action "Accept for planning"
  (`occurred_at`). "Accept successor" is an update to an accepted requirement, never a first acceptance. None where the Need was
  never accepted.
- **pending_successor** — an accepted baseline exists and the current revision is a different (successor) revision.
- **title** — the requirement's own title on the accepted revision where one exists (so an aggregate reader never reads a
  successor's Draft content), otherwise on the current revision; the reference when a revision carries none.

Audience (decision OD-2, FU-ANL-01): the module's existing readers keep their scope (`permissions.can_view`, the one read predicate
of every Needs read path). In addition the Head of Procurement Function, Accounting Officer, Auditor and technical readers
(Administrator, System Manager, Technical Operator) receive the site-wide aggregate of Submitted, Returned, Accepted for planning
and Not taken forward Needs. A Draft or Withdrawn Need contributes no record to anyone, so a Draft's contents are never disclosed
and a withdrawn requirement is not counted.

Returns an empty set from `applies` where Needs does not apply to the actor; a failed read raises.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import analytics_contract as ac
from kentender_core.services.authorization import PURPOSE_READ, authorise_record, permitted_ou_scopes
from kentender_core.services.home_viewer import is_technical_reader
from kentender_procurement.departmental_needs import constants as c
from kentender_procurement.departmental_needs.services.permissions import can_view

PAGE = "departmental-needs"
NEED_FIELDS = ["name", "need_reference", "owner", "organisation_unit", "financial_year", "current_state", "current_revision", "current_accepted_revision"]

#: The owner dispositions Analytics counts, each with its stable key. Draft and Withdrawn are not here: they contribute no record.
STATE_KEYS: dict[str, str] = {
	c.STATE_SUBMITTED: "submitted",
	c.STATE_RETURNED: "returned",
	c.STATE_ACCEPTED: "accepted",
	c.STATE_NOT_TAKEN_FORWARD: "not_taken_forward",
}
#: OD-2: the site-wide aggregate audience beyond the module's own readers (technical readers are added in `_aggregate_reader`).
AGGREGATE_ROLES = (c.ROLE_HEAD_OF_PROCUREMENT_FUNCTION, c.ROLE_ACCOUNTING_OFFICER, c.ROLE_AUDITOR)


def _site(user: str, role: str, at: datetime) -> bool:
	return authorise_record(user=user, business_role=role, organisation_unit="", at=at, purpose=PURPOSE_READ).allowed


def _aggregate_reader(user: str, at: datetime) -> bool:
	"""A technical reader, the Head of Procurement Function, the Accounting Officer or an Auditor: site-wide, aggregate."""
	return is_technical_reader(user, at) or any(_site(user, role, at) for role in AGGREGATE_ROLES)


def applies(*, user: str, at: datetime) -> set[str]:
	"""{`needs`} for anyone who holds a Needs read of any kind (a cheap role check, no Need is read); otherwise the empty set."""
	if not user or user == "Guest":
		return set()
	if _aggregate_reader(user, at) or _site(user, c.ROLE_PROCUREMENT_PLANNER, at):
		return {ac.NEEDS}
	for role in (c.ROLE_DEPARTMENTAL_AUTHOR, c.ROLE_HEAD_OF_USER_DEPARTMENT):
		if permitted_ou_scopes(user, role, at):
			return {ac.NEEDS}
	return set()


def _first_acceptances(needs: list[str]) -> dict[str, datetime]:
	"""need -> the instant of its earliest "Accept for planning" decision."""
	if not needs:
		return {}
	out: dict[str, datetime] = {}
	for row in frappe.get_all(
		"Departmental Need Decision", filters={"departmental_need": ("in", needs), "action": c.ACTION_ACCEPT},
		fields=["departmental_need", "occurred_at"], limit_page_length=0,
	):
		if not row.occurred_at:
			continue
		at = get_datetime(row.occurred_at)
		if row.departmental_need not in out or at < out[row.departmental_need]:
			out[row.departmental_need] = at
	return out


def _titles(revisions: set[str]) -> dict[str, str]:
	if not revisions:
		return {}
	return {
		row.name: cstr(row.title).strip()
		for row in frappe.get_all("Departmental Need Revision", filters={"name": ("in", sorted(revisions))}, fields=["name", "title"], limit_page_length=0)
	}


def _needs(user: str, at: datetime) -> list[Any]:
	"""The Need roots this actor may know, in a countable disposition."""
	rows = frappe.get_all(
		"Departmental Need", filters={"current_state": ("in", sorted(STATE_KEYS))}, fields=NEED_FIELDS, order_by="creation asc", limit_page_length=0,
	)
	if _aggregate_reader(user, at):
		return rows
	return [row for row in rows if can_view(row, user)[0]]


def facts(*, user: str, kind: str, at: datetime, **params: Any) -> dict[str, Any]:
	"""One record per permitted Need root (see the module docstring)."""
	if kind != ac.NEEDS:
		raise ValueError(f"Departmental Needs supplies no {kind!r} facts")
	if ac.NEEDS not in applies(user=user, at=at):
		return ac.facts_result([])
	needs = _needs(user, at)
	accepted = _first_acceptances([row.name for row in needs])
	revision_of = {row.name: cstr(row.current_accepted_revision) or cstr(row.current_revision) for row in needs}
	titles = _titles({revision for revision in revision_of.values() if revision})
	records = []
	for need in needs:
		baseline = cstr(need.current_accepted_revision)
		# Named and linked only where the Need's own read opens for this viewer (KT-ACCESS-REV-001 AR-08): the
		# Accounting Officer and the Head of Procurement Function read submitted and decided Needs, not Returned
		# ones; the aggregate still counts every one.
		readable = is_technical_reader(user, at) or can_view(need, user)[0]
		records.append(ac.record(
			ac.NEEDS, id=need.name, title=(titles.get(revision_of[need.name]) or cstr(need.need_reference)) if readable else cstr(need.need_reference),
			reference=cstr(need.need_reference),
			fiscal_year=cstr(need.financial_year), org_units=[cstr(need.organisation_unit)] if need.organisation_unit else [],
			route=[PAGE, cstr(need.need_reference)] if readable else [], state=cstr(need.current_state), state_key=STATE_KEYS[cstr(need.current_state)],
			accepted_at=accepted.get(need.name), pending_successor=bool(baseline) and cstr(need.current_revision) != baseline,
		))
	return ac.facts_result(records)
