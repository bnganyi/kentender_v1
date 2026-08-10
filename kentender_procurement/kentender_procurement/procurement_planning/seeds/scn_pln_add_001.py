# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SCN-PLN-ADD-001 — post-approval Plan Item addition (Contract §7.6)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_EFFECTIVE,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	VALIDATION_READY,
	VERSION_APPROVED,
	VERSION_DRAFT,
	VERSION_SUPERSEDED,
)
from kentender_procurement.procurement_planning.services._invariants import (
	new_concurrency_token,
)
from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import (
	upsert_planning_base,
)

SCN_TITLE = "Digital health technical staff certification programme"
CORRECTED_AMOUNT = C.PLAN_ITEM_SCN_AMOUNT


def setup(*, force: bool = True) -> dict[str, Any]:
	"""Ensure base Planning state (Approved V1 @ 455M)."""
	frappe.only_for(("System Manager", "Administrator"))
	frappe.set_user("Administrator")
	from kentender_core.seeds.kentender_mvp_v1.orchestrator import run_kentender_mvp_v1

	base = run_kentender_mvp_v1(reset=True, force=force, validate=True)
	return {"ok": bool(base.get("ok")), "base": base}


def _approve_returned_demand_for_scn() -> dict[str, Any]:
	"""Correct DMD-MOH-2027-019 to 80M and mark Approved with RSV-MOH-0002."""
	demand_name = frappe.db.get_value("Demand", {"demand_code": C.DEMAND_CODE_RETURNED}, "name")
	if not demand_name:
		raise frappe.ValidationError(f"Missing {C.DEMAND_CODE_RETURNED}")

	status = frappe.db.get_value("Demand", demand_name, "status")
	# Idempotent: already approved for SCN
	if status == "Approved" and frappe.db.exists(
		"Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}
	):
		return {"demand": demand_name, "already_approved": True}

	budget_line = frappe.db.get_value(
		"Budget Line", {"generated_reference": C.BL_HWD_2027}, "name"
	)
	if not budget_line:
		raise frappe.ValidationError(f"Missing Budget Line {C.BL_HWD_2027}")
	budget = frappe.db.get_value("Budget Line", budget_line, "budget")

	rsv_name = frappe.db.get_value(
		"Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}, "name"
	)
	if not rsv_name:
		rsv = frappe.get_doc(
			{
				"doctype": "Funding Reservation",
				"generated_reference": C.RSV_CODE_SCN,
				"budget": budget,
				"budget_line": budget_line,
				"original_amount": CORRECTED_AMOUNT,
				"remaining_reserved": CORRECTED_AMOUNT,
				"status": "Reserved",
				"currency": "KES",
				"demand_code": C.DEMAND_CODE_RETURNED,
				"demand_title": SCN_TITLE,
				"event_date": C.FIXTURE_DATE,
				"plan_item_code": C.PLAN_ITEM_CODE_SCN,
				"fixture_namespace": C.FIXTURE_NS,
			}
		)
		rsv.insert(ignore_permissions=True)
		rsv_name = rsv.name

	for di in frappe.get_all("Demand Item", filters={"demand": demand_name}, pluck="name"):
		frappe.db.set_value(
			"Demand Item",
			di,
			{
				"confirmed_estimate": CORRECTED_AMOUNT,
				"requester_estimate": CORRECTED_AMOUNT,
			},
			update_modified=False,
		)

	frappe.db.set_value(
		"Demand",
		demand_name,
		{
			"status": "Approved",
			"current_stage": "Complete",
			"confirmed_estimate": CORRECTED_AMOUNT,
			"requester_estimate": CORRECTED_AMOUNT,
			"planning_ready": 1,
			"planning_usage": "Not taken up",
			"approved_at": C.FIXTURE_NOW_STR,
		},
		update_modified=False,
	)

	alloc = frappe.db.get_value(
		"Demand Funding Allocation", {"demand": demand_name}, "name"
	)
	if alloc:
		frappe.db.set_value(
			"Demand Funding Allocation",
			alloc,
			{
				"allocation_amount": CORRECTED_AMOUNT,
				"bo_confirmation_status": "Confirmed",
				"funding_reservation": rsv_name,
				"budget_line": budget_line,
			},
			update_modified=False,
		)
	else:
		frappe.get_doc(
			{
				"doctype": "Demand Funding Allocation",
				"demand": demand_name,
				"budget_line": budget_line,
				"allocation_amount": CORRECTED_AMOUNT,
				"bo_confirmation_status": "Confirmed",
				"funding_reservation": rsv_name,
			}
		).insert(ignore_permissions=True)

	return {"demand": demand_name, "reservation": rsv_name, "already_approved": False}


def run(*, reset_first: bool = False, force: bool = True) -> dict[str, Any]:
	"""Execute SCN-PLN-ADD-001 once; second run is a no-op for duplicates."""
	frappe.only_for(("System Manager", "Administrator"))
	frappe.set_user("Administrator")

	if reset_first:
		setup(force=force)

	# Already completed?
	if frappe.db.exists("Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}):
		v2 = frappe.db.get_value(
			"Procurement Plan Version",
			{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
			["name", "status"],
			as_dict=True,
		)
		if v2 and v2.status == VERSION_APPROVED:
			return {
				"ok": True,
				"idempotent": True,
				"plan_item_code": C.PLAN_ITEM_CODE_SCN,
				"version_code": C.PROCUREMENT_PLAN_VERSION_V2,
				"total": C.PLAN_AMOUNT_V2,
			}

	demand_info = _approve_returned_demand_for_scn()
	demand = demand_info["demand"]
	plan_name = frappe.db.get_value(
		"Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}, "name"
	)
	if not plan_name:
		raise frappe.ValidationError(f"Missing plan {C.PROCUREMENT_PLAN_CODE}")

	v1_name = frappe.db.get_value(
		"Procurement Plan Version",
		{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
		"name",
	)
	pe = C.PE_MOH
	ou = C.OU_DIR_HRMD

	# Open Draft V2 (or reuse)
	v2_name = frappe.db.get_value(
		"Procurement Plan Version",
		{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
		"name",
	)
	created_v2 = False
	if not v2_name:
		v2 = frappe.get_doc(
			{
				"doctype": "Procurement Plan Version",
				"plan": plan_name,
				"version_number": 2,
				"version_code": C.PROCUREMENT_PLAN_VERSION_V2,
				"status": VERSION_DRAFT,
				"version_reason": "SCN-PLN-ADD-001 post-approval addition",
				"validation_projection": VALIDATION_READY,
				"concurrency_token": new_concurrency_token(),
			}
		)
		v2.insert(ignore_permissions=True)
		v2_name = v2.name
		created_v2 = True
		frappe.db.set_value(
			"Procurement Plan",
			plan_name,
			{"open_draft_version": v2_name},
			update_modified=False,
		)

	# Carry-forward item version for 021 on V2 if missing
	item_021 = frappe.db.get_value(
		"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE}, "name"
	)
	iv_021_v1 = frappe.db.get_value(
		"Procurement Plan Item Version",
		{"plan_item": item_021, "plan_version": v1_name},
		"name",
	)
	iv_021_v2_code = f"{C.PLAN_ITEM_CODE}-2"
	if not frappe.db.exists("Procurement Plan Item Version", {"item_version_code": iv_021_v2_code}):
		frappe.get_doc(
			{
				"doctype": "Procurement Plan Item Version",
				"plan_item": item_021,
				"plan_version": v2_name,
				"item_version_code": iv_021_v2_code,
				"source_item_version": iv_021_v1,
				"carry_forward_unchanged": 1,
				"requirement_title": "National digital health infrastructure upgrade",
				"confirmed_estimate": C.PLAN_AMOUNT_V1,
				"currency": "KES",
				"reservation_reference": C.RSV_CODE,
				"validation_projection": VALIDATION_READY,
			}
		).insert(ignore_permissions=True)

	# Proposed PPI-022
	item_022 = frappe.db.get_value(
		"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}, "name"
	)
	created_item = False
	if not item_022:
		item = frappe.get_doc(
			{
				"doctype": "Procurement Plan Item",
				"plan": plan_name,
				"plan_item_code": C.PLAN_ITEM_CODE_SCN,
				"procuring_entity": pe,
				"owner_org_unit": ou,
				"delivery_org_unit": ou,
				"baseline_state": ITEM_PROPOSED,
			}
		)
		item.insert(ignore_permissions=True)
		item_022 = item.name
		created_item = True

	iv_022_code = f"{C.PLAN_ITEM_CODE_SCN}-2"
	iv_022 = frappe.db.get_value(
		"Procurement Plan Item Version", {"item_version_code": iv_022_code}, "name"
	)
	if not iv_022:
		iv = frappe.get_doc(
			{
				"doctype": "Procurement Plan Item Version",
				"plan_item": item_022,
				"plan_version": v2_name,
				"item_version_code": iv_022_code,
				"carry_forward_unchanged": 0,
				"requirement_title": SCN_TITLE,
				"confirmed_estimate": CORRECTED_AMOUNT,
				"currency": "KES",
				"reservation_reference": C.RSV_CODE_SCN,
				"validation_projection": VALIDATION_READY,
			}
		)
		iv.insert(ignore_permissions=True)
		iv_022 = iv.name
		frappe.db.set_value(
			"Procurement Plan Item",
			item_022,
			{"draft_item_version": iv_022},
			update_modified=False,
		)

	demand_item = frappe.db.get_value(
		"Demand Item", {"demand": demand}, "name", order_by="creation asc"
	)
	alloc = frappe.db.get_value(
		"Plan Demand Allocation",
		{"plan_item": item_022, "demand": demand},
		"name",
	)
	if not alloc:
		alloc_doc = frappe.get_doc(
			{
				"doctype": "Plan Demand Allocation",
				"plan_item": item_022,
				"demand": demand,
				"demand_item": demand_item,
				"status": "Draft",
				"allocated_amount": CORRECTED_AMOUNT,
				"currency": "KES",
				"reservation_reference": C.RSV_CODE_SCN,
				"proposed_in_version": v2_name,
			}
		)
		alloc_doc.insert(ignore_permissions=True)
		alloc = alloc_doc.name

	# Approve V2 → supersede V1, activate 022
	v2_status = frappe.db.get_value("Procurement Plan Version", v2_name, "status")
	if v2_status != VERSION_APPROVED:
		now = C.FIXTURE_NOW_STR
		if v1_name:
			frappe.db.set_value(
				"Procurement Plan Version",
				v1_name,
				{
					"status": VERSION_SUPERSEDED,
					"superseded_at": now,
					"concurrency_token": new_concurrency_token(),
				},
				update_modified=True,
			)
		frappe.db.set_value(
			"Plan Demand Allocation",
			alloc,
			{
				"status": ALLOC_EFFECTIVE,
				"effective_from_version": v2_name,
				"effective_at": now,
			},
			update_modified=True,
		)
		if frappe.db.exists("DocType", "Planning Consumption"):
			pc_filters = {
				"demand": demand,
				"demand_item": demand_item,
				"plan_item_code": C.PLAN_ITEM_CODE_SCN,
			}
			if not frappe.db.exists("Planning Consumption", pc_filters):
				frappe.get_doc(
					{
						"doctype": "Planning Consumption",
						**pc_filters,
						"consumed_amount": CORRECTED_AMOUNT,
						"currency": "KES",
						"consumed_by": C.USER_PLANNING_OFFICER,
						"consumed_at": now,
					}
				).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Procurement Plan Item",
			item_022,
			{
				"baseline_state": ITEM_ACTIVE,
				"current_approved_item_version": iv_022,
				"draft_item_version": None,
			},
			update_modified=False,
		)
		frappe.db.set_value(
			"Procurement Plan Version",
			v2_name,
			{
				"status": VERSION_APPROVED,
				"effective_at": now,
				"approved_by": C.USER_PLAN_APPROVER,
				"approved_at": now,
				"concurrency_token": new_concurrency_token(),
			},
			update_modified=True,
		)
		frappe.db.set_value(
			"Procurement Plan",
			plan_name,
			{"current_approved_version": v2_name, "open_draft_version": None},
			update_modified=False,
		)
		if not frappe.db.exists(
			"Plan Decision",
			{"plan_version": v2_name, "decision_type": "Approval", "decision": "Approved"},
		):
			frappe.get_doc(
				{
					"doctype": "Plan Decision",
					"plan_version": v2_name,
					"decision_type": "Approval",
					"decision_stage": "Plan Version Approval",
					"actor": C.USER_PLAN_APPROVER,
					"actor_role": "Designated Approver",
					"decision": "Approved",
					"reason": "SCN-PLN-ADD-001 approve revision",
					"decided_at": now,
				}
			).insert(ignore_permissions=True)
		if frappe.db.has_column("Demand", "planning_usage"):
			frappe.db.set_value(
				"Demand", demand, "planning_usage", "Fully planned", update_modified=False
			)

	# Consolidated total check
	items = frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan_name, "baseline_state": ITEM_ACTIVE},
		pluck="name",
	)
	total = 0.0
	for item in items:
		iv = frappe.db.get_value(
			"Procurement Plan Item", item, "current_approved_item_version"
		)
		if iv:
			total += flt(
				frappe.db.get_value(
					"Procurement Plan Item Version", iv, "confirmed_estimate"
				)
			)

	frappe.db.commit()
	return {
		"ok": True,
		"idempotent": False,
		"created_v2": created_v2,
		"created_item": created_item,
		"plan_item_code": C.PLAN_ITEM_CODE_SCN,
		"version_code": C.PROCUREMENT_PLAN_VERSION_V2,
		"total": total,
		"expected_total": C.PLAN_AMOUNT_V2,
	}


def reset(*, force: bool = True) -> dict[str, Any]:
	"""Return to base Planning state (Approved V1 only)."""
	frappe.only_for(("System Manager", "Administrator"))
	frappe.set_user("Administrator")

	# Soft-reset Demand 019 back toward Returned if it was SCN-approved
	demand = frappe.db.get_value("Demand", {"demand_code": C.DEMAND_CODE_RETURNED}, "name")
	if demand:
		frappe.db.set_value(
			"Demand",
			demand,
			{
				"status": "Returned",
				"current_stage": "Request Preparation",
				"confirmed_estimate": 95_000_000,
				"requester_estimate": 95_000_000,
				"planning_ready": 0,
				"planning_usage": "Not taken up",
			},
			update_modified=False,
		)

	# Drop SCN reservation if present
	if frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}):
		rsv = frappe.db.get_value(
			"Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}, "name"
		)
		# Detach from allocations first
		for name in frappe.get_all(
			"Demand Funding Allocation",
			filters={"funding_reservation": rsv},
			pluck="name",
		):
			frappe.db.set_value(
				"Demand Funding Allocation",
				name,
				{"funding_reservation": None, "bo_confirmation_status": "Pending"},
				update_modified=False,
			)
		try:
			frappe.delete_doc("Funding Reservation", rsv, force=1, ignore_permissions=True)
		except Exception:
			pass

	base = upsert_planning_base(commit=True)
	return {"ok": bool(base.get("ok")), "base": base}
