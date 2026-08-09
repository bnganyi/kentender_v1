# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Minimal add Demand → Draft Plan Item + Draft allocation (Gate 01)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	ITEM_PROPOSED,
	VALIDATION_NOT_RUN,
	VERSION_EDITABLE_STATUSES,
)
from kentender_procurement.procurement_planning.services._invariants import (
	assert_version_mutable,
	next_plan_item_code,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_can_add_demand,
	assert_planning_scope,
)


def add_demand_to_plan(
	*,
	plan: str,
	demand: str,
	demand_item: str | None = None,
	allocated_amount: float | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = assert_can_add_demand(user)
	plan_name = cstr(plan).strip()
	demand_name = cstr(demand).strip()
	if not plan_name or not demand_name:
		frappe.throw(_("Plan and Demand are required."), title="PLN_ADD_REQUIRED")

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	assert_planning_scope(
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		org_unit=cstr(plan_doc.coordinating_org_unit or "").strip() or None,
		user=actor,
		require_write=True,
	)
	draft = cstr(plan_doc.open_draft_version or "").strip()
	if not draft:
		frappe.throw(
			_("Open a Draft revision before adding Demands."),
			title="PLN_NO_OPEN_DRAFT",
		)
	ver = frappe.get_doc("Procurement Plan Version", draft)
	assert_version_mutable(ver.status)
	if ver.status not in VERSION_EDITABLE_STATUSES:
		frappe.throw(_("Only Draft or Returned versions accept new items."), title="PLN_VERSION_NOT_EDITABLE")

	if not frappe.db.exists("Demand", demand_name):
		frappe.throw(_("Demand not found."), title="PLN_DEMAND_NOT_FOUND")
	demand_doc = frappe.get_doc("Demand", demand_name)
	demand_pe = cstr(demand_doc.procuring_entity or "").strip()
	if demand_pe != cstr(plan_doc.procuring_entity).strip():
		frappe.throw(
			_("Demand Procuring Entity must match the Plan Procuring Entity."),
			title="PLN_CROSS_PE_ALLOCATION",
		)

	item_name = cstr(demand_item or "").strip()
	if not item_name:
		items = frappe.get_all(
			"Demand Item",
			filters={"demand": demand_name},
			pluck="name",
			limit=1,
		)
		if not items:
			frappe.throw(_("Demand has no Demand Items."), title="PLN_NO_DEMAND_ITEM")
		item_name = items[0]
	elif not frappe.db.exists("Demand Item", item_name):
		frappe.throw(_("Demand Item not found."), title="PLN_DEMAND_ITEM_NOT_FOUND")

	di = frappe.get_doc("Demand Item", item_name)
	amount = flt(allocated_amount)
	if amount <= 0:
		amount = flt(di.confirmed_estimate or di.requester_estimate or demand_doc.confirmed_estimate or 0)
	if amount <= 0:
		frappe.throw(_("Allocated amount must be positive."), title="PLN_AMOUNT_REQUIRED")

	currency = cstr(di.currency or demand_doc.currency or plan_doc.currency or "KES")
	ou = cstr(demand_doc.owner_org_unit or plan_doc.coordinating_org_unit).strip()
	title = cstr(demand_doc.title or demand_doc.demand_code or "Plan Item")

	plan_item_code = next_plan_item_code(plan_doc.plan_code)
	item = frappe.get_doc(
		{
			"doctype": "Procurement Plan Item",
			"plan": plan_name,
			"plan_item_code": plan_item_code,
			"procuring_entity": plan_doc.procuring_entity,
			"owner_org_unit": ou,
			"delivery_org_unit": demand_doc.delivery_org_unit,
			"baseline_state": ITEM_PROPOSED,
		}
	)
	item.insert(ignore_permissions=True)

	iv_code = f"{plan_item_code}-{ver.version_number}"
	item_version = frappe.get_doc(
		{
			"doctype": "Procurement Plan Item Version",
			"plan_item": item.name,
			"plan_version": ver.name,
			"item_version_code": iv_code,
			"carry_forward_unchanged": 0,
			"requirement_title": title,
			"requirement_description": cstr(demand_doc.need_statement or "")[:500],
			"confirmed_estimate": amount,
			"currency": currency,
			"procurement_category": cstr(demand_doc.procurement_category or ""),
			"validation_projection": VALIDATION_NOT_RUN,
		}
	)
	item_version.insert(ignore_permissions=True)

	frappe.db.set_value(
		"Procurement Plan Item",
		item.name,
		{"draft_item_version": item_version.name},
		update_modified=False,
	)

	alloc = frappe.get_doc(
		{
			"doctype": "Plan Demand Allocation",
			"plan_item": item.name,
			"demand": demand_name,
			"demand_item": item_name,
			"status": ALLOC_DRAFT,
			"allocated_amount": amount,
			"currency": currency,
			"allocated_quantity": flt(di.confirmed_quantity or di.quantity),
			"proposed_in_version": ver.name,
		}
	)
	alloc.insert(ignore_permissions=True)

	# Draft must not consume Demand availability
	return {
		"ok": True,
		"plan_item": item.name,
		"plan_item_code": plan_item_code,
		"item_version": item_version.name,
		"allocation": alloc.name,
		"allocation_status": ALLOC_DRAFT,
		"actor": actor,
	}
