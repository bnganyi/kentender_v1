"""Greenfield Departmental Need to Procurement Planning allocation contract."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_core.services.authorization_policy import ResourceContext, require_capability
from kentender_procurement.departmental_needs.constants import CAP_ALLOCATE, CAP_PLANNING_READ, STATE_ACCEPTED
from kentender_procurement.procurement_planning.services._invariants import assert_version_concurrency, new_concurrency_token


def _actor(user: str | None) -> str:
	return cstr(user or frappe.session.user).strip()


def _plan_context(plan) -> ResourceContext:
	return ResourceContext("Procurement Plan", plan.name, plan.procuring_entity, plan.financial_year)


def list_eligible_needs(*, plan: str, user: str | None = None) -> dict[str, Any]:
	principal = _actor(user)
	plan_doc = frappe.get_doc("Procurement Plan", plan)
	require_capability(principal, CAP_PLANNING_READ, _plan_context(plan_doc))
	rows = frappe.get_all("Departmental Need", filters={
		"procuring_entity": plan_doc.procuring_entity,
		"target_financial_year": plan_doc.financial_year,
		"status": STATE_ACCEPTED,
	}, fields=["name", "need_reference", "title", "organisation_unit", "required_by_date"], order_by="need_reference asc")
	out = []
	for need in rows:
		require_capability(principal, CAP_PLANNING_READ, ResourceContext("Departmental Need", need.name, plan_doc.procuring_entity, plan_doc.financial_year, need.organisation_unit))
		items = []
		for item in frappe.get_all("Departmental Need Item", filters={"departmental_need": need.name}, fields=["name", "item_reference", "description", "indicative_quantity", "unit"], order_by="line_number asc"):
			held = flt(frappe.db.sql("select coalesce(sum(allocated_quantity),0) from `tabPlan Need Allocation` where departmental_need_item=%s and status in ('Draft','Effective')", item.name)[0][0])
			available = max(0.0, flt(item.indicative_quantity) - held)
			if available:
				items.append({"id": item.name, "reference": item.item_reference, "description": item.description, "quantity": flt(item.indicative_quantity), "unit": item.unit, "available_quantity": available})
		if items:
			out.append({"need": need.name, "reference": need.need_reference, "title": need.title, "organisation_unit": need.organisation_unit, "required_by": str(need.required_by_date or ""), "items": items})
	return {"ok": True, "plan": plan_doc.name, "needs": out, "eligible_need_count": len(out)}


def _parse(value) -> list[dict[str, Any]]:
	rows = json.loads(value) if isinstance(value, str) else value
	if not isinstance(rows, list) or not rows:
		frappe.throw("At least one Need-line allocation is required.", title="NDS_ALLOCATION_REQUIRED")
	return rows


def allocate_need_lines(*, plan: str, plan_item: str, allocations, expected_version_token: str,
	idempotency_key: str, reason: str = "", user: str | None = None) -> dict[str, Any]:
	principal, key = _actor(user), cstr(idempotency_key).strip()
	if not key:
		frappe.throw("An idempotency key is required.", title="NDS_IDEMPOTENCY_KEY_REQUIRED")
	existing = frappe.get_all("Plan Need Allocation", filters={"idempotency_key": ["like", f"{key}:%"]}, pluck="name")
	if existing:
		return {"ok": True, "idempotent": True, "allocations": existing}
	plan_doc = frappe.get_doc("Procurement Plan", plan)
	item = frappe.get_doc("Procurement Plan Item", plan_item)
	if item.plan != plan_doc.name:
		frappe.throw("Plan Item does not belong to the selected Plan.", title="NDS_PLAN_ITEM_MISMATCH")
	version_name = cstr(plan_doc.open_draft_version)
	if not version_name:
		frappe.throw("The Plan has no open Draft Version.", title="NDS_PLAN_DRAFT_REQUIRED")
	require_capability(principal, CAP_ALLOCATE, _plan_context(plan_doc))
	frappe.db.sql("select name from `tabProcurement Plan Version` where name=%s for update", version_name)
	assert_version_concurrency(version_name, expected_version_token)
	rows = _parse(allocations)
	created = []
	for index, row in enumerate(rows, 1):
		line_name, quantity = cstr(row.get("departmental_need_item")), flt(row.get("allocated_quantity"))
		line = frappe.db.get_value("Departmental Need Item", line_name, ["departmental_need", "indicative_quantity"], as_dict=True)
		if not line or quantity <= 0:
			frappe.throw("Each allocation requires a valid Need line and positive quantity.", title="NDS_ALLOCATION_INVALID")
		need = frappe.get_doc("Departmental Need", line.departmental_need)
		if need.status != STATE_ACCEPTED or need.procuring_entity != plan_doc.procuring_entity or need.target_financial_year != plan_doc.financial_year:
			frappe.throw("The Departmental Need is not eligible for this Plan.", title="NDS_NEED_NOT_ELIGIBLE")
		require_capability(principal, CAP_ALLOCATE, ResourceContext("Departmental Need", need.name, plan_doc.procuring_entity, plan_doc.financial_year, need.organisation_unit))
		frappe.db.sql("select name from `tabDepartmental Need Item` where name=%s for update", line_name)
		frappe.db.sql("select name from `tabPlan Need Allocation` where departmental_need_item=%s and status in ('Draft','Effective') for update", line_name)
		held = flt(frappe.db.sql("select coalesce(sum(allocated_quantity),0) from `tabPlan Need Allocation` where departmental_need_item=%s and status in ('Draft','Effective')", line_name)[0][0])
		if held + quantity > flt(line.indicative_quantity):
			frappe.throw("Allocation exceeds the available source Need-line quantity.", title="NDS_ALLOCATION_EXCEEDS_AVAILABLE")
		allocation = frappe.get_doc({
			"doctype": "Plan Need Allocation", "plan_item": item.name,
			"departmental_need": need.name, "departmental_need_item": line_name,
			"source_organisation_unit": need.organisation_unit, "allocated_quantity": quantity,
			"status": "Draft", "proposed_in_version": version_name, "reason": cstr(reason),
			"idempotency_key": f"{key}:{index}",
		}).insert(ignore_permissions=True)
		created.append(allocation.name)
	new_token = new_concurrency_token()
	frappe.db.set_value("Procurement Plan Version", version_name, "concurrency_token", new_token, update_modified=True)
	return {"ok": True, "idempotent": False, "plan": plan_doc.name, "plan_item": item.name, "allocations": created, "concurrency_token": new_token}


def activate_need_allocations(*, version: str) -> list[str]:
	rows = frappe.get_all("Plan Need Allocation", filters={"proposed_in_version": version, "status": "Draft"}, pluck="name")
	if not rows:
		return []
	frappe.db.sql("select name from `tabPlan Need Allocation` where name in %(names)s for update", {"names": rows})
	by_line: dict[str, float] = defaultdict(float)
	for name in rows:
		allocation = frappe.get_doc("Plan Need Allocation", name)
		by_line[allocation.departmental_need_item] += flt(allocation.allocated_quantity)
	for line_name, draft_quantity in by_line.items():
		line_quantity = flt(frappe.db.get_value("Departmental Need Item", line_name, "indicative_quantity"))
		effective = flt(frappe.db.sql("select coalesce(sum(allocated_quantity),0) from `tabPlan Need Allocation` where departmental_need_item=%s and status='Effective'", line_name)[0][0])
		if effective + draft_quantity > line_quantity:
			frappe.throw("Approved allocation would exceed the source Need-line quantity.", title="NDS_EFFECTIVE_ALLOCATION_EXCEEDS_LINE")
	now = now_datetime()
	for name in rows:
		frappe.db.set_value("Plan Need Allocation", name, {"status": "Effective", "effective_from_version": version, "effective_at": now}, update_modified=True)
	return rows


def reverse_need_allocations(*, plan_item: str, version: str, reason: str) -> list[str]:
	rows = frappe.get_all("Plan Need Allocation", filters={"plan_item": plan_item, "status": ["in", ["Draft", "Effective"]]}, pluck="name")
	now = now_datetime()
	for name in rows:
		frappe.db.set_value("Plan Need Allocation", name, {"status": "Reversed", "reversed_by_version": version, "reversed_at": now, "reason": reason}, update_modified=True)
	return rows
