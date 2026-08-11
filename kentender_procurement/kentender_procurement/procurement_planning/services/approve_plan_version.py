# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Approve Plan Version — Gate 05: In review + recommend + Ready → atomic lock."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	ALLOC_EFFECTIVE,
	DECISION_APPROVED,
	ITEM_ACTIVE,
	VALIDATION_READY,
	VERSION_APPROVABLE_STATUSES,
	VERSION_APPROVED,
	VERSION_SUPERSEDED,
)
from kentender_procurement.procurement_planning.services._invariants import (
	assert_version_concurrency,
	new_concurrency_token,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	APPROVE_PLAN_ROLES,
	assert_can_approve_plan,
	assert_planning_scope,
)
from kentender_procurement.procurement_planning.services.record_plan_decision import (
	has_recommendation,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan


def approve_plan_version(
	*,
	version: str,
	concurrency_token: str | None = None,
	reason: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = assert_can_approve_plan(user)
	version_name = cstr(version).strip()
	if not version_name or not frappe.db.exists("Procurement Plan Version", version_name):
		frappe.throw(_("Plan Version not found."), title="PLN_VERSION_NOT_FOUND")

	assert_version_concurrency(version_name, concurrency_token)
	ver = frappe.get_doc("Procurement Plan Version", version_name)
	if ver.status not in VERSION_APPROVABLE_STATUSES:
		frappe.throw(
			_("Only In review versions with a recommendation can be approved."),
			title="PLN_VERSION_NOT_APPROVABLE",
		)
	if not has_recommendation(version=version_name):
		frappe.throw(
			_("Professional recommendation is required before approval."),
			title="PLN_RECOMMENDATION_REQUIRED",
		)

	plan = frappe.get_doc("Procurement Plan", ver.plan)
	assert_planning_scope(
		procuring_entity=cstr(plan.procuring_entity).strip(),
		org_unit=cstr(plan.coordinating_org_unit or "").strip() or None,
		user=actor,
		require_write=True,
	)
	if plan.lifecycle_state != "Open":
		frappe.throw(_("Plan is not Open."), title="PLN_PLAN_NOT_OPEN")

	validation = validate_plan(plan=plan.name, user=actor)
	if cstr(validation.get("status")) != VALIDATION_READY:
		frappe.throw(
			_("Validation must be Ready before approval."),
			title="PLN_VALIDATION_NOT_READY",
		)

	now = now_datetime()
	prior = cstr(plan.current_approved_version or "").strip()

	# Supersede prior approved
	if prior and prior != ver.name:
		prior_status = frappe.db.get_value("Procurement Plan Version", prior, "status")
		if prior_status == VERSION_APPROVED:
			frappe.db.set_value(
				"Procurement Plan Version",
				prior,
				{
					"status": VERSION_SUPERSEDED,
					"superseded_at": now,
					"concurrency_token": new_concurrency_token(),
				},
				update_modified=True,
			)

	# Flip Draft allocations proposed in this version → Effective once
	draft_allocs = frappe.get_all(
		"Plan Demand Allocation",
		filters={
			"proposed_in_version": ver.name,
			"status": ALLOC_DRAFT,
		},
		pluck="name",
	)
	for alloc_name in draft_allocs:
		alloc = frappe.get_doc("Plan Demand Allocation", alloc_name)
		if alloc.effective_from_version:
			frappe.throw(
				_("Allocation was already made effective."),
				title="PLN_ALLOC_ALREADY_EFFECTIVE",
			)
		alloc.status = ALLOC_EFFECTIVE
		alloc.effective_from_version = ver.name
		alloc.effective_at = now
		alloc.save(ignore_permissions=True)
		_write_planning_consumption(alloc)

	# Activate items that have item versions on this plan version
	item_versions = frappe.get_all(
		"Procurement Plan Item Version",
		filters={"plan_version": ver.name},
		fields=["name", "plan_item"],
	)
	for iv in item_versions:
		frappe.db.set_value(
			"Procurement Plan Item",
			iv.plan_item,
			{
				"baseline_state": ITEM_ACTIVE,
				"current_approved_item_version": iv.name,
				"draft_item_version": None,
			},
			update_modified=False,
		)

	frappe.db.set_value(
		"Procurement Plan Version",
		ver.name,
		{
			"status": VERSION_APPROVED,
			"validation_projection": VALIDATION_READY,
			"effective_at": now,
			"approved_by": actor,
			"approved_at": now,
			"concurrency_token": new_concurrency_token(),
		},
		update_modified=True,
	)

	frappe.db.set_value(
		"Procurement Plan",
		plan.name,
		{
			"current_approved_version": ver.name,
			"open_draft_version": None,
		},
		update_modified=False,
	)

	frappe.get_doc(
		{
			"doctype": "Plan Decision",
			"plan_version": ver.name,
			"decision_type": "Approval",
			"decision_stage": "Plan Version Approval",
			"actor": actor,
			"actor_role": _primary_planning_role(actor),
			"decision": DECISION_APPROVED,
			"reason": cstr(reason or "Approved"),
			"decided_at": now,
		}
	).insert(ignore_permissions=True)

	return {
		"ok": True,
		"plan": plan.name,
		"version": ver.name,
		"version_code": ver.version_code,
		"status": VERSION_APPROVED,
		"allocations_effective": len(draft_allocs),
		"superseded_version": prior or None,
		"approved_by": actor,
		"approved_at": str(now),
	}


def _primary_planning_role(user: str) -> str:
	roles = set(frappe.get_roles(user))
	for role in (
		"Designated Approver",
		"Accounting Officer",
		"Planning Authority",
	):
		if role in roles and role in APPROVE_PLAN_ROLES:
			return role
	return "Designated Approver"


def _write_planning_consumption(alloc) -> None:
	"""Create Planning Consumption for Effective allocation (Demands bridge)."""
	if not frappe.db.exists("DocType", "Planning Consumption"):
		return
	existing = frappe.db.exists(
		"Planning Consumption",
		{
			"demand": alloc.demand,
			"demand_item": alloc.demand_item,
			"plan_item_code": frappe.db.get_value(
				"Procurement Plan Item", alloc.plan_item, "plan_item_code"
			),
		},
	)
	plan_item_code = frappe.db.get_value(
		"Procurement Plan Item", alloc.plan_item, "plan_item_code"
	)
	values = {
		"demand": alloc.demand,
		"demand_item": alloc.demand_item,
		"plan_item_code": plan_item_code,
		"consumed_amount": alloc.allocated_amount,
		"consumed_quantity": alloc.allocated_quantity,
		"currency": alloc.currency,
		"consumed_by": frappe.session.user,
		"consumed_at": now_datetime(),
	}
	if existing:
		frappe.db.set_value("Planning Consumption", existing, values, update_modified=False)
	else:
		frappe.get_doc({"doctype": "Planning Consumption", **values}).insert(
			ignore_permissions=True
		)

	# Update Demand planning_usage when consumption exists
	if frappe.db.has_column("Demand", "planning_usage"):
		frappe.db.set_value(
			"Demand",
			alloc.demand,
			"planning_usage",
			"Fully planned",
			update_modified=False,
		)
