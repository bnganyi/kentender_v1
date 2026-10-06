# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Planning rows for the shared My Work queue (§10).

Planning has exactly one navigation entry; actionable decisions reach their
actors through the workspace, this My Work projection and notifications —
never a sidebar work-queue entry (PLN-AC-059). Core collects providers
through the `kt_my_work_providers` hook; core never imports this app.

Eligibility mirrors the decision commands exactly (read-offer parity, the
NDS-807/911 classes): a row appears only for an actor the command layer
would accept — the same resolver, the same §6.1 segregation check.
"""

from __future__ import annotations

import re

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr

from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_FINANCE_CONFIRMATION_OFFICER,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PROCUREMENT_PLANNER,
)


def _row(*, task, task_type: str, title: str, reference: str, stage: str, fiscal_year: str, organisation_unit: str, assignment: str, action_label: str, route: list[str]) -> dict[str, Any]:
	return {
		"task_id": task.name,
		"task_type": task_type,
		"title": title,
		"reference": reference,
		"module": "Procurement Planning",
		"stage": stage,
		"fiscal_year": cstr(fiscal_year),
		"organisation_unit": cstr(organisation_unit),
		"assignment": _(assignment),
		"status": _("Assigned"),
		"received_at": cstr(task.creation),
		"due_at": "",
		"action_label": action_label,
		"route": route,
		"route_options": {},
		"concurrency_token": cstr(task.task_token),
		"can_claim": False,
		"can_open": True,
	}


def _validation_rows(user: str) -> list[dict[str, Any]]:
	if not authz.has_site_role(ROLE_PROCUREMENT_PLANNER, user):
		return []
	rows = []
	for task in frappe.get_all(
		"Departmental Plan Validation Task",
		filters={"status": "Open"},
		fields=["name", "task_reference", "submission", "organisation_unit", "fiscal_year", "task_token", "creation"],
		order_by="creation asc",
		limit_page_length=0,
	):
		if authz.is_segregated(user, authz.ACTION_DPP_VALIDATE, submission=task.submission):
			continue
		department = cstr(frappe.db.get_value("Organisation Unit", task.organisation_unit, "unit_name") or task.organisation_unit)
		rows.append(
			_row(
				task=task, task_type="planning.dpp_validation",
				title=_("Validate {0} departmental plan").format(department), reference=cstr(task.task_reference),
				stage=_("Departmental plan validation"), fiscal_year=task.fiscal_year, organisation_unit=task.organisation_unit,
				assignment=ROLE_PROCUREMENT_PLANNER, action_label=_("Review departmental plan"),
				route=["procurement-planning", "dpp-review", task.name],
			)
		)
	return rows


def _plan_title(plan_version: str) -> tuple[str, str]:
	row = frappe.db.get_value("Annual Plan Version", plan_version, ["annual_plan", "version_reference"], as_dict=True)
	if not row:
		return "", ""
	plan = frappe.db.get_value("Annual Plan", row.annual_plan, ["title", "fiscal_year"], as_dict=True) or {}
	return cstr(plan.get("title")), cstr(plan.get("fiscal_year"))


def _finance_rows(user: str) -> list[dict[str, Any]]:
	if not authz.has_site_role(ROLE_FINANCE_CONFIRMATION_OFFICER, user):
		return []
	rows = []
	for task in frappe.get_all(
		"Plan Finance Task", filters={"status": "Open"},
		fields=["name", "task_reference", "plan_version", "task_token", "creation"], order_by="creation asc",
	):
		if authz.is_segregated(user, authz.ACTION_FINANCE_DECIDE, plan_version=task.plan_version):
			continue
		title, fy = _plan_title(task.plan_version)
		rows.append(
			_row(
				task=task, task_type="planning.finance", title=_("Confirm plan funding — {0}").format(title),
				reference=cstr(task.task_reference), stage=_("Plan funding confirmation"), fiscal_year=fy,
				organisation_unit="", assignment=ROLE_FINANCE_CONFIRMATION_OFFICER,
				action_label=_("Open Finance task"), route=["procurement-planning", "finance", task.name],
			)
		)
	return rows


def _governance_rows(user: str) -> list[dict[str, Any]]:
	rows = []
	for stage, role, action, label in (
		("Accounting Officer adoption", ROLE_ACCOUNTING_OFFICER, authz.ACTION_AO_DECIDE, _("Adopt Annual Procurement Plan — {0}")),
		("Statutory approval", ROLE_PLAN_STATUTORY_APPROVER, authz.ACTION_STATUTORY_DECIDE, _("Approve Annual Procurement Plan — {0}")),
	):
		if not authz.has_site_role(role, user):
			continue
		for task in frappe.get_all(
			"Plan Governance Task", filters={"status": "Open", "stage": stage},
			fields=["name", "task_reference", "plan_version", "task_token", "creation"], order_by="creation asc",
		):
			if authz.is_segregated(user, action, plan_version=task.plan_version):
				continue
			title, fy = _plan_title(task.plan_version)
			rows.append(
				_row(
					task=task, task_type="planning.governance", title=label.format(title),
					reference=cstr(task.task_reference), stage=_(stage), fiscal_year=fy, organisation_unit="",
					assignment=role, action_label=_("Open decision"), route=["procurement-planning", "review", task.name],
				)
			)
	return rows


def _correction_request_rows(user: str) -> list[dict[str, Any]]:
	"""REQ-CHG-001 v1.6 §7.4A step 3 / PLN-CHG-001 v1.18 §5.4.5 — every
	Open or In progress Plan Item Correction Request is a Procurement
	Planner task until a terminal disposition (Resolved / Closed without
	change) is recorded; no segregation check applies (the request names a
	Requisition-side actor, never a Planner)."""
	if not authz.has_site_role(ROLE_PROCUREMENT_PLANNER, user):
		return []
	rows = []
	for row in frappe.get_all(
		"Plan Item Correction Request",
		filters={"status": ("in", ("Open", "In progress"))},
		fields=["name", "plan_item_id", "requisition_reference", "record_version", "creation"],
		order_by="creation asc",
		limit_page_length=0,
	):
		rows.append(
			{
				"task_id": row.name,
				"task_type": "planning.plan_item_correction",
				"title": _("Review correction request — {0}").format(row.plan_item_id),
				"reference": cstr(row.requisition_reference),
				"module": "Procurement Planning",
				"stage": _("Plan Item correction request"),
				"fiscal_year": "",
				"organisation_unit": "",
				"assignment": _(ROLE_PROCUREMENT_PLANNER),
				"status": _("Assigned"),
				"received_at": cstr(row.creation),
				"due_at": "",
				"action_label": _("Review correction request"),
				"route": ["procurement-planning", "correction-request", row.name],
				"route_options": {},
				"concurrency_token": cstr(row.record_version),
				"can_claim": False,
				"can_open": True,
			}
		)
	return rows


def _update_required_rows(user: str) -> list[dict[str, Any]]:
	"""An accepted departmental plan missing Needs accepted after it — the
	department's own prompt to Create update (§5.1 "Accepted; change required";
	§5.1.2 a later Need is pending input to a subsequent update).

	Not a task record: a derived condition, shown to exactly the actors the
	plan page offers Create update to (`dpp_read.get_departmental_plan`'s own
	`can_create_update` + `coverage_gaps`), and gone as soon as the update
	exists. Found live 25 Sep 2026: a Need accepted after its plan was accepted
	looked stranded because the only prompt sat on a page nobody was sent to.
	"""
	# The department's own subtrees for its two plan roles — not
	# `workspace_units`, which widens to "every unit" for anyone who also
	# holds a site-wide role and would then drop their departmental prompt.
	units: set[str] = set()
	for role in (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT):
		scope = authz.permitted_ou_scopes(user, role)
		if scope:  # None (technical/site-wide) is never a department's prompt
			units |= scope
	if not units:
		return []
	from kentender_procurement.procurement_planning.services import needs_intake

	rows = []
	for root in frappe.get_all(
		"Departmental Plan",
		filters={"organisation_unit": ("in", sorted(units)), "current_state": "Accepted"},
		fields=["name", "dpp_reference", "organisation_unit", "fiscal_year", "current_state", "current_version", "current_accepted_version", "record_version", "modified"],
		order_by="modified asc",
		limit_page_length=0,
	):
		if not root.current_version or cstr(root.current_version) != cstr(root.current_accepted_version):
			continue
		if authz.dpp_read_profile(root.organisation_unit, user) not in ("author", "hod"):
			continue
		late = needs_intake.late_needs(root)
		if not late:
			continue
		department = cstr(frappe.db.get_value("Organisation Unit", root.organisation_unit, "unit_name") or root.organisation_unit)
		# Owner decision 26 Sep 2026 — name the need, not just a count.
		count = _("{0} not in plan").format(needs_intake.need_list(late))
		rows.append(
			{
				"task_id": f"{root.name}:update-required",
				"task_type": "planning.dpp_update_required",
				"title": _("Update {0} departmental plan").format(department),
				"reference": cstr(root.dpp_reference),
				"module": "Procurement Planning",
				"stage": count,
				"fiscal_year": cstr(root.fiscal_year),
				"organisation_unit": cstr(root.organisation_unit),
				"assignment": _("Departmental plan"),
				"status": _("Assigned"),
				"received_at": cstr(root.modified),
				"due_at": "",
				"action_label": _("Create update"),
				"route": ["departmental-procurement-plan", cstr(root.dpp_reference)],
				"route_options": {},
				"concurrency_token": cstr(root.record_version),
				"can_claim": False,
				"can_open": True,
			}
		)
	return rows


def _update_request_rows(user: str) -> list[dict[str, Any]]:
	"""Procurement asked this department to update its accepted departmental
	plan because a line of the plan update is over budget (owner decision
	26 Sep 2026). One row per Open request, for the department's own authors
	and Head of Department; it clears when the request is Answered (its next
	update accepted) or Withdrawn, never on view."""
	from kentender_procurement.procurement_planning.services import departmental_update
	from kentender_procurement.procurement_planning.services import next_step as plan_next_step
	from kentender_procurement.procurement_planning.services.guards import money

	units: set[str] = set()
	for role in (ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT):
		scope = authz.permitted_ou_scopes(user, role)
		if scope:
			units |= scope
	if not units:
		return []
	rows = []
	for request in frappe.get_all(
		departmental_update.DOCTYPE, filters={"organisation_unit": ("in", sorted(units)), "status": departmental_update.OPEN},
		fields=["name", "departmental_plan", "organisation_unit", "budget_line_title", "budget_line_reference", "over_amount", "requested_at"],
		order_by="requested_at asc", limit_page_length=0,
	):
		root = frappe.db.get_value("Departmental Plan", request.departmental_plan, ["dpp_reference", "fiscal_year", "record_version"], as_dict=True)
		if not root or authz.dpp_read_profile(request.organisation_unit, user) not in ("author", "hod"):
			continue
		since = plan_next_step._since(request.requested_at)
		rows.append({
			"task_id": request.name,
			"task_type": "planning.dpp_update_requested",
			"title": _("Update {0} departmental plan").format(departmental_update.unit_name(request.organisation_unit)),
			"reference": cstr(root.dpp_reference),
			"module": "Procurement Planning",
			"stage": _("Procurement asks: {0} is over budget by {1}").format(request.budget_line_title or request.budget_line_reference, money(request.over_amount)),
			"fiscal_year": cstr(root.fiscal_year),
			"financial_year": cstr(root.fiscal_year),
			"organisation_unit": cstr(request.organisation_unit),
			"assignment": _("Departmental plan"),
			"status": _("Assigned"),
			"received_at": since["display"] if since else "",
			"due_at": "",
			"action_label": _("Open departmental plan"),
			"route": ["departmental-procurement-plan", cstr(root.dpp_reference)],
			"route_options": {},
			"concurrency_token": cstr(root.record_version),
			"can_claim": False,
			"can_open": True,
		})
	return rows


# --------------------------------------------------------------------------
# PLN v1.27 §7.7 hand-off register — rows with no task record behind them,
# each derived from the record's own state so it appears with the event and
# clears only on the stated state change, never on view (KT-STD-001 v1.8
# §3B.4). Task-backed rows (Finance, governance, DPP review, correction
# requests) are the builders above.
# --------------------------------------------------------------------------

_OPEN_PLAN_STATES = (
	"Draft", "Awaiting Accounting Officer", "Awaiting statutory approval",
	"Approved — publication pending", "Publication failed", "Published — activation held",
	"Withdrawn for correction",
)


def _handoff_row(*, task_id: str, task_type: str, title: str, reference: str, stage: str, fiscal_year: str,
		organisation_unit: str = "", assignment: str, action_label: str, route: list[str], received_at: Any = "",
		status: str = "Assigned", holder: dict[str, Any] | None = None, since: dict[str, Any] | None = None) -> dict[str, Any]:
	row = {
		"task_id": task_id,
		"task_type": task_type,
		"title": title,
		"reference": reference,
		"module": "Procurement Planning",
		"stage": stage,
		"fiscal_year": cstr(fiscal_year),
		"organisation_unit": cstr(organisation_unit),
		"assignment": _(assignment),
		"status": _(status),
		# a waiting row was "received" when it started waiting
		"received_at": cstr(received_at) or cstr((since or {}).get("display")),
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


def _plan_handoff_rows(user: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	assigned: list[dict[str, Any]] = []
	waiting: list[dict[str, Any]] = []
	for bucket, row, _doc, _plan, _guidance in plan_handoff_items(user):
		(assigned if bucket == "assigned" else waiting).append(row)
	return assigned, waiting


def plan_handoff_items(user: str):
	"""Each plan hand-off row with what produced it — `(bucket, row, version,
	plan, guidance)` — so a caller that also needs the owner's answer (Home's
	blocked reason) reads the heavy guidance once, not twice."""
	from kentender_procurement.procurement_planning.services import next_step as plan_next_step
	from kentender_procurement.procurement_planning.services import plan_read

	roles = {role: authz.has_site_role(role, user) for role in plan_next_step.PLAN_PARTICIPANTS}
	if not any(roles.values()):
		return
	for version in frappe.get_all(
		"Annual Plan Version", filters={"version_status": ("in", _OPEN_PLAN_STATES)},
		fields=["name"], order_by="creation asc", limit_page_length=0,
	):
		doc = frappe.get_doc("Annual Plan Version", version.name)
		plan = frappe.get_doc("Annual Plan", doc.annual_plan)
		guidance = plan_read._guidance_for(doc, plan, user)
		step = guidance["next_step"]
		stage = step.get("stage", "")
		reference = f"{plan.plan_reference} · Version {doc.version_number}"
		route = ["annual-procurement-plan", plan.plan_reference]
		base = {"reference": reference, "fiscal_year": plan.fiscal_year, "route": route}
		turn = step["kind"] in ("your_turn", "your_turn_blocked")

		if turn:
			row = _assigned_for(doc, plan, step, roles, base)
			if row:
				yield "assigned", row, doc, plan, guidance
		elif step["kind"] == "waiting":
			title = _waiting_title(doc, stage, roles)
			if title and stage == "preparation" and step["headline"].endswith("to update its departmental plan"):
				title = _("Waiting for the departmental plan update")
			if title:
				yield "waiting", _handoff_row(
					task_id=f"{doc.name}:waiting:{stage}", task_type="planning.waiting", title=title,
					# the stage by name: the holder line already says who and since
					stage=dict(plan_next_step.plan_stages()).get(stage, step["headline"]),
					assignment=ROLE_PROCUREMENT_PLANNER if roles[ROLE_PROCUREMENT_PLANNER] else "",
					action_label=_("View plan"), status="Waiting", holder=step.get("holder"), since=step.get("since"), **base,
				), doc, plan, guidance


def _assigned_for(doc, plan, step, roles, base) -> dict[str, Any] | None:
	"""The register row for a turn that no task record carries."""
	status, stage = doc.version_status, step.get("stage", "")
	planner, hopf, ao = roles[ROLE_PROCUREMENT_PLANNER], roles.get("Head of Procurement Function"), roles[ROLE_ACCOUNTING_OFFICER]
	row = lambda kind, title, assignment, detail="": _handoff_row(  # noqa: E731
		task_id=f"{doc.name}:{kind}", task_type=f"planning.{kind}", title=title, stage=detail or step["headline"],
		assignment=assignment, action_label=_("Open plan"), received_at=doc.modified, **base,
	)
	if status == "Draft" and stage == "preparation" and planner:
		returned = _latest_budget_outcome(doc.name)
		if doc.funding_state == "Returned":
			return row("finance_return", _("Correct the plan returned by Finance"), ROLE_PROCUREMENT_PLANNER, _finance_return_reason(doc.name))
		if returned:
			# received when Budget answered, not when the Draft last changed
			return _handoff_row(
				task_id=f"{doc.name}:budget_outcome", task_type="planning.budget_outcome", title=_("Continue plan update"),
				stage=returned["text"], assignment=ROLE_PROCUREMENT_PLANNER, action_label=_("Open plan"),
				received_at=returned["at"] or doc.modified, **base,
			)
		if doc.correction_of_plan_version:
			return row("governance_return", _("Correct the returned plan"), ROLE_PROCUREMENT_PLANNER)
		if step["headline"] == "Add the accepted requirements to purchases":
			return row("add_requirements", _("Add accepted requirements to the annual plan"), ROLE_PROCUREMENT_PLANNER)
		return None
	if status == "Draft" and stage == "signature" and hopf and step["kind"] == "your_turn":
		return row("sign", _("Sign and submit the annual plan"), "Head of Procurement Function")
	if status in ("Approved — publication pending", "Publication failed") and ao:
		if step["headline"] == "Record the Treasury submission":
			return row("treasury", _("Record the Treasury submission"), ROLE_ACCOUNTING_OFFICER)
		if step["headline"] == "Request withdrawal for correction":
			return row("withdrawal_request", _("Request withdrawal for correction"), ROLE_ACCOUNTING_OFFICER)
	if step["headline"] == "Withdraw the plan for correction" and roles[ROLE_PLAN_STATUTORY_APPROVER]:
		return row("withdrawal_decision", _("Decide the withdrawal request"), ROLE_PLAN_STATUTORY_APPROVER)
	if status == "Withdrawn for correction" and planner:
		return row("continue_correction", _("Continue the correction"), ROLE_PROCUREMENT_PLANNER)
	if status == "Published — activation held" and planner:
		return row("corrected_plan", _("Prepare a corrected plan"), ROLE_PROCUREMENT_PLANNER)
	return None


def _waiting_title(doc, stage: str, roles) -> str:
	"""The sender's waiting-on item (§7.7): only the responsibility that
	passed the work on waits for it, never every reader."""
	planner, hopf, ao = roles[ROLE_PROCUREMENT_PLANNER], roles.get("Head of Procurement Function"), roles[ROLE_ACCOUNTING_OFFICER]
	if stage == "funding" and planner:
		return _("Waiting for Finance")
	if stage == "preparation" and planner:
		return _("Waiting for the budget revision")
	if stage == "signature" and planner:
		return _("Waiting for signature")
	if stage == "ao" and (planner or hopf):
		return _("Waiting for adoption")
	if stage == "statutory" and ao:
		return _("Waiting for approval")
	if stage == "publication" and ao:
		return _("Waiting on publication recovery")
	return ""


def _latest_budget_outcome(plan_version: str) -> dict[str, str] | None:
	"""A Revised or Declined budget revision outcome the Planner has not yet
	acted on: it clears once funding is requested or the update cancelled
	(the Draft leaves the preparation stage). `text` names it; `at` is when
	Budget answered, as the Nairobi display."""
	from kentender_procurement.procurement_planning.services import next_step as plan_next_step

	row = frappe.db.get_value(
		"Plan Budget Revision Request", {"plan_version": plan_version, "status": ("in", ("Revised", "Declined"))},
		["status", "outcome_reason", "outcome_at", "budget_line_title"], as_dict=True, order_by="outcome_at desc",
	)
	if not row or frappe.db.exists("Plan Budget Revision Request", {"plan_version": plan_version, "status": "Open"}):
		return None
	since = plan_next_step._since(row.outcome_at)
	at = since["display"] if since else ""
	if row.status == "Declined":
		text = _("Budget revision declined for {0}: {1}").format(row.budget_line_title, row.outcome_reason) if row.outcome_reason else _("Budget revision declined for {0}").format(row.budget_line_title)
		return {"text": text, "at": at}
	return {"text": _("Budget revised for {0}").format(row.budget_line_title), "at": at}


def _finance_return_reason(plan_version: str) -> str:
	tasks = frappe.get_all("Plan Finance Task", filters={"plan_version": plan_version}, pluck="name")
	reason = frappe.db.get_value("Plan Finance Decision", {"task": ("in", tasks or [""]), "decision": "Return to planner"}, "return_reason", order_by="decided_at desc")
	return cstr(reason)


def _dpp_handoff_rows(user: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	"""ReturnDepartmentalPlan → Head of Department and Author (with the
	comment); SubmitDepartmentalPlan / AcceptDepartmentalPlan → the Head of
	Department's waiting-on items."""
	from kentender_core.services import next_step as ns
	from kentender_procurement.procurement_planning.services import dpp_read
	from kentender_procurement.procurement_planning.services import next_step as plan_next_step
	from kentender_procurement.procurement_planning.services import plan_read
	from kentender_procurement.procurement_planning.services.planning_roles import ROLE_HEAD_OF_USER_DEPARTMENT

	assigned: list[dict[str, Any]] = []
	waiting: list[dict[str, Any]] = []
	units = set()
	for role in ("Departmental Author", ROLE_HEAD_OF_USER_DEPARTMENT):
		scope = authz.permitted_ou_scopes(user, role)
		if scope:
			units |= scope
	if not units:
		return assigned, waiting
	hod_units = authz.permitted_ou_scopes(user, ROLE_HEAD_OF_USER_DEPARTMENT) or set()
	for root in frappe.get_all(
		"Departmental Plan", filters={"organisation_unit": ("in", sorted(units))},
		fields=["name", "dpp_reference", "organisation_unit", "fiscal_year", "current_state", "current_version", "current_accepted_version"],
		limit_page_length=0,
	):
		department = cstr(frappe.db.get_value("Organisation Unit", root.organisation_unit, "unit_name") or root.organisation_unit)
		base = {"reference": cstr(root.dpp_reference), "fiscal_year": root.fiscal_year, "organisation_unit": root.organisation_unit, "route": ["departmental-procurement-plan", cstr(root.dpp_reference)]}
		version = frappe.db.get_value("Departmental Plan Version", root.current_version, ["name", "version_status", "returned_from_submission", "modified"], as_dict=True) if root.current_version else None
		if version and version.version_status == "Draft" and version.returned_from_submission:
			comment = _return_comment(version.returned_from_submission)
			assigned.append(_handoff_row(
				task_id=f"{root.name}:dpp_return", task_type="planning.dpp_return",
				title=_("Correct and resubmit {0}'s departmental plan").format(department), stage=comment or _("Returned by Procurement"),
				assignment=ROLE_HEAD_OF_USER_DEPARTMENT if root.organisation_unit in hod_units else "Departmental Author",
				action_label=_("Open departmental plan"), received_at=version.modified, **base,
			))
		if root.organisation_unit not in hod_units:
			continue
		if version and version.version_status == "Submitted":
			planner = ns.holder(ROLE_PROCUREMENT_PLANNER, [cstr(frappe.db.get_value("User", u, "full_name") or u) for u in authz.users_with_site_role(ROLE_PROCUREMENT_PLANNER)])
			submitted_at = frappe.db.get_value("Departmental Plan Submission", {"dpp_version": version.name}, "submitted_at")
			waiting.append(_handoff_row(
				task_id=f"{root.name}:waiting:review", task_type="planning.waiting", title=_("Waiting for Procurement review"),
				stage=_("{0}'s departmental plan").format(department), assignment=ROLE_HEAD_OF_USER_DEPARTMENT,
				action_label=_("View plan"), status="Waiting", holder=planner,
				since=ns.since(submitted_at, plan_read._eat(submitted_at)) if submitted_at else None, **base,
			))
		elif root.current_state == "Accepted" and _unallocated_for(root):
			planner = ns.holder(ROLE_PROCUREMENT_PLANNER, [cstr(frappe.db.get_value("User", u, "full_name") or u) for u in authz.users_with_site_role(ROLE_PROCUREMENT_PLANNER)])
			waiting.append(_handoff_row(
				task_id=f"{root.name}:waiting:planning", task_type="planning.waiting", title=_("Waiting for planning"),
				stage=_("{0}'s accepted requirements are not yet in the annual plan").format(department),
				assignment=ROLE_HEAD_OF_USER_DEPARTMENT, action_label=_("View plan"), status="Waiting", holder=planner, **base,
			))
	return assigned, waiting


def _return_comment(submission: str) -> str:
	task = frappe.db.get_value("Departmental Plan Validation Task", {"submission": submission}, "decision")
	issues = frappe.db.get_value("Departmental Plan Validation Decision", task, "issues") if task else None
	try:
		rows = frappe.parse_json(issues) if issues else []
	except Exception:
		rows = []
	for row in rows or []:
		text = cstr(row.get("correction_required") or row.get("correction") or row.get("problem"))
		if text:
			return text
	return ""


def _unallocated_for(root) -> bool:
	"""Any proceeding source of this department not yet in the current
	annual plan Draft — the "Waiting for planning" item clears when every one
	is allocated (or becomes a pending input to a later update, §5.4.3)."""
	from kentender_procurement.procurement_planning.services import plan_read

	plan = frappe.db.get_value("Annual Plan", {"fiscal_year": root.fiscal_year}, ["name", "open_successor_version", "active_version"], as_dict=True)
	version = (plan.open_successor_version or plan.active_version) if plan else None
	if not version:
		return True
	allocated = plan_read._allocated_dpp_entries(version)
	return any(
		row["dpp_entry"] not in allocated and row.get("organisation_unit") == root.organisation_unit
		for row in plan_read._accepted_entry_rows(root.fiscal_year)
	)


_RAW_INSTANT = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}")


def my_work_rows(*, user: str) -> dict[str, list[dict[str, Any]]]:
	"""`kt_my_work_providers` entry: the caller's open Planning decisions."""
	if not user or user == "Guest":
		return {"assigned": [], "claimable": [], "waiting": []}
	plan_assigned, plan_waiting = _plan_handoff_rows(user)
	dpp_assigned, dpp_waiting = _dpp_handoff_rows(user)
	buckets = {
		"assigned": (
			_validation_rows(user) + _finance_rows(user) + _governance_rows(user)
			+ _correction_request_rows(user) + _update_required_rows(user) + _update_request_rows(user)
			+ plan_assigned + dpp_assigned
		),
		"claimable": [],
		"waiting": plan_waiting + dpp_waiting,
	}
	# The My Work page shows the core row's `financial_year`; Planning's rows
	# named it `fiscal_year`, so every Planning item's year column was blank
	# (found in the browser 25 Sep 2026).
	# The page shows `received_at` as given: a stored instant is formatted
	# here like every other time on screen, never a raw timestamp (found in
	# the named-user pass 26 Sep 2026: "2026-09-26 01:19:03.296127").
	from kentender_core.utils.display import display_datetime

	for rows in buckets.values():
		for row in rows:
			row.setdefault("financial_year", row.get("fiscal_year", ""))
			received = row.get("received_at")
			raw = received and (not isinstance(received, str) or _RAW_INSTANT.match(received))
			if raw:
				row["received_at"] = display_datetime(received)
	return buckets
