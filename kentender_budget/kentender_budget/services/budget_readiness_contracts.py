# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.3 §6/§9.2/§12.5 — Budget Version readiness, submission and
the single Budget Approver decision (Return or Approve, one atomic action —
no separate recommend-then-activate two-step). BUD-UI-04 Approval task.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime

from kentender_budget.services.budget_write_family import budget_write
from kentender_budget.services.budget_idempotency import run_idempotent
from kentender_budget.services.budget_locking import lock_budget, locked_doc
from kentender_budget.services.budget_money import as_float, scale_for
from kentender_budget.services.budget_money import stored as money_stored

from kentender_budget.services.budget_authorization import (
	CAP_APPROVE,
	CAP_RETURN,
	CAP_SUBMIT,
	has_budget_version_capability,
	require_budget_version_capability,
	require_budget_version_read_scope,
)
from kentender_budget.services.budget_contracts import (
	NOT_FOUND,
	_active_version,
	_budget_summary,
	_display_date,
	_display_datetime,
	_funding_source_label,
	_org_unit_label,
	_resolve_budget,
	_resolve_budget_version,
	_user_label,
	_version_summary,
	_version_totals,
	catalogue_problem,
	forbidden_task_verdict,
	forbidden_verdict,
	format_kes_full,
	stale_write_result,
	stamp_is_stale,
)
from kentender_budget.services.budget_authorization import holds_budget_approver_assignment, is_technical

_MIN_RETURN_REASON = 10
_MAX_RETURN_REASON = 500


def _as_dict(payload: dict | str | None) -> dict[str, Any]:
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return payload or {}


def _issue(code: str, message: str, rule: str = "BUDGET_NOT_READY", detail: dict[str, Any] | None = None) -> dict[str, Any]:
	"""One typed blocker (§13): `code` is the stable rule id the tests and
	the editor focus on, `rule` the §13 error code, `detail` the exact
	amounts the screen shows (never a rounded or client-derived figure)."""
	return {"code": code, "message": message, "rule": rule, "detail": detail or {}}


def _reconcile(authorised_total, line_total) -> dict[str, Any]:
	"""§11.3 — exact positive `amount_still_to_assign` or
	`amount_over_allocation`, never an unexplained signed difference.
	BUD-BR-004 "the version line sum shall equal `authorised_total`": equality
	is exact (AUD-XC-117; BUD §4.8 allows no epsilon)."""
	authorised = money_stored(authorised_total)
	lines = money_stored(line_total)
	diff = authorised - lines
	return {
		"authorised_total": as_float(authorised),
		"line_total": as_float(lines),
		"difference": as_float(diff),
		"match": diff == 0,
		"amount_still_to_assign": as_float(diff) if diff > 0 else 0.0,
		"amount_over_allocation": as_float(-diff) if diff < 0 else 0.0,
	}


def _line_version_rows(version_name: str, *, locked: bool, fields: str) -> list[Any]:
	"""A Version's Line Versions. `locked=True` is a locking read (the latest
	committed rows; a plain read can miss rows committed after this
	transaction's snapshot)."""
	if locked:
		rows = frappe.db.sql(
			f"select {fields} from `tabProcurement Budget Line Version` where budget_version = %s order by name for update",
			(version_name,),
			as_dict=True,
		)
		return [frappe._dict(r) for r in rows]
	return frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version_name}, fields=[f.strip() for f in fields.split(",")])


_LINE_FIELDS = "name, budget_line, title, owner_org_unit, funding_source, approved_amount"


def _evaluate_readiness(version, *, locked: bool = False) -> list[dict[str, Any]]:
	"""§9.2/§12.2/BUD-BR-004/017/018/019/020 — full readiness/activation guard
	set, reused by both `submit_budget_version` (pre-submission) and
	`approve_budget_version` (BUD-BR-021 full recheck). `locked=True` is the
	decision-time recheck: every read below is a locking read taken after the
	Budget lock (AUD-XC-103), so a reservation or Version change committed since
	this transaction's snapshot is seen."""
	issues: list[dict[str, Any]] = []
	currency = version.currency
	ev = "BUDGET_APPROVAL_EVIDENCE_REQUIRED"

	if not (version.approval_reference or "").strip():
		issues.append(_issue("evidence.approval_reference", _("Approval reference is required"), ev, {"field": "approval_reference"}))
	if not version.approval_date:
		issues.append(_issue("evidence.approval_date", _("Approval date is required"), ev, {"field": "approval_date"}))
	elif getdate(version.approval_date) > getdate():
		issues.append(_issue("evidence.approval_date", _("Approval date cannot be in the future"), ev, {"field": "approval_date"}))
	# 2026-09-19 — approval_document is no longer part of the evidence gate
	# (owner instruction; see budget_contracts.py's own note on this same
	# change and FOLLOW_UPS FU-23).
	if not version.authorised_total or money_stored(version.authorised_total) <= 0:
		issues.append(_issue("evidence.authorised_total", _("Approved allocation must be greater than zero"), ev, {"field": "authorised_total"}))

	lines = _line_version_rows(version.name, locked=locked, fields=_LINE_FIELDS)
	if not lines:
		issues.append(_issue("lines.empty", _("At least one budget line is required"), "BUDGET_NOT_READY", {"field": "lines"}))

	line_total = sum((money_stored(l.approved_amount) for l in lines), Decimal(0))
	if version.authorised_total:
		rec = _reconcile(version.authorised_total, line_total)
		if not rec["match"]:
			if rec["amount_still_to_assign"]:
				message = _("Amount still to assign: {0}").format(format_kes_full(rec["amount_still_to_assign"], currency=currency))
			else:
				message = _("Amount over allocation: {0}").format(format_kes_full(rec["amount_over_allocation"], currency=currency))
			issues.append(_issue("lines.total_mismatch", message, "BUDGET_TOTAL_MISMATCH", rec))

	based_on = frappe.get_doc("Procurement Budget Version", version.based_on_budget_version) if version.based_on_budget_version else None
	carried = set()
	if based_on:
		issues.extend(_evaluate_successor_guards(version, based_on, lines, locked=locked))
		carried = {l.budget_line for l in _line_version_rows(based_on.name, locked=locked, fields="budget_line")}

	# AUD-BUD-010 / BUD18-AC-056 — a NEW line may not name an inactive
	# organisation unit or an unavailable funding source; lines carried from the
	# prior Active Version keep their frozen identity.
	for line in lines:
		if line.budget_line in carried:
			continue
		problem = catalogue_problem(line.owner_org_unit, line.funding_source)
		if problem:
			issues.append(
				_issue(
					f"lines.not_eligible.{line.budget_line}",
					_("{0}: {1}").format(line.title, problem),
					"BUDGET_LINE_NOT_ELIGIBLE",
					{"budget_line": line.budget_line, "title": line.title},
				)
			)

	return issues


def _evaluate_successor_guards(version, based_on, lines: list[dict], *, locked: bool = False) -> list[dict[str, Any]]:
	issues: list[dict[str, Any]] = []
	currency = version.currency
	prior_lines = {l.budget_line: l for l in _line_version_rows(based_on.name, locked=locked, fields=_LINE_FIELDS)}
	this_lines = {l.budget_line: l for l in lines}

	total_increase = total_decrease = Decimal(0)
	for budget_line, prior in prior_lines.items():
		current = this_lines.get(budget_line)
		protected = _reserved_plus_committed(budget_line, for_update=locked)
		if current is None:
			# BUD-BR-020 — a line may be omitted only when it has no remaining
			# reservation or active commitment.
			if protected > 0:
				issues.append(
					_issue(
						f"lines.omitted_with_floor.{budget_line}",
						_("{0} has {1} reserved or committed and cannot be omitted from this update").format(
							prior.title, format_kes_full(protected, currency=currency)
						),
						"BUDGET_REVISION_FLOOR_BREACH",
						{"budget_line": budget_line, "title": prior.title, "proposed_amount": 0.0, "protected_amount": as_float(protected), "shortfall": as_float(protected), "omitted": True},
					)
				)
			else:
				total_decrease += money_stored(prior.approved_amount)
			continue
		# BUD-BR-019 — identity fields immutable after activation.
		if (
			current.title != prior.title
			or (current.owner_org_unit or None) != (prior.owner_org_unit or None)
			or current.funding_source != prior.funding_source
		):
			issues.append(
				_issue(
					f"lines.identity_changed.{budget_line}",
					_("Add a new budget line for the changed purpose, department or funding source. {0} cannot be changed in this way.").format(prior.title),
					"BUDGET_LINE_IDENTITY_IMMUTABLE",
					{"budget_line": budget_line, "title": prior.title},
				)
			)
		# BUD-BR-017 — cannot reduce below current Reserved + Committed.
		proposed = money_stored(current.approved_amount)
		if proposed < protected:
			shortfall = protected - proposed
			issues.append(
				_issue(
					f"lines.floor_breach.{budget_line}",
					_("{0} cannot be reduced to {1} because {2} is already reserved or committed. Shortfall: {3}.").format(
						prior.title,
						format_kes_full(current.approved_amount, currency=currency),
						format_kes_full(protected, currency=currency),
						format_kes_full(shortfall, currency=currency),
					),
					"BUDGET_REVISION_FLOOR_BREACH",
					{"budget_line": budget_line, "title": prior.title, "proposed_amount": as_float(proposed), "protected_amount": as_float(protected), "shortfall": as_float(shortfall)},
				)
			)
		delta = proposed - money_stored(prior.approved_amount)
		if delta > 0:
			total_increase += delta
		elif delta < 0:
			total_decrease += -delta
	for budget_line, current in this_lines.items():
		if budget_line not in prior_lines:
			total_increase += money_stored(current.approved_amount)

	if version.revision_type == "Transfer":
		difference = abs(total_increase - total_decrease)
		if difference != 0:
			issues.append(
				_issue(
					"transfer.unbalanced",
					_("The amounts moved out and moved in must match. Total moved out {0}; total moved in {1}; difference {2}.").format(
						format_kes_full(total_decrease, currency=currency), format_kes_full(total_increase, currency=currency), format_kes_full(difference, currency=currency)
					),
					"BUDGET_TRANSFER_UNBALANCED",
					{"moved_out": as_float(total_decrease), "moved_in": as_float(total_increase), "difference": as_float(difference)},
				)
			)
		if money_stored(version.authorised_total) != money_stored(based_on.authorised_total):
			issues.append(
				_issue(
					"transfer.total_changed",
					_("A transfer keeps the approved allocation unchanged ({0}).").format(format_kes_full(based_on.authorised_total, currency=currency)),
					"BUDGET_TRANSFER_UNBALANCED",
					{"authorised_total": flt(version.authorised_total), "baseline_total": flt(based_on.authorised_total)},
				)
			)

	return issues


def _reserved_plus_committed(budget_line: str, *, for_update: bool = False) -> Decimal:
	"""The exact floor of a line: reserved plus committed (BUD-BR-017)."""
	from kentender_budget.services.budget_contracts import _line_position_exact

	pos = _line_position_exact(budget_line, None, for_update=for_update)
	return pos["reserved"] + pos["committed"]


def _line_codes(rows) -> dict[str, str]:
	if not rows:
		return {}
	return {
		r.name: r.generated_reference
		for r in frappe.get_all(
			"Procurement Budget Line", filters={"name": ["in", [row.budget_line for row in rows]]}, fields=["name", "generated_reference"]
		)
	}


def _document_facts(version) -> dict[str, Any]:
	url = version.approval_document or ""
	return {"name": url.split("/").pop() if url else "", "url": url}


def _evidence(version) -> dict[str, Any]:
	return {
		"approval_reference": version.approval_reference or "",
		"approval_date": str(version.approval_date) if version.approval_date else "",
		"approval_date_display": _display_date(version.approval_date),
		"approved_allocation": flt(version.authorised_total),
		"document": _document_facts(version),
	}


def _evidence_changes(version, based_on) -> dict[str, Any]:
	"""§11.8 — material evidence changes from the baseline: reference, date,
	document. The comparison must not imply only line amounts changed."""
	if not based_on:
		return {}
	current, prior = _evidence(version), _evidence(based_on)
	return {
		"approval_reference": {"changed": current["approval_reference"] != prior["approval_reference"], "from": prior["approval_reference"], "to": current["approval_reference"]},
		"approval_date": {"changed": current["approval_date"] != prior["approval_date"], "from": prior["approval_date_display"], "to": current["approval_date_display"]},
		"document": {"changed": current["document"]["url"] != prior["document"]["url"], "from": prior["document"]["name"], "to": current["document"]["name"]},
	}


def _summary_sentence(rows: list[dict[str, Any]], total_change: float, revision_type: str, currency: str) -> str:
	"""§11.8 — one plain sentence describing the money movement."""
	ups = [r for r in rows if r["change"] > 0]
	downs = [r for r in rows if r["change"] < 0]
	if not ups and not downs:
		return _("No line amount changes. The total allocation stays the same.")
	if revision_type == "Transfer" and len(ups) == 1 and len(downs) == 1 and total_change == 0:
		return _("{0} moves from {1} to {2}. The total allocation stays the same.").format(
			format_kes_full(ups[0]["change"], currency=currency), downs[0]["title"], ups[0]["title"]
		)
	if total_change > 0:
		return _("The registered allocation increases by {0} across {1} budget line(s).").format(format_kes_full(total_change, currency=currency), len(ups))
	if total_change < 0:
		return _("The registered allocation decreases by {0} across {1} budget line(s).").format(format_kes_full(-total_change, currency=currency), len(downs))
	return _("Amounts move between {0} budget line(s). The total allocation stays the same.").format(len(ups) + len(downs))


def _task_reader_verdict() -> dict[str, Any] | None:
	"""§12.5 — business review needs a Budget Approver; AUTH §8 technical
	readers inspect read-only. Both are resolved before any lookup."""
	return forbidden_task_verdict()


def _submitted_rows(version) -> list[Any]:
	return frappe.get_all(
		"Procurement Budget Line Version",
		filters={"budget_version": version.name},
		fields=["budget_line", "title", "owner_org_unit", "funding_source", "approved_amount"],
		order_by="title asc",
	)


def _protection_rows(rows, codes, currency: str) -> tuple[list[dict[str, Any]], bool]:
	"""Live Reserved + committed per proposed line and the projected
	availability if the guard passes; an exact positive Shortfall when it
	fails. Never a negative spendable figure."""
	out = []
	unavailable = False
	for r in rows:
		try:
			protected = _reserved_plus_committed(r.budget_line)
		except Exception:
			frappe.log_error(title="Budget approval task: live position unavailable")
			unavailable = True
			protected = None
		proposed = money_stored(r.approved_amount)
		row = {
			"budget_line": r.budget_line,
			"budget_line_code": codes.get(r.budget_line, ""),
			"title": r.title,
			"proposed_amount": as_float(proposed),
			"protected_amount": None if protected is None else as_float(protected),
			"available_after_update": None,
			"shortfall": 0.0,
			"breached": False,
		}
		if protected is not None:
			if proposed >= protected:
				row["available_after_update"] = as_float(proposed - protected)
			else:
				row["shortfall"] = as_float(protected - proposed)
				row["breached"] = True
		out.append(row)
	return out, unavailable


def get_budget_approval_task(budget_version: str) -> dict[str, Any]:
	"""BUD-UI-04 Overview — §11.8/§11.13/§12.5: always reads the submitted
	version, leads with the complete initial allocation or the successor
	changes, then external evidence, then the separately observed live
	protection. No readiness checklist."""
	verdict = _task_reader_verdict()
	if verdict:
		return verdict
	try:
		version = _resolve_budget_version(budget_version)
	except frappe.DoesNotExistError:
		frappe.clear_last_message()
		return dict(NOT_FOUND)
	require_budget_version_read_scope(version)
	budget = frappe.get_doc("Procurement Budget", version.budget)
	currency = budget.currency
	based_on = frappe.get_doc("Procurement Budget Version", version.based_on_budget_version) if version.based_on_budget_version else None

	rows = _submitted_rows(version)
	codes = _line_codes(rows)
	prior = (
		{l.budget_line: money_stored(l.approved_amount) for l in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": based_on.name}, fields=["budget_line", "approved_amount"])}
		if based_on
		else {}
	)
	change_rows = []
	total_current = total_proposed = Decimal(0)
	for r in rows:
		current = prior.get(r.budget_line, Decimal(0))
		proposed = money_stored(r.approved_amount)
		change_rows.append(
			{
				"budget_line": r.budget_line,
				"budget_line_code": codes.get(r.budget_line, ""),
				"title": r.title,
				"current_amount": as_float(current) if based_on else None,
				"proposed_amount": as_float(proposed),
				"change": as_float(proposed - current),
				"omitted": False,
			}
		)
		total_current += current
		total_proposed += proposed
	if based_on:
		present = {r.budget_line for r in rows}
		for line_name, amount in prior.items():
			if line_name not in present:
				title = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": based_on.name, "budget_line": line_name}, "title")
				change_rows.append({"budget_line": line_name, "budget_line_code": codes.get(line_name, ""), "title": title, "current_amount": as_float(amount), "proposed_amount": 0.0, "change": as_float(-amount), "omitted": True})
				total_current += amount

	protection_rows, unavailable = _protection_rows(rows, codes, currency) if based_on else ([], False)
	issues = _evaluate_readiness(version)
	positions_as_at = now_datetime()
	is_submitted = version.status == "Submitted for approval"
	can_approve = is_submitted and not issues and not unavailable and has_budget_version_capability(frappe.session.user, CAP_APPROVE, version)

	return {
		"kind": "successor" if based_on else "initial",
		"budget": _budget_summary(budget),
		"version": _version_summary(version),
		"based_on": _version_summary(based_on) if based_on else None,
		"revision_type": version.revision_type or "",
		"approval_document": version.approval_document or "",
		"changes": {
			"rows": change_rows,
			"total_current": as_float(total_current) if based_on else None,
			"total_proposed": as_float(total_proposed),
			"total_change": as_float(total_proposed - total_current) if based_on else None,
			"summary": _summary_sentence(change_rows, total_proposed - total_current, version.revision_type or "", currency) if based_on else "",
		},
		"protection": {
			"as_at": str(positions_as_at),
			"as_at_display": _display_datetime(positions_as_at),
			"rows": protection_rows,
			"unavailable": unavailable,
		},
		"evidence": _evidence(version),
		"evidence_changes": _evidence_changes(version, based_on),
		"line_details": [
			{
				"budget_line": r.budget_line,
				"budget_line_code": codes.get(r.budget_line, ""),
				"title": r.title,
				"available_to": _org_unit_label(r.owner_org_unit),
				"funding_source": _funding_source_label(r.funding_source),
				"amount": flt(r.approved_amount),
			}
			for r in rows
		],
		"blockers": issues,
		"submission": {
			"submitted_by": _user_label(version.submitted_by),
			"submitted_at": str(version.submitted_at) if version.submitted_at else "",
			"submitted_at_display": _display_datetime(version.submitted_at),
		},
		"decision": (
			{"decided_by": _user_label(version.decided_by), "decided_at_display": _display_datetime(version.decided_at), "status": version.status, "return_reason": version.return_reason or ""}
			if version.decided_by
			else None
		),
		"capabilities": {
			"can_return": is_submitted and has_budget_version_capability(frappe.session.user, CAP_RETURN, version),
			"can_approve": can_approve,
			"is_technical_reader": is_technical(frappe.session.user) and not has_budget_version_capability(frappe.session.user, CAP_RETURN, version),
		},
	}


def get_budget_approval_task_lines(budget_version: str) -> dict[str, Any]:
	"""BUD-UI-04 Budget Lines tab — §11.9: submitted line set with live
	Reserved + committed and Available after update (or Shortfall)."""
	verdict = _task_reader_verdict()
	if verdict:
		return verdict
	try:
		version = _resolve_budget_version(budget_version)
	except frappe.DoesNotExistError:
		frappe.clear_last_message()
		return dict(NOT_FOUND)
	require_budget_version_read_scope(version)
	currency = version.currency

	rows = _submitted_rows(version)
	codes = _line_codes(rows)
	is_successor = bool(version.based_on_budget_version)
	protection, unavailable = _protection_rows(rows, codes, currency) if is_successor else ([], False)
	by_line = {p["budget_line"]: p for p in protection}
	out = []
	total_amount = total_protected = total_after = total_shortfall = Decimal(0)
	for r in rows:
		p = by_line.get(r.budget_line, {})
		amount = money_stored(r.approved_amount)
		total_amount += amount
		protected = p.get("protected_amount") if is_successor else None
		after = p.get("available_after_update") if is_successor else None
		shortfall = p.get("shortfall", 0.0) if is_successor else 0.0
		if protected is not None:
			total_protected += money_stored(protected)
		if after is not None:
			total_after += money_stored(after)
		total_shortfall += money_stored(shortfall)
		out.append(
			{
				"budget_line": r.budget_line,
				"budget_line_code": codes.get(r.budget_line, ""),
				"title": r.title,
				"available_to": _org_unit_label(r.owner_org_unit),
				"funding_source": _funding_source_label(r.funding_source),
				"amount": as_float(amount),
				"protected_amount": protected,
				"available_after_update": after,
				"shortfall": shortfall,
				"breached": bool(p.get("breached")),
			}
		)
	return {
		"rows": out,
		"total_amount": as_float(total_amount),
		"total_protected": as_float(total_protected) if is_successor else None,
		"total_available_after_update": as_float(total_after) if is_successor else None,
		"total_shortfall": as_float(total_shortfall) if is_successor else None,
		"is_successor": is_successor,
		"unavailable": unavailable,
		"as_at_display": _display_datetime(now_datetime()),
	}


def get_budget_approval_task_changes(budget_version: str) -> dict[str, Any]:
	"""BUD-UI-04 Changes tab — §11.10: server-calculated line diff against
	`based_on_budget_version`, the changed evidence, and the live protection.
	Version 1 returns the explicit initial-baseline state (§12.5)."""
	verdict = _task_reader_verdict()
	if verdict:
		return verdict
	try:
		version = _resolve_budget_version(budget_version)
	except frappe.DoesNotExistError:
		frappe.clear_last_message()
		return dict(NOT_FOUND)
	require_budget_version_read_scope(version)
	task = get_budget_approval_task(version.name)
	if task.get("outcome"):
		return task
	if task["kind"] == "initial":
		return {
			"is_initial_baseline": True,
			"rows": [{"budget_line": r["budget_line"], "budget_line_code": r["budget_line_code"], "title": r["title"], "submitted_amount": r["proposed_amount"]} for r in task["changes"]["rows"]],
			"total_submitted": task["changes"]["total_proposed"],
		}
	return {
		"is_initial_baseline": False,
		"rows": [
			{"budget_line": r["budget_line"], "budget_line_code": r["budget_line_code"], "title": r["title"], "active_amount": r["current_amount"], "submitted_amount": r["proposed_amount"], "change": r["change"], "omitted": r["omitted"]}
			for r in task["changes"]["rows"]
		],
		"total_active": task["changes"]["total_current"],
		"total_submitted": task["changes"]["total_proposed"],
		"total_change": task["changes"]["total_change"],
		"summary": task["changes"]["summary"],
		"evidence_changes": task["evidence_changes"],
		"protection": task["protection"],
		"blockers": task["blockers"],
	}


def _stale(version) -> dict[str, Any]:
	return stale_write_result(version)


def _is_stale(version, payload: dict[str, Any]) -> bool:
	"""The stamp is mandatory on every state-changing command (AUD-XC-119)."""
	return stamp_is_stale(version, payload)


def submit_budget_version(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `submit_budget_version` — Draft → Submitted for approval."""
	payload = _as_dict(payload)
	return run_idempotent(payload=payload, fn=lambda: _submit_budget_version(payload), budget_for=lambda r: (r.get("version") or {}).get("budget"))


def _submit_budget_version(payload: dict[str, Any]) -> dict[str, Any]:
	version = _resolve_budget_version(payload.get("budget_version") or "")
	require_budget_version_capability(frappe.session.user, CAP_SUBMIT, version)

	if version.status != "Draft":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}
	if _is_stale(version, payload):
		return _stale(version)

	# AUD-XC-103 — Version decisions take the Budget lock first and decide from
	# locked reads (Closed Budgets admit no new approval work: AUD-BUD-003).
	lock_budget(version.budget, lines=False)
	version = locked_doc("Procurement Budget Version", version.name)
	if version.status != "Draft":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}
	if _is_stale(version, payload):
		return _stale(version)
	if _budget_is_closed(version.budget):
		return _closed(version)

	issues = _evaluate_readiness(version, locked=True)
	if issues:
		return {"ok": False, "code": "BUDGET_NOT_READY", "blockers": issues, "version": _version_summary(version)}

	from kentender_budget.services.budget_audit_contracts import EVENT_SUBMITTED, record_event
	from kentender_budget.services.budget_submission_attempts import open_attempt

	# AUD-XC-105 / AUD-BUD-002 — the submission event and the immutable attempt
	# are part of the submission: if either cannot be written the submit fails
	# and nothing is kept (a swallowed audit write would leave an approval with
	# no submitter to segregate against).
	savepoint = "budget_submit"
	frappe.db.savepoint(savepoint)
	try:
		version.status = "Submitted for approval"
		version.submitted_by = frappe.session.user
		version.submitted_at = now_datetime()
		version.decided_by = None
		version.decided_at = None
		version.return_reason = ""
		with budget_write():
			version.save(ignore_permissions=True)
		open_attempt(version)
		record_event(
			budget=version.budget,
			budget_version=version.name,
			event_type=EVENT_SUBMITTED,
			actor=frappe.session.user,
			correlation_id=frappe.generate_hash(length=12),
			calling_module="Budget & Funding",
		)
	except Exception:
		frappe.db.rollback(save_point=savepoint)
		raise
	return {"ok": True, "version": _version_summary(version)}


def _budget_is_closed(budget: str) -> bool:
	"""BUD-BR-023 — a Budget with a Closed Version is Closed (locking read)."""
	return bool(frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Closed"}, "name", for_update=True))


def _closed(version) -> dict[str, Any]:
	return {
		"ok": False,
		"code": "BUDGET_CLOSED",
		"errors": {"status": _("This budget is closed and cannot be updated or approved.")},
		"version": _version_summary(version),
	}


def return_budget_version(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `return_budget_version` — Submitted for approval → Draft, reason required."""
	payload = _as_dict(payload)
	return run_idempotent(payload=payload, fn=lambda: _return_budget_version(payload), budget_for=lambda r: (r.get("version") or {}).get("budget"))


def _return_budget_version(payload: dict[str, Any]) -> dict[str, Any]:
	version = _resolve_budget_version(payload.get("budget_version") or "")
	require_budget_version_capability(frappe.session.user, CAP_RETURN, version)

	if version.status != "Submitted for approval":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}
	if _is_stale(version, payload):
		return _stale(version)

	reason = (payload.get("return_reason") or payload.get("reason") or "").strip()
	if not (_MIN_RETURN_REASON <= len(reason) <= _MAX_RETURN_REASON):
		return {
			"ok": False,
			"errors": {"return_reason": _("Return reason must be between {0} and {1} characters").format(_MIN_RETURN_REASON, _MAX_RETURN_REASON)},
		}

	lock_budget(version.budget, lines=False)
	version = locked_doc("Procurement Budget Version", version.name)
	if version.status != "Submitted for approval":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}
	if _is_stale(version, payload):
		return _stale(version)

	version.status = "Draft"
	version.decided_by = frappe.session.user
	version.decided_at = now_datetime()
	version.return_reason = reason
	with budget_write():
		version.save(ignore_permissions=True)
	from kentender_budget.services.budget_submission_attempts import record_decision

	# AUD-BUD-002 — the decision lands on the attempt it decided; the version's
	# own fields are cleared again by the next submission.
	record_decision(version, "Returned", reason)

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
	return run_idempotent(payload=payload, fn=lambda: _approve_budget_version(payload), budget_for=lambda r: (r.get("version") or {}).get("budget"))


def _approve_budget_version(payload: dict[str, Any]) -> dict[str, Any]:
	version = _resolve_budget_version(payload.get("budget_version") or "")
	require_budget_version_capability(frappe.session.user, CAP_APPROVE, version)

	if version.status != "Submitted for approval":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}
	if _is_stale(version, payload):
		return _stale(version)

	# BUD-BR-021 / §8.2A step 2 (AUD-XC-103, AUD-BUD-003) — "under one
	# transaction lock": the Budget's Version rows then its Line rows, in the
	# order reserve/adjust/close/the Finance decision use, so none of them can
	# interleave with this activation. Everything decided below is re-read with
	# locking reads: a plain read would still show the position and status this
	# transaction saw before it waited.
	lock_budget(version.budget)
	version = locked_doc("Procurement Budget Version", version.name)
	if version.status != "Submitted for approval":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}
	if _is_stale(version, payload):
		return _stale(version)
	# AUD-XC-105 — the locked row names the submitter of the attempt actually
	# being decided; a resubmission that landed while this call waited for the
	# lock cannot slip past the earlier segregation check.
	if version.submitted_by and version.submitted_by == frappe.session.user:
		from kentender_core.services.responsibility_errors import fail

		fail("AUTH_SEGREGATION_BLOCKED")
	# BUD-BR-023 — a Closed Budget cannot be re-activated by an already-open
	# successor.
	if _budget_is_closed(version.budget):
		return _closed(version)

	issues = _evaluate_readiness(version, locked=True)
	if issues:
		return {"ok": False, "code": "BUDGET_NOT_READY", "blockers": issues, "version": _version_summary(version)}

	prior_active = _active_version(version.budget, for_update=True)

	# BUD-BR-002's database-level unique guard admits at most one Active
	# version per Budget at any instant — the prior Active version must be
	# superseded *before* the new one is saved as Active, not after, or the
	# new version's own save collides with the guard while the old row is
	# still Active.
	if prior_active and prior_active.name != version.name:
		prior_active.status = "Superseded"
		prior_active.superseded_at = now_datetime()
		with budget_write():
			prior_active.save(ignore_permissions=True)

	version.status = "Active"
	version.decided_by = frappe.session.user
	version.decided_at = now_datetime()
	with budget_write():
		version.save(ignore_permissions=True)
	from kentender_budget.services.budget_submission_attempts import record_decision

	record_decision(version, "Approved")
	# BUD-BR-029 — in this activation transaction: every Open budget revision
	# request on a line this successor changed or omitted becomes Revised.
	from kentender_budget.services.budget_revision_request_contracts import revise_on_activation

	revise_on_activation(version)

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


def _fy_end(fiscal_year: str):
	end_date = frappe.db.get_value("Fiscal Year", fiscal_year, "year_end_date")
	return getdate(end_date) if end_date else None


def _remaining_holds(version_name: str, *, locked: bool = False) -> tuple[list[dict[str, Any]], Decimal, bool]:
	"""Every remaining reservation on the Version's lines, including Needs
	Attention (still reserved). Returns (rows, total, needs_attention)."""
	from kentender_budget.services.budget_contracts import _ACTIVE_RESERVATION_STATUSES, _line_active_reservations

	totals = _version_totals(version_name, for_update=locked)
	rows = []
	total = Decimal(0)
	needs_attention = False
	for line in totals["lines"]:
		if locked:
			held = [
				frappe._dict(r)
				for r in frappe.db.sql(
					"select name, generated_reference, status, remaining_amount from `tabFunding Reservation` where budget_line = %s and status in %s for update",
					(line["budget_line"], tuple(_ACTIVE_RESERVATION_STATUSES)),
					as_dict=True,
				)
			]
		else:
			held = frappe.get_all(
				"Funding Reservation",
				filters={"budget_line": line["budget_line"], "status": ["in", _ACTIVE_RESERVATION_STATUSES]},
				fields=["name", "generated_reference", "status", "remaining_amount"],
			)
		reservations = [r for r in held if money_stored(r.remaining_amount) > 0]
		if not reservations:
			continue
		still = sum((money_stored(r.remaining_amount) for r in reservations), Decimal(0))
		total += still
		flagged = any(r.status == "Needs Attention" for r in reservations)
		needs_attention = needs_attention or flagged
		rows.append(
			{
				"budget_line": line["budget_line"],
				"budget_line_code": line.get("code", ""),
				"title": line["title"],
				"still_reserved": as_float(still),
				"requires_review": flagged,
				"reservations": [{"id": r.name, "code": r.generated_reference, "status": r.status, "remaining_amount": as_float(money_stored(r.remaining_amount))} for r in reservations],
				"line_url": f"/app/budget-funding/line/{line.get('code', '')}" if line.get("code") else "",
			}
		)
	return rows, total, needs_attention


def _closure_status_for(doc, version, *, locked: bool = False) -> dict[str, Any]:
	currency = doc.currency
	end = _fy_end(doc.fiscal_year)
	as_at = now_datetime()
	base = {
		"budget": _budget_summary(doc),
		"version": _version_summary(version),
		"fiscal_year": {"id": doc.fiscal_year, "label": doc.fiscal_year, "end_date": str(end) if end else "", "end_date_display": _display_date(end) if end else ""},
		"as_at": str(as_at),
		"as_at_display": _display_datetime(as_at),
		"currency": currency,
		"can_close": False,
		"rows": [],
		"remaining_total": 0.0,
		"needs_attention": False,
		"active_commitments_total": None,
	}
	if version.status == "Closed":
		base.update({"state": "closed", "closed_by": _user_label(version.closed_by), "closed_at": str(version.closed_at) if version.closed_at else "", "closed_at_display": _display_datetime(version.closed_at)})
		return base
	if not end or getdate() <= end:
		base["state"] = "before_year_end"
		return base
	try:
		rows, total, needs_attention = _remaining_holds(version.name, locked=locked)
		totals = _version_totals(version.name, for_update=locked)
	except Exception:
		frappe.log_error(title="Budget closure: funding position unavailable")
		base["state"] = "unavailable"
		return base
	base.update({"rows": rows, "remaining_total": as_float(total), "needs_attention": needs_attention, "active_commitments_total": totals["committed"]})
	if total > 0:
		base["state"] = "blocked"
		return base
	base["state"] = "ready"
	base["can_close"] = has_budget_version_capability(frappe.session.user, CAP_APPROVE, version)
	return base


def get_budget_closure_status(budget: str) -> dict[str, Any]:
	"""§9.4/§11.18/§12.8 — the year-end closure read. Approver or technical
	read only; a failed position read is `unavailable`, never zero."""
	verdict = forbidden_verdict()
	if verdict:
		return verdict
	try:
		doc = _resolve_budget(budget)
	except frappe.DoesNotExistError:
		frappe.clear_last_message()
		return dict(NOT_FOUND)
	if not holds_budget_approver_assignment(frappe.session.user):
		return {"outcome": "FORBIDDEN", "forbidden": {"heading": "You do not have access to close this budget", "text": "Closing a budget needs the Budget Approver responsibility. Ask your KenTender administrator to assign it in System setup."}}
	version = _active_version(doc.name)
	if not version:
		closed = frappe.get_all("Procurement Budget Version", filters={"budget": doc.name, "status": "Closed"}, order_by="version_number desc", limit=1, pluck="name")
		if not closed:
			return dict(NOT_FOUND)
		version = frappe.get_doc("Procurement Budget Version", closed[0])
	require_budget_version_read_scope(version)
	return _closure_status_for(doc, version)


def close_budget(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `close_budget` — Active → Closed after the FY-end and remaining-
	hold guards pass (§6, §12.8, BUD-BR-023). Revalidates every guard and
	the live authority at commit under the Budget's version lock."""
	payload = _as_dict(payload)
	return run_idempotent(payload=payload, fn=lambda: _close_budget(payload), budget_for=lambda r: (r.get("version") or {}).get("budget") or r.get("budget_id"))


def _close_budget(payload: dict[str, Any]) -> dict[str, Any]:
	doc = _resolve_budget(payload.get("budget") or "")
	version = _active_version(doc.name)
	if not version:
		closed = frappe.get_all("Procurement Budget Version", filters={"budget": doc.name, "status": "Closed"}, order_by="version_number desc", limit=1, pluck="name")
		if closed:
			closed_version = frappe.get_doc("Procurement Budget Version", closed[0])
			return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget is already closed.")}, "version": _version_summary(closed_version), "budget_id": doc.name}
		frappe.throw(_("No Active Budget Version to close"), frappe.ValidationError, title="BUDGET_INVALID_STATE")
	require_budget_version_capability(frappe.session.user, CAP_APPROVE, version)
	if _is_stale(version, payload):
		return _stale(version)

	# AUD-XC-103 — same lock order as reserve/approve (Version rows, then line
	# rows); the Version is re-read as a locking read (a plain reload would show
	# the snapshot) and every remaining hold is read with locking reads, so a
	# reservation committed while this call waited blocks the closure and a
	# reservation arriving after it is refused as BUDGET_CLOSED.
	lock_budget(doc.name)
	version = locked_doc("Procurement Budget Version", version.name)
	if version.status != "Active":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"status": _("This budget has changed. Refresh to see the available actions.")}, "version": _version_summary(version)}
	if _is_stale(version, payload):
		return _stale(version)

	status = _closure_status_for(doc, version, locked=True)
	if status["state"] == "before_year_end":
		return {"ok": False, "code": "BUDGET_INVALID_STATE", "errors": {"fiscal_year": _("This budget can be closed only after {0}.").format(status["fiscal_year"]["end_date_display"])}, "closure": status, "version": _version_summary(version)}
	if status["state"] == "unavailable":
		return {"ok": False, "code": "BUDGET_HISTORICAL_BASIS_UNAVAILABLE", "errors": {"reservations": _("The funding position could not be checked. Try again before closing this budget.")}, "closure": status, "version": _version_summary(version)}
	if status["state"] == "blocked":
		return {
			"ok": False,
			"code": "BUDGET_INVALID_STATE",
			"errors": {"reservations": _("This budget cannot be closed yet. {0} remains reserved for requisitions.").format(format_kes_full(status["remaining_total"], currency=doc.currency))},
			"closure": status,
			"version": _version_summary(version),
		}

	version.status = "Closed"
	version.closed_by = frappe.session.user
	version.closed_at = now_datetime()
	with budget_write():
		version.save(ignore_permissions=True)
	# BUD-BR-030 — closing declines every remaining Open revision request.
	from kentender_budget.services.budget_revision_request_contracts import decline_on_close

	decline_on_close(doc.name)

	from kentender_budget.services.budget_audit_contracts import EVENT_CLOSED, safe_record_event

	safe_record_event(
		budget=doc.name,
		budget_version=version.name,
		event_type=EVENT_CLOSED,
		actor=frappe.session.user,
		correlation_id=(payload.get("idempotency_key") or frappe.generate_hash(length=12)),
		calling_module="Budget & Funding",
	)
	version.reload()
	return {"ok": True, "version": _version_summary(version), "closure": _closure_status_for(doc, version)}
