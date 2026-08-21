"""Atomic, idempotent annual Plan registration for PLN-UI-02."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_core.services.financial_context import procuring_entity_financial_context
from kentender_procurement.procurement_planning.mvp1_constants import PLAN_OPEN, PLAN_TYPE_ANNUAL, VALIDATION_NOT_RUN, VERSION_DRAFT
from kentender_procurement.procurement_planning.services._invariants import new_concurrency_token, next_plan_code
from kentender_procurement.procurement_planning.services.planning_permissions import assert_can_create_plan, assert_pe_resolved_for_create, assert_planning_scope


def _existing_result(pe: str, fy: str) -> dict[str, Any] | None:
	row = frappe.db.get_value(
		"Procurement Plan", {"procuring_entity": pe, "financial_year": fy},
		["name", "plan_code", "open_draft_version", "current_approved_version"], as_dict=True,
	)
	if not row:
		return None
	version = row.open_draft_version or row.current_approved_version
	return {
		"ok": True, "created": False, "plan": row.name, "plan_code": row.plan_code,
		"version": version, "route": f"/app/procurement-plan-builder?plan={row.name}",
		"message": "The annual Procurement Plan already exists. No duplicate was created.",
	}


def create_procurement_plan(*, procuring_entity: str, financial_year: str, user: str | None = None) -> dict[str, Any]:
	actor = assert_can_create_plan(user)
	selected_pe = cstr(procuring_entity).strip()
	selected_fy = cstr(financial_year).strip()
	if not selected_pe or not selected_fy:
		frappe.throw(
			frappe._("Explicit Procuring Entity and financial year context is required."),
			title="PLN_CREATE_CONTEXT_REQUIRED",
		)
	pe = assert_pe_resolved_for_create(user=actor, selected_pe=selected_pe)
	# Registration is PE-scoped. The Planner role supplies mutation capability;
	# the scope assignment need only authorise the explicitly selected PE. Item
	# formation remains independently constrained to writable source OUs.
	assert_planning_scope(procuring_entity=pe, user=actor, require_write=False)
	context = procuring_entity_financial_context(procuring_entity=pe, financial_year=selected_fy)
	if context["is_past"]:
		frappe.throw(frappe._("A new annual Plan cannot be registered for a past financial year."), title="PLN_FY_PAST")
	existing = _existing_result(pe, context["financial_year"])
	if existing:
		return existing
	lock_name = f"pln:create:{pe}:{context['financial_year']}"[:64]
	if not frappe.db.sql("select get_lock(%s, 10)", lock_name)[0][0]:
		frappe.throw(frappe._("Plan registration is busy. Try again."), title="PLN_CREATE_BUSY")
	try:
		existing = _existing_result(pe, context["financial_year"])
		if existing:
			return existing
		plan_code = next_plan_code(pe, context["financial_year"])
		plan = frappe.get_doc({
			"doctype": "Procurement Plan", "plan_code": plan_code, "title": context["title"],
			"procuring_entity": pe, "financial_year": context["financial_year"],
			"period_start": context["period_start"], "period_end": context["period_end"],
			"currency": context["currency"], "plan_type": PLAN_TYPE_ANNUAL,
			"lifecycle_state": PLAN_OPEN,
		}).insert(ignore_permissions=True)
		version_code = f"{plan_code}-V1"
		version = frappe.get_doc({
			"doctype": "Procurement Plan Version", "plan": plan.name, "version_number": 1,
			"version_code": version_code, "status": VERSION_DRAFT, "open_version_slot": plan.name,
			"version_reason": "Initial annual Plan registration", "validation_projection": VALIDATION_NOT_RUN,
			"concurrency_token": new_concurrency_token(),
		}).insert(ignore_permissions=True)
		frappe.db.set_value("Procurement Plan", plan.name, "open_draft_version", version.name, update_modified=False)
		frappe.get_doc({
			"doctype": "Plan Decision", "plan_version": version.name, "decision_type": "Registration",
			"decision_stage": "Annual Plan registration", "actor": actor, "actor_role": "Procurement Planner",
			"decision": "Registered", "reason": "Initial Draft Version 1 created from governed PE/FY context.",
			"decided_at": now_datetime(),
		}).insert(ignore_permissions=True)
		return {
			"ok": True, "created": True, "plan": plan.name, "plan_code": plan_code,
			"version": version.name, "version_code": version_code,
			"route": f"/app/procurement-plan-builder?plan={plan.name}",
			"message": "Annual Procurement Plan registered. Draft Version 1 is ready for planning.",
		}
	except frappe.DuplicateEntryError:
		existing = _existing_result(pe, context["financial_year"])
		if existing:
			return existing
		raise
	finally:
		frappe.db.sql("select release_lock(%s)", lock_name)
