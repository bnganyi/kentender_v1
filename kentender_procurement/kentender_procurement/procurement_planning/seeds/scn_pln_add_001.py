# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SCN-PLN-ADD-001 — post-approval Plan Item addition (Demo v2.7 §7.6)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.mvp1_constants import (
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	VERSION_APPROVED,
	VERSION_DRAFT,
)
from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import (
	upsert_planning_base,
)
from kentender_procurement.procurement_planning.services.add_demand_to_plan import (
	add_demand_to_plan,
)
from kentender_procurement.procurement_planning.services.approve_plan_version import (
	approve_plan_version,
)
from kentender_procurement.procurement_planning.services.get_plan_update import (
	save_plan_update,
)
from kentender_procurement.procurement_planning.services.plan_item_finance import (
	confirm_plan_item_funding,
)
from kentender_procurement.procurement_planning.services.record_plan_decision import (
	record_plan_decision,
)
from kentender_procurement.procurement_planning.services.submit_plan_for_review import (
	submit_plan_for_review,
)
from kentender_procurement.procurement_planning.services.update_plan_item import (
	update_plan_item,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	complete_plan_item_for_signoff,
)

SCN_TITLE = "Digital health technical staff certification programme"
CORRECTED_AMOUNT = C.PLAN_ITEM_SCN_AMOUNT
UPDATE_REASON = "SCN-PLN-ADD-001 post-approval addition"


def setup(*, force: bool = True) -> dict[str, Any]:
	"""Ensure base Planning state (Approved V1 @ 455M)."""
	frappe.only_for(("System Manager", "Administrator"))
	frappe.set_user("Administrator")
	from kentender_core.seeds.kentender_mvp_v1.orchestrator import run_kentender_mvp_v1

	base = run_kentender_mvp_v1(reset=True, force=force, validate=True)
	return {"ok": bool(base.get("ok")), "base": base}


def _approve_returned_demand_for_scn() -> dict[str, Any]:
	"""Correct DMD-MOH-2027-019 to 80M Planning Ready — no reservation."""
	demand_name = frappe.db.get_value("Demand", {"demand_code": C.DEMAND_CODE_RETURNED}, "name")
	if not demand_name:
		raise frappe.ValidationError(f"Missing {C.DEMAND_CODE_RETURNED}")

	status = frappe.db.get_value("Demand", demand_name, "status")
	ready = int(frappe.db.get_value("Demand", demand_name, "planning_ready") or 0)
	if status == "Approved" and ready:
		return {"demand": demand_name, "already_approved": True}

	budget_line = frappe.db.get_value(
		"Budget Line", {"generated_reference": C.BL_HWD_2027}, "name"
	)
	if not budget_line:
		raise frappe.ValidationError(f"Missing Budget Line {C.BL_HWD_2027}")

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
	values = {
		"allocation_amount": CORRECTED_AMOUNT,
		"budget_line": budget_line,
		"funding_reservation": None,
		"reservation_status": None,
		"bo_confirmation_status": "Pending",
	}
	if alloc:
		frappe.db.set_value("Demand Funding Allocation", alloc, values, update_modified=False)
	else:
		frappe.get_doc(
			{
				"doctype": "Demand Funding Allocation",
				"demand": demand_name,
				"budget_line": budget_line,
				"allocation_amount": CORRECTED_AMOUNT,
				"bo_confirmation_status": "Pending",
			}
		).insert(ignore_permissions=True)

	return {"demand": demand_name, "already_approved": False}


def _pin_scn_item_identity(plan_item: str) -> str:
	"""Keep Demo identities PPI-MOH-2027-022 / PPI-MOH-2027-022-2 (name may stay autonamed)."""
	if frappe.db.get_value("Procurement Plan Item", plan_item, "plan_item_code") != C.PLAN_ITEM_CODE_SCN:
		frappe.db.set_value(
			"Procurement Plan Item",
			plan_item,
			"plan_item_code",
			C.PLAN_ITEM_CODE_SCN,
			update_modified=False,
		)
	iv = frappe.db.get_value("Procurement Plan Item", plan_item, "draft_item_version")
	if iv:
		frappe.db.set_value(
			"Procurement Plan Item Version",
			iv,
			"item_version_code",
			f"{C.PLAN_ITEM_CODE_SCN}-2",
			update_modified=False,
		)
	return plan_item


def _complete_item_if_needed(plan_item: str) -> None:
	planner = C.USER_PLANNING_OFFICER
	iv = frappe.db.get_value("Procurement Plan Item", plan_item, "draft_item_version")
	if not iv:
		return
	method = frappe.db.get_value("Procurement Plan Item Version", iv, "procurement_method")
	has_ms = frappe.db.get_value("Procurement Plan Item Version", iv, "ms_invitation_published")
	if method and has_ms:
		return
	complete = complete_plan_item_for_signoff(plan_item=plan_item, user=planner)
	if complete.get("ok") is False:
		raise frappe.ValidationError(complete.get("errors") or complete)


def _draft_total(plan_name: str, version_name: str) -> float:
	total = 0.0
	for it in frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan_name, "baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]]},
		pluck="name",
	):
		amt = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": it, "plan_version": version_name},
			"confirmed_estimate",
		)
		total += flt(amt)
	return total


def _snapshot(*, idempotent: bool, stopped_before_finance: bool = False, stopped_before_approve: bool = False) -> dict[str, Any]:
	plan_name = frappe.db.get_value(
		"Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}, "name"
	)
	v2_name = frappe.db.get_value(
		"Procurement Plan Version",
		{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
		"name",
	)
	total = _draft_total(plan_name, v2_name) if plan_name and v2_name else 0.0
	if not stopped_before_finance and not stopped_before_approve:
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
	return {
		"ok": True,
		"idempotent": idempotent,
		"plan_item_code": C.PLAN_ITEM_CODE_SCN,
		"version_code": C.PROCUREMENT_PLAN_VERSION_V2,
		"total": total,
		"expected_total": C.PLAN_AMOUNT_V2,
		"stopped_before_finance": stopped_before_finance,
		"stopped_before_approve": stopped_before_approve,
	}


def _ensure_draft_item(*, demand: str, plan_name: str) -> str:
	item_022 = frappe.db.get_value(
		"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}, "name"
	)
	planner = C.USER_PLANNING_OFFICER
	if not item_022:
		added = add_demand_to_plan(plan=plan_name, demand=demand, user=planner)
		if not added.get("ok"):
			raise frappe.ValidationError(added.get("errors") or added)
		item_022 = _pin_scn_item_identity(added["plan_item"])
	_complete_item_if_needed(item_022)
	saved = save_plan_update(
		plan=plan_name,
		update_reason=UPDATE_REASON,
		user=planner,
	)
	if not saved.get("ok"):
		raise frappe.ValidationError(saved.get("errors") or saved)
	return item_022


def _ensure_finance(item_022: str, plan_name: str) -> None:
	if frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}):
		return
	_complete_item_if_needed(item_022)
	_complete_carry_forward_items(plan_name)
	planner = C.USER_PLANNING_OFFICER
	req = update_plan_item(plan_item=item_022, user=planner, request_finance=True)
	if req.get("ok") is False:
		raise frappe.ValidationError(req.get("errors") or req)
	if not req.get("complete"):
		raise frappe.ValidationError(req.get("field_issues") or req)
	confirmed = confirm_plan_item_funding(
		plan_item=item_022,
		note="SCN-PLN-ADD-001 post-Planning Finance",
		user=C.USER_BUD_DUAL,
	)
	if not confirmed.get("ok"):
		raise frappe.ValidationError(confirmed.get("errors") or confirmed)


def _complete_carry_forward_items(plan_name: str) -> None:
	"""Unchanged Active items must have method/schedule on the Draft successor IV."""
	planner = C.USER_PLANNING_OFFICER
	v2_name = frappe.db.get_value(
		"Procurement Plan Version",
		{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
		"name",
	)
	for item in frappe.get_all(
		"Procurement Plan Item",
		filters={"plan": plan_name, "baseline_state": ITEM_ACTIVE},
		pluck="name",
	):
		iv = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": item, "plan_version": v2_name},
			"name",
		) if v2_name else None
		iv = iv or frappe.db.get_value("Procurement Plan Item", item, "draft_item_version")
		if not iv:
			continue
		frappe.db.set_value(
			"Procurement Plan Item",
			item,
			"draft_item_version",
			iv,
			update_modified=False,
		)
		method = frappe.db.get_value("Procurement Plan Item Version", iv, "procurement_method")
		has_ms = frappe.db.get_value(
			"Procurement Plan Item Version", iv, "ms_invitation_published"
		)
		if method and has_ms:
			continue
		complete = complete_plan_item_for_signoff(plan_item=item, user=planner)
		if complete.get("ok") is False:
			raise frappe.ValidationError(complete.get("errors") or complete)


def _ensure_approved(plan_name: str) -> None:
	v2_name = frappe.db.get_value(
		"Procurement Plan Version",
		{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
		"name",
	)
	status = frappe.db.get_value("Procurement Plan Version", v2_name, "status")
	if status == VERSION_APPROVED:
		return
	_complete_carry_forward_items(plan_name)
	planner = C.USER_PLANNING_OFFICER
	token = frappe.db.get_value("Procurement Plan Version", v2_name, "concurrency_token")
	from kentender_procurement.procurement_planning.services.validate_plan import (
		validate_plan,
	)

	validation = validate_plan(plan=plan_name, user=planner)
	submitted = submit_plan_for_review(
		plan=plan_name, concurrency_token=token, user=planner
	)
	if not submitted.get("ok"):
		raise frappe.ValidationError(
			{
				**(submitted.get("errors") or {}),
				"validation": validation,
			}
		)
	v2_name = submitted.get("version") or v2_name
	token = submitted.get("concurrency_token")
	recommended = record_plan_decision(
		version=v2_name,
		decision="recommend",
		concurrency_token=token,
		user=C.USER_PLANNING_REVIEWER,
	)
	if not recommended.get("ok"):
		raise frappe.ValidationError(recommended.get("errors") or recommended)
	token = recommended.get("concurrency_token") or frappe.db.get_value(
		"Procurement Plan Version", v2_name, "concurrency_token"
	)
	approved = approve_plan_version(
		version=v2_name,
		concurrency_token=token,
		reason=UPDATE_REASON,
		user=C.USER_PLAN_APPROVER,
	)
	if not approved.get("ok"):
		raise frappe.ValidationError(approved.get("errors") or approved)


def run(
	*,
	reset_first: bool = False,
	force: bool = True,
	stop_before_finance: bool = False,
	stop_before_approve: bool = False,
) -> dict[str, Any]:
	"""Execute SCN-PLN-ADD-001 via live Planning services.

	``stop_before_finance`` — Draft V2 + Proposed 022, no RSV-0002 (REMOVE / FUND-SHORT / AC-013).
	``stop_before_approve`` — after Finance; RSV-0002 exists; V1 still Approved.
	"""
	frappe.only_for(("System Manager", "Administrator"))
	prev = frappe.session.user
	frappe.set_user("Administrator")
	try:
		if reset_first:
			setup(force=force)

		item_state = frappe.db.get_value(
			"Procurement Plan Item",
			{"plan_item_code": C.PLAN_ITEM_CODE_SCN},
			"baseline_state",
		)
		v2 = frappe.db.get_value(
			"Procurement Plan Version",
			{"version_code": C.PROCUREMENT_PLAN_VERSION_V2},
			["name", "status"],
			as_dict=True,
		)
		has_rsv = bool(
			frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN})
		)

		if stop_before_finance and v2 and v2.status == VERSION_DRAFT and item_state == ITEM_PROPOSED and not has_rsv:
			return _snapshot(idempotent=True, stopped_before_finance=True)
		if stop_before_approve and v2 and v2.status == VERSION_DRAFT and item_state == ITEM_PROPOSED and has_rsv:
			return _snapshot(idempotent=True, stopped_before_approve=True)
		if (
			(not stop_before_finance)
			and (not stop_before_approve)
			and v2
			and v2.status == VERSION_APPROVED
			and item_state == ITEM_ACTIVE
		):
			return _snapshot(idempotent=True)

		demand_info = _approve_returned_demand_for_scn()
		plan_name = frappe.db.get_value(
			"Procurement Plan", {"plan_code": C.PROCUREMENT_PLAN_CODE}, "name"
		)
		if not plan_name:
			raise frappe.ValidationError(f"Missing plan {C.PROCUREMENT_PLAN_CODE}")

		item_022 = _ensure_draft_item(demand=demand_info["demand"], plan_name=plan_name)
		if stop_before_finance:
			frappe.db.commit()
			return _snapshot(idempotent=False, stopped_before_finance=True)

		_ensure_finance(item_022, plan_name)
		if stop_before_approve:
			frappe.db.commit()
			return _snapshot(idempotent=False, stopped_before_approve=True)

		_ensure_approved(plan_name)
		frappe.db.commit()
		return _snapshot(idempotent=False)
	finally:
		frappe.set_user(prev or "Administrator")


def reset(*, force: bool = True) -> dict[str, Any]:
	"""Return to base Planning state (Approved V1 only)."""
	frappe.only_for(("System Manager", "Administrator"))
	frappe.set_user("Administrator")
	_ = force

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
		for di in frappe.get_all("Demand Item", filters={"demand": demand}, pluck="name"):
			frappe.db.set_value(
				"Demand Item",
				di,
				{"confirmed_estimate": 95_000_000, "requester_estimate": 95_000_000},
				update_modified=False,
			)

	if frappe.db.exists("Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}):
		rsv = frappe.db.get_value(
			"Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}, "name"
		)
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
		from kentender_budget.api.dia_budget_control import release_reservation

		release_reservation(
			reservation_id=C.RSV_CODE_SCN, reason="SCN-PLN-ADD-001 reset"
		)
		if frappe.db.exists("Funding Reservation", rsv):
			try:
				frappe.delete_doc(
					"Funding Reservation", rsv, force=1, ignore_permissions=True
				)
			except Exception:
				pass

	base = upsert_planning_base(commit=True)
	return {"ok": bool(base.get("ok")), "base": base}
