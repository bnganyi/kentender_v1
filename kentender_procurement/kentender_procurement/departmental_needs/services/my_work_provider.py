"""Departmental Needs rows for the shared My Work queue.

The reviewer's open decisions (§4.4 review tasks) reach them through the
established My Work queue and notification mechanism, not through a module
sidebar entry (§10). The protected review-task record, its permissions and
the decision screens are unchanged — this module only *projects* the open
tasks into My Work via kentender_core's `kt_my_work_providers` hook, which is
the sanctioned direction (core collects, this app publishes; core never
imports this app).

Eligibility mirrors the workspace's row actions exactly (§12.2 via
`workspace._actions`): the caller holds an active Head of User Department
responsibility assignment (AUTH-ADR-001 v1.6) covering the task's exact
Organisation Unit, and is not the Need's own author (maker-checker, NDS-AC-042).

NDS-CHG-001 v1.15 §7.6 adds the author's side of each hand-off: a returned
Need is the author's assigned item ("Correct and resubmit …"), and a Need the
author passed on — submitted, its update submitted, or its withdrawal
requested — is the author's waiting-on item, holding whom it waits for and
since when from the Need's own next step (`guidance.need_guidance`).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_core.services.authorization import is_technical
from kentender_core.utils.display import display_datetime
from kentender_procurement.departmental_needs.constants import (
	ACTION_RETURN,
	ACTION_RETURN_SUCCESSOR,
	REVISION_RETURNED,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	STATE_ACCEPTED,
	STATE_RETURNED,
	STATE_SUBMITTED,
	TASK_OPEN,
	TASK_WITHDRAWAL,
)
from kentender_procurement.departmental_needs.services.permissions import in_scope


def _row(task: Any, need: Any) -> dict[str, Any]:
	withdrawal = task.task_type == TASK_WITHDRAWAL
	title = (
		cstr(frappe.db.get_value("Departmental Need Revision", task.need_revision, "title"))
		if task.need_revision
		else ""
	)
	route = ["departmental-needs", "review", task.name]
	if withdrawal:
		route.append("withdrawal")
	return {
		"task_id": task.name,
		"task_type": "needs.withdrawal" if withdrawal else "needs.review",
		"title": title or cstr(need.need_reference),
		"reference": cstr(need.need_reference),
		"module": "Departmental Needs",
		"stage": _("Withdrawal review") if withdrawal else _("Departmental review"),
		"financial_year": cstr(task.financial_year),
		"organisation_unit": cstr(task.organisation_unit or ""),
		"assignment": _(ROLE_HEAD_OF_USER_DEPARTMENT),
		"status": _("Assigned"),
		# shown as given: formatted like every other time on screen, never a
		# raw timestamp (the same fix Planning's rows had, 26 Sep 2026)
		"received_at": display_datetime(task.opened_at) if task.opened_at else "",
		"due_at": "",
		"action_label": _("Review withdrawal") if withdrawal else _("Review need"),
		"route": route,
		"route_options": {},
		"concurrency_token": cstr(task.decision_token),
		"can_claim": False,
		"can_open": True,
	}


def _title(revision: str, need: Any) -> str:
	title = cstr(frappe.db.get_value("Departmental Need Revision", revision, "title")) if revision else ""
	return title or cstr(need.need_reference)


def _handoff(need: Any, *, kind: str, title: str, stage: str, status: str, action_label: str, route: list[str],
		received_at: Any = "", holder: dict[str, Any] | None = None, since: dict[str, Any] | None = None) -> dict[str, Any]:
	row = {
		"task_id": f"{need.name}:{kind}",
		"task_type": f"needs.{kind}",
		"title": title,
		"reference": cstr(need.need_reference),
		"module": "Departmental Needs",
		"stage": stage,
		"financial_year": cstr(need.financial_year),
		"organisation_unit": cstr(need.organisation_unit or ""),
		"assignment": _(ROLE_DEPARTMENTAL_AUTHOR),
		"status": _(status),
		# a waiting row was "received" when it started waiting
		"received_at": display_datetime(received_at) if received_at else cstr((since or {}).get("display")),
		"due_at": "",
		"action_label": action_label,
		"route": route,
		"route_options": {},
		"concurrency_token": "",
		"can_claim": False,
		"can_open": status == "Assigned",
	}
	if holder:
		row["holder"] = holder
	if since:
		row["since"] = since
	return row


def _author_rows(user: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	"""§7.6 — the author's own hand-offs: ReturnNeed / ReturnSuccessor land
	as an assigned correction; SubmitNeed / SubmitSuccessor /
	RequestWithdrawal leave a waiting-on item until someone else acts."""
	from kentender_procurement.departmental_needs.services.guidance import (
		STAGE_ACCEPTED,
		STAGE_REVIEW,
		_open_withdrawal,
		need_guidance,
	)

	assigned: list[dict[str, Any]] = []
	waiting: list[dict[str, Any]] = []
	for need in frappe.get_all(
		"Departmental Need",
		filters={"owner": user, "current_state": ("in", [STATE_RETURNED, STATE_SUBMITTED, STATE_ACCEPTED])},
		fields=["name", "need_reference", "owner", "organisation_unit", "financial_year", "current_state",
			"current_revision", "current_accepted_revision", "modified"],
		order_by="modified asc",
		limit_page_length=0,
	):
		route = ["departmental-needs", cstr(need.need_reference)]
		title = _title(need.current_revision, need)
		if need.current_state == STATE_RETURNED:
			returned = frappe.db.get_value(
				"Departmental Need Decision", {"departmental_need": need.name, "action": ACTION_RETURN},
				["reason", "occurred_at"], order_by="occurred_at desc", as_dict=True,
			)
			assigned.append(_handoff(
				need, kind="correction", title=_("Correct and resubmit {0}").format(title),
				stage=cstr(returned.reason) if returned and returned.reason else _("Returned for correction"),
				status="Assigned", action_label=_("Correct need"), route=[*route, "edit"],
				received_at=returned.occurred_at if returned else need.modified,
			))
			continue
		if need.current_state == STATE_ACCEPTED and cstr(need.current_revision) != cstr(need.current_accepted_revision):
			status = cstr(frappe.db.get_value("Departmental Need Revision", need.current_revision, "revision_status"))
			if status == REVISION_RETURNED:
				returned = frappe.db.get_value(
					"Departmental Need Decision", {"departmental_need": need.name, "action": ACTION_RETURN_SUCCESSOR},
					["reason", "occurred_at"], order_by="occurred_at desc", as_dict=True,
				)
				assigned.append(_handoff(
					need, kind="correction", title=_("Correct and resubmit the update of {0}").format(title),
					stage=cstr(returned.reason) if returned and returned.reason else _("Returned for correction"),
					status="Assigned", action_label=_("Correct update"), route=[*route, "edit"],
					received_at=returned.occurred_at if returned else need.modified,
				))
				continue
		# The waiting item is the Need's own next step for its author, so the
		# row and the page name the same holder and the same instant.
		step = need_guidance(frappe.get_doc("Departmental Need", need.name), principal=user, actions=[], intake_open=True)["next_step"]
		if step.get("kind") != "waiting" or not step.get("holder"):
			continue
		if step.get("stage") == STAGE_REVIEW:
			label = _("Waiting for review of the proposed changes") if need.current_state == STATE_ACCEPTED else _("Waiting for Head of Department review")
		elif step.get("stage") == STAGE_ACCEPTED and _open_withdrawal(need.name):
			label = _("Waiting for a Planning change") if step["holder"].get("role") == ROLE_PROCUREMENT_PLANNER else _("Waiting for the withdrawal decision")
		else:
			# The author's own draft update passed nothing on, and a late
			# Need's position is the department's Planning item (PLN §7.7).
			continue
		waiting.append(_handoff(
			need, kind="waiting", title=label, stage=title, status="Waiting", action_label=_("View need"),
			route=route, holder=step.get("holder"), since=step.get("since"),
		))
	return assigned, waiting


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	"""`kt_my_work_providers` entry: the caller's open departmental decisions,
	and (v1.15 §7.6) the author's own corrections and waiting-on items.

	Role-assigned work has no claim step — any in-scope HoD may decide, and the
	task's decision token already serialises concurrent decisions — so every
	decision row lands in the "assigned" bucket.
	"""
	empty: dict[str, list[dict[str, Any]]] = {"assigned": [], "claimable": [], "waiting": []}
	if user in ("Guest", ""):
		return empty
	# §8/KT-STD-001 v1.5 §3A.6 — a technical reader (Administrator or System
	# Manager) decides nothing, so My Work must stay empty for them even
	# though `frappe.get_roles` projects every role onto Administrator and
	# would otherwise let the check below pass.
	if is_technical(user):
		return empty
	author_assigned, author_waiting = _author_rows(user)
	empty["assigned"] = author_assigned
	empty["waiting"] = author_waiting
	if ROLE_HEAD_OF_USER_DEPARTMENT not in frappe.get_roles(user):
		return empty
	tasks = frappe.get_all(
		"Departmental Need Review Task",
		filters={"status": TASK_OPEN},
		fields=[
			"name",
			"departmental_need",
			"need_revision",
			"task_type",
			"organisation_unit",
			"financial_year",
			"decision_token",
			"opened_at",
		],
		order_by="opened_at asc",
	)
	rows = []
	for task in tasks:
		if not in_scope(
			user,
			business_role=ROLE_HEAD_OF_USER_DEPARTMENT,
			organisation_unit=task.organisation_unit,
		):
			continue
		need = frappe.db.get_value(
			"Departmental Need",
			task.departmental_need,
			["name", "need_reference", "owner"],
			as_dict=True,
		)
		if not need or cstr(need.owner) == cstr(user):
			continue
		rows.append(_row(task, need))
	empty["assigned"] = rows + author_assigned
	return empty
