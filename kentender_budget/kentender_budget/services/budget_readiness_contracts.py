# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 §6/§9.2/§12.5 — Budget Version readiness, submission and
the single Budget Approver decision (Return or Approve, one atomic action —
no separate recommend-then-activate two-step). BUD-UI-04 Approval task.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, format_datetime, getdate, now_datetime

from kentender_budget.services.budget_authorization import (
	CAP_APPROVE,
	CAP_RETURN,
	CAP_SUBMIT,
	has_budget_version_capability,
	require_budget_version_capability,
	require_budget_version_read_scope,
)
from kentender_budget.services.budget_contracts import (
	_active_version,
	_budget_summary,
	_funding_source_label,
	_org_unit_label,
	_resolve_budget,
	_resolve_budget_version,
	_user_label,
	_version_summary,
	_version_totals,
	resolve_scoped_entity,
)

_MIN_RETURN_REASON = 10
_MAX_RETURN_REASON = 500


def _as_dict(payload: dict | str | None) -> dict[str, Any]:
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return payload or {}


def _issue(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _evaluate_readiness(version) -> list[dict[str, str]]:
	"""§9.2/§12.2/BUD-BR-004/017/018/019/020 — full readiness/activation guard
	set, reused by both `submit_budget_version` (pre-submission) and
	`approve_budget_version` (BUD-BR-021 full recheck)."""
	issues: list[dict[str, str]] = []

	if not (version.approval_reference or "").strip():
		issues.append(_issue("evidence.approval_reference", _("Approval reference is required")))
	if not version.approval_date:
		issues.append(_issue("evidence.approval_date", _("Approval date is required")))
	elif getdate(version.approval_date) > getdate():
		issues.append(_issue("evidence.approval_date", _("Approval date cannot be in the future")))
	if not (version.approval_document or "").strip():
		issues.append(_issue("evidence.approval_document", _("Approval document is required")))
	if not version.authorised_total or flt(version.authorised_total) <= 0:
		issues.append(_issue("evidence.authorised_total", _("Authorised total must be greater than zero")))

	lines = frappe.get_all(
		"Budget Line Version",
		filters={"budget_version": version.name},
		fields=["name", "budget_line", "title", "owner_org_unit", "funding_source", "approved_amount"],
	)
	if not lines:
		issues.append(_issue("lines.empty", _("At least one Budget Line is required")))

	line_total = sum(flt(l.approved_amount) for l in lines)
	if version.authorised_total and abs(flt(version.authorised_total) - line_total) >= 0.01:
		issues.append(_issue("lines.total_mismatch", _("Budget Line total does not equal the authorised total")))

	based_on = frappe.get_doc("Budget Version", version.based_on_budget_version) if version.based_on_budget_version else None
	if based_on:
		issues.extend(_evaluate_successor_guards(version, based_on, lines))

	return issues


def _evaluate_successor_guards(version, based_on, lines: list[dict]) -> list[dict[str, str]]:
	issues: list[dict[str, str]] = []
	prior_lines = {
		l.budget_line: l
		for l in frappe.get_all(
			"Budget Line Version",
			filters={"budget_version": based_on.name},
			fields=["budget_line", "title", "owner_org_unit", "funding_source", "approved_amount"],
		)
	}
	this_lines = {l.budget_line: l for l in lines}

	total_increase = total_decrease = 0.0
	for budget_line, prior in prior_lines.items():
		current = this_lines.get(budget_line)
		floor = _reserved_plus_committed(budget_line)
		if current is None:
			# BUD-BR-020 — a line may be omitted only when it has no remaining
			# reservation or active commitment.
			if floor > 0:
				issues.append(
					_issue(
						f"lines.omitted_with_floor.{budget_line}",
						_("{0} has a remaining reservation or commitment and cannot be omitted").format(prior.title),
					)
				)
			continue
		# BUD-BR-019 — identity fields immutable after activation.
		if (
			current.title != prior.title
			or current.owner_org_unit != prior.owner_org_unit
			or current.funding_source != prior.funding_source
		):
			issues.append(
				_issue(
					f"lines.identity_changed.{budget_line}",
					_("{0} changed title, owner scope or funding source — a new Budget Line is required").format(
						prior.title
					),
				)
			)
		# BUD-BR-017 — cannot reduce below current Reserved + Committed.
		if flt(current.approved_amount) < floor:
			issues.append(
				_issue(
					f"lines.floor_breach.{budget_line}",
					_("{0} proposed amount is below its current reserved and committed floor").format(prior.title),
				)
			)
		delta = flt(current.approved_amount) - flt(prior.approved_amount)
		if delta > 0:
			total_increase += delta
		elif delta < 0:
			total_decrease += -delta

	if version.revision_type == "Transfer":
		if abs(total_increase - total_decrease) >= 0.01:
			issues.append(_issue("transfer.unbalanced", _("Transfer increases and decreases do not balance")))
		if abs(flt(version.authorised_total) - flt(based_on.authorised_total)) >= 0.01:
			issues.append(_issue("transfer.total_changed", _("A Transfer must preserve the authorised total")))

	return issues


def _reserved_plus_committed(budget_line: str) -> float:
	from kentender_budget.services.budget_contracts import _line_position

	pos = _line_position(budget_line, None)
	return pos["reserved"] + pos["committed"]


def _readiness_checklist(version, issues: list[dict[str, str]]) -> list[dict[str, str]]:
	codes = {i["code"] for i in issues}

	def status(prefix: str) -> str:
		return "Needs attention" if any(c.startswith(prefix) for c in codes) else "Ready"

	checklist = [
		{"key": "evidence", "label": _("Approval details complete"), "result": status("evidence.")},
		{"key": "totals", "label": _("Budget Line total matches authorised total"), "result": status("lines.total_mismatch")},
	]
	if version.based_on_budget_version:
		checklist.append({"key": "floors", "label": _("Reservation and commitment floors"), "result": status("lines.floor_breach") or status("lines.omitted_with_floor")})
		if version.revision_type == "Transfer":
			checklist.append({"key": "transfer", "label": _("Transfer balance"), "result": status("transfer.")})
	else:
		checklist.append({"key": "lines_complete", "label": _("Budget Lines complete"), "result": status("lines.empty")})
	return checklist


def get_budget_approval_task(budget_version: str) -> dict[str, Any]:
	"""BUD-UI-04 Overview tab — §12.5: always reads the submitted version, no
	tab substitutes the current Active version."""
	version = _resolve_budget_version(budget_version)
	require_budget_version_read_scope(version)
	budget = frappe.get_doc("Budget", version.budget)
	resolve_scoped_entity(budget.procuring_entity)

	issues = _evaluate_readiness(version)
	return {
		"budget": _budget_summary(budget),
		"version": _version_summary(version),
		"based_on": _version_summary(frappe.get_doc("Budget Version", version.based_on_budget_version))
		if version.based_on_budget_version
		else None,
		"revision_type": version.revision_type or "",
		"approval_document": version.approval_document or "",
		"readiness": _readiness_checklist(version, issues),
		"blockers": issues,
		"submission": {
			"submitted_by": _user_label(version.submitted_by),
			"submitted_at": str(version.submitted_at) if version.submitted_at else "",
			"submitted_at_display": format_datetime(version.submitted_at) if version.submitted_at else "",
		},
		"capabilities": {
			"can_return": version.status == "Submitted for approval"
			and has_budget_version_capability(frappe.session.user, CAP_RETURN, version),
			"can_approve": version.status == "Submitted for approval"
			and not issues
			and has_budget_version_capability(frappe.session.user, CAP_APPROVE, version),
		},
	}


def get_budget_approval_task_lines(budget_version: str) -> dict[str, Any]:
	"""BUD-UI-04 Budget Lines tab — submitted line set + current floors."""
	version = _resolve_budget_version(budget_version)
	require_budget_version_read_scope(version)

	rows = frappe.get_all(
		"Budget Line Version",
		filters={"budget_version": version.name},
		fields=["budget_line", "title", "owner_org_unit", "funding_source", "approved_amount"],
		order_by="title asc",
	)
	codes = (
		{
			r.name: r.generated_reference
			for r in frappe.get_all(
				"Budget Line", filters={"name": ["in", [row.budget_line for row in rows]]}, fields=["name", "generated_reference"]
			)
		}
		if rows
		else {}
	)
	out = []
	total_amount = total_floor = 0.0
	for r in rows:
		floor = _reserved_plus_committed(r.budget_line) if version.based_on_budget_version else 0.0
		headroom = flt(r.approved_amount) - floor
		total_amount += flt(r.approved_amount)
		total_floor += floor
		out.append(
			{
				"budget_line": r.budget_line,
				"budget_line_code": codes.get(r.budget_line, ""),
				"title": r.title,
				"owner_org_unit": _org_unit_label(r.owner_org_unit),
				"funding_source": _funding_source_label(r.funding_source),
				"amount": flt(r.approved_amount),
				"floor": floor,
				"headroom": headroom,
			}
		)
	return {
		"rows": out,
		"total_amount": total_amount,
		"total_floor": total_floor,
		"total_headroom": total_amount - total_floor,
		"is_successor": bool(version.based_on_budget_version),
	}


def get_budget_approval_task_changes(budget_version: str) -> dict[str, Any]:
	"""BUD-UI-04 Changes tab — server-calculated diff vs `based_on_budget_version`.
	Version 1 returns the explicit initial-baseline state, never an invented
	predecessor (§12.5)."""
	version = _resolve_budget_version(budget_version)
	require_budget_version_read_scope(version)

	rows = frappe.get_all(
		"Budget Line Version",
		filters={"budget_version": version.name},
		fields=["budget_line", "title", "approved_amount"],
		order_by="title asc",
	)
	codes = (
		{
			r.name: r.generated_reference
			for r in frappe.get_all(
				"Budget Line", filters={"name": ["in", [row.budget_line for row in rows]]}, fields=["name", "generated_reference"]
			)
		}
		if rows
		else {}
	)
	if not version.based_on_budget_version:
		total = sum(flt(r.approved_amount) for r in rows)
		return {
			"is_initial_baseline": True,
			"rows": [
				{
					"budget_line": r.budget_line,
					"budget_line_code": codes.get(r.budget_line, ""),
					"title": r.title,
					"submitted_amount": flt(r.approved_amount),
				}
				for r in rows
			],
			"total_submitted": total,
		}

	prior = {
		l.budget_line: flt(l.approved_amount)
		for l in frappe.get_all(
			"Budget Line Version", filters={"budget_version": version.based_on_budget_version}, fields=["budget_line", "approved_amount"]
		)
	}
	changes = []
	total_active = total_submitted = 0.0
	affected_reservations = affected_commitments = floor_breaches = 0
	for r in rows:
		active_amount = prior.get(r.budget_line, 0.0)
		change = flt(r.approved_amount) - active_amount
		total_active += active_amount
		total_submitted += flt(r.approved_amount)
		floor = _reserved_plus_committed(r.budget_line)
		if change < 0 and abs(change) > 0 and flt(r.approved_amount) < floor:
			floor_breaches += 1
		if floor > 0:
			affected_reservations += 1
		changes.append(
			{
				"budget_line": r.budget_line,
				"budget_line_code": codes.get(r.budget_line, ""),
				"title": r.title,
				"active_amount": active_amount,
				"submitted_amount": flt(r.approved_amount),
				"change": change,
			}
		)
	return {
		"is_initial_baseline": False,
		"rows": changes,
		"total_active": total_active,
		"total_submitted": total_submitted,
		"total_change": total_submitted - total_active,
		"impact": {
			"active_reservations_affected": affected_reservations,
			"active_commitments_affected": affected_commitments,
			"floor_breaches": floor_breaches,
			"transfer_difference": abs(flt(version.authorised_total) - flt(total_submitted)),
		},
	}


def submit_budget_version(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `submit_budget_version` — Draft → Submitted for approval."""
	payload = _as_dict(payload)
	version = _resolve_budget_version(payload.get("budget_version") or "")
	require_budget_version_capability(frappe.session.user, CAP_SUBMIT, version)

	if version.status != "Draft":
		frappe.throw(_("Only a Draft version can be submitted"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	issues = _evaluate_readiness(version)
	if issues:
		return {"ok": False, "code": "BUDGET_NOT_READY", "blockers": issues}

	version.status = "Submitted for approval"
	version.submitted_by = frappe.session.user
	version.submitted_at = now_datetime()
	version.decided_by = None
	version.decided_at = None
	version.return_reason = ""
	version.save(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_SUBMITTED, safe_record_event

	safe_record_event(
		budget=version.budget,
		budget_version=version.name,
		event_type=EVENT_SUBMITTED,
		actor=frappe.session.user,
		correlation_id=frappe.generate_hash(length=12),
		calling_module="Budget & Funding",
	)
	return {"ok": True, "version": _version_summary(version)}


def return_budget_version(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `return_budget_version` — Submitted for approval → Draft, reason required."""
	payload = _as_dict(payload)
	version = _resolve_budget_version(payload.get("budget_version") or "")
	require_budget_version_capability(frappe.session.user, CAP_RETURN, version)

	if version.status != "Submitted for approval":
		frappe.throw(_("Only a Submitted version can be returned"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	# §12.5 "Every command carries Budget Version ID, expected status and
	# expected record version" — mirrors approve_budget_version's own check.
	expected_modified = payload.get("expected_modified")
	if expected_modified and str(version.modified) != str(expected_modified):
		frappe.throw(_("This Budget Version was changed by someone else"), frappe.ValidationError, title="BUDGET_STALE_WRITE")

	reason = (payload.get("return_reason") or payload.get("reason") or "").strip()
	if not (_MIN_RETURN_REASON <= len(reason) <= _MAX_RETURN_REASON):
		return {
			"ok": False,
			"errors": {"return_reason": _("Return reason must be between {0} and {1} characters").format(_MIN_RETURN_REASON, _MAX_RETURN_REASON)},
		}

	version.status = "Draft"
	version.decided_by = frappe.session.user
	version.decided_at = now_datetime()
	version.return_reason = reason
	version.save(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_RETURNED, safe_record_event

	safe_record_event(
		budget=version.budget,
		budget_version=version.name,
		event_type=EVENT_RETURNED,
		actor=frappe.session.user,
		correlation_id=frappe.generate_hash(length=12),
		calling_module="Budget & Funding",
		reason=reason,
	)
	return {"ok": True, "version": _version_summary(version)}


def approve_budget_version(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `approve_budget_version` — revalidate authority, evidence, line
	total, floors, transfer balance, scope and concurrency; atomically
	activate and supersede the previous Active version (BUD-BR-021/022).
	One atomic action — there is no separate later activation step."""
	payload = _as_dict(payload)
	version = _resolve_budget_version(payload.get("budget_version") or "")
	require_budget_version_capability(frappe.session.user, CAP_APPROVE, version)

	if version.status != "Submitted for approval":
		frappe.throw(_("Only a Submitted version can be approved"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	expected_modified = payload.get("expected_modified")
	if expected_modified and str(version.modified) != str(expected_modified):
		frappe.throw(_("This Budget Version was changed by someone else"), frappe.ValidationError, title="BUDGET_STALE_WRITE")

	issues = _evaluate_readiness(version)
	if issues:
		return {"ok": False, "code": "BUDGET_NOT_READY", "blockers": issues}

	prior_active = _active_version(version.budget)

	version.status = "Active"
	version.decided_by = frappe.session.user
	version.decided_at = now_datetime()
	version.save(ignore_permissions=True)

	if prior_active and prior_active.name != version.name:
		prior_active.status = "Superseded"
		prior_active.superseded_at = now_datetime()
		prior_active.save(ignore_permissions=True)

	correlation_id = frappe.generate_hash(length=12)
	from kentender_budget.services.budget_audit_contracts import EVENT_APPROVED, EVENT_SUPERSEDED, safe_record_event

	safe_record_event(
		budget=version.budget,
		budget_version=version.name,
		event_type=EVENT_APPROVED,
		actor=frappe.session.user,
		correlation_id=correlation_id,
		calling_module="Budget & Funding",
	)
	if prior_active and prior_active.name != version.name:
		safe_record_event(
			budget=version.budget,
			budget_version=prior_active.name,
			event_type=EVENT_SUPERSEDED,
			actor=frappe.session.user,
			correlation_id=correlation_id,
			calling_module="Budget & Funding",
		)
	return {"ok": True, "version": _version_summary(version)}


def close_budget(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `close_budget` — Active → Closed after the FY and remaining-
	reservation guards pass (§6.2, BUD-BR-023)."""
	payload = _as_dict(payload)
	doc = _resolve_budget(payload.get("budget") or "")
	version = _active_version(doc.name)
	if not version:
		frappe.throw(_("No Active Budget Version to close"), frappe.ValidationError, title="BUDGET_INVALID_STATE")
	require_budget_version_capability(frappe.session.user, CAP_APPROVE, version)

	end_date = frappe.db.get_value("Financial Year", doc.financial_year, "end_date")
	if end_date and getdate() <= getdate(end_date):
		return {"ok": False, "errors": {"financial_year": _("The Financial Year has not yet ended")}}

	totals = _version_totals(version.name)
	if totals["reserved"] > 0:
		return {"ok": False, "errors": {"reservations": _("Budget Lines still have a remaining reservation")}}

	version.status = "Closed"
	version.closed_by = frappe.session.user
	version.closed_at = now_datetime()
	version.save(ignore_permissions=True)

	from kentender_budget.services.budget_audit_contracts import EVENT_CLOSED, safe_record_event

	safe_record_event(
		budget=doc.name,
		budget_version=version.name,
		event_type=EVENT_CLOSED,
		actor=frappe.session.user,
		correlation_id=frappe.generate_hash(length=12),
		calling_module="Budget & Funding",
	)
	return {"ok": True, "version": _version_summary(version)}
