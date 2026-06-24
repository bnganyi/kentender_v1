# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7 cross-module regression — shared snapshots and planning pipeline helpers."""

from __future__ import annotations

import subprocess
from typing import Any

import frappe
from frappe.utils import add_days, today

from kentender_budget.api.dia_budget_control import get_budget_line_context
from kentender_core.seeds import constants as C
from kentender_core.seeds._common import ensure_currency_kes, ensure_department
from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_lifecycle.demand_journey_bootstrap import (
	ensure_procurement_journey_for_demand_code,
)
from kentender_procurement.procurement_planning.pp2_constants import PLAN_ACTIVE, PLAN_DRAFT, READINESS_PASSED
from kentender_procurement.procurement_planning.services.package_creation_service import (
	create_package_from_planning_inclusion,
)
from kentender_procurement.procurement_planning.services.package_method_decision_service import (
	record_package_method_decision,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	run_package_readiness_checks,
)
from kentender_procurement.procurement_planning.services.package_release_service import (
	mark_package_ready_for_release,
	release_package_to_tender_management,
)
from kentender_procurement.procurement_planning.services.package_review_service import (
	record_package_review_decision,
	submit_package_for_review,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	include_demand_in_procurement_plan,
)

_DEMAND_AUTHORITY_FIELDS = (
	"title",
	"total_amount",
	"status",
	"budget_line",
	"demand_id",
	"finance_approved_by",
	"finance_approved_at",
	"hod_approved_by",
	"hod_approved_at",
	"reservation_reference",
	"reservation_status",
)

_BUDGET_AUTHORITY_FIELDS = (
	"title",
	"budget_line_code",
	"fiscal_year",
	"amount_allocated",
	"amount_available",
	"amount_reserved",
	"amount_consumed",
	"is_active",
	"strategic_plan",
	"program",
	"sub_program",
)

_WORKS_METHOD_PAYLOAD = {
	"procurement_category": "Works",
	"procurement_method": "Open Tender",
	"required_std_category": "Works",
	"required_std_type": "Building and Associated Civil Engineering Works",
	"method_basis": "Template",
	"override_flag": False,
}


def demand_authority_snapshot(demand_name: str) -> dict[str, Any]:
	"""Capture upstream demand fields Planning must not mutate (PP2-REG-001)."""
	row = frappe.db.get_value("Demand", demand_name, _DEMAND_AUTHORITY_FIELDS, as_dict=True)
	return dict(row or {})


def budget_authority_snapshot(budget_line_name: str) -> dict[str, Any]:
	"""Capture budget line authority fields Planning must not mutate (PP2-REG-002)."""
	row = frappe.db.get_value("Budget Line", budget_line_name, _BUDGET_AUTHORITY_FIELDS, as_dict=True)
	return dict(row or {})


def seed_budget_line() -> tuple[str | None, str | None, str | None, str | None]:
	ensure_currency_kes()
	bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": "BL-MOH-2026-001"}, "name")
	if not bl_name:
		bl_name = frappe.db.get_value(
			"Budget Line",
			{"procuring_entity": C.ENTITY_MOH, "is_active": 1},
			"name",
			order_by="modified desc",
		)
	if not bl_name:
		bl_name = frappe.db.get_value(
			"Budget Line",
			{"is_active": 1},
			"name",
			order_by="modified desc",
		)
	if not bl_name:
		return None, None, None, None
	ctx = get_budget_line_context(bl_name)
	if not ctx.get("ok"):
		return None, None, None, None
	ent = (ctx.get("data") or {}).get("procuring_entity")
	dept = ensure_department(f"Dept P7 {frappe.generate_hash(length=4)}", ent)
	bl_code = (ctx.get("data") or {}).get("budget_line_code") or bl_name
	return bl_name, ent, dept, bl_code


def mk_active_plan(track: list[tuple[str, str]]) -> str:
	plan = frappe.get_doc(
		{
			"doctype": "Procurement Plan",
			"plan_name": f"P7 plan {frappe.generate_hash(length=4)}",
			"plan_code": f"PP-P7-{frappe.generate_hash()[:6]}",
			"fiscal_year": 2029,
			"procuring_entity": C.ENTITY_MOH,
			"currency": "KES",
			"status": PLAN_DRAFT,
			"is_active": 1,
		}
	)
	plan.insert(ignore_permissions=True)
	frappe.db.set_value("Procurement Plan", plan.name, "status", PLAN_ACTIVE, update_modified=False)
	track.append(("Procurement Plan", plan.name))
	return plan.name


def mk_approved_demand(
	bl_name: str,
	entity: str,
	dept: str,
	track: list[tuple[str, str]],
	*,
	requisition_type: str = "Works",
	total_amount: float = 500_000.0,
) -> frappe.model.document.Document:
	doc = frappe.get_doc(
		{
			"doctype": "Demand",
			"title": f"P7 demand {frappe.generate_hash(length=4)}",
			"demand_id": f"DEM-P7-{frappe.generate_hash()[:8]}",
			"procuring_entity": entity,
			"requesting_department": dept,
			"request_date": today(),
			"required_by_date": today(),
			"requisition_type": requisition_type,
			"priority_level": "Normal",
			"demand_type": "Planned",
			"specification_summary": "P7 regression scope",
			"budget_line": bl_name,
			"items": [
				{
					"item_description": "P7 line",
					"category": "c",
					"uom": "ea",
					"quantity": 1,
					"estimated_unit_cost": total_amount,
				}
			],
		}
	)
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	frappe.db.set_value("Demand", doc.name, "status", "Approved", update_modified=False)
	doc.reload()
	track.append(("Demand", doc.name))
	return doc


def _journey_suffix(journey_code: str) -> str:
	jc = (journey_code or "").strip()
	if jc.upper().startswith("JRN-"):
		return jc[4:]
	return jc


def seed_upstream_handoffs(
	journey_code: str,
	demand_code: str,
	budget_line_code: str,
	track: list[tuple[str, str]],
) -> None:
	suffix = _journey_suffix(journey_code)
	cards = (
		(
			f"DEMAPP-{suffix}",
			"Demand Approval Certificate",
			"Demand Intake and Approval",
			"Procurement Planning",
			"Demand",
			demand_code,
		),
		(
			f"BUDCONF-{suffix}",
			"Budget Funding Confirmation",
			"Budget",
			"Demand Intake and Approval",
			"Budget Line",
			budget_line_code,
		),
	)
	for handoff_code, title, source_mod, target_mod, src_type, src_code in cards:
		create_or_update_handoff_card(
			{
				"handoff_code": handoff_code,
				"handoff_title": title,
				"journey_code": journey_code,
				"source_module": source_mod,
				"target_module": target_mod,
				"status": "Consumed",
				"next_action": "Proceed to procurement planning.",
				"source_object_type": src_type,
				"source_object_code": src_code,
			}
		)
		track.append(("Procurement Handoff Card", handoff_code))


def require_active_template() -> str | None:
	tpl = frappe.get_all("Procurement Template", filters={"is_active": 1}, limit=1, pluck="name")
	if not tpl:
		return None
	row = frappe.db.get_value(
		"Procurement Template",
		tpl[0],
		("risk_profile_id", "kpi_profile_id", "vendor_management_profile_id"),
		as_dict=True,
	)
	if not row or not all(row.values()):
		return None
	return tpl[0]


def run_planning_pipeline_through_release(
	track: list[tuple[str, str]],
	*,
	with_release: bool = True,
	through: str = "release",
) -> dict[str, str]:
	"""Include → package → … → optional release.

	:param through: ``package`` after create; ``approved`` after review approve;
	    ``ready`` after mark-ready; ``release`` full path (subject to ``with_release``).
	"""
	if not require_active_template():
		raise RuntimeError("No active Procurement Template with profiles available")

	bl_name, entity, dept, bl_code = seed_budget_line()
	if not bl_name:
		raise RuntimeError("No budget line available for P7 pipeline")
	plan_name = mk_active_plan(track)
	demand = mk_approved_demand(bl_name, entity, dept, track)
	item_code = f"DEMITEM-P7-{frappe.generate_hash()[:8]}"
	frappe.db.commit()

	journey_code = ensure_procurement_journey_for_demand_code(demand.demand_id) or ""
	if journey_code:
		track.append(("Procurement Journey", journey_code))

	incl = include_demand_in_procurement_plan(
		demand.demand_id,
		[item_code],
		plan_name,
		"Administrator",
	)
	inclusion_code = incl.get("inclusion_code") or ""
	if inclusion_code:
		track.append(("Procurement Handoff Card", inclusion_code))

	pkg_out = create_package_from_planning_inclusion(inclusion_code, "Administrator")
	package_code = pkg_out.get("package_code") or ""
	if not package_code:
		raise RuntimeError(f"Package creation failed: {pkg_out}")
	track.append(("Procurement Package", package_code))
	for lc in pkg_out.get("package_line_codes") or []:
		track.append(("Procurement Package Line", lc))
	if journey_code:
		frappe.db.set_value(
			"Procurement Package",
			package_code,
			"journey_code",
			journey_code,
			update_modified=False,
		)

	if through == "package":
		return {
			"demand_name": demand.name,
			"demand_id": demand.demand_id,
			"budget_line_name": bl_name,
			"budget_line_code": bl_code,
			"plan_name": plan_name,
			"package_code": package_code,
			"journey_code": journey_code,
			"release_code": "",
			"inclusion_code": inclusion_code,
			"readiness_code": "",
		}

	record_package_method_decision(package_code, _WORKS_METHOD_PAYLOAD, "Administrator")
	submit_package_for_review(package_code, "Administrator")
	record_package_review_decision(package_code, {"decision": "Approved"}, "Administrator")
	if journey_code:
		seed_upstream_handoffs(journey_code, demand.demand_id, bl_code, track)
	frappe.db.set_value(
		"Procurement Package",
		package_code,
		{"schedule_start": today(), "schedule_end": add_days(today(), 30)},
		update_modified=False,
	)
	readiness_out = run_package_readiness_checks(package_code, "Administrator")
	readiness_code = readiness_out.get("readiness_code") or ""
	if readiness_code:
		track.append(("Package Readiness Result", readiness_code))
	if (readiness_out.get("result_status") or "").strip() != READINESS_PASSED:
		raise RuntimeError(f"Readiness did not pass: {readiness_out}")

	if through == "approved":
		return {
			"demand_name": demand.name,
			"demand_id": demand.demand_id,
			"budget_line_name": bl_name,
			"budget_line_code": bl_code,
			"plan_name": plan_name,
			"package_code": package_code,
			"journey_code": journey_code,
			"release_code": "",
			"inclusion_code": inclusion_code,
			"readiness_code": readiness_code,
		}

	mark_package_ready_for_release(package_code, "Administrator")

	if through == "ready":
		return {
			"demand_name": demand.name,
			"demand_id": demand.demand_id,
			"budget_line_name": bl_name,
			"budget_line_code": bl_code,
			"plan_name": plan_name,
			"package_code": package_code,
			"journey_code": journey_code,
			"release_code": "",
			"inclusion_code": inclusion_code,
			"readiness_code": readiness_code,
		}

	release_code = ""
	if with_release and through == "release":
		from unittest.mock import MagicMock, patch

		xmv = MagicMock()
		xmv.has_critical.return_value = False
		with patch.multiple(
			"kentender_procurement.procurement_planning.services.package_release_service",
			deliver_procurement_package_release=MagicMock(),
			package_has_release_tender=MagicMock(return_value=True),
			validate_package_for_release_xmv=MagicMock(return_value=xmv),
		):
			rel = release_package_to_tender_management(package_code, "Administrator")
		release_code = rel.get("release_code") or ""
		if release_code:
			track.append(("Procurement Handoff Card", release_code))

	return {
		"demand_name": demand.name,
		"demand_id": demand.demand_id,
		"budget_line_name": bl_name,
		"budget_line_code": bl_code,
		"plan_name": plan_name,
		"package_code": package_code,
		"journey_code": journey_code,
		"release_code": release_code,
		"inclusion_code": inclusion_code,
		"readiness_code": readiness_code,
	}


def run_bench_test_module(site: str, *, app: str, module: str) -> subprocess.CompletedProcess[str]:
	"""Run a single Frappe test module via bench (P7-006..010 gates)."""
	return subprocess.run(
		["bench", "--site", site, "run-tests", "--app", app, "--module", module],
		cwd="/home/midasuser/frappe-bench",
		capture_output=True,
		text=True,
	)


def assert_module_gate_passes(site: str, *, app: str, modules: list[str]) -> None:
	failures: list[str] = []
	for module in modules:
		proc = run_bench_test_module(site, app=app, module=module)
		if proc.returncode != 0:
			failures.append(
				f"{module} exit={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
			)
	if failures:
		raise AssertionError("Module regression gate failed:\n" + "\n---\n".join(failures))
