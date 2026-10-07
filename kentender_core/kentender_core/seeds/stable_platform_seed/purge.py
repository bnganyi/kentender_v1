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
WORKS_PKG_CODE_LEGACY = "PKG-MOH-2026-001"
PLAN_CODE = "PLAN-MOH-2026"
from kentender_strategy.seeds.works_master_strategy_purge import purge_non_works_strategy_hierarchy
from kentender_core.services.command_write_guard import purge_doc

_KEEP_DEMAND_CODES: Final[frozenset[str]] = frozenset({WORKS_DEMAND_CODE, IT_DEMAND_CODE})
_KEEP_BUDGET_NAMES: Final[frozenset[str]] = frozenset({BUDGET_NAME})
_KEEP_BUDGET_LINE_CODES: Final[frozenset[str]] = frozenset({WORKS_BUDGET_LINE_CODE, IT_BUDGET_LINE_CODE})
_KEEP_PLAN_CODES: Final[frozenset[str]] = frozenset({WORKS_PLAN_CODE, PLAN_CODE})
_KEEP_PKG_CODES: Final[frozenset[str]] = frozenset({WORKS_PKG_CODE, WORKS_PKG_CODE_LEGACY, IT_PKG_CODE})
_KEEP_JOURNEYS: Final[frozenset[str]] = frozenset({WORKS_JOURNEY_CODE})
_KEEP_HANDOFF_CODES: Final[frozenset[str]] = frozenset((IT_INCLUSION_CODE,))

def _doctype_exists(doctype: str) -> bool:
	return bool(frappe.db.exists("DocType", doctype))


def _hard_delete(doctype: str, name: str) -> None:
	"""Force-delete without flooding Redis RQ (bulk seed purge)."""
	if not frappe.db.exists(doctype, name):
		return
	# frappe.delete_doc enqueues link cleanup unless in_test (now=True).
	was = bool(getattr(frappe.flags, "in_test", False))
	frappe.flags.in_test = True
	try:
		# command-only doctypes (Budget, Planning, ...) open their own maintenance window
		purge_doc(doctype, name)
	finally:
		frappe.flags.in_test = was

_PKG_CHILD_DOCTYPES: Final[tuple[tuple[str, str], ...]] = (
	("Package Review Decision", "package_code"),
	("Package Readiness Result", "package_code"),
	("Package Method Decision", "package_code"),
	("Planning Correction Supersession Record", "package_code"),
)


def _delete_package_lines(package_code: str) -> None:
	"""PP2 Package Line DocType retired."""
	return


def _delete_package_cascade(package_code: str) -> None:
	"""PP2 Package DocType retired."""
	return


def _purge_budgets(*, dry_run: bool) -> list[str]:
	# MVP-1 Budget: identity is generated_reference (legacy field was budget_name).
	if not _doctype_exists("Procurement Budget"):
		return []
	removed: list[str] = []
	for row in frappe.get_all("Procurement Budget", fields=["name", "generated_reference", "title"]):
		code = (row.get("generated_reference") or row.get("title") or "").strip()
		if code in _KEEP_BUDGET_NAMES or row["name"] in _KEEP_BUDGET_NAMES:
			continue
		removed.append(row["name"])
		if dry_run:
			continue
		frappe.db.sql("UPDATE `tabProcurement Budget` SET `status`=%s WHERE `name`=%s", ("Draft", row["name"]))
		for line in frappe.get_all("Procurement Budget Line", filters={"budget": row["name"]}, pluck="name"):
			frappe.flags.budget_line_force_delete = True
			try:
				_hard_delete("Procurement Budget Line", line)
			finally:
				frappe.flags.budget_line_force_delete = False
		_hard_delete("Procurement Budget", row["name"])
	return removed


def _purge_budget_lines(*, dry_run: bool) -> list[str]:
	# MVP-1 Budget Line: identity is generated_reference (legacy was budget_line_code).
	if not _doctype_exists("Procurement Budget Line"):
		return []
	removed: list[str] = []
	for row in frappe.get_all("Procurement Budget Line", fields=["name", "generated_reference", "title"]):
		code = (row.get("generated_reference") or row.get("title") or "").strip()
		if code in _KEEP_BUDGET_LINE_CODES:
			continue
		removed.append(row["name"])
		if dry_run:
			continue
		frappe.flags.budget_line_force_delete = True
		try:
			_hard_delete("Procurement Budget Line", row["name"])
		finally:
			frappe.flags.budget_line_force_delete = False
	return removed


def _purge_demands(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	for row in frappe.get_all("Demand", fields=["name", "demand_code", "demand_id"]):
		code = (row.get("demand_code") or row.get("demand_id") or "").strip()
		if code in _KEEP_DEMAND_CODES:
			continue
		removed.append(row["name"])
		if dry_run:
			continue
		frappe.db.delete("Demand Item", {"parent": row["name"]})
		_hard_delete("Demand", row["name"])
	return removed


def _purge_procurement_plans(*, dry_run: bool) -> list[str]:
	removed: list[str] = []
	if not _doctype_exists("Procurement Plan"):
		return removed
	for row in frappe.get_all("Procurement Plan", fields=["name", "plan_code"]):
		code = (row.get("plan_code") or row.get("name") or "").strip()
		if code in _KEEP_PLAN_CODES:
			continue
		removed.append(row["name"])
		if not dry_run:
			_hard_delete("Procurement Plan", row["name"])
	return removed


def _purge_procurement_packages(*, dry_run: bool) -> list[str]:
	"""PP2 Package DocType retired."""
	return []


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
			_hard_delete("Procurement Handoff Card", name)
			deleted_handoffs.append(name)

	deleted_journeys: list[str] = []
	for j in journeys_to_remove:
		name = j["name"]
		if frappe.db.exists("Procurement Journey", name):
			_hard_delete("Procurement Journey", name)
			deleted_journeys.append(name)

	return {
		"ok": True,
		"dry_run": False,
		"deleted_handoff_cards": deleted_handoffs,
		"deleted_journeys": deleted_journeys,
		"counts": {"handoff_cards": len(deleted_handoffs), "journeys": len(deleted_journeys)},
	}


def _purge_std_versions(*, dry_run: bool) -> list[str]:
	"""No-op: the STD Engine package registry was retired on 2026-09-05.

	The ``STD Version`` DocType and its dependents were deleted outright, so
	there is nothing left to purge. Returns an empty list rather than querying
	a dropped table.
	"""
	return []


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
	result["removed"]["std_versions"] = _purge_std_versions(dry_run=dry_run)

	if dry_run:
		result["would_run"] = {"purge_plc_outside_registry": True}
	else:
		result["purge_plc_outside_registry"] = _purge_plc_outside_stable_registry(dry_run=False)
		frappe.db.commit()
		result["ok"] = bool(strategy.get("ok")) and not strategy.get("skipped_strategic_plans")

	result["counts"] = {k: len(v) for k, v in result["removed"].items()}
	result["counts"]["strategic_plans"] = len(strategy.get("removed_strategic_plans") or [])
	return result
