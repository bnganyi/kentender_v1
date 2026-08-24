# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget readiness / review / activation — BUD-UI-11 / BUD-FR-050–055 / AC-002 / AC-018."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, format_datetime, now_datetime

from kentender_budget.services.budget_contracts import _resolve_budget, resolve_scoped_entity
from kentender_budget.services.budget_authorization import (
	CAP_BUDGET_APPROVE,
	CAP_BUDGET_REVIEW,
	CAP_BUDGET_RETURN,
	CAP_BUDGET_SUBMIT,
	CAP_BUDGET_VIEW,
	authorized_budget_task,
	can_budget,
	complete_budget_task,
	create_budget_task,
	require_budget_capability,
	require_budget_task,
)
from kentender_budget.services.budget_permissions import (
	ROLE_AUDITOR,
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_VIEWER,
	can_register_budget,
	visible_statuses_for_user,
	can_review_budget,
	require_any_role,
	user_roles,
)

_READ_ROLES = (ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_VIEWER, ROLE_AUDITOR)

_STATUS_CHIP = {
	"Draft": "Draft State",
	"Returned": "Returned",
	"Submitted": "Under review",
	"Active": "Active",
	"Closed": "Closed",
	"Cancelled": "Cancelled",
}


def _as_dict(payload: dict | str | None) -> dict[str, Any]:
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return payload or {}


def _issue(
	code: str,
	message: str,
	*,
	action_label: str,
	action_route: str,
	group: str,
) -> dict[str, Any]:
	return {
		"code": code,
		"message": message,
		"action_label": action_label,
		"action_route": action_route,
		"group": group,
	}


def _evaluate_readiness(doc) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	"""Return (groups, flat blockers) from live Budget + Lines."""
	code = doc.generated_reference
	overview_route = f"budget-overview/{code}"
	lines_route = f"budget-lines/{code}"

	source_checks: list[tuple[bool, dict[str, Any] | None]] = []
	# (ok, issue_or_None)
	source_items = [
		(
			bool((doc.authoritative_reference or "").strip()),
			_issue(
				"source.authoritative_reference",
				_("Authoritative approval reference missing"),
				action_label=_("Add evidence"),
				action_route=overview_route,
				group="source",
			),
		),
		(
			bool(doc.approval_date),
			_issue(
				"source.approval_date",
				_("Approval date missing"),
				action_label=_("Add evidence"),
				action_route=overview_route,
				group="source",
			),
		),
		(
			bool((doc.approval_evidence or "").strip()),
			_issue(
				"source.approval_evidence",
				_("External approval evidence missing"),
				action_label=_("Add evidence"),
				action_route=overview_route,
				group="source",
			),
		),
		(
			bool((doc.fiscal_period or "").strip()),
			_issue(
				"source.fiscal_period",
				_("Fiscal period is invalid or missing"),
				action_label=_("Open overview"),
				action_route=overview_route,
				group="source",
			),
		),
		(
			bool((doc.currency or "").strip()),
			_issue(
				"source.currency",
				_("Currency is invalid or missing"),
				action_label=_("Open overview"),
				action_route=overview_route,
				group="source",
			),
		),
	]
	source_checks = source_items

	lines = frappe.get_all(
		"Budget Line",
		filters={"budget": doc.name, "is_active": 1},
		fields=[
			"name",
			"generated_reference",
			"organisational_owner",
			"classification",
			"funding_source_type",
			"funding_source_name",
			"approved_amount",
			"primary_target_code",
		],
		order_by="order_index asc, creation asc",
	)

	line_issues: list[dict[str, Any]] = []
	line_complete = 0
	line_total = 0

	# Presence of lines
	line_total += 1
	if lines:
		line_complete += 1
	else:
		line_issues.append(
			_issue(
				"lines.empty",
				_("No Budget Line"),
				action_label=_("Review budget line"),
				action_route=lines_route,
				group="lines",
			)
		)

	line_sum = 0.0
	missing_primary = 0
	for ln in lines:
		line_sum += flt(ln.approved_amount)
		checks = [
			bool((ln.organisational_owner or "").strip()),
			bool((ln.classification or "").strip()),
			bool((ln.funding_source_type or "").strip())
			and bool((ln.funding_source_name or "").strip()),
			flt(ln.approved_amount) > 0,
			bool((ln.primary_target_code or "").strip()),
		]
		line_total += len(checks)
		line_complete += sum(1 for c in checks if c)
		if not checks[0]:
			line_issues.append(
				_issue(
					f"lines.owner.{ln.generated_reference}",
					_("Line owner missing on {0}").format(ln.generated_reference),
					action_label=_("Review budget line"),
					action_route=lines_route,
					group="lines",
				)
			)
		if not checks[1]:
			line_issues.append(
				_issue(
					f"lines.classification.{ln.generated_reference}",
					_("Classification missing on {0}").format(ln.generated_reference),
					action_label=_("Review budget line"),
					action_route=lines_route,
					group="lines",
				)
			)
		if not checks[2]:
			line_issues.append(
				_issue(
					f"lines.funding.{ln.generated_reference}",
					_("Funding source incomplete on {0}").format(ln.generated_reference),
					action_label=_("Review budget line"),
					action_route=lines_route,
					group="lines",
				)
			)
		if not checks[3]:
			line_issues.append(
				_issue(
					f"lines.amount.{ln.generated_reference}",
					_("Non-positive approved amount on {0}").format(ln.generated_reference),
					action_label=_("Review budget line"),
					action_route=lines_route,
					group="lines",
				)
			)
		if not checks[4]:
			missing_primary += 1

	if missing_primary:
		line_issues.append(
			_issue(
				"lines.primary_target",
				_("Primary strategic target missing on {0} line").format(missing_primary)
				if missing_primary == 1
				else _("Primary strategic target missing on {0} lines").format(missing_primary),
				action_label=_("Review budget line"),
				action_route=lines_route,
				group="lines",
			)
		)

	ext = flt(doc.external_approved_total)
	line_total += 1
	if ext > 0 and lines and abs(ext - line_sum) >= 0.01:
		line_issues.append(
			_issue(
				"lines.external_total",
				_("Line totals do not match the external approved total"),
				action_label=_("Review budget line"),
				action_route=lines_route,
				group="lines",
			)
		)
	else:
		line_complete += 1

	# Strategy
	strategy_issues: list[dict[str, Any]] = []
	strategy_complete = 0
	strategy_total = 0
	for ln_name in [r.name for r in lines]:
		line_doc = frappe.get_doc("Budget Line", ln_name)
		for st in line_doc.get("supporting_targets") or []:
			strategy_total += 1
			if (st.target_code or "").strip() and not (st.reason or "").strip():
				strategy_issues.append(
					_issue(
						f"strategy.supporting.{line_doc.generated_reference}",
						_("Supporting Strategy target without a reason on {0}").format(
							line_doc.generated_reference
						),
						action_label=_("Review budget line"),
						action_route=lines_route,
						group="strategy",
					)
				)
			else:
				strategy_complete += 1

	if strategy_total == 0:
		# No strategy rows to evaluate — treat as complete empty-ok.
		strategy_total = 1
		strategy_complete = 1

	# Governance
	gov_items = [
		(
			bool((doc.budget_owner or "").strip()),
			_issue(
				"governance.owner",
				_("Budget owner is required"),
				action_label=_("Open overview"),
				action_route=overview_route,
				group="governance",
			),
		),
		(
			bool(doc.procuring_entity),
			_issue(
				"governance.entity",
				_("Procuring entity is required"),
				action_label=_("Open overview"),
				action_route=overview_route,
				group="governance",
			),
		),
		(
			doc.status not in ("Cancelled",),
			_issue(
				"governance.status",
				_("Budget is cancelled and cannot proceed"),
				action_label=_("Open overview"),
				action_route=overview_route,
				group="governance",
			),
		),
	]

	def _group(
		key: str,
		title: str,
		items: list[tuple[bool, dict[str, Any] | None]] | None = None,
		*,
		complete: int | None = None,
		total: int | None = None,
		issues: list[dict[str, Any]] | None = None,
	) -> dict[str, Any]:
		if items is not None:
			total = len(items)
			complete = sum(1 for ok, _ in items if ok)
			issues = [iss for ok, iss in items if not ok and iss]
		issues = issues or []
		return {
			"key": key,
			"title": title,
			"complete_count": int(complete or 0),
			"total_count": int(total or 0),
			"issues": issues,
			"status": "issue" if issues else "ok",
			"summary": issues[0]["message"]
			if issues
			else _("All {0} requirements met.").format(title.lower()),
		}

	groups = [
		_group("source", _("Source"), source_checks),
		_group(
			"lines",
			_("Budget Lines"),
			complete=line_complete,
			total=line_total,
			issues=line_issues,
		),
		_group(
			"strategy",
			_("Strategy Alignment"),
			complete=strategy_complete,
			total=strategy_total,
			issues=strategy_issues,
		),
		_group("governance", _("Governance"), gov_items),
	]

	blockers: list[dict[str, Any]] = []
	for g in groups:
		for iss in g["issues"]:
			blockers.append(iss)
	return groups, blockers


def _capabilities(doc, blockers: list[dict[str, Any]], task_id: str = "") -> dict[str, Any]:
	is_officer = can_budget(CAP_BUDGET_SUBMIT, doc)
	task, commands = authorized_budget_task(
		actor=frappe.session.user,
		subject_type="Budget",
		subject_id=doc.name,
		capabilities=(CAP_BUDGET_REVIEW, CAP_BUDGET_RETURN, CAP_BUDGET_APPROVE),
		task_id=task_id,
	)
	is_reviewer = CAP_BUDGET_REVIEW in commands or CAP_BUDGET_RETURN in commands
	is_authority = CAP_BUDGET_APPROVE in commands
	status = doc.status
	has_blockers = bool(blockers)
	reviewed = bool((doc.reviewed_by or "").strip())
	submitter = (doc.submitted_by or "").strip()
	actor = frappe.session.user

	can_submit = (
		status in ("Draft", "Returned")
		and is_officer
		and not has_blockers
	)
	can_return = status == "Submitted" and is_reviewer
	can_mark = status == "Submitted" and is_reviewer and not reviewed
	can_activate = (
		status == "Submitted"
		and is_authority
		and reviewed
		and not has_blockers
		and (not submitter or submitter != actor)
	)
	activate_lock = ""
	if status == "Submitted" and is_authority:
		if has_blockers:
			activate_lock = _("Resolve readiness blockers before activation")
		elif not reviewed:
			activate_lock = _("Mark as reviewed before activation")
		elif submitter and submitter == actor:
			activate_lock = _("Submitter cannot activate the same Budget (AC-018)")

	return {
		"can_run_check": status in ("Draft", "Returned", "Submitted", "Active"),
		"can_submit": can_submit,
		"can_return": can_return,
		"can_mark_reviewed": can_mark,
		"can_activate": can_activate,
		"activate_lock_reason": activate_lock,
		"read_only": status in ("Active", "Closed", "Cancelled"),
		"show_activation_record": status == "Active",
		# Active: same chrome Request revision as Overview/Lines. Draft/Submitted use in-tab actions.
		"primary_action": "request_revision" if status == "Active" else "",
		"primary_label": "Request revision" if status == "Active" else "",
		"task_id": task.name if task else "",
		"concurrency_token": task.concurrency_token if task else "",
	}


def get_budget_readiness(budget: str, task_id: str | None = None) -> dict[str, Any]:
	"""Grouped readiness checklist + capabilities for the Review tab."""
	require_any_role(*_READ_ROLES)
	doc = _resolve_budget(budget)
	require_budget_capability(CAP_BUDGET_VIEW, doc)
	resolve_scoped_entity(doc.procuring_entity)
	allowed = visible_statuses_for_user()
	if allowed is not None and doc.status not in allowed:
		frappe.throw(
			_("Not permitted to view {0} budgets").format(doc.status),
			frappe.PermissionError,
		)

	groups, blockers = _evaluate_readiness(doc)
	caps = _capabilities(doc, blockers, (task_id or "").strip())

	# Keep portfolio attention counter in sync with live issue count for Draft/Returned.
	live_count = len(blockers)
	if doc.status in ("Draft", "Returned") and int(doc.readiness_issue_count or 0) != live_count:
		frappe.db.set_value(
			"Budget",
			doc.name,
			"readiness_issue_count",
			live_count,
			update_modified=False,
		)
		doc.readiness_issue_count = live_count

	return {
		"budget": {
			"id": doc.name,
			"code": doc.generated_reference,
			"name": doc.title,
			"title": doc.title,
			"status": doc.status,
			"status_label": _STATUS_CHIP.get(doc.status, doc.status),
			"fiscal_period": doc.fiscal_period,
			"currency": doc.currency or "KES",
			"procuring_entity": doc.procuring_entity,
		},
		"groups": groups,
		"blockers": blockers,
		"blocker_count": len(blockers),
		"governance": {
			"submitted_by": doc.submitted_by or "",
			"submitted_at": str(doc.submitted_at) if doc.submitted_at else "",
			"submitted_at_display": format_datetime(doc.submitted_at) if doc.submitted_at else "",
			"reviewed_by": doc.reviewed_by or "",
			"reviewed_at": str(doc.reviewed_at) if doc.reviewed_at else "",
			"reviewed_at_display": format_datetime(doc.reviewed_at) if doc.reviewed_at else "",
			"activated_by": doc.activated_by or "",
			"activated_at": str(doc.activated_at) if doc.activated_at else "",
			"activated_at_display": format_datetime(doc.activated_at) if doc.activated_at else "",
			"return_reason": doc.return_reason or "",
			"authoritative_reference": doc.authoritative_reference or "",
		},
		"disclaimer": _(
			"Activation confirms that the approved financial baseline has been verified "
			"for procurement use in KenTender. It does not constitute statutory budget approval."
		),
		"capabilities": caps,
	}


def submit_budget(payload: dict | str | None = None) -> dict[str, Any]:
	"""Draft/Returned → Submitted when readiness passes."""
	payload = _as_dict(payload)
	doc = _resolve_budget(payload.get("budget") or "")
	require_budget_capability(CAP_BUDGET_SUBMIT, doc)

	if doc.status not in ("Draft", "Returned"):
		return {
			"ok": False,
			"errors": {"status": _("Only Draft or Returned budgets can be submitted")},
		}

	_groups, blockers = _evaluate_readiness(doc)
	if blockers:
		return {
			"ok": False,
			"errors": {"blockers": blockers[0]["message"]},
			"blockers": blockers,
			"readiness": get_budget_readiness(doc.generated_reference),
		}

	task = create_budget_task(
		doc,
		capability=CAP_BUDGET_REVIEW,
		task_type="budget.review",
		iteration=0,
	)
	prior = doc.status
	doc.status = "Submitted"
	doc.submitted_by = frappe.session.user
	doc.submitted_at = now_datetime()
	doc.reviewed_by = None
	doc.reviewed_at = None
	doc.return_reason = ""
	doc.readiness_issue_count = 0
	doc.save(ignore_permissions=True)
	from kentender_budget.services.budget_audit_contracts import (
		EVENT_SUBMITTED,
		safe_record_event,
	)

	safe_record_event(
		budget=doc.name,
		event_type=EVENT_SUBMITTED,
		record_code=doc.generated_reference,
		record_doctype="Budget",
		actor=frappe.session.user,
		actor_kind="user",
		before_summary=prior,
		after_summary="Submitted",
		change_summary=f"Status: {prior} → Submitted",
		source_reference=doc.authoritative_reference or "",
	)
	from kentender_budget.services.budget_notification_service import (
		EVENT_BUDGET_SUBMITTED,
		notify_budget_users,
	)

	notify_budget_users(EVENT_BUDGET_SUBMITTED, budget_doc=doc)
	return {"ok": True, "task_id": task.name, "readiness": get_budget_readiness(doc.generated_reference)}


def return_budget(payload: dict | str | None = None) -> dict[str, Any]:
	"""Submitted → Returned; Reviewer/Authority; comment required."""
	payload = _as_dict(payload)
	doc = _resolve_budget(payload.get("budget") or "")
	task, token = require_budget_task(
		payload,
		capability=CAP_BUDGET_RETURN,
		subject_type="Budget",
		subject_id=doc.name,
	)

	if doc.status != "Submitted":
		return {
			"ok": False,
			"errors": {"status": _("Only Submitted budgets can be returned")},
		}

	comment = (payload.get("comment") or payload.get("return_reason") or "").strip()
	if not comment:
		return {
			"ok": False,
			"errors": {"comment": _("Comment is required when returning a Budget")},
		}

	complete_budget_task(task, token, capability=CAP_BUDGET_RETURN, target_state="Returned")
	doc.status = "Returned"
	doc.return_reason = comment
	doc.reviewed_by = None
	doc.reviewed_at = None
	doc.save(ignore_permissions=True)
	from kentender_budget.services.budget_audit_contracts import (
		EVENT_RETURNED,
		safe_record_event,
	)

	safe_record_event(
		budget=doc.name,
		event_type=EVENT_RETURNED,
		record_code=doc.generated_reference,
		record_doctype="Budget",
		actor=frappe.session.user,
		actor_kind="user",
		before_summary="Submitted",
		after_summary="Returned",
		change_summary="Status: Submitted → Returned",
		source_reference=doc.authoritative_reference or "",
		reason=comment,
	)
	from kentender_budget.services.budget_notification_service import (
		EVENT_BUDGET_RETURNED,
		notify_budget_users,
	)

	notify_budget_users(EVENT_BUDGET_RETURNED, budget_doc=doc)
	return {"ok": True, "readiness": get_budget_readiness(doc.generated_reference)}


def mark_budget_reviewed(payload: dict | str | None = None) -> dict[str, Any]:
	"""Record reviewer completion; status remains Submitted."""
	payload = _as_dict(payload)
	doc = _resolve_budget(payload.get("budget") or "")
	task, token = require_budget_task(
		payload,
		capability=CAP_BUDGET_REVIEW,
		subject_type="Budget",
		subject_id=doc.name,
	)

	if doc.status != "Submitted":
		return {
			"ok": False,
			"errors": {"status": _("Only Submitted budgets can be marked reviewed")},
		}

	_groups, blockers = _evaluate_readiness(doc)
	if blockers:
		return {
			"ok": False,
			"errors": {"blockers": blockers[0]["message"]},
			"blockers": blockers,
		}

	complete_budget_task(task, token, capability=CAP_BUDGET_REVIEW)
	authority_task = create_budget_task(
		doc,
		capability=CAP_BUDGET_APPROVE,
		task_type="budget.approve",
		predecessor_task_id=task.name,
		iteration=0,
	)
	doc.reviewed_by = frappe.session.user
	doc.reviewed_at = now_datetime()
	doc.save(ignore_permissions=True)
	from kentender_budget.services.budget_audit_contracts import (
		EVENT_REVIEWED,
		safe_record_event,
	)

	safe_record_event(
		budget=doc.name,
		event_type=EVENT_REVIEWED,
		record_code=doc.generated_reference,
		record_doctype="Budget",
		actor=frappe.session.user,
		actor_kind="user",
		before_summary="Submitted",
		after_summary="Reviewed",
		change_summary="Reviewer completion recorded (status remains Submitted)",
		source_reference=doc.authoritative_reference or "",
	)
	from kentender_budget.services.budget_notification_service import (
		EVENT_BUDGET_REVIEWED,
		notify_budget_users,
	)

	notify_budget_users(EVENT_BUDGET_REVIEWED, budget_doc=doc)
	return {"ok": True, "task_id": authority_task.name, "readiness": get_budget_readiness(doc.generated_reference)}


def activate_budget(payload: dict | str | None = None) -> dict[str, Any]:
	"""Submitted → Active; Authority; reviewed; AC-018 submitter lock."""
	payload = _as_dict(payload)
	doc = _resolve_budget(payload.get("budget") or "")
	task, token = require_budget_task(
		payload,
		capability=CAP_BUDGET_APPROVE,
		subject_type="Budget",
		subject_id=doc.name,
	)

	if doc.status != "Submitted":
		return {
			"ok": False,
			"errors": {"status": _("Only Submitted budgets can be activated")},
		}

	if not (doc.reviewed_by or "").strip():
		return {
			"ok": False,
			"errors": {"reviewed_by": _("Budget must be marked reviewed before activation")},
		}

	if doc.submitted_by and doc.submitted_by == frappe.session.user:
		return {
			"ok": False,
			"errors": {"status": _("Submitter cannot activate the same Budget (AC-018)")},
		}

	_groups, blockers = _evaluate_readiness(doc)
	if blockers:
		return {
			"ok": False,
			"errors": {"blockers": blockers[0]["message"]},
			"blockers": blockers,
		}

	if not (doc.authoritative_reference or "").strip() or not (doc.approval_evidence or "").strip():
		return {
			"ok": False,
			"errors": {
				"approval_evidence": _("Authoritative approval reference and evidence are required"),
			},
		}

	complete_budget_task(
		task,
		token,
		capability=CAP_BUDGET_APPROVE,
		prior_actions=[
			{"user": doc.submitted_by or "", "capability": CAP_BUDGET_SUBMIT},
			{"user": doc.reviewed_by or "", "capability": CAP_BUDGET_REVIEW},
		],
	)
	doc.status = "Active"
	doc.activated_by = frappe.session.user
	doc.activated_at = now_datetime()
	doc.readiness_issue_count = 0
	doc.save(ignore_permissions=True)
	from kentender_budget.services.budget_audit_contracts import (
		EVENT_ACTIVATED,
		safe_record_event,
	)

	safe_record_event(
		budget=doc.name,
		event_type=EVENT_ACTIVATED,
		record_code=doc.generated_reference,
		record_doctype="Budget",
		actor=frappe.session.user,
		actor_kind="user",
		before_summary="Submitted",
		after_summary="Active",
		change_summary="Status: Submitted → Active",
		source_reference=doc.authoritative_reference or "",
	)
	from kentender_budget.services.budget_notification_service import (
		EVENT_BUDGET_ACTIVATED,
		notify_budget_users,
	)

	notify_budget_users(EVENT_BUDGET_ACTIVATED, budget_doc=doc)
	return {"ok": True, "readiness": get_budget_readiness(doc.generated_reference)}
