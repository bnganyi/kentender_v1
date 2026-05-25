# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Per-fixture setup functions for NEG-PP2 loaders (setup-only; no blocker assertions)."""

from __future__ import annotations

from typing import Any, Callable

import frappe

from kentender_procurement.procurement_planning.seeds.negative_fixtures import bootstrap
from kentender_procurement.procurement_planning.seeds.negative_fixtures.constants import (
	FIXTURE_NEG_PP2_BUDGET_MISSING,
	FIXTURE_NEG_PP2_DEMAND_NOT_APPROVED,
	FIXTURE_NEG_PP2_DUP_DEMANDITEM,
	FIXTURE_NEG_PP2_METHOD_MISSING,
	FIXTURE_NEG_PP2_PKG_NO_LINE,
	FIXTURE_NEG_PP2_POST_RELEASE_EDIT,
	FIXTURE_NEG_PP2_READINESS_STALE,
	FIXTURE_NEG_PP2_RELEASE_STALE,
	FIXTURE_NEG_PP2_STD_MISSING,
	FIXTURE_NEG_PP2_SUPPLIER_ACCESS,
	FIXTURE_NEG_PP2_TENDER_BASELINE_MISMATCH,
	FIXTURE_NEG_PP2_TOTAL_MISMATCH,
	NEG_ENTITY_CODES,
	SUPPLIER_TEST_USER,
)
from kentender_procurement.procurement_planning.services.package_method_decision_service import (
	record_package_method_decision,
)

SetupFn = Callable[[], dict[str, Any]]


def _codes(fixture_code: str) -> dict[str, str]:
	return dict(NEG_ENTITY_CODES[fixture_code])


def setup_demand_not_approved() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_DEMAND_NOT_APPROVED)
	bootstrap.ensure_pp2_prerequisites()
	bl_name, entity, dept, _bl_code = bootstrap.resolve_budget_line()
	if not bl_name:
		frappe.throw("Budget line unavailable for NEG fixture.", title="NEG_FIXTURE_SETUP")
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_demand(
		demand_code=codes["demand_code"],
		budget_line=bl_name,
		entity=entity,
		dept=dept,
		status="Submitted",
	)
	bootstrap.upsert_journey(journey_code=codes["journey_code"], demand_code=codes["demand_code"])
	return {
		"records": codes,
		"context": {
			"plan_code": codes["plan_code"],
			"demand_code": codes["demand_code"],
			"demand_item_code": f"DEMITEM-{codes['demand_code']}",
		},
	}


def setup_budget_missing() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_BUDGET_MISSING)
	bootstrap.ensure_pp2_prerequisites()
	_, entity, dept, _bl_code = bootstrap.resolve_budget_line()
	if not entity:
		frappe.throw("Procuring entity unavailable for NEG fixture.", title="NEG_FIXTURE_SETUP")
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_demand(
		demand_code=codes["demand_code"],
		budget_line=None,
		entity=entity,
		dept=dept,
		status="Approved",
	)
	bootstrap.upsert_journey(journey_code=codes["journey_code"], demand_code=codes["demand_code"])
	return {
		"records": codes,
		"context": {
			"plan_code": codes["plan_code"],
			"demand_code": codes["demand_code"],
			"demand_item_code": f"DEMITEM-{codes['demand_code']}",
		},
	}


def setup_dup_demanditem() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_DUP_DEMANDITEM)
	bootstrap.ensure_pp2_prerequisites()
	bl_name, entity, dept, bl_code = bootstrap.resolve_budget_line()
	if not bl_name:
		frappe.throw("Budget line unavailable for NEG fixture.", title="NEG_FIXTURE_SETUP")
	plan_code = codes["plan_code"]
	demand_code = codes["demand_code"]
	demand_code_b = f"{demand_code}-B"
	item_code = codes["demand_item_code"]
	journey_code = codes["journey_code"]
	bootstrap.upsert_plan(plan_code=plan_code)
	bootstrap.upsert_demand(
		demand_code=demand_code,
		budget_line=bl_name,
		entity=entity,
		dept=dept,
	)
	bootstrap.upsert_demand(
		demand_code=demand_code_b,
		budget_line=bl_name,
		entity=entity,
		dept=dept,
	)
	bootstrap.upsert_journey(journey_code=journey_code, demand_code=demand_code)

	first = bootstrap.include_and_package(
		demand_code=demand_code,
		plan_code=plan_code,
		journey_code=journey_code,
		demand_item_code=item_code,
		inclusion_code=codes["inclusion_code"],
		package_code=codes["package_code_a"],
	)
	bootstrap.upsert_empty_package(
		plan_code=plan_code,
		package_code=codes["package_code_b"],
		journey_code=journey_code,
	)
	bootstrap.add_active_package_line(
		package_code=codes["package_code_b"],
		demand_code=demand_code_b,
		budget_line=bl_name,
		demand_item_code=item_code,
	)
	return {
		"records": {**codes, "package_code": codes["package_code_a"], "package_code_b": codes["package_code_b"]},
		"context": {
			"demand_item_code": item_code,
			"package_code_a": first["package_code"],
			"package_code_b": codes["package_code_b"],
			"demand_code_b": demand_code_b,
		},
	}


def setup_pkg_no_line() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_PKG_NO_LINE)
	bootstrap.ensure_pp2_prerequisites()
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_empty_package(
		plan_code=codes["plan_code"],
		package_code=codes["package_code"],
		journey_code=codes["journey_code"],
	)
	return {
		"records": codes,
		"context": {"package_code": codes["package_code"]},
	}


def setup_total_mismatch() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_TOTAL_MISMATCH)
	bootstrap.ensure_pp2_prerequisites()
	bl_name, entity, dept, bl_code = bootstrap.resolve_budget_line()
	if not bl_name:
		frappe.throw("Budget line unavailable for NEG fixture.", title="NEG_FIXTURE_SETUP")
	item_code = f"DEMITEM-{codes['demand_code']}"
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_demand(
		demand_code=codes["demand_code"],
		budget_line=bl_name,
		entity=entity,
		dept=dept,
	)
	bootstrap.upsert_journey(journey_code=codes["journey_code"], demand_code=codes["demand_code"])
	out = bootstrap.include_and_package(
		demand_code=codes["demand_code"],
		plan_code=codes["plan_code"],
		journey_code=codes["journey_code"],
		demand_item_code=item_code,
		inclusion_code=codes["inclusion_code"],
		package_code=codes["package_code"],
	)
	frappe.db.set_value(
		"Procurement Package",
		codes["package_code"],
		"estimated_value",
		250000,
		update_modified=False,
	)
	line_name = frappe.db.get_value(
		"Procurement Package Line",
		{"package_id": codes["package_code"], "is_active": 1},
		"name",
	)
	if line_name:
		frappe.db.set_value("Procurement Package Line", line_name, "amount", 100000, update_modified=False)
	record_package_method_decision(codes["package_code"], bootstrap._WORKS_METHOD, bootstrap.SEED_ACTOR)
	bootstrap.seed_upstream_handoffs(
		journey_code=codes["journey_code"],
		demand_code=codes["demand_code"],
		budget_line_code=bl_code,
	)
	return {
		"records": {**codes, **out},
		"context": {"package_code": codes["package_code"], "budget_line_code": bl_code},
	}


def setup_method_missing() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_METHOD_MISSING)
	bootstrap.ensure_pp2_prerequisites()
	bl_name, entity, dept, bl_code = bootstrap.resolve_budget_line()
	if not bl_name:
		frappe.throw("Budget line unavailable for NEG fixture.", title="NEG_FIXTURE_SETUP")
	item_code = f"DEMITEM-{codes['demand_code']}"
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_demand(
		demand_code=codes["demand_code"],
		budget_line=bl_name,
		entity=entity,
		dept=dept,
	)
	bootstrap.upsert_journey(journey_code=codes["journey_code"], demand_code=codes["demand_code"])
	out = bootstrap.include_and_package(
		demand_code=codes["demand_code"],
		plan_code=codes["plan_code"],
		journey_code=codes["journey_code"],
		demand_item_code=item_code,
		inclusion_code=codes["inclusion_code"],
		package_code=codes["package_code"],
	)
	bootstrap.seed_package_missing_method(package_code=codes["package_code"])
	bootstrap.seed_upstream_handoffs(
		journey_code=codes["journey_code"],
		demand_code=codes["demand_code"],
		budget_line_code=bl_code,
	)
	return {
		"records": {**codes, **out},
		"context": {"package_code": codes["package_code"]},
	}


def setup_std_missing() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_STD_MISSING)
	bootstrap.ensure_pp2_prerequisites()
	bl_name, entity, dept, bl_code = bootstrap.resolve_budget_line()
	if not bl_name:
		frappe.throw("Budget line unavailable for NEG fixture.", title="NEG_FIXTURE_SETUP")
	item_code = f"DEMITEM-{codes['demand_code']}"
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_demand(
		demand_code=codes["demand_code"],
		budget_line=bl_name,
		entity=entity,
		dept=dept,
	)
	bootstrap.upsert_journey(journey_code=codes["journey_code"], demand_code=codes["demand_code"])
	out = bootstrap.include_and_package(
		demand_code=codes["demand_code"],
		plan_code=codes["plan_code"],
		journey_code=codes["journey_code"],
		demand_item_code=item_code,
		inclusion_code=codes["inclusion_code"],
		package_code=codes["package_code"],
	)
	bootstrap.seed_method_decision_missing_std(
		method_decision_code=codes["method_decision_code"],
		package_code=codes["package_code"],
	)
	bootstrap.seed_upstream_handoffs(
		journey_code=codes["journey_code"],
		demand_code=codes["demand_code"],
		budget_line_code=bl_code,
	)
	return {
		"records": {**codes, **out},
		"context": {"package_code": codes["package_code"], "method_decision_code": codes["method_decision_code"]},
	}


def setup_readiness_stale() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_READINESS_STALE)
	bootstrap.ensure_pp2_prerequisites()
	bl_name, entity, dept, bl_code = bootstrap.resolve_budget_line()
	if not bl_name:
		frappe.throw("Budget line unavailable for NEG fixture.", title="NEG_FIXTURE_SETUP")
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_demand(
		demand_code=codes["demand_code"],
		budget_line=bl_name,
		entity=entity,
		dept=dept,
	)
	bootstrap.upsert_journey(journey_code=codes["journey_code"], demand_code=codes["demand_code"])
	item_code = f"DEMITEM-{codes['demand_code']}"
	out = bootstrap.build_ready_for_release(
		plan_code=codes["plan_code"],
		demand_code=codes["demand_code"],
		journey_code=codes["journey_code"],
		inclusion_code=codes["inclusion_code"],
		package_code=codes["package_code"],
		demand_item_code=item_code,
		budget_line_code=bl_code,
	)
	bootstrap.mark_readiness_stale(codes["package_code"])
	return {
		"records": {**codes, **out},
		"context": {"package_code": codes["package_code"], "readiness_code": out.get("readiness_code")},
	}


def setup_release_stale() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_RELEASE_STALE)
	bootstrap.ensure_pp2_prerequisites()
	bl_name, entity, dept, bl_code = bootstrap.resolve_budget_line()
	if not bl_name:
		frappe.throw("Budget line unavailable for NEG fixture.", title="NEG_FIXTURE_SETUP")
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_demand(
		demand_code=codes["demand_code"],
		budget_line=bl_name,
		entity=entity,
		dept=dept,
	)
	bootstrap.upsert_journey(journey_code=codes["journey_code"], demand_code=codes["demand_code"])
	item_code = f"DEMITEM-{codes['demand_code']}"
	bootstrap.build_ready_for_release(
		plan_code=codes["plan_code"],
		demand_code=codes["demand_code"],
		journey_code=codes["journey_code"],
		inclusion_code=codes["inclusion_code"],
		package_code=codes["package_code"],
		demand_item_code=item_code,
		budget_line_code=bl_code,
	)
	release_code = bootstrap.release_package(
		package_code=codes["package_code"],
		journey_code=codes["journey_code"],
		release_code=codes["release_code"],
	)
	bootstrap.upsert_tm2_tender(
		tender_code=codes["tender_code"],
		package_code=codes["package_code"],
		plan_name=codes["plan_code"],
	)
	frappe.db.set_value(
		"Procurement Package",
		codes["package_code"],
		"estimated_value",
		999999,
		update_modified=True,
	)
	return {
		"records": {**codes, "release_code": release_code},
		"context": {
			"package_code": codes["package_code"],
			"release_code": release_code,
			"tender_code": codes["tender_code"],
		},
	}


def setup_post_release_edit() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_POST_RELEASE_EDIT)
	bootstrap.ensure_pp2_prerequisites()
	bl_name, entity, dept, bl_code = bootstrap.resolve_budget_line()
	if not bl_name:
		frappe.throw("Budget line unavailable for NEG fixture.", title="NEG_FIXTURE_SETUP")
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_demand(
		demand_code=codes["demand_code"],
		budget_line=bl_name,
		entity=entity,
		dept=dept,
	)
	bootstrap.upsert_journey(journey_code=codes["journey_code"], demand_code=codes["demand_code"])
	item_code = f"DEMITEM-{codes['demand_code']}"
	bootstrap.build_ready_for_release(
		plan_code=codes["plan_code"],
		demand_code=codes["demand_code"],
		journey_code=codes["journey_code"],
		inclusion_code=codes["inclusion_code"],
		package_code=codes["package_code"],
		demand_item_code=item_code,
		budget_line_code=bl_code,
	)
	release_code = bootstrap.release_package(
		package_code=codes["package_code"],
		journey_code=codes["journey_code"],
		release_code=codes["release_code"],
	)
	return {
		"records": {**codes, "release_code": release_code},
		"context": {"package_code": codes["package_code"], "release_code": release_code},
	}


def setup_tender_baseline_mismatch() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_TENDER_BASELINE_MISMATCH)
	bootstrap.ensure_pp2_prerequisites()
	bl_name, entity, dept, bl_code = bootstrap.resolve_budget_line()
	if not bl_name:
		frappe.throw("Budget line unavailable for NEG fixture.", title="NEG_FIXTURE_SETUP")
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_demand(
		demand_code=codes["demand_code"],
		budget_line=bl_name,
		entity=entity,
		dept=dept,
	)
	bootstrap.upsert_journey(journey_code=codes["journey_code"], demand_code=codes["demand_code"])
	item_code = f"DEMITEM-{codes['demand_code']}"
	bootstrap.build_ready_for_release(
		plan_code=codes["plan_code"],
		demand_code=codes["demand_code"],
		journey_code=codes["journey_code"],
		inclusion_code=codes["inclusion_code"],
		package_code=codes["package_code"],
		demand_item_code=item_code,
		budget_line_code=bl_code,
	)
	release_code = bootstrap.release_package(
		package_code=codes["package_code"],
		journey_code=codes["journey_code"],
		release_code=codes["release_code"],
	)
	bootstrap.upsert_tm2_tender(
		tender_code=codes["tender_code"],
		package_code=codes["package_code"],
		plan_name=codes["plan_code"],
		procurement_method="Restricted Tender",
		procurement_category="Goods",
	)
	return {
		"records": {**codes, "release_code": release_code},
		"context": {
			"package_code": codes["package_code"],
			"release_code": release_code,
			"tender_code": codes["tender_code"],
		},
	}


def setup_supplier_access() -> dict[str, Any]:
	codes = _codes(FIXTURE_NEG_PP2_SUPPLIER_ACCESS)
	bootstrap.ensure_pp2_prerequisites()
	bootstrap.upsert_plan(plan_code=codes["plan_code"])
	bootstrap.upsert_empty_package(
		plan_code=codes["plan_code"],
		package_code=codes["package_code"],
		journey_code="JRN-NEG-SUPPLIER-ACCESS-001",
	)
	return {
		"records": codes,
		"context": {
			"plan_code": codes["plan_code"],
			"package_code": codes["package_code"],
			"supplier_user": SUPPLIER_TEST_USER,
			"doctype": "Procurement Plan",
		},
	}


SETUP_BY_FIXTURE: dict[str, SetupFn] = {
	FIXTURE_NEG_PP2_DEMAND_NOT_APPROVED: setup_demand_not_approved,
	FIXTURE_NEG_PP2_BUDGET_MISSING: setup_budget_missing,
	FIXTURE_NEG_PP2_DUP_DEMANDITEM: setup_dup_demanditem,
	FIXTURE_NEG_PP2_PKG_NO_LINE: setup_pkg_no_line,
	FIXTURE_NEG_PP2_TOTAL_MISMATCH: setup_total_mismatch,
	FIXTURE_NEG_PP2_METHOD_MISSING: setup_method_missing,
	FIXTURE_NEG_PP2_STD_MISSING: setup_std_missing,
	FIXTURE_NEG_PP2_READINESS_STALE: setup_readiness_stale,
	FIXTURE_NEG_PP2_RELEASE_STALE: setup_release_stale,
	FIXTURE_NEG_PP2_POST_RELEASE_EDIT: setup_post_release_edit,
	FIXTURE_NEG_PP2_TENDER_BASELINE_MISMATCH: setup_tender_baseline_mismatch,
	FIXTURE_NEG_PP2_SUPPLIER_ACCESS: setup_supplier_access,
}
