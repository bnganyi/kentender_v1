# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-SUP-001A/B — Budget in-app Notification Log facade."""

from __future__ import annotations

from typing import Iterable

import frappe
from frappe import _
from frappe.utils import flt

from kentender_budget.services.budget_permissions import (
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
)
from kentender_core.services.notification_service import emit_notification_log

EVENT_BUDGET_SUBMITTED = "budget_submitted"
EVENT_BUDGET_RETURNED = "budget_returned"
EVENT_BUDGET_REVIEWED = "budget_reviewed"
EVENT_BUDGET_ACTIVATED = "budget_activated"
EVENT_REVISION_SUBMITTED = "revision_submitted"
EVENT_REVISION_RETURNED = "revision_returned"
EVENT_REVISION_REJECTED = "revision_rejected"
EVENT_REVISION_APPLIED = "revision_applied"
EVENT_FUNDING_INSUFFICIENT = "funding_insufficient"

_ROUTE_PORTFOLIO = "/app/budget-funding"
_ROUTE_REVIEW = "/app/budget-review"
_ROUTE_REVISION_REVIEW = "/app/budget-revision-review"
_ROUTE_CHECK_RESERVE = "/app/budget-check-reserve"

# Events that notify reviewers/authority — skip the acting user to avoid self-spam.
_SKIP_ACTOR_EVENTS = frozenset(
	{
		EVENT_BUDGET_SUBMITTED,
		EVENT_REVISION_SUBMITTED,
		EVENT_BUDGET_REVIEWED,
		EVENT_FUNDING_INSUFFICIENT,
	}
)


def _entity_label(budget_doc) -> str:
	pe = getattr(budget_doc, "procuring_entity", None) or ""
	if not pe:
		return ""
	code = frappe.db.get_value("Procuring Entity", pe, "entity_code") or ""
	title = frappe.db.get_value("Procuring Entity", pe, "entity_name") or pe
	if code:
		return f"{title} ({code})"
	return str(title)


def _users_with_roles(roles: Iterable[str]) -> set[str]:
	role_list = [r for r in roles if r]
	if not role_list:
		return set()
	rows = frappe.get_all(
		"Has Role",
		filters={"role": ["in", role_list], "parenttype": "User"},
		pluck="parent",
	)
	users: set[str] = set()
	for u in rows:
		if not u or u == "Guest":
			continue
		if frappe.db.get_value("User", u, "enabled"):
			users.add(u)
	return users


def _filter_by_entity(users: set[str], procuring_entity: str | None) -> set[str]:
	"""Keep users with PE User Permission when any such permissions exist for the PE."""
	pe = (procuring_entity or "").strip()
	if not pe or not users:
		return users
	scoped = frappe.get_all(
		"User Permission",
		filters={"allow": "Procuring Entity", "for_value": pe, "user": ["in", list(users)]},
		pluck="user",
	)
	if scoped:
		return set(scoped)
	# No PE permissions among candidates — fall back to role holders (tests / open Desk).
	return users


def _recipients_for_event(
	event_type: str,
	budget_doc,
	revision_doc=None,
) -> list[str]:
	pe = getattr(budget_doc, "procuring_entity", None)
	submitted_by = ""
	budget_owner = (getattr(budget_doc, "budget_owner", None) or "").strip()
	if revision_doc is not None:
		submitted_by = (getattr(revision_doc, "submitted_by", None) or "").strip()
	else:
		submitted_by = (getattr(budget_doc, "submitted_by", None) or "").strip()

	if event_type in (EVENT_BUDGET_SUBMITTED, EVENT_REVISION_SUBMITTED):
		users = _filter_by_entity(
			_users_with_roles([ROLE_REVIEWER, ROLE_AUTHORITY]), pe
		)
	elif event_type == EVENT_BUDGET_REVIEWED:
		users = _filter_by_entity(_users_with_roles([ROLE_AUTHORITY]), pe)
		if submitted_by:
			users.add(submitted_by)
	elif event_type == EVENT_BUDGET_ACTIVATED:
		users = {u for u in (submitted_by, budget_owner) if u}
	elif event_type in (
		EVENT_BUDGET_RETURNED,
		EVENT_REVISION_RETURNED,
		EVENT_REVISION_REJECTED,
		EVENT_REVISION_APPLIED,
	):
		primary = submitted_by or budget_owner
		users = {primary} if primary else set()
	elif event_type == EVENT_FUNDING_INSUFFICIENT:
		users = _filter_by_entity(
			_users_with_roles([ROLE_OFFICER, ROLE_AUTHORITY]), pe
		)
	else:
		users = set()

	actor = frappe.session.user
	if event_type in _SKIP_ACTOR_EVENTS and actor in users and len(users) > 1:
		users.discard(actor)
	elif event_type in _SKIP_ACTOR_EVENTS and actor in users and len(users) == 1:
		# Keep sole recipient even if actor (e.g. only Authority is Administrator).
		pass

	return sorted(u for u in users if u and u != "Guest")


def _route_for_event(event_type: str) -> str:
	if event_type in (
		EVENT_BUDGET_SUBMITTED,
		EVENT_BUDGET_REVIEWED,
		EVENT_BUDGET_RETURNED,
	):
		return _ROUTE_REVIEW
	if event_type == EVENT_BUDGET_ACTIVATED:
		return _ROUTE_PORTFOLIO
	if event_type in (
		EVENT_REVISION_SUBMITTED,
		EVENT_REVISION_RETURNED,
		EVENT_REVISION_REJECTED,
		EVENT_REVISION_APPLIED,
	):
		return _ROUTE_REVISION_REVIEW
	if event_type == EVENT_FUNDING_INSUFFICIENT:
		return _ROUTE_CHECK_RESERVE
	return _ROUTE_PORTFOLIO


def _subject_message(
	event_type: str,
	budget_doc,
	revision_doc=None,
	extra_message: str = "",
) -> tuple[str, str]:
	code = getattr(budget_doc, "generated_reference", None) or budget_doc.name
	title = getattr(budget_doc, "title", None) or code
	rev_code = ""
	if revision_doc is not None:
		rev_code = (
			getattr(revision_doc, "generated_reference", None) or revision_doc.name
		)

	mapping = {
		EVENT_BUDGET_SUBMITTED: (
			_("Budget {0} submitted for review").format(code),
			_("Budget {0} ({1}) is ready for review.").format(code, title),
		),
		EVENT_BUDGET_RETURNED: (
			_("Budget {0} returned").format(code),
			_("Budget {0} was returned for correction.").format(code),
		),
		EVENT_BUDGET_REVIEWED: (
			_("Budget {0} ready for activation").format(code),
			_("Budget {0} has been marked reviewed and is ready for activation.").format(
				code
			),
		),
		EVENT_BUDGET_ACTIVATED: (
			_("Budget {0} activated").format(code),
			_("Budget {0} is now Active.").format(code),
		),
		EVENT_REVISION_SUBMITTED: (
			_("Revision {0} submitted").format(rev_code or code),
			_("Budget revision {0} for {1} awaits review.").format(
				rev_code or "—", code
			),
		),
		EVENT_REVISION_RETURNED: (
			_("Revision {0} returned").format(rev_code or code),
			_("Budget revision {0} was returned for correction.").format(
				rev_code or code
			),
		),
		EVENT_REVISION_REJECTED: (
			_("Revision {0} rejected").format(rev_code or code),
			_("Budget revision {0} was rejected.").format(rev_code or code),
		),
		EVENT_REVISION_APPLIED: (
			_("Revision {0} applied").format(rev_code or code),
			_("Budget revision {0} was applied to {1}.").format(
				rev_code or code, code
			),
		),
		EVENT_FUNDING_INSUFFICIENT: (
			_("Insufficient funding on {0}").format(code),
			_("A reservation request against {0} failed due to insufficient funding.").format(
				code
			),
		),
	}
	subject, message = mapping.get(
		event_type,
		(_("Budget alert {0}").format(code), _("Budget event: {0}").format(event_type)),
	)
	if extra_message:
		message = f"{message} {extra_message}".strip()
	return subject, message


def _transition_token(event_type: str, budget_doc, revision_doc=None, correlation_suffix: str = "") -> str:
	if correlation_suffix:
		return correlation_suffix
	if revision_doc is not None:
		ts = getattr(revision_doc, "submitted_at", None) or getattr(
			revision_doc, "modified", None
		)
		return f"{revision_doc.name}:{revision_doc.status}:{ts}"
	if event_type == EVENT_BUDGET_SUBMITTED:
		return str(getattr(budget_doc, "submitted_at", None) or budget_doc.modified)
	if event_type == EVENT_BUDGET_RETURNED:
		return f"returned:{getattr(budget_doc, 'modified', '')}"
	if event_type == EVENT_BUDGET_REVIEWED:
		return str(getattr(budget_doc, "reviewed_at", None) or budget_doc.modified)
	if event_type == EVENT_BUDGET_ACTIVATED:
		return str(getattr(budget_doc, "activated_at", None) or budget_doc.modified)
	return str(getattr(budget_doc, "modified", "") or budget_doc.name)


def notify_budget_users(
	event_type: str,
	*,
	budget_doc,
	revision_doc=None,
	extra_message: str = "",
	correlation_suffix: str = "",
) -> list[str | None]:
	"""Emit Notification Log rows for an event. Never raises."""
	try:
		recipients = _recipients_for_event(event_type, budget_doc, revision_doc)
		if not recipients:
			return []
		subject, message = _subject_message(
			event_type, budget_doc, revision_doc, extra_message
		)
		route = _route_for_event(event_type)
		entity = _entity_label(budget_doc)
		token = _transition_token(
			event_type, budget_doc, revision_doc, correlation_suffix
		)
		doc_type = "Budget Revision" if revision_doc is not None else "Budget"
		doc_name = (
			revision_doc.name if revision_doc is not None else budget_doc.name
		)
		created: list[str | None] = []
		for user in recipients:
			key = f"kt-budget:{event_type}:{doc_name}:{token}:{user}"
			created.append(
				emit_notification_log(
					for_user=user,
					subject=subject,
					message=message,
					document_type=doc_type,
					document_name=doc_name,
					event_type=event_type,
					entity_scope=entity,
					route=route,
					correlation_key=key,
					from_user=frappe.session.user,
				)
			)
		return created
	except Exception:
		frappe.logger("kentender.notification").error(
			"notify_budget_users failed | event=%s",
			event_type,
			exc_info=True,
		)
		return []


def notify_funding_insufficient(
	*,
	budget_doc,
	budget_line_code: str,
	demand_code: str,
	requested_amount: float,
	shortfall_display: str = "",
) -> list[str | None]:
	"""BUD-SUP-001B — notify before reserve_funding throws."""
	suffix = (
		f"{demand_code or ''}|{budget_line_code or ''}|"
		f"{flt(requested_amount):.2f}"
	)
	extra = ""
	if shortfall_display:
		extra = _("Shortfall: {0}.").format(shortfall_display)
	return notify_budget_users(
		EVENT_FUNDING_INSUFFICIENT,
		budget_doc=budget_doc,
		extra_message=extra,
		correlation_suffix=suffix,
	)
