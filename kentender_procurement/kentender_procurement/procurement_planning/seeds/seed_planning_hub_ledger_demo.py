# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning Hub ledger demo seed — purge junk plans + realistic status mix.

Keeps the WORKS master active plan (``PLAN-MOH-2026``) and four companion rows
covering Draft, Closed, Superseded, and Cancelled for hub ledger / badge testing.

Deletes every other ``Procurement Plan`` (e.g. governance-test ``PP-CMP-*`` rows).

Run::

    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_planning.seeds.seed_planning_hub_ledger_demo.run
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_procurement.procurement_planning.pp2_constants import (
	PLAN_CANCELLED,
	PLAN_CLOSED,
	PLAN_DRAFT,
	PLAN_SUPERSEDED,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	CURRENCY,
	PLAN_CODE as MASTER_PLAN_CODE,
	PLAN_PLANNING_CYCLE_CODE,
)

_KEEP_PLAN_CODES: frozenset[str] = frozenset(
	{
		MASTER_PLAN_CODE,
		"PLAN-MOH-2027",
		"PLAN-MOH-2025",
		"PLAN-MOH-2024",
		"PLAN-MOH-2023-CXL",
	}
)

_DEMO_PLANS: tuple[dict[str, Any], ...] = (
	{
		"plan_code": "PLAN-MOH-2027",
		"plan_name": "Ministry of Health Procurement Plan FY 2027/2028",
		"plan_description": (
			"Draft procurement plan for the upcoming fiscal year. "
			"Awaiting final budget allocation and Planning Authority approval."
		),
		"fiscal_year": 2027,
		"planning_cycle_code": "BUDGET-MOH-2027",
		"status": PLAN_DRAFT,
		"is_active": 1,
		"total_planned_value": 920_000_000.0,
	},
	{
		"plan_code": "PLAN-MOH-2025",
		"plan_name": "Ministry of Health Procurement Plan FY 2025/2026",
		"plan_description": (
			"Closed procurement plan for FY 2025/2026. All packages were released or "
			"closed before the fiscal year end."
		),
		"fiscal_year": 2025,
		"planning_cycle_code": "BUDGET-MOH-2025",
		"status": PLAN_CLOSED,
		"is_active": 0,
		"total_planned_value": 1_100_000_000.0,
	},
	{
		"plan_code": "PLAN-MOH-2024",
		"plan_name": "Ministry of Health Procurement Plan FY 2024/2025",
		"plan_description": (
			"Superseded by the FY 2025/2026 plan after a mid-cycle restructuring of "
			"Works programme priorities."
		),
		"fiscal_year": 2024,
		"planning_cycle_code": "BUDGET-MOH-2024",
		"status": PLAN_SUPERSEDED,
		"is_active": 0,
		"total_planned_value": 875_000_000.0,
	},
	{
		"plan_code": "PLAN-MOH-2023-CXL",
		"plan_name": "Ministry of Health Procurement Plan FY 2023/2024",
		"plan_description": (
			"Cancelled before activation due to a national budget reallocation in Q1 FY 2023/2024."
		),
		"fiscal_year": 2023,
		"planning_cycle_code": "BUDGET-MOH-2023",
		"status": PLAN_CANCELLED,
		"is_active": 0,
		"total_planned_value": 640_000_000.0,
		"workflow_reason": "National exchequer reallocation — plan cycle deferred.",
	},
)


def _resolve_entity() -> str:
	entity = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOH"}, "name")
	if entity:
		return entity
	entity = frappe.db.get_value("Procuring Entity", {"entity_code": "MOH"}, "name")
	if entity:
		return entity
	frappe.throw("Procuring Entity PE-MOH not found.", title="MISSING_PROCURING_ENTITY")


def _purge_extra_plans(*, dry_run: bool = False) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("Procurement Plan", fields=["name", "plan_code"]):
		code = (row.get("plan_code") or row.get("name") or "").strip()
		if code in _KEEP_PLAN_CODES:
			continue
		removed.append(code or row["name"])
		if dry_run:
			continue
		if frappe.db.exists("Procurement Plan", row["name"]):
			frappe.delete_doc("Procurement Plan", row["name"], force=True, ignore_permissions=True)
	return removed


def _upsert_demo_plan(*, entity: str, spec: dict[str, Any]) -> dict[str, Any]:
	code = str(spec["plan_code"]).strip()
	target_status = spec["status"]
	base_values = {
		"plan_name": spec["plan_name"],
		"plan_code": code,
		"plan_description": spec.get("plan_description") or "",
		"fiscal_year": int(spec["fiscal_year"]),
		"planning_cycle_code": spec.get("planning_cycle_code") or PLAN_PLANNING_CYCLE_CODE,
		"procuring_entity": entity,
		"currency": CURRENCY,
		"is_active": int(spec.get("is_active", 0)),
		"is_master_seed": 0,
	}
	if spec.get("workflow_reason"):
		base_values["workflow_reason"] = spec["workflow_reason"]

	action = "updated"
	if not frappe.db.exists("Procurement Plan", code):
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				**base_values,
				"status": PLAN_DRAFT,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		action = "created"

	frappe.db.set_value(
		"Procurement Plan",
		code,
		{
			**base_values,
			"status": target_status,
			"total_planned_value": flt(spec.get("total_planned_value") or 0),
		},
		update_modified=True,
	)
	return {"plan_code": code, "status": target_status, "action": action}


def seed_planning_hub_ledger_demo(*, dry_run: bool = False) -> dict[str, Any]:
	"""Purge non-canonical plans and upsert the hub ledger demo set."""
	frappe.set_user("Administrator")
	if not frappe.db.exists("DocType", "Procurement Plan"):
		frappe.throw("Procurement Plan DocType is not installed.")

	if not frappe.db.exists("Procurement Plan", MASTER_PLAN_CODE):
		frappe.throw(
			f"WORKS master plan {MASTER_PLAN_CODE} is missing. "
			"Run seed_procurement_planning_works_master first.",
			title="MISSING_MASTER_PLAN",
		)

	removed = _purge_extra_plans(dry_run=dry_run)
	upserted: list[dict[str, Any]] = []
	if not dry_run:
		entity = _resolve_entity()
		for spec in _DEMO_PLANS:
			upserted.append(_upsert_demo_plan(entity=entity, spec=spec))
		frappe.db.commit()

	statuses = {MASTER_PLAN_CODE: "Active"}
	statuses.update({row["plan_code"]: row["status"] for row in _DEMO_PLANS})
	return {
		"ok": True,
		"dry_run": dry_run,
		"kept_plan_codes": sorted(_KEEP_PLAN_CODES),
		"removed_plan_codes": removed,
		"upserted": upserted,
		"status_by_code": statuses,
		"ledger_count": len(_KEEP_PLAN_CODES),
	}


def run(*, dry_run: bool = False) -> dict[str, Any]:
	"""Console entry point."""
	return seed_planning_hub_ledger_demo(dry_run=dry_run)
