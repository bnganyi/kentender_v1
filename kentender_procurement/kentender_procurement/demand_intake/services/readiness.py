# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DIA staged readiness — draft save, submission, review, planning handoff (UI refactor §23–24)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate


def _check(id: str, label: str, ok: bool, *, required: bool = True) -> dict[str, Any]:
	return {"id": id, "label": label, "ok": bool(ok), "required": required}


def evaluate_draft_save(doc) -> dict[str, Any]:
	"""Minimal draft save contract — title only (UI refactor §24.1)."""
	checks: list[dict[str, Any]] = [
		_check("title", _("Title provided"), bool((doc.title or "").strip())),
	]
	required_checks = [c for c in checks if c.get("required")]
	ready = all(c["ok"] for c in required_checks)
	return {"ready": ready, "checks": checks}


def assert_draft_save(doc) -> None:
	"""Raise ValidationError when draft save contract fails."""
	result = evaluate_draft_save(doc)
	if result.get("ready"):
		return
	for check in result.get("checks") or []:
		if check.get("required") and not check.get("ok"):
			frappe.throw(_(check.get("label") or _("Demand draft cannot be saved.")), title=_("Cannot save draft"))


def _item_row_checks(doc) -> list[dict[str, Any]]:
	"""Per-row line item validation for submission (§24.2)."""
	checks: list[dict[str, Any]] = []
	rows = doc.get("items") or []
	if not rows:
		checks.append(_check("line_items", _("At least one line item entered"), False))
		return checks

	checks.append(_check("line_items", _("At least one line item entered"), True))

	desc_ok = all((getattr(r, "item_description", None) or "").strip() for r in rows)
	checks.append(_check("item_description", _("Each line item has a description"), desc_ok))

	category_ok = all((getattr(r, "category", None) or "").strip() for r in rows)
	checks.append(_check("item_category", _("Each line item has a category"), category_ok))

	uom_ok = all((getattr(r, "uom", None) or "").strip() for r in rows)
	checks.append(_check("item_uom", _("Each line item has a unit of measure"), uom_ok))

	qty_ok = all(flt(getattr(r, "quantity", None)) > 0 for r in rows)
	checks.append(_check("item_quantity", _("Each line item quantity is greater than zero"), qty_ok))

	cost_ok = all(flt(getattr(r, "estimated_unit_cost", None)) >= 0 for r in rows)
	checks.append(_check("item_unit_cost", _("Each line item unit cost is zero or greater"), cost_ok))

	return checks


def evaluate_submission_readiness(doc) -> dict[str, Any]:
	"""Requester completeness for Submit for Approval (budget/strategy optional)."""
	checks: list[dict[str, Any]] = []

	checks.append(_check("title", _("Title provided"), bool((doc.title or "").strip())))
	checks.append(_check("department", _("Department selected"), bool(doc.requesting_department)))
	checks.append(_check("procuring_entity", _("Procuring entity selected"), bool(doc.procuring_entity)))
	checks.append(_check("requester", _("Requester assigned"), bool(doc.requested_by)))
	checks.append(
		_check(
			"dates",
			_("Request date and required-by date provided"),
			bool(doc.request_date and doc.required_by_date),
		)
	)
	checks.append(
		_check(
			"demand_type",
			_("Demand type selected"),
			bool((doc.demand_type or "").strip()),
		)
	)
	checks.append(
		_check(
			"requisition_type",
			_("Demand category selected"),
			bool((doc.requisition_type or "").strip()),
		)
	)
	checks.append(
		_check(
			"priority_level",
			_("Priority selected"),
			bool((doc.priority_level or "").strip()),
		)
	)
	checks.extend(_item_row_checks(doc))
	checks.append(
		_check(
			"total_amount",
			_("Total requested amount is greater than zero"),
			flt(doc.total_amount) > 0,
		)
	)
	checks.append(
		_check(
			"beneficiary_summary",
			_("Business justification provided"),
			bool((doc.beneficiary_summary or "").strip()),
		)
	)
	checks.append(
		_check(
			"specification_summary",
			_("Scope / requested outcome provided"),
			bool((doc.specification_summary or "").strip()),
		)
	)

	demand_type = (doc.demand_type or "Planned").strip()
	if demand_type == "Emergency":
		checks.append(
			_check(
				"emergency_justification",
				_("Emergency justification provided"),
				bool((doc.emergency_justification or "").strip()),
			)
		)

	if doc.request_date and doc.required_by_date and demand_type != "Emergency":
		rd = getdate(doc.required_by_date)
		rq = getdate(doc.request_date)
		checks.append(
			_check(
				"required_by_date",
				_("Required-by date is on or after request date"),
				rd >= rq,
			)
		)

	checks.append(
		_check(
			"budget_line",
			_("Budget line linked"),
			bool(doc.budget_line),
			required=False,
		)
	)
	checks.append(
		_check(
			"strategic_plan",
			_("Strategy linkage present"),
			bool(doc.strategic_plan),
			required=False,
		)
	)

	required_checks = [c for c in checks if c.get("required")]
	ready = all(c["ok"] for c in required_checks)
	return {"ready": ready, "checks": checks}


def evaluate_review_action(doc, *, action: str) -> dict[str, Any]:
	"""Review-stage checks for approve / return / reject (§24.3)."""
	action = (action or "").strip().lower()
	checks: list[dict[str, Any]] = []

	if action in ("return", "reject", "return_from_hod", "reject_from_hod", "return_from_finance", "reject_from_finance"):
		checks.append(
			_check(
				"reason",
				_("Reason provided"),
				False,
				required=True,
			)
		)
		return {"ready": False, "checks": checks, "action": action}

	if action in ("approve", "approve_hod", "approve_finance"):
		sub = evaluate_submission_readiness(doc)
		checks.append(
			_check(
				"submission_complete",
				_("Requester submission requirements met"),
				bool(sub.get("ready")),
			)
		)
		if action == "approve_finance":
			checks.append(_check("budget_line", _("Budget line linked for finance approval"), bool(doc.budget_line)))
		ready = all(c["ok"] for c in checks if c.get("required"))
		return {"ready": ready, "checks": checks, "action": action}

	return {"ready": True, "checks": checks, "action": action}


def assert_review_approve_ready(doc, *, action: str = "approve") -> None:
	result = evaluate_review_action(doc, action=action)
	if result.get("ready"):
		return
	for check in result.get("checks") or []:
		if check.get("required") and not check.get("ok"):
			frappe.throw(_(check.get("label") or _("Review action is not allowed.")), title=_("Review validation"))


def evaluate_approval_integrity(doc) -> dict[str, Any]:
	"""Approved demands must carry finance reservation metadata (Phase L1)."""
	status = (doc.status or "").strip()
	blockers: list[dict[str, Any]] = []
	if status == "Approved":
		approval_ok = bool(doc.hod_approved_by and doc.finance_approved_by)
		blockers.append(
			{
				"id": "approval_complete",
				"label": _("Approval complete"),
				"ok": approval_ok,
				"owner": _("HoD + Finance"),
				"action_hint": None,
			}
		)
		if doc.budget_line:
			reservation = (doc.reservation_status or "None").strip()
			res_ref = (doc.reservation_reference or "").strip()
			reservation_ok = reservation == "Reserved" and bool(res_ref)
			blockers.append(
				{
					"id": "budget_reservation",
					"label": _("Budget reservation is in place"),
					"ok": reservation_ok,
					"owner": _("Finance"),
					"action_hint": _("Send back to Finance for budget reservation"),
				}
			)
	open_blockers = [b for b in blockers if not b.get("ok")]
	return {
		"blocked": bool(open_blockers),
		"blocker_count": len(open_blockers),
		"blockers": blockers,
	}


def evaluate_planning_panel_checks(doc) -> dict[str, Any]:
	"""Planning tab ownership table — maps readiness + integrity to owner/action rows."""
	integrity = evaluate_approval_integrity(doc)
	planning = evaluate_planning_readiness(doc)
	status = (doc.status or "").strip()

	approval_blocker = next((b for b in integrity.get("blockers") or [] if b.get("id") == "approval_complete"), None)
	reservation_blocker = next(
		(b for b in integrity.get("blockers") or [] if b.get("id") == "budget_reservation"), None
	)
	planning_ready = bool(planning.get("ready")) and not integrity.get("blocked")

	strategy_ok = False
	if doc.budget_line:
		try:
			from kentender_budget.api.dia_budget_control import get_budget_line_context

			ctx = get_budget_line_context(doc.budget_line)
			if ctx.get("ok"):
				strategy_ok = bool((ctx.get("data") or {}).get("strategic_plan"))
		except Exception:
			pass

	checks: list[dict[str, Any]] = [
		{
			"id": "approval_complete",
			"requirement": _("Approval complete"),
			"status_label": _("Complete") if approval_blocker and approval_blocker.get("ok") else _("Missing"),
			"ok": bool(approval_blocker and approval_blocker.get("ok")),
			"owner": _("HoD + Finance"),
			"action_id": None,
			"action_label": None,
		},
		{
			"id": "budget_reservation",
			"requirement": _("Budget reservation"),
			"status_label": _("Complete")
			if reservation_blocker and reservation_blocker.get("ok")
			else _("Missing"),
			"ok": bool(reservation_blocker and reservation_blocker.get("ok")),
			"owner": _("Finance"),
			"action_id": "return_approved_to_finance" if reservation_blocker and not reservation_blocker.get("ok") else None,
			"action_label": _("Send back to Finance") if reservation_blocker and not reservation_blocker.get("ok") else None,
		},
		{
			"id": "strategy_linkage",
			"requirement": _("Strategy linkage"),
			"status_label": _("Complete") if strategy_ok else _("Missing"),
			"ok": strategy_ok,
			"owner": _("System/Finance"),
			"action_id": None,
			"action_label": None,
		},
		{
			"id": "budget_line",
			"requirement": _("Budget line"),
			"status_label": _("Complete") if doc.budget_line else _("Missing"),
			"ok": bool(doc.budget_line),
			"owner": _("Finance"),
			"action_id": None,
			"action_label": None,
		},
		{
			"id": "planning_handoff",
			"requirement": _("Planning handoff"),
			"status_label": _("Ready") if planning_ready else _("Pending"),
			"ok": planning_ready,
			"owner": _("System"),
			"action_id": None,
			"action_label": None,
		},
	]
	if status == "Planning Ready":
		for row in checks:
			if row["id"] == "planning_handoff":
				row["status_label"] = _("Ready")
				row["ok"] = True
	return {
		"integrity_blocked": bool(integrity.get("blocked")),
		"planning_ready": planning_ready,
		"checks": checks,
		"integrity_blockers": integrity.get("blockers") or [],
	}


def evaluate_planning_handoff_readiness(doc) -> dict[str, Any]:
	"""Planner enrichment before planning handoff actions (§24.4)."""
	checks: list[dict[str, Any]] = []

	checks.append(
		_check(
			"approved",
			_("Demand is finance-approved"),
			(doc.status or "") == "Approved",
		)
	)
	checks.append(_check("budget_line", _("Budget line linked"), bool(doc.budget_line)))
	checks.append(_check("delivery_location", _("Delivery location provided"), bool((doc.delivery_location or "").strip())))

	budget_line_ok = False
	strategy_ok = False
	budget_available_ok = False
	if doc.budget_line:
		try:
			from kentender_budget.api.dia_budget_control import check_available_budget, get_budget_line_context

			ctx = get_budget_line_context(doc.budget_line)
			if ctx.get("ok"):
				data = ctx.get("data") or {}
				budget_line_ok = True
				strategy_ok = bool(data.get("strategic_plan"))
				if doc.procuring_entity and data.get("procuring_entity") != doc.procuring_entity:
					budget_line_ok = False
				if budget_line_ok and flt(doc.total_amount) > 0:
					chk = check_available_budget(doc.budget_line, flt(doc.total_amount))
					budget_available_ok = bool(chk.get("ok"))
		except Exception:
			pass

	checks.append(_check("budget_line_valid", _("Budget line is valid for this demand"), budget_line_ok))
	checks.append(_check("strategy_linkage", _("Strategy linkage resolved from budget line"), strategy_ok))
	checks.append(
		_check(
			"budget_availability",
			_("Sufficient budget available for requested amount"),
			budget_available_ok,
		)
	)

	reservation = (doc.reservation_status or "None").strip()
	reservation_ok = reservation in ("Reserved", "None", "Released")
	checks.append(
		_check(
			"reservation_status",
			_("Budget reservation is in place or not required yet"),
			reservation_ok,
		)
	)

	required_checks = [c for c in checks if c.get("required")]
	ready = all(c["ok"] for c in required_checks)
	return {"ready": ready, "checks": checks}


def evaluate_planning_readiness(doc) -> dict[str, Any]:
	"""Planner/budget completeness before Mark Planning Ready (§24.5)."""
	checks: list[dict[str, Any]] = []

	checks.append(
		_check(
			"approved",
			_("Demand is finance-approved"),
			(doc.status or "") == "Approved",
		)
	)
	checks.append(_check("budget_line", _("Budget line linked"), bool(doc.budget_line)))

	budget_line_ok = False
	strategy_ok = False
	budget_available_ok = False
	if doc.budget_line:
		try:
			from kentender_budget.api.dia_budget_control import check_available_budget, get_budget_line_context

			ctx = get_budget_line_context(doc.budget_line)
			if ctx.get("ok"):
				data = ctx.get("data") or {}
				budget_line_ok = True
				strategy_ok = bool(data.get("strategic_plan"))
				if doc.procuring_entity and data.get("procuring_entity") != doc.procuring_entity:
					budget_line_ok = False
				if budget_line_ok and flt(doc.total_amount) > 0:
					chk = check_available_budget(doc.budget_line, flt(doc.total_amount))
					budget_available_ok = bool(chk.get("ok"))
		except Exception:
			pass

	checks.append(_check("budget_line_valid", _("Budget line is valid for this demand"), budget_line_ok))
	checks.append(_check("strategy_linkage", _("Strategy linkage resolved from budget line"), strategy_ok))
	checks.append(
		_check(
			"budget_availability",
			_("Sufficient budget available for requested amount"),
			budget_available_ok,
		)
	)

	reservation = (doc.reservation_status or "None").strip()
	reservation_ok = reservation in ("Reserved", "None", "Released")
	if (doc.status or "") == "Approved" and doc.budget_line:
		reservation_ok = reservation == "Reserved"
	checks.append(
		_check(
			"reservation_status",
			_("Budget reservation is in place"),
			reservation_ok,
		)
	)

	required_checks = [c for c in checks if c.get("required")]
	ready = all(c["ok"] for c in required_checks)
	return {"ready": ready, "checks": checks}


def assert_submission_ready(doc) -> None:
	"""Raise ValidationError when submission readiness fails."""
	result = evaluate_submission_readiness(doc)
	if result.get("ready"):
		return
	for check in result.get("checks") or []:
		if check.get("required") and not check.get("ok"):
			frappe.throw(_(check.get("label") or _("Demand is not ready to submit.")), title=_("Cannot submit"))


def assert_planning_handoff_ready(doc) -> None:
	"""Raise ValidationError when planning handoff readiness fails."""
	result = evaluate_planning_handoff_readiness(doc)
	if result.get("ready"):
		return
	for check in result.get("checks") or []:
		if check.get("required") and not check.get("ok"):
			frappe.throw(
				_(check.get("label") or _("Demand is not ready for planning handoff.")),
				title=_("Planning handoff"),
			)


def assert_planning_ready(doc) -> None:
	"""Raise ValidationError when planning readiness fails."""
	result = evaluate_planning_readiness(doc)
	if result.get("ready"):
		return
	for check in result.get("checks") or []:
		if check.get("required") and not check.get("ok"):
			frappe.throw(
				_(check.get("label") or _("Demand is not ready for planning handoff.")),
				title=_("Planning readiness"),
			)
