# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-UI-08 — consolidated plan review / approval read DTO."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, formatdate

from kentender_procurement.procurement_planning.mvp1_constants import (
	DOCTYPE_DECISION,
	FINANCE_CONFIRMED,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	VALIDATION_READY,
	VERSION_IN_REVIEW,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	CAP_PLAN_VIEW,
	actor_planning_roles,
	is_planning_read_only,
	require_capability,
)
from kentender_procurement.procurement_planning.services.plan_item_finance import (
	effective_finance_status,
)
from kentender_procurement.procurement_planning.services.preference_reservation import (
	COVERAGE_RATE,
	plan_coverage,
	scheme_is_assigned,
)
from kentender_procurement.procurement_planning.services.planning_tasks import assert_task_assignment
from kentender_procurement.procurement_planning.services.validate_plan import (
	effective_validation_status,
)


def _money(amount: float, currency: str) -> str:
	return f"{currency} {flt(amount):,.2f}"


def _ou_label(ou: str) -> str:
	if not ou:
		return ""
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)


def get_plan_review(*, task: str, user: str | None = None) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	if not actor or actor == "Guest":
		frappe.throw(
			frappe._("Login required."),
			frappe.PermissionError,
			title="PLN_LOGIN_REQUIRED",
		)

	task_id = cstr(task).strip()
	version_name = frappe.db.get_value("Procurement Plan Version", {"review_task_id": task_id}, "name")
	if not version_name:
		frappe.throw(frappe._("Task not found."), frappe.PermissionError, title="PLN_TASK_NOT_FOUND")
	task_version = frappe.get_doc("Procurement Plan Version", version_name)
	assert_task_assignment(record=task_version, task=task_id, id_field="review_task_id", assignee_field="review_task_assignee", state_field="review_task_state", actor=actor)
	plan_name = cstr(task_version.plan)

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	pe = cstr(plan_doc.procuring_entity).strip()
	ou = None
	# Record visibility first; task vs neutral branched below (PLN-FR-080…083).
	require_capability(
		CAP_PLAN_VIEW,
		procuring_entity=pe,
		org_unit=ou,
		user=actor,
		require_write=False,
	)

	focus = version_name
	if not focus:
		frappe.throw(frappe._("No Plan Version available for review."), title="PLN_VERSION_NOT_FOUND")

	ver = frappe.db.get_value(
		"Procurement Plan Version",
		focus,
		[
			"name",
			"version_code",
			"version_number",
			"status",
			"validation_projection",
			"concurrency_token",
		],
		as_dict=True,
	)
	if not ver:
		frappe.throw(frappe._("Plan Version not found."), title="PLN_VERSION_NOT_FOUND")

	surface = "task"

	currency = plan_doc.currency or "KES"
	items_out: list[dict[str, Any]] = []
	planned_total = 0.0
	open_tender_total = 0.0
	designation_values: list[float] = []

	for it in frappe.get_all(
		"Procurement Plan Item",
		filters={
			"plan": plan_name,
			"baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]],
		},
		fields=["name", "plan_item_code", "baseline_state", "owner_org_unit"],
		order_by="creation asc",
	):
		iv_name = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": it.name, "plan_version": focus},
			"name",
		)
		if not iv_name:
			continue
		iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
		amount = flt(iv.confirmed_estimate)
		planned_total += amount
		method = cstr(iv.procurement_method or "")
		if method.lower() == "open tender":
			open_tender_total += amount
		ou = cstr(it.owner_org_unit or "")
		if scheme_is_assigned(getattr(iv, "preference_reservation_scheme", None)):
			designation_values.append(flt(getattr(iv, "planned_reserved_value", 0)))
		completion = ""
		if iv.ms_delivery_completion:
			completion = formatdate(iv.ms_delivery_completion, "dd MMMM yyyy")
		validation = cstr(
			getattr(iv, "validation_projection", None) or ver.validation_projection or "Not run"
		)
		finance_status = effective_finance_status(iv)
		items_out.append(
			{
				"plan_item": it.name,
				"plan_item_code": it.plan_item_code,
				"baseline_state": cstr(it.baseline_state),
				"change_label": "Added" if cstr(it.baseline_state) == ITEM_PROPOSED else "Unchanged",
				"title": cstr(iv.requirement_title or it.plan_item_code),
				"owner_org_unit": ou,
				"owner_org_unit_label": _ou_label(ou),
				"amount": amount,
				"amount_display": _money(amount, currency),
				"method": method or "—",
				"completion": completion or "—",
				"validation_projection": validation,
				"finance_status": finance_status,
				"finance_status_label": finance_status,
				"editor_route": f"/app/procurement-plan-item-editor/{it.name}",
			}
		)

	finance_confirmed_count = sum(
		1 for i in items_out if cstr(i.get("finance_status")) == FINANCE_CONFIRMED
	)
	finance_item_count = len(items_out)
	finance_complete = bool(finance_item_count) and finance_confirmed_count == finance_item_count
	finance_confirmed_label = f"{finance_confirmed_count} of {finance_item_count}"

	ready_count = sum(
		1
		for i in items_out
		if cstr(i.get("validation_projection")) == VALIDATION_READY
	)

	coverage = plan_coverage(
		planned_total=planned_total,
		designation_values=designation_values,
		currency=currency,
	)
	statutory_rows: list[dict[str, Any]] = []
	if designation_values:
		required = flt(coverage.get("required"))
		planned_cov = flt(coverage.get("planned"))
		cov_status = cstr(coverage.get("status_label") or "")
		if cov_status == "Ready":
			cov_status = "Compliant"
		statutory_rows = [
			{
				"obligation": f"{int(COVERAGE_RATE * 100)}% AGPO Minimum",
				"required_treatment": f"{required:,.2f}",
				"planned_treatment": f"{planned_cov:,.2f}",
				"status": cov_status,
			}
		]

	validation = effective_validation_status(
		plan=plan_name, version=focus, stored=cstr(ver.validation_projection or "")
	)
	issues_ready = validation == VALIDATION_READY
	if issues_ready and finance_complete:
		issues_message = "All required planning and funding checks are ready for decision."
	elif not finance_complete:
		issues_message = (
			"Confirm current Finance for every included Plan Item before this decision."
		)
	else:
		issues_message = "Resolve validation issues before recording this decision."

	roles = actor_planning_roles(actor)
	read_only_actor = is_planning_read_only(actor)
	task_surface = surface == "task" and not read_only_actor
	can_return = task_surface and cstr(ver.status) == VERSION_IN_REVIEW
	can_approve = task_surface and cstr(ver.status) == VERSION_IN_REVIEW and issues_ready and finance_complete
	review_actions = [
		*([{"code": "approve", "label": "Approve update"}] if can_approve else []),
		*([{"code": "return", "label": "Return to planner"}] if can_return else []),
	]

	if not task_surface:
		rail_mode = "readonly"
		current_decision_label = (
			"In review" if cstr(ver.status) == VERSION_IN_REVIEW else cstr(ver.status)
		)
		primary_cta_label = ""
	elif can_approve or cstr(ver.status) == VERSION_IN_REVIEW:
		rail_mode = "approver"
		current_decision_label = "Professional review"
		primary_cta_label = "Approve update" if can_approve else ""
	else:
		rail_mode = "readonly"
		current_decision_label = (
			"In review" if cstr(ver.status) == VERSION_IN_REVIEW else cstr(ver.status)
		)
		primary_cta_label = ""

	authority_label = "Designated Approver"
	for role in ("Designated Approver", "Accounting Officer", "Planning Authority"):
		if role in roles:
			authority_label = role
			break

	pe_label = (
		frappe.db.get_value("Procuring Entity", plan_doc.procuring_entity, "entity_name")
		or plan_doc.procuring_entity
	)
	prepared_by = pe_label

	trail: list[dict[str, str]] = []
	for row in frappe.get_all(
		DOCTYPE_DECISION,
		filters={"plan_version": focus},
		fields=["decision", "actor", "actor_role", "decided_at", "reason"],
		order_by="decided_at desc",
		limit_page_length=20,
	):
		trail.append(
			{
				"label": cstr(row.decision),
				"actor": cstr(row.actor),
				"actor_role": cstr(row.actor_role or ""),
				"date": formatdate(row.decided_at, "dd MMMM yyyy") if row.decided_at else "",
				"reason": cstr(row.reason or ""),
			}
		)
	return {
		"ok": True,
		"surface": surface,
		"plan": plan_doc.name,
		"plan_code": plan_doc.plan_code,
		"title": plan_doc.title,
		"procuring_entity": plan_doc.procuring_entity,
		"procuring_entity_label": pe_label,
		"financial_year": plan_doc.financial_year,
		"version": ver.name,
		"version_number": int(ver.version_number or 1),
		"version_number_label": f"Version {int(ver.version_number or 1)}",
		"version_status": cstr(ver.status),
		"validation_projection": validation,
		"concurrency_token": cstr(ver.concurrency_token or ""),
		"task": task_id,
		"task_token": cstr(task_version.review_task_token),
		"task_iteration": int(task_version.review_task_iteration or 1),
		"submitted_by": cstr(task_version.submitted_by),
		"submitted_at": str(task_version.submitted_at or ""),
		"item_count": len(items_out),
		"planned_total": planned_total,
		"planned_total_display": _money(planned_total, currency),
		"finance_confirmed_count": finance_confirmed_count,
		"finance_item_count": finance_item_count,
		"finance_confirmed_label": finance_confirmed_label,
		"finance_complete": finance_complete,
		"finance_confirmation_label": "Complete" if finance_complete else "Incomplete",
		"contributions_label": finance_confirmed_label,
		"departmental_submission_label": (
			"Complete" if finance_complete else finance_confirmed_label
		),
		"open_tender_total": open_tender_total,
		"open_tender_display": _money(open_tender_total, currency),
		"items": items_out,
		"statutory_coverage": statutory_rows,
		"preference_reservation_coverage": coverage,
		"issues_ready": issues_ready,
		"issues_message": issues_message,
		"current_decision_label": current_decision_label,
		"prepared_by": prepared_by,
		"authority_label": authority_label,
		"rail_mode": rail_mode,
		"primary_cta_label": primary_cta_label,
		"prior_decision_trail": trail,
		"can_return": bool(can_return),
		"can_approve": bool(can_approve),
		"available_actions": review_actions,
		"read_only": (not task_surface) or rail_mode == "readonly",
		"builder_route": f"/app/procurement-plan-builder?plan={plan_name}",
		"workspace_route": "/app/planning-workspace",
		"secondary_line": (
			f"{cstr(plan_doc.title)} · {cstr(ver.status) or 'Draft'} Version {int(ver.version_number or 1)}"
		),
	}
