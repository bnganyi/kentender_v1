# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Purge dev/UAT rows outside the WORKS master seed registry (spec §4.1–4.2).

Removes Playwright smoke rows (e.g. ``WS MasterDetail w*`` / ``WS-MD-w*``), duplicate strategic
plans, extra budgets/demands/packages/tenders, and non-canonical PLC rows.

After purge, run the full WORKS master seed::

    bench --site kentender.midas.com execute \\
      kentender_procurement.procurement_lifecycle.seeds.purge_non_works_master_seed.reset_and_reseed

Or purge only::

    bench --site kentender.midas.com execute \\
      kentender_procurement.procurement_lifecycle.seeds.purge_non_works_master_seed.run \\
      --kwargs '{"dry_run": False}'
"""

from __future__ import annotations

from typing import Any, Final

import frappe

from kentender_budget.seeds.works_master_budget_seed import BUDGET_LINE_CODE, BUDGET_NAME
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import DEMAND_ID
from kentender_procurement.procurement_lifecycle.seeds.purge_plc_outside_works_master_registry import (
	purge_procurement_lifecycle_plc_outside_works_master_registry,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
	PLAN_CODE,
)
from kentender_procurement.tender_management.seeds.purge_smoke_test_tenders import run as purge_smoke_tenders
from kentender_strategy.seeds.works_master_strategy_purge import purge_non_works_strategy_hierarchy

_KEEP_TENDER: Final[str] = "TND-MOH-2026-001"
_KEEP_STD_INSTANCE: Final[str] = "STDINST-TND-MOH-2026-001"


def _purge_budgets(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("Budget", fields=["name", "budget_name"]):
		if (row.get("budget_name") or "").strip() == BUDGET_NAME:
			continue
		removed.append(row["name"])
		if dry_run:
			continue
		frappe.db.sql("UPDATE `tabBudget` SET `status`=%s WHERE `name`=%s", ("Draft", row["name"]))
		for line in frappe.get_all("Budget Line", filters={"budget": row["name"]}, pluck="name"):
			if frappe.db.exists("Budget Line", line):
				frappe.flags.budget_line_force_delete = True
				try:
					frappe.delete_doc("Budget Line", line, force=True, ignore_permissions=True)
				finally:
					frappe.flags.budget_line_force_delete = False
		if frappe.db.exists("Budget", row["name"]):
			frappe.delete_doc("Budget", row["name"], force=True, ignore_permissions=True)
	return removed


def _purge_budget_lines(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("Budget Line", fields=["name", "budget_line_code"]):
		if (row.get("budget_line_code") or "").strip() == BUDGET_LINE_CODE:
			continue
		removed.append(row["name"])
		if not dry_run and frappe.db.exists("Budget Line", row["name"]):
			frappe.flags.budget_line_force_delete = True
			try:
				frappe.delete_doc("Budget Line", row["name"], force=True, ignore_permissions=True)
			finally:
				frappe.flags.budget_line_force_delete = False
	return removed


def _purge_demands(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("Demand", fields=["name", "demand_id"]):
		if (row.get("demand_id") or "").strip() == DEMAND_ID:
			continue
		removed.append(row["name"])
		if dry_run:
			continue
		frappe.db.delete("Demand Item", {"parent": row["name"]})
		if frappe.db.exists("Demand", row["name"]):
			frappe.delete_doc("Demand", row["name"], force=True, ignore_permissions=True)
	return removed


def _purge_procurement_plans(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("Procurement Plan", fields=["name", "plan_code"]):
		if (row.get("plan_code") or row.get("name") or "").strip() == PLAN_CODE:
			continue
		removed.append(row["name"])
		if not dry_run and frappe.db.exists("Procurement Plan", row["name"]):
			frappe.delete_doc("Procurement Plan", row["name"], force=True, ignore_permissions=True)
	return removed


def _purge_procurement_packages(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("Procurement Package", fields=["name", "package_code"]):
		if (row.get("package_code") or row.get("name") or "").strip() == PKG_CODE:
			continue
		removed.append(row["name"])
		if dry_run:
			continue
		frappe.db.delete("Procurement Package Line", {"parent": row["name"]})
		if frappe.db.exists("Procurement Package", row["name"]):
			frappe.delete_doc("Procurement Package", row["name"], force=True, ignore_permissions=True)
	return removed


def _purge_non_master_tenders(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("TM2 Tender", fields=["name", "tender_code"]):
		code = (row.get("tender_code") or row.get("name") or "").strip()
		if code == _KEEP_TENDER:
			continue
		removed.append(row["name"])
		if dry_run:
			continue
		tm2 = row["name"]
		for addendum in frappe.get_all("TM2 Addendum", filters={"tm2_tender": tm2}, pluck="name"):
			for air in frappe.get_all(
				"TM2 Addendum Impact Record",
				filters={"tm2_addendum": addendum},
				pluck="name",
			):
				if frappe.db.exists("TM2 Addendum Impact Record", air):
					frappe.delete_doc("TM2 Addendum Impact Record", air, force=True, ignore_permissions=True)
			if frappe.db.exists("TM2 Addendum", addendum):
				frappe.delete_doc("TM2 Addendum", addendum, force=True, ignore_permissions=True)
		frappe.db.delete("Tender Publication Snapshot", {"tm2_tender": tm2})
		for tbl in (
			"TM2 Tender Timeline",
			"TM2 Tender Access Rule",
			"TM2 Tender Audit Event",
			"TM2 Tender STD Binding",
			"TM2 Tender Closing Record",
			"TM2 Tender Invitation",
		):
			frappe.db.delete(tbl, {"tm2_tender": tm2})
		for inst in frappe.get_all("Tender STD Instance", filters={"tm2_tender": tm2}, pluck="name"):
			if inst == _KEEP_STD_INSTANCE:
				continue
			for tbl in (
				"Tender STD Generated Output",
				"Tender STD Instance BOQ",
				"Tender STD Instance Snapshot",
			):
				frappe.db.delete(tbl, {"tender_std_instance": inst})
			if frappe.db.exists("Tender STD Instance", inst):
				frappe.delete_doc("Tender STD Instance", inst, force=True, ignore_permissions=True)
		if frappe.db.exists("TM2 Tender", tm2):
			frappe.delete_doc("TM2 Tender", tm2, force=True, ignore_permissions=True)
	return removed


def purge_non_works_master_seed(*, dry_run: bool = False) -> dict[str, Any]:
	"""Delete rows outside the WORKS master seed registry (see module docstring)."""
	frappe.set_user("Administrator")

	strategy = purge_non_works_strategy_hierarchy(
		dry_run=dry_run,
		delete_blocking_demands_and_budget_lines=not dry_run,
	)

	result: dict[str, Any] = {
		"ok": bool(strategy.get("ok")),
		"dry_run": dry_run,
		"strategy_purge": strategy,
		"removed": {},
	}

	result["removed"]["budgets"] = _purge_budgets(dry_run=dry_run)
	result["removed"]["budget_lines"] = _purge_budget_lines(dry_run=dry_run)
	result["removed"]["demands"] = _purge_demands(dry_run=dry_run)
	result["removed"]["procurement_plans"] = _purge_procurement_plans(dry_run=dry_run)
	result["removed"]["procurement_packages"] = _purge_procurement_packages(dry_run=dry_run)
	result["removed"]["tm2_tenders"] = _purge_non_master_tenders(dry_run=dry_run)

	if dry_run:
		result["would_run"] = {
			"purge_smoke_test_tenders": True,
			"purge_plc_outside_registry": True,
		}
	else:
		result["purge_smoke_test_tenders"] = purge_smoke_tenders()
		result["purge_plc_outside_registry"] = purge_procurement_lifecycle_plc_outside_works_master_registry(
			dry_run=False
		)
		frappe.db.commit()
		result["ok"] = bool(strategy.get("ok")) and not strategy.get("skipped_strategic_plans")

	result["counts"] = {k: len(v) for k, v in result["removed"].items()}
	result["counts"]["strategic_plans"] = len(strategy.get("removed_strategic_plans") or [])
	return result


def reset_and_reseed(*, checkpoint: str = "TENDER_PUBLISHED") -> dict[str, Any]:
	"""Purge non-master rows, reload full WORKS master seed, validate."""
	from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
		validate_procurement_lifecycle_works_master_seed,
	)
	from kentender_procurement.procurement_lifecycle.seeds.works_master_full_seed import (
		run_works_master_full_seed,
	)
	from kentender_strategy.seeds.works_master_strategy_purge import verify_works_master_strategy_seed

	purge = purge_non_works_master_seed(dry_run=False)
	seed = run_works_master_full_seed(checkpoint=checkpoint, reset=True)
	validate = validate_procurement_lifecycle_works_master_seed(checkpoint=checkpoint)
	strategy_verify = verify_works_master_strategy_seed()
	frappe.db.commit()
	return {
		"ok": bool(purge.get("ok") and seed.get("ok") and validate.get("ok") and strategy_verify.get("ok")),
		"purge": purge,
		"seed": seed,
		"validate": validate,
		"strategy_verify": strategy_verify,
	}


def run(*, dry_run: bool = False) -> dict[str, Any]:
	"""Console entry point for purge-only."""
	return purge_non_works_master_seed(dry_run=dry_run)
