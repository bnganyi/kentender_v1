# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Purge dev/UAT rows outside the stable platform seed registry (Works + IT)."""

from __future__ import annotations

from typing import Any, Final

import frappe

from kentender_budget.seeds.works_master_budget_seed import BUDGET_LINE_CODE as WORKS_BUDGET_LINE_CODE
from kentender_budget.seeds.works_master_budget_seed import BUDGET_NAME
from kentender_core.seeds.stable_platform_seed.constants import (
	IT_BUDGET_LINE_CODE,
	IT_DEMAND_CODE,
	IT_INCLUSION_CODE,
	IT_PKG_CODE,
	IT_STD_FAMILY_CODE,
	IT_STD_VERSION_CODE,
	WORKS_DEMAND_CODE,
	WORKS_JOURNEY_CODE,
	WORKS_PKG_CODE,
	WORKS_PLAN_CODE,
)
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import DEMAND_ID as WORKS_DEMAND_ID
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
	BASE_HANDOFF_CODES,
	JOURNEY_CODE,
	OPENING_HANDOFF_CODES,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE as WORKS_PKG_CODE_LEGACY,
	PLAN_CODE,
)
from kentender_procurement.tender_management.seeds.purge_smoke_test_tenders import run as purge_smoke_tenders
from kentender_strategy.seeds.works_master_strategy_purge import purge_non_works_strategy_hierarchy

_KEEP_DEMAND_CODES: Final[frozenset[str]] = frozenset({WORKS_DEMAND_CODE, WORKS_DEMAND_ID, IT_DEMAND_CODE})
_KEEP_BUDGET_NAMES: Final[frozenset[str]] = frozenset({BUDGET_NAME})
_KEEP_BUDGET_LINE_CODES: Final[frozenset[str]] = frozenset({WORKS_BUDGET_LINE_CODE, IT_BUDGET_LINE_CODE})
_KEEP_PLAN_CODES: Final[frozenset[str]] = frozenset({WORKS_PLAN_CODE, PLAN_CODE})
_KEEP_PKG_CODES: Final[frozenset[str]] = frozenset({WORKS_PKG_CODE, WORKS_PKG_CODE_LEGACY, IT_PKG_CODE})
_KEEP_TENDER: Final[str] = "TND-MOH-2026-001"
_KEEP_STD_INSTANCE: Final[str] = "STDINST-TND-MOH-2026-001"
_KEEP_JOURNEYS: Final[frozenset[str]] = frozenset({WORKS_JOURNEY_CODE, JOURNEY_CODE})
_KEEP_HANDOFF_CODES: Final[frozenset[str]] = frozenset(
	tuple(BASE_HANDOFF_CODES) + tuple(OPENING_HANDOFF_CODES) + (IT_INCLUSION_CODE,)
)

_TM2_DOCTYPES: Final[tuple[str, ...]] = (
	"TM2 Tender",
	"TM2 Addendum",
	"TM2 Addendum Impact Record",
	"Tender Publication Snapshot",
	"TM2 Tender Timeline",
	"TM2 Tender Access Rule",
	"TM2 Tender Audit Event",
	"TM2 Tender STD Binding",
	"TM2 Tender Closing Record",
	"TM2 Tender Invitation",
	"Tender STD Instance",
	"Tender STD Generated Output",
	"Tender STD Instance BOQ",
	"Tender STD Instance Snapshot",
)


def _tm2_module_available() -> bool:
	return bool(frappe.db.exists("DocType", "TM2 Tender"))


def _doctype_exists(doctype: str) -> bool:
	return bool(frappe.db.exists("DocType", doctype))

_PKG_CHILD_DOCTYPES: Final[tuple[tuple[str, str], ...]] = (
	("Package Review Decision", "package_code"),
	("Package Readiness Result", "package_code"),
	("Package Method Decision", "package_code"),
	("Planning Correction Supersession Record", "package_code"),
)


def _delete_package_lines(package_code: str) -> None:
	for line_name in frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": package_code},
		pluck="name",
	):
		frappe.flags.skip_package_line_rollup = True
		try:
			if frappe.db.exists("Procurement Package Line", line_name):
				frappe.delete_doc("Procurement Package Line", line_name, force=True, ignore_permissions=True)
		finally:
			frappe.flags.pop("skip_package_line_rollup", None)


def _delete_package_cascade(package_code: str) -> None:
	pkg = (package_code or "").strip()
	if not pkg:
		return
	for doctype, field in _PKG_CHILD_DOCTYPES:
		for name in frappe.get_all(doctype, filters={field: pkg}, pluck="name"):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
	_delete_package_lines(pkg)
	if frappe.db.exists("Procurement Package", pkg):
		frappe.delete_doc("Procurement Package", pkg, force=True, ignore_permissions=True)


def _purge_budgets(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("Budget", fields=["name", "budget_name"]):
		if (row.get("budget_name") or "").strip() in _KEEP_BUDGET_NAMES:
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
		if (row.get("budget_line_code") or "").strip() in _KEEP_BUDGET_LINE_CODES:
			continue
		removed.append(row["name"])
		if dry_run or not frappe.db.exists("Budget Line", row["name"]):
			continue
		frappe.flags.budget_line_force_delete = True
		try:
			frappe.delete_doc("Budget Line", row["name"], force=True, ignore_permissions=True)
		finally:
			frappe.flags.budget_line_force_delete = False
	return removed


def _purge_demands(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("Demand", fields=["name", "demand_id"]):
		if (row.get("demand_id") or "").strip() in _KEEP_DEMAND_CODES:
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
		code = (row.get("plan_code") or row.get("name") or "").strip()
		if code in _KEEP_PLAN_CODES:
			continue
		removed.append(row["name"])
		if not dry_run and frappe.db.exists("Procurement Plan", row["name"]):
			frappe.delete_doc("Procurement Plan", row["name"], force=True, ignore_permissions=True)
	return removed


def _purge_procurement_packages(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("Procurement Package", fields=["name", "package_code"]):
		code = (row.get("package_code") or row.get("name") or "").strip()
		if code in _KEEP_PKG_CODES:
			continue
		removed.append(row["name"])
		if dry_run:
			continue
		_delete_package_cascade(code)
	return removed


def _purge_non_master_tenders(*, dry_run: bool) -> list[str]:
	if not _tm2_module_available():
		return []
	removed: list[str] = []
	for row in frappe.get_all("TM2 Tender", fields=["name", "tender_code"]):
		code = (row.get("tender_code") or row.get("name") or "").strip()
		if code == _KEEP_TENDER:
			continue
		removed.append(row["name"])
		if dry_run:
			continue
		tm2 = row["name"]
		if _doctype_exists("TM2 Addendum"):
			for addendum in frappe.get_all("TM2 Addendum", filters={"tm2_tender": tm2}, pluck="name"):
				if _doctype_exists("TM2 Addendum Impact Record"):
					for air in frappe.get_all(
						"TM2 Addendum Impact Record",
						filters={"tm2_addendum": addendum},
						pluck="name",
					):
						if frappe.db.exists("TM2 Addendum Impact Record", air):
							frappe.delete_doc("TM2 Addendum Impact Record", air, force=True, ignore_permissions=True)
				if frappe.db.exists("TM2 Addendum", addendum):
					frappe.delete_doc("TM2 Addendum", addendum, force=True, ignore_permissions=True)
		if _doctype_exists("Tender Publication Snapshot"):
			frappe.db.delete("Tender Publication Snapshot", {"tm2_tender": tm2})
		for tbl in (
			"TM2 Tender Timeline",
			"TM2 Tender Access Rule",
			"TM2 Tender Audit Event",
			"TM2 Tender STD Binding",
			"TM2 Tender Closing Record",
			"TM2 Tender Invitation",
		):
			if _doctype_exists(tbl):
				frappe.db.delete(tbl, {"tm2_tender": tm2})
		if _doctype_exists("Tender STD Instance"):
			for inst in frappe.get_all("Tender STD Instance", filters={"tm2_tender": tm2}, pluck="name"):
				if inst == _KEEP_STD_INSTANCE:
					continue
				for tbl in (
					"Tender STD Generated Output",
					"Tender STD Instance BOQ",
					"Tender STD Instance Snapshot",
				):
					if _doctype_exists(tbl):
						frappe.db.delete(tbl, {"tender_std_instance": inst})
				if frappe.db.exists("Tender STD Instance", inst):
					frappe.delete_doc("Tender STD Instance", inst, force=True, ignore_permissions=True)
		if frappe.db.exists("TM2 Tender", tm2):
			frappe.delete_doc("TM2 Tender", tm2, force=True, ignore_permissions=True)
	return removed


def _handoff_is_canonical(row: dict[str, Any]) -> bool:
	code = (row.get("handoff_code") or row.get("name") or "").strip()
	jc = (row.get("journey_code") or "").strip()
	if code not in _KEEP_HANDOFF_CODES:
		return False
	return jc in _KEEP_JOURNEYS


def _purge_plc_outside_stable_registry(*, dry_run: bool) -> dict[str, Any]:
	handoffs = frappe.get_all(
		"Procurement Handoff Card",
		fields=["name", "handoff_code", "journey_code"],
	)
	handoffs_to_remove = [h for h in handoffs if not _handoff_is_canonical(h)]

	journeys = frappe.get_all("Procurement Journey", fields=["name", "journey_code"])
	journeys_to_remove = [j for j in journeys if (j.get("journey_code") or j.get("name") or "").strip() not in _KEEP_JOURNEYS]

	if dry_run:
		return {
			"ok": True,
			"dry_run": True,
			"would_delete_handoff_cards": [h["name"] for h in handoffs_to_remove],
			"would_delete_journeys": [j["name"] for j in journeys_to_remove],
		}

	deleted_handoffs: list[str] = []
	for h in handoffs_to_remove:
		name = h["name"]
		if frappe.db.exists("Procurement Handoff Card", name):
			frappe.delete_doc("Procurement Handoff Card", name, force=True, ignore_permissions=True)
			deleted_handoffs.append(name)

	deleted_journeys: list[str] = []
	for j in journeys_to_remove:
		name = j["name"]
		if frappe.db.exists("Procurement Journey", name):
			frappe.delete_doc("Procurement Journey", name, force=True, ignore_permissions=True)
			deleted_journeys.append(name)

	return {
		"ok": True,
		"dry_run": False,
		"deleted_handoff_cards": deleted_handoffs,
		"deleted_journeys": deleted_journeys,
		"counts": {"handoff_cards": len(deleted_handoffs), "journeys": len(deleted_journeys)},
	}


def _purge_std_versions(*, dry_run: bool) -> list[str]:
	from kentender_procurement.std_engine.package_import.draft_cleanup import clear_draft_package_state

	removed: list[str] = []
	for row in frappe.get_all("STD Version", fields=["name", "lifecycle_state", "family_code"]):
		code = (row.get("name") or "").strip()
		if code == IT_STD_VERSION_CODE:
			continue
		removed.append(code)
		if dry_run:
			continue
		lifecycle = (row.get("lifecycle_state") or "").strip()
		family = (row.get("family_code") or "").strip() or None
		if lifecycle == "ACTIVE":
			continue
		clear_draft_package_state(code, family_code=family if family != IT_STD_FAMILY_CODE else None)
	return removed


def purge_non_stable_platform_seed(*, dry_run: bool = False) -> dict[str, Any]:
	"""Delete rows outside the stable platform registry while keeping Works + IT seed codes."""
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
	result["removed"]["std_versions"] = _purge_std_versions(dry_run=dry_run)

	if dry_run:
		result["would_run"] = {
			"purge_smoke_test_tenders": _tm2_module_available(),
			"purge_plc_outside_registry": True,
		}
	else:
		if _tm2_module_available():
			result["purge_smoke_test_tenders"] = purge_smoke_tenders()
		else:
			result["purge_smoke_test_tenders"] = {"skipped": True, "reason": "tm2_module_unavailable"}
		result["purge_plc_outside_registry"] = _purge_plc_outside_stable_registry(dry_run=False)
		frappe.db.commit()
		result["ok"] = bool(strategy.get("ok")) and not strategy.get("skipped_strategic_plans")

	result["counts"] = {k: len(v) for k, v in result["removed"].items()}
	result["counts"]["strategic_plans"] = len(strategy.get("removed_strategic_plans") or [])
	return result
