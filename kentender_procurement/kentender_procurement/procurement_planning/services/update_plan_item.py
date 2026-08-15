# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-008 — strict, concurrency-safe PLN-UI-06 commands."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, getdate, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import VALIDATION_NOT_RUN, VALIDATION_READY, VERSION_EDITABLE_STATUSES
from kentender_procurement.procurement_planning.services._invariants import assert_version_concurrency, assert_version_mutable, new_concurrency_token
from kentender_procurement.procurement_planning.services.get_plan_item_editor import CATEGORY_OPTIONS
from kentender_procurement.procurement_planning.services.plan_item_field_issues import MILESTONE_FIELDS, collect_plan_item_field_issues
from kentender_procurement.procurement_planning.services.planning_permissions import assert_can_add_demand, assert_planning_scope

_WRITABLE = frozenset({
	"requirement_description", "procurement_category", "procurement_method", "arrangement",
	"multi_year_justification", "annual_funding_schedule", "lotting_decision",
	"expected_lot_count", "lot_basis", "schedule_change_reason", *MILESTONE_FIELDS,
})

HOD_IMMUTABLE_MSG = "Approved Demand source, scope, quantity, ownership, value and funding cannot be changed here in Planning."
STITCH_FINANCE_ISSUE = "Complete the required Plan Item fields and seven-date schedule before requesting Finance confirmation."


def _request_finance_issues(iv: Any, field_issues: dict[str, str]) -> dict[str, str]:
	extra = dict(field_issues or {})
	for key in ("requirement_description", "procurement_category", "procurement_method", "arrangement", "lotting_decision"):
		if not cstr(getattr(iv, key, None) or "").strip():
			extra[key] = STITCH_FINANCE_ISSUE
	for key in MILESTONE_FIELDS:
		if not getattr(iv, key, None):
			extra[key] = STITCH_FINANCE_ISSUE
	return extra


def _source_issues(*, plan: Any, plan_item: str) -> dict[str, str]:
	issues: dict[str, str] = {}
	for row in frappe.get_all("Plan Demand Allocation", filters={"plan_item": plan_item, "status": ["in", ["Draft", "Effective"]]}, fields=["demand", "demand_item"]):
		status = cstr(frappe.db.get_value("Demand", row.demand, "status") or "")
		if status != "Approved":
			issues["form"] = "Every source Demand must remain Approved before Finance confirmation."
			break
		required = frappe.db.get_value("Demand Item", row.demand_item, "required_by_date") or frappe.db.get_value("Demand", row.demand, "required_by_date")
		if required and (getdate(required) < getdate(plan.period_start) or getdate(required) > getdate(plan.period_end)):
			issues["form"] = "A source required-by date falls outside the governed Plan period."
			break
	return issues


def _marker_exists(plan_item: str, marker: str) -> bool:
	return bool(frappe.db.exists("Comment", {"reference_doctype": "Procurement Plan Item", "reference_name": plan_item, "content": marker}))


def update_plan_item(
	*, plan_item: str, fields: dict[str, Any] | None = None, user: str | None = None,
	request_finance: bool | int | None = None, expected_version_token: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	actor = assert_can_add_demand(user)
	item_name = cstr(plan_item).strip()
	payload = fields or {}
	key = cstr(idempotency_key or "").strip()
	if not key:
		return {"ok": False, "errors": {"form": "An idempotency key is required."}}
	if not item_name or not frappe.db.exists("Procurement Plan Item", item_name):
		return {"ok": False, "errors": {"form": "Plan Item not found."}}
	want_finance = bool(cint(request_finance))
	finance_savepoint = f"pln_ui06_{frappe.generate_hash(length=8)}" if want_finance else ""
	if finance_savepoint:
		frappe.db.savepoint(finance_savepoint)
	marker = f"PLN_ITEM_UPDATE|{'finance' if want_finance else 'save'}|{key}"
	if _marker_exists(item_name, marker):
		item = frappe.get_doc("Procurement Plan Item", item_name)
		plan = frappe.get_doc("Procurement Plan", item.plan)
		return {"ok": True, "idempotent": True, "plan_item": item_name, "finance_status": frappe.db.get_value("Procurement Plan Item Version", item.draft_item_version, "finance_status"), "concurrency_token": frappe.db.get_value("Procurement Plan Version", plan.open_draft_version, "concurrency_token")}

	unknown = sorted(set(payload) - _WRITABLE)
	if unknown:
		return {"ok": False, "error_code": "PLN_ITEM_FIELDS_NOT_PERMITTED", "errors": {key: HOD_IMMUTABLE_MSG for key in unknown}}
	method = cstr(payload.get("procurement_method") or "Open tender").strip()
	if method != "Open tender":
		return {"ok": False, "error_code": "PROCUREMENT_METHOD_NOT_CONFIGURED", "errors": {"procurement_method": "Only Open tender is configured for the MVP."}}
	category = cstr(payload.get("procurement_category") or "").strip()
	if category and category not in CATEGORY_OPTIONS:
		return {"ok": False, "error_code": "PROCUREMENT_CATEGORY_NOT_CONFIGURED", "errors": {"procurement_category": "Select an approved procurement category."}}

	item = frappe.get_doc("Procurement Plan Item", item_name)
	plan = frappe.get_doc("Procurement Plan", item.plan)
	assert_planning_scope(procuring_entity=cstr(plan.procuring_entity), org_unit=cstr(item.owner_org_unit or "") or None, user=actor, require_write=True)
	draft = cstr(plan.open_draft_version or "").strip()
	if not draft:
		return {"ok": False, "errors": {"form": "Open a Draft revision before editing items."}}
	frappe.db.sql("select name from `tabProcurement Plan Version` where name=%s for update", draft)
	assert_version_concurrency(draft, expected_version_token)
	ver = frappe.get_doc("Procurement Plan Version", draft)
	assert_version_mutable(ver.status)
	if cstr(ver.status) not in VERSION_EDITABLE_STATUSES:
		return {"ok": False, "errors": {"form": "Only Draft or Returned versions are editable."}}
	iv_name = cstr(item.draft_item_version or "").strip() or cstr(frappe.db.get_value("Procurement Plan Item Version", {"plan_item": item_name, "plan_version": draft}, "name") or "")
	if not iv_name:
		return {"ok": False, "errors": {"form": "Draft Plan Item Version not found."}}
	frappe.db.sql("select name from `tabProcurement Plan Item Version` where name=%s for update", iv_name)
	iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	if cstr(iv.finance_status) == "Awaiting confirmation":
		return {"ok": False, "error_code": "PLN_ITEM_AWAITING_FINANCE", "errors": {"form": "This Plan Item is read-only while Finance confirmation is awaiting action."}}

	field_issues = collect_plan_item_field_issues(iv=iv, payload=payload, include_preference=False)
	for field in _WRITABLE:
		if field not in payload:
			continue
		value = payload[field]
		if field == "expected_lot_count":
			try:
				value = int(value or 0)
			except (TypeError, ValueError):
				value = 0
		elif field in MILESTONE_FIELDS:
			try:
				value = getdate(value) if value else None
			except Exception:
				continue
		iv.set(field, value)
	iv.procurement_method = "Open tender"
	iv.validation_projection = VALIDATION_NOT_RUN
	iv.save(ignore_permissions=True)
	field_issues = collect_plan_item_field_issues(iv=iv, payload={}, include_preference=False)
	for milestone in MILESTONE_FIELDS:
		value = getattr(iv, milestone, None)
		if value and (getdate(value) < getdate(plan.period_start) or getdate(value) > getdate(plan.period_end)):
			field_issues[milestone] = "Milestone date must fall within the governed Plan period."
	if want_finance:
		field_issues.update(_source_issues(plan=plan, plan_item=item_name))
		field_issues = _request_finance_issues(iv, field_issues)
	if want_finance and field_issues:
		frappe.db.rollback(save_point=finance_savepoint)
		return {"ok": True, "complete": False, "field_issues": field_issues, "attention_message": STITCH_FINANCE_ISSUE, "plan_item": item_name, "item_version": iv.name, "concurrency_token": cstr(ver.concurrency_token)}

	finance_status = cstr(iv.finance_status or "Not requested")
	if want_finance:
		iv.validation_projection = VALIDATION_READY
		iv.save(ignore_permissions=True)
		from kentender_procurement.procurement_planning.services.plan_item_finance import request_plan_item_finance
		finance = request_plan_item_finance(plan_item=item_name, user=actor)
		if not finance.get("ok") or not finance.get("complete"):
			frappe.throw("Finance request could not be created.", title="PLN_FINANCE_REQUEST_FAILED")
		finance_status = cstr(finance.get("finance_status"))
	new_token = new_concurrency_token()
	frappe.db.set_value("Procurement Plan Version", draft, {"concurrency_token": new_token}, update_modified=True)
	frappe.get_doc({"doctype": "Comment", "comment_type": "Info", "reference_doctype": "Procurement Plan Item", "reference_name": item_name, "content": marker}).insert(ignore_permissions=True)
	frappe.get_doc({
		"doctype": "Plan Decision", "plan_version": draft, "plan_item": item_name,
		"decision_type": "Plan Item editor", "decision_stage": "Plan Item editor",
		"actor": actor, "actor_role": "Procurement Planner",
		"decision": "Finance requested" if want_finance else "Draft saved",
		"reason": "PLN-UI-06 command", "decided_at": now_datetime(),
	}).insert(ignore_permissions=True)
	return {
		"ok": True, "idempotent": False, "complete": want_finance,
		"plan": plan.name, "plan_item": item_name, "item_version": iv.name,
		"finance_status": finance_status, "field_issues": field_issues,
		"concurrency_token": new_token,
		"back_route": f"/app/procurement-plan-builder?plan={plan.name}",
	}
