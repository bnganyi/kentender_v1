# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SCN-PLN-REMOVE-001 — draft-only removal of PPI-MOH-2027-022 (Demo v2.7 §7.8)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.mvp1_constants import (
	ITEM_REMOVED,
)
from kentender_procurement.procurement_planning.seeds import scn_pln_add_001 as add_scn
from kentender_procurement.procurement_planning.services.get_plan_builder import (
	get_plan_builder,
)
from kentender_procurement.procurement_planning.services.list_eligible_demands import (
	_already_planned_amount,
)
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	remove_plan_item_from_plan,
)

REMOVE_REASON = "Added for demonstration; remove from this draft"


def setup(*, force: bool = True) -> dict[str, Any]:
	"""Base bundle + ADD-001 through Proposed PPI-022 (before Finance / V2 approve)."""
	frappe.only_for(("System Manager", "Administrator"))
	base = add_scn.setup(force=force)
	prepared = add_scn.run(reset_first=False, force=force, stop_before_finance=True)
	return {"ok": bool(base.get("ok") and prepared.get("ok")), "base": base, "prepared": prepared}


def run(*, reset_first: bool = False, force: bool = True) -> dict[str, Any]:
	frappe.only_for(("System Manager", "Administrator"))
	if reset_first:
		setup(force=force)
	else:
		add_scn.run(reset_first=False, force=force, stop_before_finance=True)

	item_name = frappe.db.get_value(
		"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}, "name"
	)
	plan_name = frappe.db.get_value(
		"Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}, "name"
	)
	if not item_name or not plan_name:
		raise frappe.ValidationError("SCN-PLN-REMOVE-001 requires Proposed PPI-MOH-2027-022 on Draft V2")

	state = frappe.db.get_value("Procurement Plan Item", item_name, "baseline_state")
	v2_name = frappe.db.get_value(
		"Procurement Plan Version", {"version_code": C.PROCUREMENT_PLAN_VERSION_V2}, "name"
	)
	planner = C.USER_PLANNING_OFFICER
	token = frappe.db.get_value("Procurement Plan Version", v2_name, "concurrency_token")

	if state == ITEM_REMOVED:
		return _snapshot(plan_name, item_name, idempotent=True)

	frappe.set_user(planner)
	result = remove_plan_item_from_plan(
		plan=plan_name,
		plan_item=item_name,
		reason=REMOVE_REASON,
		concurrency_token=token,
		user=planner,
	)
	frappe.set_user("Administrator")
	if not result.get("ok"):
		raise frappe.ValidationError(result.get("errors") or result)
	frappe.db.commit()
	return _snapshot(plan_name, item_name, idempotent=False, remove_result=result)


def reset(*, force: bool = True) -> dict[str, Any]:
	"""Restore Draft V2 with Proposed PPI-022 (do not hard-delete lineage)."""
	frappe.only_for(("System Manager", "Administrator"))
	return setup(force=force)


def _snapshot(
	plan_name: str,
	item_name: str,
	*,
	idempotent: bool,
	remove_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
	planner = C.USER_PLANNING_OFFICER
	builder = get_plan_builder(plan=plan_name, user=planner)
	demand = frappe.db.get_value("Demand", {"demand_code": C.DEMAND_CODE_RETURNED}, "name")
	# Eligibility is a Demand projection (status / usage / remaining allocs), not the
	# DHP-scoped planner's list_eligible filter. 019 is HRMD-owned.
	status = frappe.db.get_value("Demand", demand, "status") if demand else None
	usage = frappe.db.get_value("Demand", demand, "planning_usage") if demand else None
	ready = int(frappe.db.get_value("Demand", demand, "planning_ready") or 0) if demand else 0
	planned_remaining = flt(_already_planned_amount(demand)) if demand else 0.0
	demand_eligible = bool(
		demand
		and status == "Approved"
		and ready
		and usage != "Fully planned"
		and planned_remaining <= 0.0001
	)
	v1_status = frappe.db.get_value(
		"Procurement Plan Version",
		{"version_code": C.PROCUREMENT_PLAN_VERSION_CODE},
		"status",
	)
	return {
		"ok": True,
		"idempotent": idempotent,
		"plan": plan_name,
		"plan_item": item_name,
		"plan_item_code": C.PLAN_ITEM_CODE_SCN,
		"baseline_state": frappe.db.get_value("Procurement Plan Item", item_name, "baseline_state"),
		"planned_total": flt(builder.get("planned_total")),
		"expected_total": C.PLAN_AMOUNT_V1,
		"demand_code": C.DEMAND_CODE_RETURNED,
		"demand_eligible": demand_eligible,
		"approved_v1_status": v1_status,
		"tender_code": C.TENDER_CODE,
		"remove_result": remove_result,
	}
