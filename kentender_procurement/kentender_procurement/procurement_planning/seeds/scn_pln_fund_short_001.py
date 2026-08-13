# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SCN-PLN-FUND-SHORT-001 — optional 80/25/55 shortfall on PPI-MOH-2027-022 (Demo v2.7 §7.7)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.mvp1_constants import (
	FINANCE_AWAITING,
)
from kentender_procurement.procurement_planning.seeds import scn_pln_add_001 as add_scn

HOLD_AMOUNT = 55_000_000.0
HOLD_LABEL = "Concurrent workforce funding hold — scenario only"
SCENARIO_DEMAND_CODE = "SCN-PLN-FUND-SHORT-001"


def setup(*, force: bool = True) -> dict[str, Any]:
	"""Base bundle + ADD-001 through Proposed PPI-022 (before Finance / V2 approve)."""
	frappe.only_for(("System Manager", "Administrator"))
	base = add_scn.setup(force=force)
	prepared = add_scn.run(reset_first=False, force=force, stop_before_approve=True)
	return {"ok": bool(base.get("ok") and prepared.get("ok")), "base": base, "prepared": prepared}


def run(*, reset_first: bool = False, force: bool = True) -> dict[str, Any]:
	frappe.only_for(("System Manager", "Administrator"))
	prev = frappe.session.user
	frappe.set_user("Administrator")
	try:
		return _run(reset_first=reset_first, force=force)
	finally:
		frappe.set_user(prev if prev else "Administrator")


def _run(*, reset_first: bool = False, force: bool = True) -> dict[str, Any]:
	if reset_first:
		setup(force=force)
	else:
		add_scn.run(reset_first=False, force=force, stop_before_approve=True)

	item_name = frappe.db.get_value(
		"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}, "name"
	)
	if not item_name:
		raise frappe.ValidationError("SCN-PLN-FUND-SHORT-001 requires Proposed PPI-MOH-2027-022")

	_detach_scn_reservation()
	hold = _ensure_short_hold()
	_complete_and_request_finance(item_name)

	line = frappe.db.get_value("Budget Line", {"generated_reference": C.BL_HWD_2027}, "name")
	approved = flt(frappe.db.get_value("Budget Line", line, "approved_amount"))
	reserved = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
	committed = flt(frappe.db.get_value("Budget Line", line, "amount_committed"))
	available = approved - reserved - committed
	shortfall = max(0.0, C.PLAN_ITEM_SCN_AMOUNT - available)
	iv = frappe.db.get_value("Procurement Plan Item", item_name, "draft_item_version")
	finance_status = (
		frappe.db.get_value("Procurement Plan Item Version", iv, "finance_status") if iv else ""
	)
	frappe.db.commit()
	return {
		"ok": True,
		"idempotent": bool(hold.get("idempotent")),
		"plan_item": item_name,
		"plan_item_code": C.PLAN_ITEM_CODE_SCN,
		"version_code": C.PROCUREMENT_PLAN_VERSION_V2,
		"finance_status": finance_status,
		"hold": C.RSV_SHORT_CODE,
		"amount_required": C.PLAN_ITEM_SCN_AMOUNT,
		"available": available,
		"shortfall": shortfall,
	}


def reset(*, force: bool = True) -> dict[str, Any]:
	"""Release/delete only the scenario hold. Do not touch RSV-MOH-0001."""
	frappe.only_for(("System Manager", "Administrator"))
	frappe.set_user("Administrator")
	_ = force
	_release_short_hold()
	frappe.db.commit()
	return {"ok": True, "hold": C.RSV_SHORT_CODE, "released": True}


def _detach_scn_reservation() -> None:
	"""ADD-001 pre-creates RSV-MOH-0002; shortfall must not own that reservation."""
	rsv_name = frappe.db.get_value(
		"Funding Reservation", {"generated_reference": C.RSV_CODE_SCN}, "name"
	)
	if rsv_name:
		for dfa in frappe.get_all(
			"Demand Funding Allocation",
			filters={"funding_reservation": rsv_name},
			pluck="name",
		):
			frappe.db.set_value(
				"Demand Funding Allocation",
				dfa,
				{"funding_reservation": "", "reservation_status": ""},
				update_modified=False,
			)
		remaining = flt(
			frappe.db.get_value("Funding Reservation", rsv_name, "remaining_reserved")
		)
		line = frappe.db.get_value("Funding Reservation", rsv_name, "budget_line")
		status = frappe.db.get_value("Funding Reservation", rsv_name, "status")
		if line and remaining and status in ("Reserved", "Partially converted"):
			cur = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
			frappe.db.set_value(
				"Budget Line",
				line,
				"amount_reserved",
				max(0.0, cur - remaining),
				update_modified=False,
			)
		frappe.delete_doc("Funding Reservation", rsv_name, force=1, ignore_permissions=True)

	item_name = frappe.db.get_value(
		"Procurement Plan Item", {"plan_item_code": C.PLAN_ITEM_CODE_SCN}, "name"
	)
	if item_name:
		for iv in frappe.get_all(
			"Procurement Plan Item Version", filters={"plan_item": item_name}, pluck="name"
		):
			if (
				frappe.db.get_value("Procurement Plan Item Version", iv, "reservation_reference")
				== C.RSV_CODE_SCN
			):
				frappe.db.set_value(
					"Procurement Plan Item Version",
					iv,
					"reservation_reference",
					"",
					update_modified=False,
				)
		for alloc in frappe.get_all(
			"Plan Demand Allocation", filters={"plan_item": item_name}, pluck="name"
		):
			if (
				frappe.db.get_value("Plan Demand Allocation", alloc, "reservation_reference")
				== C.RSV_CODE_SCN
			):
				frappe.db.set_value(
					"Plan Demand Allocation",
					alloc,
					"reservation_reference",
					"",
					update_modified=False,
				)


def _ensure_short_hold() -> dict[str, Any]:
	line = frappe.db.get_value("Budget Line", {"generated_reference": C.BL_HWD_2027}, "name")
	if not line:
		raise frappe.ValidationError(f"Missing Budget Line {C.BL_HWD_2027}")
	budget = frappe.db.get_value("Budget Line", line, "budget")
	existing = frappe.db.get_value(
		"Funding Reservation", {"generated_reference": C.RSV_SHORT_CODE}, "name"
	)
	if existing:
		status = frappe.db.get_value("Funding Reservation", existing, "status")
		if status in ("Reserved", "Partially converted"):
			return {"name": existing, "idempotent": True}
		frappe.delete_doc("Funding Reservation", existing, force=1, ignore_permissions=True)

	rsv = frappe.get_doc(
		{
			"doctype": "Funding Reservation",
			"generated_reference": C.RSV_SHORT_CODE,
			"budget": budget,
			"budget_line": line,
			"original_amount": HOLD_AMOUNT,
			"remaining_reserved": HOLD_AMOUNT,
			"status": "Reserved",
			"currency": "KES",
			"demand_code": SCENARIO_DEMAND_CODE,
			"demand_title": HOLD_LABEL,
			"event_date": C.FIXTURE_DATE,
			"plan_item_code": "",
			"fixture_namespace": C.FIXTURE_NS,
		}
	)
	rsv.insert(ignore_permissions=True)
	cur = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
	frappe.db.set_value(
		"Budget Line",
		line,
		"amount_reserved",
		cur + HOLD_AMOUNT,
		update_modified=True,
	)
	return {"name": rsv.name, "idempotent": False}


def _complete_and_request_finance(item_name: str) -> None:
	"""Mark PPI-022 complete + Awaiting. DHP planner cannot write HRMD-owned 022."""
	frappe.set_user("Administrator")
	iv_name = frappe.db.get_value("Procurement Plan Item", item_name, "draft_item_version")
	if not iv_name:
		raise frappe.ValidationError("Draft Plan Item Version missing for PPI-MOH-2027-022")
	status = frappe.db.get_value("Procurement Plan Item Version", iv_name, "finance_status")
	if status == FINANCE_AWAITING:
		return
	iv = frappe.get_doc("Procurement Plan Item Version", iv_name)
	iv.requirement_description = "Complete for Finance confirmation"
	iv.procurement_category = "ICT infrastructure and services"
	iv.procurement_method = "Open tender"
	iv.arrangement = "Single year"
	iv.lotting_decision = "Single lot"
	iv.ms_invitation_published = "2027-09-15"
	iv.ms_tender_opening = "2027-10-20"
	iv.ms_evaluation_completed = "2027-11-15"
	iv.ms_award_approval = "2027-12-15"
	iv.ms_contract_signature = "2028-01-15"
	iv.ms_delivery_completion = "2028-03-31"
	iv.finance_status = FINANCE_AWAITING
	iv.save(ignore_permissions=True)


def _release_short_hold() -> None:
	name = frappe.db.get_value(
		"Funding Reservation", {"generated_reference": C.RSV_SHORT_CODE}, "name"
	)
	if not name:
		return
	from kentender_budget.api.dia_budget_control import release_reservation

	release_reservation(reservation_id=C.RSV_SHORT_CODE)
	if frappe.db.exists("Funding Reservation", name):
		frappe.delete_doc("Funding Reservation", name, force=1, ignore_permissions=True)
