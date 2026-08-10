# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-006 — Aggregate compatible Draft allocations onto one Proposed Plan Item."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	ITEM_PROPOSED,
	VERSION_EDITABLE_STATUSES,
)
from kentender_procurement.procurement_planning.services._invariants import assert_version_mutable
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_can_add_demand,
	assert_planning_scope,
)


def aggregate_plan_allocations(
	*,
	plan_item: str,
	demand: str,
	demand_item: str | None = None,
	allocated_amount: float | None = None,
	aggregation_reason: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Add another eligible Demand allocation to an existing Proposed item (Draft edit)."""
	actor = assert_can_add_demand(user)
	item_name = cstr(plan_item).strip()
	demand_name = cstr(demand).strip()
	reason = cstr(aggregation_reason or "").strip()
	if not item_name or not demand_name:
		frappe.throw(frappe._("Plan Item and Demand are required."), title="PLN_AGG_REQUIRED")
	if not reason:
		frappe.throw(
			frappe._("Aggregation requires an accountable reason."),
			title="PLN_AGG_REASON_REQUIRED",
		)

	item = frappe.get_doc("Procurement Plan Item", item_name)
	if cstr(item.baseline_state) != ITEM_PROPOSED:
		frappe.throw(
			frappe._("Only Proposed Plan Items accept additional Draft allocations."),
			title="PLN_AGG_ITEM_STATE",
		)
	plan = frappe.get_doc("Procurement Plan", item.plan)
	assert_planning_scope(
		procuring_entity=cstr(plan.procuring_entity).strip(),
		org_unit=cstr(item.owner_org_unit or "").strip() or None,
		user=actor,
		require_write=True,
	)
	draft = cstr(plan.open_draft_version or "").strip()
	if not draft:
		frappe.throw(frappe._("Open a Draft revision first."), title="PLN_NO_OPEN_DRAFT")
	ver = frappe.get_doc("Procurement Plan Version", draft)
	assert_version_mutable(ver.status)
	if ver.status not in VERSION_EDITABLE_STATUSES:
		frappe.throw(frappe._("Version is not editable."), title="PLN_VERSION_NOT_EDITABLE")

	demand_doc = frappe.get_doc("Demand", demand_name)
	if cstr(demand_doc.procuring_entity).strip() != cstr(plan.procuring_entity).strip():
		frappe.throw(
			frappe._("Demand Procuring Entity must match the Plan Procuring Entity."),
			title="PLN_CROSS_PE_ALLOCATION",
		)
	if cstr(demand_doc.status) != "Approved" or not int(demand_doc.planning_ready or 0):
		frappe.throw(frappe._("Demand is not eligible for planning."), title="PLN_DEMAND_NOT_ELIGIBLE")
	if cstr(demand_doc.planning_usage or "") == "Fully planned":
		frappe.throw(frappe._("Demand is fully planned."), title="PLN_DEMAND_FULLY_PLANNED")

	# Anti-splitting: refuse if this Demand already has an allocation on a *different* Proposed item
	# in the same Draft version (procedure-avoidance via parallel items).
	existing_other = frappe.db.sql(
		"""
		select a.name from `tabPlan Demand Allocation` a
		inner join `tabProcurement Plan Item` i on i.name = a.plan_item
		where a.demand = %s and a.status = %s and a.proposed_in_version = %s
		  and a.plan_item != %s and i.baseline_state = %s
		limit 1
		""",
		(demand_name, ALLOC_DRAFT, draft, item_name, ITEM_PROPOSED),
	)
	if existing_other:
		frappe.throw(
			frappe._(
				"This Demand already has a Draft allocation on another Proposed Plan Item. "
				"Anti-splitting blocks parallel items without consolidation."
			),
			title="PLN_ANTI_SPLIT",
		)

	item_row = cstr(demand_item or "").strip()
	if not item_row:
		items = frappe.get_all(
			"Demand Item", filters={"demand": demand_name}, pluck="name", limit=1
		)
		if not items:
			frappe.throw(frappe._("Demand has no Demand Items."), title="PLN_NO_DEMAND_ITEM")
		item_row = items[0]
	di = frappe.get_doc("Demand Item", item_row)
	amount = flt(allocated_amount)
	if amount <= 0:
		amount = flt(di.confirmed_estimate or di.requester_estimate or demand_doc.confirmed_estimate)
	approved = flt(demand_doc.confirmed_estimate or demand_doc.requester_estimate)
	already = flt(
		frappe.db.sql(
			"""
			select coalesce(sum(allocated_amount), 0) from `tabPlan Demand Allocation`
			where demand=%s and status in ('Draft', 'Effective')
			""",
			demand_name,
		)[0][0]
	)
	if already + amount > approved + 0.0001:
		frappe.throw(
			frappe._("Allocated amount exceeds approved available scope."),
			title="PLN_AMOUNT_EXCEEDS_AVAILABLE",
		)

	currency = cstr(di.currency or demand_doc.currency or plan.currency or "KES")
	alloc = frappe.get_doc(
		{
			"doctype": "Plan Demand Allocation",
			"plan_item": item_name,
			"demand": demand_name,
			"demand_item": item_row,
			"status": ALLOC_DRAFT,
			"allocated_amount": amount,
			"currency": currency,
			"allocated_quantity": flt(di.confirmed_quantity or di.quantity),
			"proposed_in_version": draft,
			"reason": reason,
			"reservation_reference": cstr(
				frappe.db.get_value(
					"Demand Funding Allocation",
					{"demand": demand_name},
					"funding_reservation",
				)
				or ""
			),
		}
	)
	alloc.insert(ignore_permissions=True)

	iv_name = cstr(item.draft_item_version or "").strip()
	if iv_name and frappe.db.exists("Procurement Plan Item Version", iv_name):
		iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
		iv.aggregation_decision = "Combine"
		iv.aggregation_reason = reason
		iv.confirmed_estimate = flt(iv.confirmed_estimate) + amount
		iv.save(ignore_permissions=True)

	return {
		"ok": True,
		"plan_item": item_name,
		"allocation": alloc.name,
		"allocation_status": ALLOC_DRAFT,
		"aggregation_reason": reason,
		"reservation_reference": alloc.reservation_reference,
		"actor": actor,
		# Expected benefit must never be presented as realised savings.
		"expected_benefit_realised": False,
	}
