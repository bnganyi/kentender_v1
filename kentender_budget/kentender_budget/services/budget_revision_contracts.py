# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Budget Revision contracts — BUD-UI-08/09 / BUD-FR-090–099 / AC-016–018."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, formatdate, getdate, now_datetime

from kentender_budget.services.budget_contracts import (
	_resolve_budget,
	parse_money_amount,
	resolve_scoped_entity,
)
from kentender_budget.services.budget_line_contracts import format_kes_full
from kentender_budget.services.budget_permissions import (
	ROLE_AUDITOR,
	ROLE_AUTHORITY,
	ROLE_OFFICER,
	ROLE_REVIEWER,
	ROLE_VIEWER,
	can_register_budget,
	can_review_budget,
	require_any_role,
	user_roles,
)
from kentender_budget.services.budget_reference import allocate_budget_revision_reference

_READ_ROLES = (ROLE_OFFICER, ROLE_REVIEWER, ROLE_AUTHORITY, ROLE_VIEWER, ROLE_AUDITOR)
_WRITE_ROLES = (ROLE_OFFICER,)
_REVIEW_ROLES = (ROLE_REVIEWER, ROLE_AUTHORITY)
_APPLY_ROLES = (ROLE_AUTHORITY,)
_EDITABLE_STATUSES = ("Draft", "Returned")
_IMMUTABLE_STATUSES = ("Submitted", "Applied", "Rejected", "Cancelled")


def list_budget_revisions(budget: str) -> dict[str, Any]:
	"""Return revision list DTO for an Active (or any) Budget."""
	require_any_role(*_READ_ROLES)
	doc = _resolve_budget(budget)
	resolve_scoped_entity(doc.procuring_entity)
	currency = doc.currency or "KES"

	rows = []
	if frappe.db.exists("DocType", "Budget Revision"):
		for r in frappe.get_all(
			"Budget Revision",
			filters={"budget": doc.name},
			fields=[
				"name",
				"generated_reference",
				"status",
				"revision_type",
				"external_approval_reference",
				"approval_date",
				"effective_date",
				"reason",
				"creation",
				"modified",
				"submitted_by",
				"submitted_at",
			],
			order_by="modified desc",
		):
			line_count = frappe.db.count("Budget Revision Line", {"parent": r.name})
			change_total = _revision_change_total(r.name)
			open_action = ""
			action_label = ""
			if r.status in _EDITABLE_STATUSES:
				open_action = "edit"
				action_label = _("Edit revision")
			elif r.status == "Submitted":
				open_action = "review"
				action_label = _("Review revision")
			elif r.status in ("Applied", "Rejected"):
				open_action = "view"
				action_label = _("View revision")
			rows.append(
				{
					"id": r.name,
					"code": r.generated_reference,
					"status": r.status,
					"status_label": "Pending Review" if r.status == "Submitted" else r.status,
					"revision_type": r.revision_type,
					"external_approval_reference": r.external_approval_reference or "",
					"approval_date": formatdate(r.approval_date) if r.approval_date else "",
					"effective_date": formatdate(r.effective_date) if r.effective_date else "",
					"reason": (r.reason or "")[:160],
					"line_count": line_count,
					"change_total": change_total,
					"change_total_display": _signed_money(change_total, currency),
					"submitted_by": r.submitted_by or "",
					"submitted_at": str(r.submitted_at) if r.submitted_at else "",
					"open_action": open_action,
					"action_label": action_label,
				}
			)

	can_create = doc.status == "Active" and can_register_budget()
	primary = "request_revision" if doc.status == "Active" else ""
	return {
		"budget": {
			"id": doc.name,
			"code": doc.generated_reference,
			"name": doc.title,
			"title": doc.title,
			"status": doc.status,
			"status_label": "Under review" if doc.status == "Submitted" else doc.status,
			"currency": currency,
			"procuring_entity": doc.procuring_entity,
		},
		"rows": rows,
		"row_count": len(rows),
		"pagination": {
			"showing_from": 1 if rows else 0,
			"showing_to": len(rows),
			"total": len(rows),
			"label": f"Showing 1 to {len(rows)} of {len(rows)} entries" if rows else "Showing 0 entries",
		},
		"capabilities": {
			"primary_action": primary,
			"primary_label": "Request revision" if primary == "request_revision" else "",
			"can_create": can_create,
			"view_funding_performance": True,
			"read_only": not can_create,
		},
	}


def get_budget_revision_create_context(
	budget: str, revision: str | None = None
) -> dict[str, Any]:
	"""Lines + floors for Create revision canvas (Active only). Optional revision reopen."""
	require_any_role(*_WRITE_ROLES)
	doc = _resolve_budget(budget)
	resolve_scoped_entity(doc.procuring_entity)
	if doc.status != "Active":
		frappe.throw(
			_("Budget revisions can only be created for Active budgets"),
			frappe.ValidationError,
		)
	if not can_register_budget():
		frappe.throw(_("Not permitted to create budget revisions"), frappe.PermissionError)

	currency = doc.currency or "KES"
	existing = None
	revision_key = (revision or "").strip()
	if revision_key:
		existing = _resolve_revision(revision_key, budget_name=doc.name)
		if existing.status not in _EDITABLE_STATUSES:
			frappe.throw(
				_("Only Draft or Returned revisions can be reopened"),
				frappe.ValidationError,
			)

	change_by_line: dict[str, float] = {}
	if existing:
		for r in existing.lines:
			change_by_line[r.budget_line] = flt(r.change_amount)

	lines = []
	before_total = 0.0
	change_total = 0.0
	for line in frappe.get_all(
		"Budget Line",
		filters={"budget": doc.name, "is_active": 1},
		fields=[
			"name",
			"generated_reference",
			"title",
			"approved_amount",
			"amount_reserved",
			"amount_committed",
		],
		order_by="order_index asc, generated_reference asc",
	):
		before = flt(line.approved_amount)
		reserved = flt(line.amount_reserved)
		committed = flt(line.amount_committed)
		floor = reserved + committed
		change = flt(change_by_line.get(line.name) or 0)
		after = before + change
		before_total += before
		change_total += change
		lines.append(
			{
				"id": line.name,
				"code": line.generated_reference,
				"name": line.title,
				"title": line.title,
				"before_amount": before,
				"before_display": format_kes_full(before, currency=currency),
				"reserved": reserved,
				"reserved_display": format_kes_full(reserved, currency=currency),
				"committed": committed,
				"committed_display": format_kes_full(committed, currency=currency),
				"floor": floor,
				"floor_display": format_kes_full(floor, currency=currency),
				"change_amount": change,
				"after_amount": after,
				"after_display": format_kes_full(after, currency=currency),
				"impact_status": (
					"Increase" if change > 0 else ("Decrease" if change < 0 else "Balanced")
				),
			}
		)

	demand_count, tender_count = _downstream_impact_counts(doc.name)
	result = {
		"budget": {
			"id": doc.name,
			"code": doc.generated_reference,
			"name": doc.title,
			"title": doc.title,
			"status": doc.status,
			"currency": currency,
		},
		"lines": lines,
		"impact": {
			"before_total": before_total,
			"before_display": format_kes_full(before_total, currency=currency),
			"change_total": change_total,
			"change_display": _signed_money(change_total, currency),
			"after_total": before_total + change_total,
			"after_display": format_kes_full(before_total + change_total, currency=currency),
			"affected_demands": demand_count,
			"affected_tenders": tender_count,
		},
		"capabilities": {
			"can_save_draft": True,
			"can_submit": True,
			"constraint_note": _("Revised amount cannot be below Reserved + Committed."),
		},
		"revision": None,
	}
	if existing:
		result["revision"] = {
			"id": existing.name,
			"code": existing.generated_reference,
			"status": existing.status,
			"external_approval_reference": existing.external_approval_reference or "",
			"approval_date": str(existing.approval_date) if existing.approval_date else "",
			"effective_date": str(existing.effective_date) if existing.effective_date else "",
			"reason": existing.reason or "",
			"approval_evidence": existing.approval_evidence or "",
			"revision_type": existing.revision_type,
			"review_comment": existing.review_comment or "",
		}
	return result


def create_budget_revision(payload: dict | None = None) -> dict[str, Any]:
	"""Save a Draft Budget Revision (BUD-UI-08). Does not apply amounts."""
	require_any_role(*_WRITE_ROLES)
	if not can_register_budget():
		frappe.throw(_("Not permitted to create budget revisions"), frappe.PermissionError)

	payload = payload or {}
	doc = _resolve_budget(payload.get("budget") or "")
	resolve_scoped_entity(doc.procuring_entity)
	if doc.status != "Active":
		return {
			"ok": False,
			"errors": {"budget": _("Budget revisions can only be created for Active budgets")},
		}

	errors, line_rows, impact = _validate_revision_payload(doc, payload, require_submit_fields=False)
	if errors:
		return {"ok": False, "errors": errors}

	revision_name = (payload.get("revision") or payload.get("code") or "").strip()
	existing = None
	if revision_name:
		existing = _resolve_revision(revision_name, budget_name=doc.name)
		if existing.status not in _EDITABLE_STATUSES:
			return {
				"ok": False,
				"errors": {"status": _("Only Draft or Returned revisions can be edited")},
			}

	if existing:
		existing.update(
			{
				"external_approval_reference": (payload.get("external_approval_reference") or "").strip(),
				"approval_date": _optional_date(payload.get("approval_date")),
				"effective_date": _optional_date(payload.get("effective_date")),
				"reason": (payload.get("reason") or "").strip(),
				"approval_evidence": (payload.get("approval_evidence") or "").strip(),
				"revision_type": (payload.get("revision_type") or "Line amendment").strip()
				or "Line amendment",
				"lines": [],
			}
		)
		for row in line_rows:
			existing.append("lines", row)
		existing.save()
		rev = existing
	else:
		ref = allocate_budget_revision_reference(doc.procuring_entity)
		rev = frappe.get_doc(
			{
				"doctype": "Budget Revision",
				"budget": doc.name,
				"generated_reference": ref,
				"status": "Draft",
				"revision_type": (payload.get("revision_type") or "Line amendment").strip()
				or "Line amendment",
				"external_approval_reference": (payload.get("external_approval_reference") or "").strip(),
				"approval_date": _optional_date(payload.get("approval_date")),
				"effective_date": _optional_date(payload.get("effective_date")),
				"reason": (payload.get("reason") or "").strip(),
				"approval_evidence": (payload.get("approval_evidence") or "").strip(),
				"lines": line_rows,
			}
		)
		rev.insert()

	return {
		"ok": True,
		"revision": _revision_dto(rev, doc.currency or "KES", impact),
	}


def submit_budget_revision(payload: dict | str | None = None) -> dict[str, Any]:
	"""Submit a Draft/Returned revision for review (BUD-UI-08/09)."""
	require_any_role(*_WRITE_ROLES)
	if not can_register_budget():
		frappe.throw(_("Not permitted to submit budget revisions"), frappe.PermissionError)

	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	payload = payload or {}

	# Allow submit-with-payload (save then submit) or submit by code alone.
	if payload.get("budget") and (payload.get("lines") is not None or payload.get("external_approval_reference")):
		saved = create_budget_revision(payload)
		if not saved.get("ok"):
			return saved
		revision_key = saved["revision"]["code"]
	else:
		revision_key = (payload.get("revision") or payload.get("code") or "").strip()

	if not revision_key:
		return {"ok": False, "errors": {"revision": _("Revision is required")}}

	rev = _resolve_revision(revision_key)
	budget = frappe.get_doc("Budget", rev.budget)
	resolve_scoped_entity(budget.procuring_entity)

	if rev.status not in _EDITABLE_STATUSES:
		return {
			"ok": False,
			"errors": {"status": _("Only Draft or Returned revisions can be submitted")},
		}

	# Re-validate with submit-required fields + AC-016.
	payload_check = {
		"external_approval_reference": rev.external_approval_reference,
		"approval_date": rev.approval_date,
		"effective_date": rev.effective_date,
		"reason": rev.reason,
		"approval_evidence": rev.approval_evidence,
		"lines": [
			{
				"budget_line": r.budget_line,
				"change_amount": r.change_amount,
				"after_amount": r.after_amount,
			}
			for r in rev.lines
		],
	}
	errors, _rows, impact = _validate_revision_payload(
		budget, payload_check, require_submit_fields=True
	)
	if errors:
		return {"ok": False, "errors": errors}

	rev.status = "Submitted"
	rev.submitted_by = frappe.session.user
	rev.submitted_at = now_datetime()
	rev.review_comment = ""
	rev.save()

	from kentender_budget.services.budget_notification_service import (
		EVENT_REVISION_SUBMITTED,
		notify_budget_users,
	)

	notify_budget_users(
		EVENT_REVISION_SUBMITTED, budget_doc=budget, revision_doc=rev
	)

	return {
		"ok": True,
		"revision": _revision_dto(rev, budget.currency or "KES", impact),
	}


def get_budget_revision_review_context(revision: str) -> dict[str, Any]:
	"""Read-only review DTO for a Submitted (or terminal) Budget Revision — BUD-UI-09."""
	require_any_role(*_READ_ROLES)
	rev = _resolve_revision(revision)
	budget = frappe.get_doc("Budget", rev.budget)
	resolve_scoped_entity(budget.procuring_entity)
	currency = budget.currency or "KES"

	blockers, warnings, financial, strategy, downstream, lines = _build_review_groups(
		rev, budget, currency
	)
	roles = user_roles()
	is_authority = bool(roles.intersection({ROLE_AUTHORITY, "System Manager"})) or (
		frappe.session.user == "Administrator"
	)
	is_reviewer = can_review_budget()
	is_submitter = bool(rev.submitted_by) and rev.submitted_by == frappe.session.user
	can_apply = (
		rev.status == "Submitted"
		and is_authority
		and not is_submitter
		and not blockers
	)
	can_return = rev.status == "Submitted" and is_reviewer
	can_reject = rev.status == "Submitted" and is_authority

	status_label = "Pending Review" if rev.status == "Submitted" else rev.status
	return {
		"budget": {
			"id": budget.name,
			"code": budget.generated_reference,
			"name": budget.title,
			"title": budget.title,
			"status": budget.status,
			"currency": currency,
			"fiscal_period": budget.fiscal_period or "",
		},
		"revision": {
			"id": rev.name,
			"code": rev.generated_reference,
			"status": rev.status,
			"status_label": status_label,
			"revision_type": rev.revision_type,
			"external_approval_reference": rev.external_approval_reference or "",
			"approval_date": formatdate(rev.approval_date) if rev.approval_date else "",
			"approval_date_raw": str(rev.approval_date) if rev.approval_date else "",
			"effective_date": formatdate(rev.effective_date) if rev.effective_date else "",
			"effective_date_raw": str(rev.effective_date) if rev.effective_date else "",
			"reason": rev.reason or "",
			"approval_evidence": rev.approval_evidence or "",
			"submitted_by": rev.submitted_by or "",
			"submitted_at": str(rev.submitted_at) if rev.submitted_at else "",
			"submitted_at_display": (
				formatdate(rev.submitted_at) if rev.submitted_at else ""
			),
			"review_comment": rev.review_comment or "",
			"applied_by": rev.applied_by or "",
			"applied_at": str(rev.applied_at) if rev.applied_at else "",
		},
		"lines": lines,
		"financial": financial,
		"strategy": strategy,
		"downstream": downstream,
		"blockers": blockers,
		"warnings": warnings,
		"capabilities": {
			"can_apply": can_apply,
			"can_return": can_return,
			"can_reject": can_reject,
			"apply_locked_reason": (
				_("Resolve blockers to apply")
				if blockers
				else (
					_("Submitter cannot apply their own revision")
					if is_submitter and rev.status == "Submitted"
					else ""
				)
			),
			"primary_action": "apply_revision" if can_apply else "",
			"primary_label": "Apply revision" if can_apply else "Apply revision",
		},
	}


def review_budget_revision(revision: str | None = None) -> dict[str, Any]:
	"""Pack §8 alias for get_budget_revision_review_context."""
	return get_budget_revision_review_context(revision or "")


def return_budget_revision(payload: dict | str | None = None) -> dict[str, Any]:
	"""Submitted → Returned; Reviewer or Authority; comment required."""
	require_any_role(*_REVIEW_ROLES)
	if not can_review_budget():
		frappe.throw(_("Not permitted to return budget revisions"), frappe.PermissionError)

	payload = _as_dict(payload)
	rev, budget, err = _load_submitted_for_action(payload)
	if err:
		return err

	comment = (payload.get("comment") or payload.get("review_comment") or "").strip()
	if not comment:
		return {
			"ok": False,
			"errors": {"comment": _("Comment is required when returning a revision")},
		}

	rev.status = "Returned"
	rev.review_comment = comment
	rev.save(ignore_permissions=True)
	from kentender_budget.services.budget_notification_service import (
		EVENT_REVISION_RETURNED,
		notify_budget_users,
	)

	notify_budget_users(
		EVENT_REVISION_RETURNED, budget_doc=budget, revision_doc=rev
	)
	return {
		"ok": True,
		"revision": _revision_dto(rev, budget.currency or "KES"),
	}


def reject_budget_revision(payload: dict | str | None = None) -> dict[str, Any]:
	"""Submitted → Rejected; Authority; comment required."""
	require_any_role(*_APPLY_ROLES)
	roles = user_roles()
	if not (
		roles.intersection({ROLE_AUTHORITY, "System Manager"})
		or frappe.session.user == "Administrator"
	):
		frappe.throw(_("Not permitted to reject budget revisions"), frappe.PermissionError)

	payload = _as_dict(payload)
	rev, budget, err = _load_submitted_for_action(payload)
	if err:
		return err

	comment = (payload.get("comment") or payload.get("review_comment") or "").strip()
	if not comment:
		return {
			"ok": False,
			"errors": {"comment": _("Comment is required when rejecting a revision")},
		}

	rev.status = "Rejected"
	rev.review_comment = comment
	rev.save(ignore_permissions=True)
	from kentender_budget.services.budget_notification_service import (
		EVENT_REVISION_REJECTED,
		notify_budget_users,
	)

	notify_budget_users(
		EVENT_REVISION_REJECTED, budget_doc=budget, revision_doc=rev
	)
	return {
		"ok": True,
		"revision": _revision_dto(rev, budget.currency or "KES"),
	}


def apply_budget_revision(payload: dict | str | None = None) -> dict[str, Any]:
	"""Submitted → Applied; Authority; AC-016/018; atomic line updates."""
	require_any_role(*_APPLY_ROLES)
	roles = user_roles()
	if not (
		roles.intersection({ROLE_AUTHORITY, "System Manager"})
		or frappe.session.user == "Administrator"
	):
		frappe.throw(_("Not permitted to apply budget revisions"), frappe.PermissionError)

	payload = _as_dict(payload)
	rev, budget, err = _load_submitted_for_action(payload)
	if err:
		return err

	if rev.submitted_by and rev.submitted_by == frappe.session.user:
		return {
			"ok": False,
			"errors": {
				"status": _("Submitter cannot apply their own revision (AC-018)"),
			},
		}

	currency = budget.currency or "KES"
	blockers, _warnings, _fin, _strat, _down, _lines = _build_review_groups(
		rev, budget, currency
	)
	if blockers:
		return {
			"ok": False,
			"errors": {"blockers": blockers[0]["message"]},
			"blockers": blockers,
		}

	if not (rev.external_approval_reference or "").strip():
		return {
			"ok": False,
			"errors": {
				"external_approval_reference": _("External approval reference is required"),
			},
		}

	# Atomic apply — update lines then revision.
	try:
		for row in rev.lines:
			line = frappe.get_doc("Budget Line", row.budget_line)
			if line.budget != budget.name:
				frappe.throw(_("Revision line does not belong to this budget"))
			# Re-check live floor (AC-016).
			floor = flt(line.amount_reserved) + flt(line.amount_committed)
			after = flt(row.after_amount)
			if after < floor:
				frappe.throw(
					_(
						"{0}: revised amount ({1}) is below reserved + committed ({2})"
					).format(
						line.generated_reference,
						format_kes_full(after, currency=currency),
						format_kes_full(floor, currency=currency),
					),
					frappe.ValidationError,
				)
			line.approved_amount = after
			line.save(ignore_permissions=True)

		# Keep budget external total aligned with active lines.
		total = sum(
			flt(a)
			for a in frappe.get_all(
				"Budget Line",
				filters={"budget": budget.name, "is_active": 1},
				pluck="approved_amount",
			)
		)
		budget.external_approved_total = total
		budget.save(ignore_permissions=True)

		rev.status = "Applied"
		rev.applied_by = frappe.session.user
		rev.applied_at = now_datetime()
		rev.save(ignore_permissions=True)
	except Exception:
		frappe.db.rollback()
		raise

	from kentender_budget.services.budget_audit_contracts import (
		EVENT_REVISION,
		safe_record_event,
	)

	net = _revision_change_total(rev.name)
	safe_record_event(
		budget=budget.name,
		event_type=EVENT_REVISION,
		record_code=rev.generated_reference,
		record_doctype="Budget Revision",
		actor=frappe.session.user,
		actor_kind="user",
		before_summary="",
		after_summary=_signed_money(net, currency),
		change_summary=f"Net Change: {_signed_money(net, currency)}",
		source_reference=rev.external_approval_reference or "",
		reason=rev.reason or "",
	)
	from kentender_budget.services.budget_notification_service import (
		EVENT_REVISION_APPLIED,
		notify_budget_users,
	)

	notify_budget_users(
		EVENT_REVISION_APPLIED, budget_doc=budget, revision_doc=rev
	)

	return {
		"ok": True,
		"revision": _revision_dto(rev, currency),
		"budget": {
			"id": budget.name,
			"code": budget.generated_reference,
			"external_approved_total": flt(budget.external_approved_total),
			"external_approved_total_display": format_kes_full(
				budget.external_approved_total, currency=currency
			),
		},
	}


def _as_dict(payload: dict | str | None) -> dict:
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	return payload or {}


def _load_submitted_for_action(payload: dict):
	revision_key = (payload.get("revision") or payload.get("code") or "").strip()
	if not revision_key:
		return None, None, {"ok": False, "errors": {"revision": _("Revision is required")}}
	rev = _resolve_revision(revision_key)
	budget = frappe.get_doc("Budget", rev.budget)
	resolve_scoped_entity(budget.procuring_entity)
	if rev.status != "Submitted":
		return (
			None,
			None,
			{
				"ok": False,
				"errors": {"status": _("Only Submitted revisions can be reviewed")},
			},
		)
	return rev, budget, None


def _build_review_groups(rev, budget, currency: str):
	"""Compute blockers, warnings, and three review groups from live line state."""
	blockers: list[dict[str, Any]] = []
	warnings: list[dict[str, Any]] = []
	lines: list[dict[str, Any]] = []
	additions = 0.0
	deductions = 0.0
	change_total = 0.0
	before_total = 0.0
	after_total = 0.0

	for r in rev.lines:
		line = frappe.get_doc("Budget Line", r.budget_line) if r.budget_line else None
		reserved = flt(line.amount_reserved) if line else flt(r.reserved_snapshot)
		committed = flt(line.amount_committed) if line else flt(r.committed_snapshot)
		floor = reserved + committed
		before = flt(r.before_amount)
		change = flt(r.change_amount)
		after = flt(r.after_amount)
		before_total += before
		change_total += change
		after_total += after
		if change > 0:
			additions += change
		elif change < 0:
			deductions += abs(change)

		line_code = (line.generated_reference if line else r.line_code) or ""
		line_title = (line.title if line else r.line_title) or ""
		below = after < floor
		if below:
			msg = _(
				"Revised amount for '{0}' ({1}) is below the current Reserved + Committed total ({2}). You cannot reduce a budget line below its active obligations."
			).format(
				line_title or line_code,
				format_kes_full(after, currency=currency),
				format_kes_full(floor, currency=currency),
			)
			blockers.append(
				{
					"code": "AC-016",
					"line_code": line_code,
					"line_title": line_title,
					"after_amount": after,
					"after_display": format_kes_full(after, currency=currency),
					"floor": floor,
					"floor_display": format_kes_full(floor, currency=currency),
					"message": msg,
				}
			)

		lines.append(
			{
				"budget_line": r.budget_line,
				"code": line_code,
				"name": line_title,
				"before_amount": before,
				"before_display": format_kes_full(before, currency=currency),
				"change_amount": change,
				"change_display": _signed_money(change, currency),
				"after_amount": after,
				"after_display": format_kes_full(after, currency=currency),
				"reserved": reserved,
				"reserved_display": format_kes_full(reserved, currency=currency),
				"committed": committed,
				"committed_display": format_kes_full(committed, currency=currency),
				"floor": floor,
				"floor_display": format_kes_full(floor, currency=currency),
				"impact_status": "Below floor" if below else (r.impact_status or ""),
				"is_blocker": below,
			}
		)

	if not (rev.external_approval_reference or "").strip():
		blockers.append(
			{
				"code": "BUD-FR-092",
				"line_code": "",
				"line_title": "",
				"message": _("External approval reference is required before apply"),
			}
		)

	demand_count, tender_count, tender_cards = _downstream_review_cards(budget.name, currency)
	if change_total < -0.009 and (demand_count or tender_count):
		warnings.append(
			{
				"code": "DOWNSTREAM",
				"title": _("Downstream funding reduced"),
				"message": _(
					"This revision reduces approved funding while reservations or commitments exist."
				),
			}
		)

	balanced = abs(change_total) < 0.009
	financial = {
		"net_change": change_total,
		"net_change_display": (
			format_kes_full(0, currency=currency)
			if balanced
			else _signed_money(change_total, currency)
		),
		"balanced": balanced,
		"balance_label": "BALANCED" if balanced else ("INCREASE" if change_total > 0 else "DECREASE"),
		"additions": additions,
		"additions_display": format_kes_full(additions, currency=currency),
		"deductions": deductions,
		"deductions_display": format_kes_full(deductions, currency=currency),
		"before_total": before_total,
		"before_display": format_kes_full(before_total, currency=currency),
		"after_total": after_total,
		"after_display": format_kes_full(after_total, currency=currency),
	}

	strategy_items = [
		{
			"severity": "ok",
			"title": _("Line Strategy references preserved"),
			"message": _(
				"Budget Line identities and Strategy target links are unchanged by amount application."
			),
		}
	]
	if warnings:
		strategy_items.append(
			{
				"severity": "warning",
				"title": _("Review Strategy coverage after apply"),
				"message": _(
					"Funding reductions may affect Strategy Plan Value Commitment treatments."
				),
			}
		)
	strategy = {"items": strategy_items}
	downstream = {
		"affected_demands": demand_count,
		"affected_tenders": tender_count,
		"cards": tender_cards,
		"empty_message": (
			_("No linked reservations or commitments on this budget.")
			if not tender_cards and not demand_count
			else ""
		),
	}
	return blockers, warnings, financial, strategy, downstream, lines


def _downstream_review_cards(budget_name: str, currency: str) -> tuple[int, int, list[dict]]:
	demand_count, tender_count = _downstream_impact_counts(budget_name)
	cards: list[dict[str, Any]] = []
	if frappe.db.exists("DocType", "Funding Reservation"):
		rows = frappe.get_all(
			"Funding Reservation",
			filters={"budget": budget_name, "current_downstream_reference": ["!=", ""]},
			fields=["current_downstream_reference", "budget_line", "remaining_reserved"],
			limit=5,
		)
		seen: set[str] = set()
		for row in rows:
			ref = row.current_downstream_reference
			if not ref or ref in seen:
				continue
			seen.add(ref)
			line_title = ""
			if row.budget_line:
				line_title = frappe.db.get_value("Budget Line", row.budget_line, "title") or ""
			cards.append(
				{
					"kind": "reservation",
					"code": ref,
					"name": line_title or ref,
					"amount_display": format_kes_full(row.remaining_reserved or 0, currency=currency),
					"risk_message": _("Linked reservation may need release or reallocation after apply."),
				}
			)
	return demand_count, tender_count, cards


def _validate_revision_payload(
	budget,
	payload: dict,
	*,
	require_submit_fields: bool,
) -> tuple[dict[str, str], list[dict[str, Any]], dict[str, Any]]:
	errors: dict[str, str] = {}
	currency = budget.currency or "KES"

	ext_ref = (payload.get("external_approval_reference") or "").strip()
	reason = (payload.get("reason") or "").strip()
	approval_date = payload.get("approval_date")
	effective_date = payload.get("effective_date")

	if require_submit_fields:
		if not ext_ref:
			errors["external_approval_reference"] = _("External revision reference is required")
		if not approval_date:
			errors["approval_date"] = _("Approval date is required")
		else:
			try:
				getdate(approval_date)
			except Exception:
				errors["approval_date"] = _("Enter a valid approval date")
		if not effective_date:
			errors["effective_date"] = _("Effective date is required")
		else:
			try:
				getdate(effective_date)
			except Exception:
				errors["effective_date"] = _("Enter a valid effective date")
		if not reason:
			errors["reason"] = _("Reason is required")
		# Approval evidence is optional on create/submit.
	else:
		# Soft validate dates when provided on draft.
		for key in ("approval_date", "effective_date"):
			raw = payload.get(key)
			if raw:
				try:
					getdate(raw)
				except Exception:
					errors[key] = _("Enter a valid date")

	raw_lines = payload.get("lines") or []
	if not raw_lines:
		errors["lines"] = _("At least one line change is required")
		return errors, [], _empty_impact(currency)

	# Transfer balancing: multi-line with mixed signs that don't net (fail-closed for Transfer type).
	revision_type = (payload.get("revision_type") or "Line amendment").strip() or "Line amendment"

	line_rows: list[dict[str, Any]] = []
	before_total = 0.0
	change_total = 0.0
	after_total = 0.0
	floor_errors: list[str] = []

	seen_lines: set[str] = set()
	for idx, raw in enumerate(raw_lines):
		line_key = (raw.get("budget_line") or raw.get("line") or raw.get("code") or "").strip()
		line_doc = _resolve_line(budget.name, line_key)
		if not line_doc:
			errors[f"lines[{idx}]"] = _("Budget line is required")
			continue
		if line_doc.name in seen_lines:
			errors[f"lines[{idx}]"] = _("Duplicate line in revision")
			continue
		seen_lines.add(line_doc.name)

		before = flt(line_doc.approved_amount)
		reserved = flt(line_doc.amount_reserved)
		committed = flt(line_doc.amount_committed)
		floor = reserved + committed

		if raw.get("after_amount") is not None and str(raw.get("after_amount")).strip() != "":
			after = parse_money_amount(raw.get("after_amount"))
			if after is None:
				errors[f"lines[{idx}].after_amount"] = _("Enter a valid revised amount")
				continue
			change = after - before
		else:
			change = parse_money_amount(raw.get("change_amount"))
			if change is None:
				change = 0.0
			after = before + change

		if after < floor:
			# AC-016 / BUD-FR-095
			msg = _(
				"{0}: revised amount ({1}) is below reserved + committed ({2})"
			).format(
				line_doc.generated_reference,
				format_kes_full(after, currency=currency),
				format_kes_full(floor, currency=currency),
			)
			floor_errors.append(msg)
			errors[f"line:{line_doc.generated_reference}"] = msg
			impact_status = "Below floor"
		elif change > 0:
			impact_status = "Increase"
		elif change < 0:
			impact_status = "Decrease"
		else:
			impact_status = "Balanced"

		before_total += before
		change_total += change
		after_total += after
		line_rows.append(
			{
				"budget_line": line_doc.name,
				"line_code": line_doc.generated_reference,
				"line_title": line_doc.title,
				"before_amount": before,
				"change_amount": change,
				"after_amount": after,
				"reserved_snapshot": reserved,
				"committed_snapshot": committed,
				"impact_status": impact_status,
			}
		)

	if revision_type == "Transfer" and abs(change_total) > 0.009:
		errors["revision_type"] = _("Transfer revisions must balance to zero net change")

	if floor_errors and "lines" not in errors:
		errors["lines"] = floor_errors[0]

	# Draft may save with zero-change lines for scaffold; require at least one non-zero on submit.
	if require_submit_fields and line_rows and abs(change_total) < 0.009 and not floor_errors:
		errors["lines"] = _("Submit requires at least one non-zero line change")

	demand_count, tender_count = _downstream_impact_counts(budget.name)
	impact = {
		"before_total": before_total,
		"before_display": format_kes_full(before_total, currency=currency),
		"change_total": change_total,
		"change_display": _signed_money(change_total, currency),
		"after_total": after_total,
		"after_display": format_kes_full(after_total, currency=currency),
		"affected_demands": demand_count,
		"affected_tenders": tender_count,
	}
	return errors, line_rows, impact


def _revision_change_total(revision_name: str) -> float:
	total = 0.0
	for amt in frappe.get_all(
		"Budget Revision Line",
		filters={"parent": revision_name},
		pluck="change_amount",
	):
		total += flt(amt)
	return total


def _downstream_impact_counts(budget_name: str) -> tuple[int, int]:
	"""Demand / tender counts from existing §9.3 links when present."""
	demands = 0
	tenders = 0
	if frappe.db.exists("DocType", "Funding Reservation"):
		demands = frappe.db.count("Funding Reservation", {"budget": budget_name})
		# Distinct downstream tender refs on reservations.
		refs = frappe.get_all(
			"Funding Reservation",
			filters={"budget": budget_name, "current_downstream_reference": ["!=", ""]},
			pluck="current_downstream_reference",
		)
		tenders = len({r for r in refs if r})
	if frappe.db.exists("DocType", "Procurement Commitment") and not tenders:
		tenders = frappe.db.count("Procurement Commitment", {"budget": budget_name})
	return demands, tenders


def _resolve_line(budget_name: str, key: str):
	if not key:
		return None
	name = frappe.db.get_value(
		"Budget Line",
		{"budget": budget_name, "generated_reference": key},
		"name",
	)
	if not name and frappe.db.exists("Budget Line", key):
		line = frappe.get_doc("Budget Line", key)
		if line.budget == budget_name:
			return line
		return None
	if not name:
		return None
	return frappe.get_doc("Budget Line", name)


def _resolve_revision(key: str, budget_name: str | None = None):
	name = frappe.db.get_value("Budget Revision", {"generated_reference": key}, "name")
	if not name and frappe.db.exists("Budget Revision", key):
		name = key
	if not name:
		frappe.throw(_("Budget Revision {0} not found").format(key), frappe.DoesNotExistError)
	doc = frappe.get_doc("Budget Revision", name)
	if budget_name and doc.budget != budget_name:
		frappe.throw(_("Revision does not belong to this budget"), frappe.ValidationError)
	return doc


def _optional_date(raw):
	if not raw:
		return None
	return getdate(raw)


def _signed_money(amount: float, currency: str) -> str:
	amt = flt(amount)
	if amt > 0:
		return f"+ {format_kes_full(amt, currency=currency)}"
	if amt < 0:
		return f"- {format_kes_full(abs(amt), currency=currency)}"
	return format_kes_full(0, currency=currency)


def _empty_impact(currency: str) -> dict[str, Any]:
	return {
		"before_total": 0.0,
		"before_display": format_kes_full(0, currency=currency),
		"change_total": 0.0,
		"change_display": _signed_money(0.0, currency),
		"after_total": 0.0,
		"after_display": format_kes_full(0, currency=currency),
		"affected_demands": 0,
		"affected_tenders": 0,
	}


def _revision_dto(rev, currency: str, impact: dict[str, Any] | None = None) -> dict[str, Any]:
	lines = []
	for r in rev.lines:
		lines.append(
			{
				"budget_line": r.budget_line,
				"code": r.line_code,
				"name": r.line_title,
				"before_amount": flt(r.before_amount),
				"before_display": format_kes_full(r.before_amount, currency=currency),
				"change_amount": flt(r.change_amount),
				"change_display": _signed_money(flt(r.change_amount), currency),
				"after_amount": flt(r.after_amount),
				"after_display": format_kes_full(r.after_amount, currency=currency),
				"reserved": flt(r.reserved_snapshot),
				"reserved_display": format_kes_full(r.reserved_snapshot, currency=currency),
				"committed": flt(r.committed_snapshot),
				"committed_display": format_kes_full(r.committed_snapshot, currency=currency),
				"impact_status": r.impact_status,
			}
		)
	if impact is None:
		change_total = sum(flt(r.change_amount) for r in rev.lines)
		before_total = sum(flt(r.before_amount) for r in rev.lines)
		after_total = sum(flt(r.after_amount) for r in rev.lines)
		d, t = _downstream_impact_counts(rev.budget)
		impact = {
			"before_total": before_total,
			"before_display": format_kes_full(before_total, currency=currency),
			"change_total": change_total,
			"change_display": _signed_money(change_total, currency),
			"after_total": after_total,
			"after_display": format_kes_full(after_total, currency=currency),
			"affected_demands": d,
			"affected_tenders": t,
		}
	return {
		"id": rev.name,
		"code": rev.generated_reference,
		"status": rev.status,
		"revision_type": rev.revision_type,
		"external_approval_reference": rev.external_approval_reference or "",
		"approval_date": str(rev.approval_date) if rev.approval_date else "",
		"effective_date": str(rev.effective_date) if rev.effective_date else "",
		"reason": rev.reason or "",
		"approval_evidence": rev.approval_evidence or "",
		"submitted_by": rev.submitted_by or "",
		"submitted_at": str(rev.submitted_at) if rev.submitted_at else "",
		"review_comment": rev.review_comment or "",
		"applied_by": rev.applied_by or "",
		"applied_at": str(rev.applied_at) if rev.applied_at else "",
		"lines": lines,
		"impact": impact,
	}
