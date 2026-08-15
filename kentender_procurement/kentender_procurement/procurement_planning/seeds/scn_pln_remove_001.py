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
from kentender_procurement.procurement_planning.services.get_plan_builder import get_plan_builder
from kentender_procurement.procurement_planning.services.remove_plan_item import (
	cancel_empty_plan_update,
	remove_plan_item_from_plan,
)

REMOVE_REASON = "Added for demonstration; remove from this draft"
POST_REMOVAL_AT_UTC = "2027-08-19 06:15:00"  # 09:15 EAT


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
		draft_version=v2_name,
		expected_version_token=token,
		idempotency_key="SCN-PLN-REMOVE-001",
		user=planner,
	)
	frappe.set_user("Administrator")
	if not result.get("ok"):
		raise frappe.ValidationError(result.get("errors") or result)
	frappe.db.set_value("Procurement Plan", plan_name, "modified", POST_REMOVAL_AT_UTC, update_modified=False)
	frappe.db.set_value("Procurement Plan Version", v2_name, "modified", POST_REMOVAL_AT_UTC, update_modified=False)
	frappe.db.set_value("Procurement Plan Item", item_name, "modified", POST_REMOVAL_AT_UTC, update_modified=False)
	for item_version in frappe.get_all("Procurement Plan Item Version", filters={"plan_version": v2_name}, pluck="name"):
		frappe.db.set_value("Procurement Plan Item Version", item_version, "modified", POST_REMOVAL_AT_UTC, update_modified=False)
	frappe.db.commit()
	return _snapshot(plan_name, item_name, idempotent=False, remove_result=result)


def cancel(*, reset_first: bool = False, force: bool = True) -> dict[str, Any]:
	"""Prepare and cancel the empty successor; repeat calls replay the same decision."""
	removed = run(reset_first=reset_first, force=force)
	plan_name = removed["plan"]
	version = frappe.db.get_value("Procurement Plan Version", {"version_code": C.PROCUREMENT_PLAN_VERSION_V2}, "name")
	if frappe.db.get_value("Procurement Plan Version", version, "status") == "Cancelled":
		return {**removed, "cancelled": True, "idempotent": True}
	frappe.set_user(C.USER_PLANNING_OFFICER)
	result = cancel_empty_plan_update(
		plan=plan_name,
		successor_version=version,
		expected_version_token=frappe.db.get_value("Procurement Plan Version", version, "concurrency_token"),
		idempotency_key="SCN-PLN-REMOVE-001-CANCEL",
		user=C.USER_PLANNING_OFFICER,
	)
	frappe.set_user("Administrator")
	frappe.db.commit()
	return {**removed, "cancelled": True, "cancel_result": result}


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
	update = get_plan_builder(plan=plan_name, user=planner)
	demand = frappe.db.get_value("Demand", {"demand_code": C.DEMAND_CODE_RETURNED}, "name")
	# Eligibility is a Demand projection (status / usage / remaining allocs), not the
	# DHP-scoped planner's list_eligible filter. 019 is HRMD-owned.
	status = frappe.db.get_value("Demand", demand, "status") if demand else None
	usage = frappe.db.get_value("Demand", demand, "planning_usage") if demand else None
	ready = int(frappe.db.get_value("Demand", demand, "planning_ready") or 0) if demand else 0
	need_items = (
		frappe.get_all("Demand Item", filters={"demand": demand}, pluck="name")
		if demand else []
	)
	has_active_hold = bool(
		need_items
		and frappe.db.exists(
			"Plan Demand Allocation",
			{"demand_item": ["in", need_items], "status": ["in", ["Draft", "Effective"]]},
		)
	)
	demand_eligible = bool(
		demand
		and status == "Approved"
		and ready
		and usage != "Fully planned"
		and not has_active_hold
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
		"planned_total": flt(update.get("planned_total")),
		"expected_total": C.PLAN_AMOUNT_V1,
		"demand_code": C.DEMAND_CODE_RETURNED,
		"demand_eligible": demand_eligible,
		"approved_v1_status": v1_status,
		"tender_code": C.TENDER_CODE,
		"remove_result": remove_result,
	}
