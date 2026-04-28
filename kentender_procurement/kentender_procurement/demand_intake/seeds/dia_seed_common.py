# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Phase G — shared helpers for DIA seed packs (G1).

Business IDs DIA-MOH-2026-0001 … 0009 are reserved for demo/smoke data.
Prerequisite budget lines (G2): BL-MOH-2026-001, BL-MOH-2026-002, BL-MOH-2027-001
(run `bench execute kentender_core.seeds.seed_budget_line_dia.run` once per site).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_budget.api.dia_budget_control import get_active_reservation_for_source, release_reservation
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import find_department
from kentender_core.seeds.seed_core_minimal import run as run_core_minimal
from kentender_procurement.demand_intake.api.lifecycle import (
	approve_finance,
	approve_hod,
	cancel_demand,
	mark_planning_ready,
	reject_from_hod,
	submit_demand,
)

DIA_SEED_DEMAND_IDS: tuple[str, ...] = tuple(f"DIA-MOH-2026-{i:04d}" for i in range(1, 10))

U_REQ = "requisitioner@moh.test"
U_HOD = "hod.approver@moh.test"
U_FIN = "finance.reviewer@moh.test"
U_PLAN = "planner@moh.test"


def ensure_core_prerequisites() -> dict:
	"""Idempotent MOH users/departments (no budget writes)."""
	frappe.only_for(("System Manager", "Administrator"))
	return run_core_minimal()


def ensure_budget_line_prerequisites() -> None:
	"""G2 — require DIA budget lines; do not run destructive budget clears here."""
	frappe.only_for(("System Manager", "Administrator"))
	missing: list[str] = []
	for code in ("BL-MOH-2026-001", "BL-MOH-2026-002", "BL-MOH-2027-001"):
		if not frappe.db.exists("Budget Line", {"budget_line_code": code}):
			missing.append(code)
	if missing:
		frappe.throw(
			_(
				"Missing Budget Line(s): {0}. Run:\n"
				"bench --site <site> execute kentender_core.seeds.seed_budget_line_dia.run"
			).format(", ".join(missing)),
			title=_("DIA seed prerequisites"),
		)


def _release_active_reservation_for_demand(demand_name: str) -> None:
	doc = frappe.get_doc("Demand", demand_name)
	rid = (doc.reservation_reference or "").strip()
	if not rid:
		lookup = get_active_reservation_for_source("Demand", demand_name)
		if lookup.get("ok"):
			rid = ((lookup.get("data") or {}).get("reservation_id") or "").strip()
	if not rid:
		return
	release_reservation(rid, reason="DIA seed cleanup", actor=frappe.session.user)


def clear_dia_seed_demands() -> list[str]:
	"""Remove demands with reserved DIA-MOH-2026-0001…0009 IDs (releases reservations first)."""
	frappe.only_for(("System Manager", "Administrator"))
	removed: list[str] = []
	for did in DIA_SEED_DEMAND_IDS:
		name = frappe.db.get_value("Demand", {"demand_id": did}, "name")
		if not name:
			continue
		_release_active_reservation_for_demand(name)
		frappe.delete_doc("Demand", name, force=True, ignore_permissions=True)
		removed.append(did)
	return removed


def _dept_clinical() -> str:
	d = find_department(C.DEPT_CLIN, C.ENTITY_MOH)
	if not d:
		frappe.throw(_("Clinical department not found for MOH. Run seed_core_minimal."), title=_("DIA seed"))
	return d


def _budget_line(code: str = "BL-MOH-2026-001") -> str:
	n = frappe.db.get_value("Budget Line", {"budget_line_code": code}, "name")
	if not n:
		frappe.throw(_("Budget line {0} not found.").format(code), title=_("DIA seed"))
	return n


def _item_row(qty: float, unit_cost: float) -> dict:
	return {
		"item_description": "Seeded catalogue line",
		"category": "Medical supplies",
		"uom": "ea",
		"quantity": qty,
		"estimated_unit_cost": unit_cost,
	}


def _new_demand_dict(
	*,
	title: str,
	demand_id: str,
	requested_by: str,
	demand_type: str = "Planned",
	status: str = "Draft",
	bl_code: str = "BL-MOH-2026-001",
	qty: float = 2,
	unit_cost: float = 5_000.0,
	**extra,
) -> dict:
	rd = extra.pop("request_date", None) or "2026-06-01"
	rq_by = extra.pop("required_by_date", None) or "2026-12-31"
	base = {
		"doctype": "Demand",
		"demand_id": demand_id,
		"title": title,
		"procuring_entity": C.ENTITY_MOH,
		"requesting_department": _dept_clinical(),
		"requested_by": requested_by,
		"request_date": rd,
		"required_by_date": rq_by,
		"priority_level": "Normal",
		"demand_type": demand_type,
		"requisition_type": "Goods",
		"budget_line": _budget_line(bl_code),
		"beneficiary_summary": "Seeded beneficiary / justification summary for DIA pack.",
		"specification_summary": "Seeded specification summary for DIA pack.",
		"delivery_location": "Nairobi HQ",
		"requested_delivery_period_days": 30,
		"items": [_item_row(qty, unit_cost)],
		"status": status,
	}
	base.update(extra)
	return base


def _insert_demand(row: dict) -> frappe.model.document.Document:
	d = frappe.get_doc(row)
	d.flags.ignore_mandatory = True
	d.insert(ignore_permissions=True)
	target = row.get("demand_id")
	if target and frappe.db.get_value("Demand", d.name, "demand_id") != target:
		frappe.db.set_value("Demand", d.name, "demand_id", target)
	return frappe.get_doc("Demand", d.name)


def _as(user: str, fn, *args, **kwargs):
	from kentender_procurement.utils.session_actor import with_optional_user_actor

	def inner():
		return fn(*args, **kwargs)

	return with_optional_user_actor(user, inner)


def _submit(name: str, user: str = U_REQ):
	_as(user, submit_demand, name)


def _hod_approve(name: str):
	_as(U_HOD, approve_hod, name)


def _hod_reject(name: str, reason: str = "Seed: HoD rejection for demo."):
	def _call():
		return reject_from_hod(demand_name=name, rejection_reason=reason)

	_as(U_HOD, _call)


def _fin_approve(name: str):
	_as(U_FIN, approve_finance, name)


def _mark_planning(name: str):
	_as(U_PLAN, mark_planning_ready, name)


def _cancel_approved(name: str, user: str = U_REQ, reason: str = "Seed: cancelled after approval for demo."):
	def _call():
		return cancel_demand(demand_name=name, cancellation_reason=reason)

	_as(user, _call)


def seed_basic_demands() -> dict[str, str]:
	"""G1 — seed_dia_basic: DIA-MOH-2026-0001 … 0006 (smoke contract core)."""
	out: dict[str, str] = {}

	# 0001 — Draft Planned
	d1 = _insert_demand(_new_demand_dict(title="DIA seed 0001 Draft", demand_id="DIA-MOH-2026-0001", requested_by=U_REQ))
	out["DIA-MOH-2026-0001"] = d1.name

	# 0002 — Pending HoD (different owner from HoD for segregation)
	d2 = _insert_demand(_new_demand_dict(title="DIA seed 0002 Pending HoD", demand_id="DIA-MOH-2026-0002", requested_by=U_REQ))
	_submit(d2.name)
	out["DIA-MOH-2026-0002"] = d2.name

	# 0003 — Pending Finance
	d3 = _insert_demand(_new_demand_dict(title="DIA seed 0003 Pending Finance", demand_id="DIA-MOH-2026-0003", requested_by=U_REQ))
	_submit(d3.name)
	_hod_approve(d3.name)
	out["DIA-MOH-2026-0003"] = d3.name

	# 0004 — Approved + Reserved (separate chain; stays Approved for read-only smoke)
	d4 = _insert_demand(_new_demand_dict(title="DIA seed 0004 Approved", demand_id="DIA-MOH-2026-0004", requested_by=U_REQ, qty=3, unit_cost=10_000))
	_submit(d4.name)
	_hod_approve(d4.name)
	_fin_approve(d4.name)
	out["DIA-MOH-2026-0004"] = d4.name

	# 0005 — Planning Ready (second approved demand, then handoff)
	d5 = _insert_demand(_new_demand_dict(title="DIA seed 0005 Planning Ready", demand_id="DIA-MOH-2026-0005", requested_by=U_REQ, qty=1, unit_cost=25_000))
	_submit(d5.name)
	_hod_approve(d5.name)
	_fin_approve(d5.name)
	_mark_planning(d5.name)
	out["DIA-MOH-2026-0005"] = d5.name

	# 0006 — Rejected at HoD
	d6 = _insert_demand(_new_demand_dict(title="DIA seed 0006 HoD Rejected", demand_id="DIA-MOH-2026-0006", requested_by=U_REQ))
	_submit(d6.name)
	_hod_reject(d6.name)
	out["DIA-MOH-2026-0006"] = d6.name

	return out


def seed_extended_demands(*, exceptions_variant: bool = False) -> dict[str, str]:
	"""G1 — seed_dia_extended / seed_dia_exceptions: full DIA-MOH-2026-0001 … 0009."""
	out = seed_basic_demands()

	# 0007 — Cancelled (Approved + reservation, then owner cancel)
	d7 = _insert_demand(
		_new_demand_dict(title="DIA seed 0007 Cancelled", demand_id="DIA-MOH-2026-0007", requested_by=U_REQ, qty=2, unit_cost=15_000)
	)
	_submit(d7.name)
	_hod_approve(d7.name)
	_fin_approve(d7.name)
	_cancel_approved(d7.name)
	out["DIA-MOH-2026-0007"] = d7.name

	# 0008 — Unplanned Draft (exception fields)
	d8 = _insert_demand(
		_new_demand_dict(
			title="DIA seed 0008 Unplanned Draft",
			demand_id="DIA-MOH-2026-0008",
			requested_by=U_REQ,
			demand_type="Unplanned",
			qty=1,
			unit_cost=4_000,
			impact_if_not_procured="Seed impact if not procured (unplanned).",
		)
	)
	out["DIA-MOH-2026-0008"] = d8.name

	# 0009 — Emergency Pending Finance (over budget after HoD approve for finance-fail smoke)
	d9 = _insert_demand(
		_new_demand_dict(
			title="DIA seed 0009 Emergency Over Budget",
			demand_id="DIA-MOH-2026-0009",
			requested_by=U_REQ,
			demand_type="Emergency",
			qty=50_000,
			unit_cost=500_000,
			impact_if_not_procured="Seed emergency impact.",
			emergency_justification="Seed emergency justification for governance demo.",
		)
	)
	_submit(d9.name)
	_hod_approve(d9.name)
	out["DIA-MOH-2026-0009"] = d9.name

	if exceptions_variant:
		# Turn 0002 into a returned draft while keeping the same business ID (queue: Returned).
		name2 = out["DIA-MOH-2026-0002"]
		frappe.delete_doc("Demand", name2, force=True, ignore_permissions=True)
		d2b = _insert_demand(
			_new_demand_dict(
				title="DIA seed 0002 Returned Draft",
				demand_id="DIA-MOH-2026-0002",
				requested_by=U_REQ,
				status="Draft",
				return_reason="Seed: returned from HoD for corrections.",
				returned_by=U_HOD,
				returned_at=now_datetime(),
			)
		)
		out["DIA-MOH-2026-0002"] = d2b.name

	return out
