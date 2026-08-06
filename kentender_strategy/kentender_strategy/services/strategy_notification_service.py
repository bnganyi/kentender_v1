# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""XMOD-STR-009 / REQ §17 — Strategy in-app Notification Log facade."""

from __future__ import annotations

from typing import Iterable

import frappe
from frappe import _

from kentender_core.services.notification_service import emit_notification_log
from kentender_strategy.services.strategy_permissions import (
	ROLE_MANAGER,
	ROLE_PERF_VERIFIER,
	ROLE_PLANNING,
	ROLE_REVIEWER,
)

EVENT_PLAN_SUBMITTED = "plan_submitted"
EVENT_PLAN_RETURNED = "plan_returned"
EVENT_PLAN_APPROVED = "plan_approved"
EVENT_PLAN_ACTIVATED = "plan_activated"
EVENT_PLAN_SUPERSEDED = "plan_superseded"

EVENT_PVO_SUBMITTED = "pvo_submitted"
EVENT_PVO_RETURNED = "pvo_returned"
EVENT_PVO_ACTIVATED = "pvo_activated"
EVENT_PVO_RETIRED = "pvo_retired"
EVENT_PVO_SUPERSEDED = "pvo_superseded"

EVENT_MEASUREMENT_SUBMITTED = "measurement_submitted"
EVENT_MEASUREMENT_RETURNED = "measurement_returned"
EVENT_MEASUREMENT_VERIFIED = "measurement_verified"
EVENT_MEASUREMENT_REJECTED = "measurement_rejected"

EVENT_CA_ASSIGNED = "ca_assigned"
EVENT_CA_SUBMITTED = "ca_submitted"
EVENT_CA_RETURNED = "ca_returned"
EVENT_CA_VERIFIED = "ca_verified"

_ROUTE_ALIGNMENT = "/app/strategy-alignment"

_SKIP_ACTOR_EVENTS = frozenset(
	{
		EVENT_PLAN_SUBMITTED,
		EVENT_PVO_SUBMITTED,
		EVENT_MEASUREMENT_SUBMITTED,
		EVENT_CA_SUBMITTED,
	}
)


def _entity_label(procuring_entity: str | None) -> str:
	pe = (procuring_entity or "").strip()
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
	return users


def _plan_code(plan_doc) -> str:
	return getattr(plan_doc, "plan_code", None) or plan_doc.name


def _plan_pe(plan_doc) -> str | None:
	return getattr(plan_doc, "procuring_entity", None)


def _recipients_for_event(event_type: str, *, context: dict) -> list[str]:
	pe = context.get("procuring_entity")
	submitted_by = (context.get("submitted_by") or "").strip()
	owner = (context.get("owner") or "").strip()

	if event_type in (EVENT_PLAN_SUBMITTED, EVENT_PVO_SUBMITTED):
		users = _filter_by_entity(_users_with_roles([ROLE_REVIEWER, ROLE_PLANNING]), pe)
	elif event_type == EVENT_PLAN_APPROVED:
		users = _filter_by_entity(_users_with_roles([ROLE_PLANNING, ROLE_MANAGER]), pe)
		if submitted_by:
			users.add(submitted_by)
	elif event_type in (EVENT_PLAN_ACTIVATED, EVENT_PLAN_SUPERSEDED, EVENT_PVO_ACTIVATED):
		users = {u for u in (submitted_by, owner) if u}
		if not users:
			users = _filter_by_entity(_users_with_roles([ROLE_MANAGER]), pe)
	elif event_type in (EVENT_PLAN_RETURNED, EVENT_PVO_RETURNED):
		users = {submitted_by} if submitted_by else _filter_by_entity(
			_users_with_roles([ROLE_MANAGER]), pe
		)
	elif event_type in (EVENT_PVO_RETIRED, EVENT_PVO_SUPERSEDED):
		users = _filter_by_entity(_users_with_roles([ROLE_MANAGER]), pe)
	elif event_type == EVENT_MEASUREMENT_SUBMITTED:
		users = _filter_by_entity(_users_with_roles([ROLE_PERF_VERIFIER]), pe)
	elif event_type in (
		EVENT_MEASUREMENT_RETURNED,
		EVENT_MEASUREMENT_VERIFIED,
		EVENT_MEASUREMENT_REJECTED,
	):
		users = {submitted_by} if submitted_by else set()
	elif event_type == EVENT_CA_ASSIGNED:
		users = {owner} if owner else ({submitted_by} if submitted_by else set())
	elif event_type == EVENT_CA_SUBMITTED:
		users = _filter_by_entity(_users_with_roles([ROLE_PERF_VERIFIER]), pe)
	elif event_type in (EVENT_CA_RETURNED, EVENT_CA_VERIFIED):
		users = {owner} if owner else set()
	else:
		users = set()

	actor = frappe.session.user
	if event_type in _SKIP_ACTOR_EVENTS and actor in users and len(users) > 1:
		users.discard(actor)

	return sorted(u for u in users if u and u != "Guest")


def _route_for_event(event_type: str, *, context: dict) -> str:
	plan_code = (context.get("plan_code") or "").strip()
	target_code = (context.get("target_code") or "").strip()
	pvo_code = (context.get("objective_code") or "").strip()

	if event_type in (
		EVENT_PLAN_SUBMITTED,
		EVENT_PLAN_RETURNED,
		EVENT_PLAN_APPROVED,
	):
		return f"/app/strategy-plan-review/{plan_code}" if plan_code else _ROUTE_ALIGNMENT
	if event_type in (EVENT_PLAN_ACTIVATED, EVENT_PLAN_SUPERSEDED):
		return f"/app/strategy-plan-overview/{plan_code}" if plan_code else _ROUTE_ALIGNMENT
	if event_type in (
		EVENT_PVO_SUBMITTED,
		EVENT_PVO_RETURNED,
		EVENT_PVO_ACTIVATED,
		EVENT_PVO_RETIRED,
		EVENT_PVO_SUPERSEDED,
	):
		if pvo_code:
			return f"/app/strategy-pvo-editor/{pvo_code}"
		return "/app/strategy-pvo-catalogue"
	if event_type == EVENT_MEASUREMENT_SUBMITTED:
		if plan_code and target_code:
			return f"/app/strategy-measurement-verify/{plan_code}/{target_code}"
		return _ROUTE_ALIGNMENT
	if event_type in (
		EVENT_MEASUREMENT_RETURNED,
		EVENT_MEASUREMENT_REJECTED,
		EVENT_MEASUREMENT_VERIFIED,
	):
		if plan_code and target_code:
			slug = (
				"strategy-measurement-verify"
				if event_type == EVENT_MEASUREMENT_VERIFIED
				else "strategy-measurement-submit"
			)
			return f"/app/{slug}/{plan_code}/{target_code}"
		return _ROUTE_ALIGNMENT
	if event_type in (
		EVENT_CA_ASSIGNED,
		EVENT_CA_SUBMITTED,
		EVENT_CA_RETURNED,
		EVENT_CA_VERIFIED,
	):
		return f"/app/strategy-corrective-actions/{plan_code}" if plan_code else _ROUTE_ALIGNMENT
	return _ROUTE_ALIGNMENT


def _subject_message(event_type: str, *, context: dict) -> tuple[str, str]:
	label = context.get("label") or context.get("plan_code") or context.get("document_name") or "—"
	mapping = {
		EVENT_PLAN_SUBMITTED: (
			_("Strategic plan {0} submitted for review").format(label),
			_("Plan {0} is ready for review.").format(label),
		),
		EVENT_PLAN_RETURNED: (
			_("Strategic plan {0} returned").format(label),
			_("Plan {0} was returned for correction.").format(label),
		),
		EVENT_PLAN_APPROVED: (
			_("Strategic plan {0} approved").format(label),
			_("Plan {0} is approved and awaiting activation.").format(label),
		),
		EVENT_PLAN_ACTIVATED: (
			_("Strategic plan {0} activated").format(label),
			_("Plan {0} is now Active.").format(label),
		),
		EVENT_PLAN_SUPERSEDED: (
			_("Strategic plan {0} superseded").format(label),
			_("Plan {0} was superseded by a new Active version.").format(label),
		),
		EVENT_PVO_SUBMITTED: (
			_("Public value objective {0} submitted").format(label),
			_("Objective {0} awaits review.").format(label),
		),
		EVENT_PVO_RETURNED: (
			_("Public value objective {0} returned").format(label),
			_("Objective {0} was returned for correction.").format(label),
		),
		EVENT_PVO_ACTIVATED: (
			_("Public value objective {0} activated").format(label),
			_("Objective {0} is now Active.").format(label),
		),
		EVENT_PVO_RETIRED: (
			_("Public value objective {0} retired").format(label),
			_("Objective {0} was retired.").format(label),
		),
		EVENT_PVO_SUPERSEDED: (
			_("Public value objective {0} superseded").format(label),
			_("Objective {0} was superseded.").format(label),
		),
		EVENT_MEASUREMENT_SUBMITTED: (
			_("Measurement {0} submitted").format(label),
			_("A performance measurement awaits verification.").format(label),
		),
		EVENT_MEASUREMENT_RETURNED: (
			_("Measurement {0} returned").format(label),
			_("A performance measurement was returned for correction.").format(label),
		),
		EVENT_MEASUREMENT_VERIFIED: (
			_("Measurement {0} verified").format(label),
			_("A performance measurement was verified.").format(label),
		),
		EVENT_MEASUREMENT_REJECTED: (
			_("Measurement {0} rejected").format(label),
			_("A performance measurement was rejected.").format(label),
		),
		EVENT_CA_ASSIGNED: (
			_("Corrective action assigned on {0}").format(label),
			_("A corrective action was opened for verified underperformance.").format(label),
		),
		EVENT_CA_SUBMITTED: (
			_("Corrective action submitted on {0}").format(label),
			_("A corrective action awaits verification.").format(label),
		),
		EVENT_CA_RETURNED: (
			_("Corrective action returned on {0}").format(label),
			_("A corrective action was returned to the owner.").format(label),
		),
		EVENT_CA_VERIFIED: (
			_("Corrective action verified on {0}").format(label),
			_("A corrective action was verified complete.").format(label),
		),
	}
	return mapping.get(
		event_type,
		(_("Strategy alert {0}").format(label), _("Strategy event: {0}").format(event_type)),
	)


def notify_strategy_users(
	event_type: str,
	*,
	document_type: str,
	document_name: str,
	procuring_entity: str | None = None,
	plan_code: str | None = None,
	target_code: str | None = None,
	objective_code: str | None = None,
	submitted_by: str | None = None,
	owner: str | None = None,
	label: str | None = None,
	correlation_suffix: str = "",
) -> list[str | None]:
	"""Emit Notification Log rows for a Strategy event. Never raises."""
	try:
		context = {
			"procuring_entity": procuring_entity,
			"plan_code": plan_code,
			"target_code": target_code,
			"objective_code": objective_code,
			"submitted_by": submitted_by,
			"owner": owner,
			"label": label or plan_code or objective_code or document_name,
			"document_name": document_name,
		}
		recipients = _recipients_for_event(event_type, context=context)
		if not recipients:
			return []
		subject, message = _subject_message(event_type, context=context)
		route = _route_for_event(event_type, context=context)
		entity = _entity_label(procuring_entity)
		token = correlation_suffix or str(
			frappe.db.get_value(document_type, document_name, "modified") or document_name
		)
		created: list[str | None] = []
		for user in recipients:
			key = f"kt-strategy:{event_type}:{document_name}:{token}:{user}"
			created.append(
				emit_notification_log(
					for_user=user,
					subject=subject,
					message=message,
					document_type=document_type,
					document_name=document_name,
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
			"notify_strategy_users failed | event=%s",
			event_type,
			exc_info=True,
		)
		return []


def notify_plan_transition(plan_doc, action: str) -> list[str | None]:
	action_map = {
		"Submit": EVENT_PLAN_SUBMITTED,
		"Resubmit": EVENT_PLAN_SUBMITTED,
		"Return for correction": EVENT_PLAN_RETURNED,
		"Approve": EVENT_PLAN_APPROVED,
		"Activate": EVENT_PLAN_ACTIVATED,
		"Supersede": EVENT_PLAN_SUPERSEDED,
	}
	event = action_map.get(action)
	if not event:
		return []
	return notify_strategy_users(
		event,
		document_type="Strategic Plan",
		document_name=plan_doc.name,
		procuring_entity=_plan_pe(plan_doc),
		plan_code=_plan_code(plan_doc),
		submitted_by=getattr(plan_doc, "submitted_by", None),
		label=_plan_code(plan_doc),
		correlation_suffix=f"{plan_doc.status}:{getattr(plan_doc, 'modified', '')}",
	)


def notify_pvo_transition(pvo_doc, action: str) -> list[str | None]:
	action_map = {
		"Submit": EVENT_PVO_SUBMITTED,
		"Return": EVENT_PVO_RETURNED,
		"Activate": EVENT_PVO_ACTIVATED,
		"Retire": EVENT_PVO_RETIRED,
		"Supersede": EVENT_PVO_SUPERSEDED,
	}
	event = action_map.get(action)
	if not event:
		return []
	code = getattr(pvo_doc, "objective_code", None) or pvo_doc.name
	return notify_strategy_users(
		event,
		document_type="Public Value Objective",
		document_name=pvo_doc.name,
		procuring_entity=getattr(pvo_doc, "procuring_entity", None),
		objective_code=code,
		submitted_by=getattr(pvo_doc, "submitted_by", None),
		label=code,
		correlation_suffix=f"{pvo_doc.status}:{getattr(pvo_doc, 'modified', '')}",
	)


def notify_measurement_transition(meas_doc, action: str) -> list[str | None]:
	action_map = {
		"Submit": EVENT_MEASUREMENT_SUBMITTED,
		"Resubmit": EVENT_MEASUREMENT_SUBMITTED,
		"Return": EVENT_MEASUREMENT_RETURNED,
		"Verify": EVENT_MEASUREMENT_VERIFIED,
		"Reject": EVENT_MEASUREMENT_REJECTED,
	}
	event = action_map.get(action)
	if not event:
		return []
	plan_code = (
		frappe.db.get_value("Strategic Plan", meas_doc.plan_version, "plan_code")
		if meas_doc.plan_version
		else None
	)
	target_code = (
		frappe.db.get_value("Performance Target", meas_doc.performance_target, "target_code")
		if meas_doc.performance_target
		else None
	)
	pe = (
		frappe.db.get_value("Strategic Plan", meas_doc.plan_version, "procuring_entity")
		if meas_doc.plan_version
		else None
	)
	label = getattr(meas_doc, "measurement_code", None) or meas_doc.name
	return notify_strategy_users(
		event,
		document_type="Performance Measurement",
		document_name=meas_doc.name,
		procuring_entity=pe,
		plan_code=plan_code,
		target_code=target_code,
		submitted_by=getattr(meas_doc, "submitted_by", None),
		label=label,
		correlation_suffix=f"{meas_doc.workflow_status}:{getattr(meas_doc, 'modified', '')}",
	)


def notify_ca_transition(ca_doc, action: str) -> list[str | None]:
	action_map = {
		"Submit completion": EVENT_CA_SUBMITTED,
		"Return": EVENT_CA_RETURNED,
		"Verify": EVENT_CA_VERIFIED,
	}
	event = action_map.get(action)
	if not event:
		return []
	plan_code = (
		frappe.db.get_value("Strategic Plan", ca_doc.plan_version, "plan_code")
		if ca_doc.plan_version
		else None
	)
	pe = (
		frappe.db.get_value("Strategic Plan", ca_doc.plan_version, "procuring_entity")
		if ca_doc.plan_version
		else None
	)
	return notify_strategy_users(
		event,
		document_type="Strategy Corrective Action",
		document_name=ca_doc.name,
		procuring_entity=pe,
		plan_code=plan_code,
		owner=getattr(ca_doc, "owner", None),
		submitted_by=getattr(ca_doc, "owner", None),
		label=plan_code or ca_doc.name,
		correlation_suffix=f"{ca_doc.status}:{getattr(ca_doc, 'modified', '')}",
	)


def notify_ca_assigned(ca_doc, *, assignee: str | None = None) -> list[str | None]:
	plan_code = (
		frappe.db.get_value("Strategic Plan", ca_doc.plan_version, "plan_code")
		if ca_doc.plan_version
		else None
	)
	pe = (
		frappe.db.get_value("Strategic Plan", ca_doc.plan_version, "procuring_entity")
		if ca_doc.plan_version
		else None
	)
	# Prefer explicit assignee: DocType field "owner" collides with Frappe standard owner.
	owner = (assignee or "").strip() or (getattr(ca_doc, "owner", None) or "").strip()
	return notify_strategy_users(
		EVENT_CA_ASSIGNED,
		document_type="Strategy Corrective Action",
		document_name=ca_doc.name,
		procuring_entity=pe,
		plan_code=plan_code,
		owner=owner,
		label=plan_code or ca_doc.name,
		correlation_suffix=f"assigned:{ca_doc.name}",
	)
