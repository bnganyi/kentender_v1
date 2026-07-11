# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clear stable platform seed data before regeneration."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.stable_platform_seed.constants import (
	IT_BUDGET_LINE_CODE,
	IT_DEMAND_CODE,
	IT_INCLUSION_CODE,
	IT_OBJECTIVE_CODE,
	IT_PKG_CODE,
	IT_PKG_LINE_CODE,
	IT_PROGRAM_CODE,
	IT_STD_FAMILY_CODE,
	IT_STD_VERSION_CODE,
	IT_SUB_PROGRAM_CODE,
	IT_TARGET_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.clear import (
	run_clear as clear_pp2_works_planning,
)


def _dev_or_test_clear_allowed() -> bool:
	if frappe.in_test:
		return True
	if getattr(frappe.conf, "developer_mode", False):
		return True
	if getattr(frappe.conf, "allow_tests", False):
		return True
	return False


def _delete_doc(doctype: str, name: str, deleted: dict[str, int]) -> None:
	if not name or not frappe.db.exists(doctype, name):
		return
	frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
	deleted[doctype] = deleted.get(doctype, 0) + 1


def _clear_it_planning(*, deleted: dict[str, int]) -> None:
	for doctype, filter_field in (
		("Package Method Decision", "package_code"),
		("Package Readiness Result", "package_code"),
		("Package Review Decision", "package_code"),
	):
		for name in frappe.get_all(doctype, filters={filter_field: IT_PKG_CODE}, pluck="name"):
			_delete_doc(doctype, name, deleted)

	line_name = frappe.db.get_value(
		"Procurement Package Line",
		{"package_line_code": IT_PKG_LINE_CODE},
		"name",
	)
	if line_name:
		frappe.flags.skip_package_line_rollup = True
		try:
			_delete_doc("Procurement Package Line", line_name, deleted)
		finally:
			frappe.flags.pop("skip_package_line_rollup", None)

	for line_name in frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": IT_PKG_CODE},
		pluck="name",
	):
		frappe.flags.skip_package_line_rollup = True
		try:
			_delete_doc("Procurement Package Line", line_name, deleted)
		finally:
			frappe.flags.pop("skip_package_line_rollup", None)

	_delete_doc("Procurement Package", IT_PKG_CODE, deleted)
	_delete_doc("Procurement Handoff Card", IT_INCLUSION_CODE, deleted)


def _clear_it_demand(*, deleted: dict[str, int]) -> None:
	demand_name = frappe.db.get_value("Demand", {"demand_id": IT_DEMAND_CODE}, "name")
	if not demand_name:
		return
	frappe.db.delete("Demand Item", {"parent": demand_name})
	_delete_doc("Demand", demand_name, deleted)


def _clear_it_budget_line(*, deleted: dict[str, int]) -> None:
	line_name = frappe.db.get_value("Budget Line", {"budget_line_code": IT_BUDGET_LINE_CODE}, "name")
	if not line_name:
		return
	frappe.flags.budget_line_force_delete = True
	try:
		_delete_doc("Budget Line", line_name, deleted)
	finally:
		frappe.flags.budget_line_force_delete = False


def _clear_it_strategy(*, deleted: dict[str, int]) -> None:
	plan_name = None
	program_name = frappe.db.get_value(
		"Strategy Program",
		{"program_code": IT_PROGRAM_CODE},
		"name",
	)
	if program_name:
		plan_name = frappe.db.get_value("Strategy Program", program_name, "strategic_plan")

	prev_status = None
	if plan_name and frappe.db.exists("Strategic Plan", plan_name):
		prev_status = frappe.db.get_value("Strategic Plan", plan_name, "status")
		if (prev_status or "").strip() != "Draft":
			frappe.db.set_value("Strategic Plan", plan_name, "status", "Draft", update_modified=False)

	sub_program_name = None
	if program_name:
		sub_program_name = frappe.db.get_value(
			"Sub Program",
			{"program": program_name, "sub_program_code": IT_SUB_PROGRAM_CODE},
			"name",
		)

	objective_name = None
	if sub_program_name:
		objective_name = frappe.db.get_value(
			"Strategy Objective",
			{"sub_program": sub_program_name, "objective_code": IT_OBJECTIVE_CODE},
			"name",
		)

	target_name = None
	if objective_name:
		target_name = frappe.db.get_value(
			"Strategy Target",
			{"objective": objective_name, "target_code": IT_TARGET_CODE},
			"name",
		)

	for doctype, name in (
		("Strategy Target", target_name),
		("Strategy Objective", objective_name),
		("Sub Program", sub_program_name),
		("Strategy Program", program_name),
	):
		_delete_doc(doctype, name or "", deleted)

	if plan_name and prev_status and (prev_status or "").strip() != "Draft":
		frappe.db.set_value("Strategic Plan", plan_name, "status", prev_status, update_modified=False)


def _clear_it_std_draft() -> dict[str, Any]:
	from kentender_procurement.std_engine.package_import.draft_cleanup import clear_draft_package_state

	if not frappe.db.exists("STD Version", IT_STD_VERSION_CODE):
		return {"cleared": False, "reason": "not_imported"}
	lifecycle = frappe.db.get_value("STD Version", IT_STD_VERSION_CODE, "lifecycle_state")
	if lifecycle == "ACTIVE":
		return {"cleared": False, "reason": "active_version_protected"}
	clear_draft_package_state(IT_STD_VERSION_CODE, family_code=IT_STD_FAMILY_CODE)
	return {"cleared": True, "package_id": IT_STD_VERSION_CODE}


def clear_stable_platform_seed(
	*,
	purge_non_master: bool = True,
	clear_it_std: bool = True,
	skip_guard: bool = False,
) -> dict[str, Any]:
	"""Delete stable platform seed rows so they can be regenerated.

	:param purge_non_master: Remove Playwright/smoke rows outside the WORKS master registry.
	:param clear_it_std: Remove DRAFT IT STD package rows (never deletes ACTIVE).
	:param skip_guard: Allow clear outside dev/test (used by tests).
	"""
	frappe.set_user("Administrator")
	if not skip_guard and not _dev_or_test_clear_allowed():
		return {
			"ok": False,
			"error_code": "SEED_CLEAR_BLOCKED",
			"message": (
				"clear_stable_platform_seed is allowed only in development/test "
				"(frappe.in_test, developer_mode, or allow_tests)."
			),
		}

	deleted: dict[str, int] = {}
	_clear_it_planning(deleted=deleted)
	_clear_it_demand(deleted=deleted)
	_clear_it_budget_line(deleted=deleted)
	_clear_it_strategy(deleted=deleted)

	pp2_clear = clear_pp2_works_planning(skip_guard=skip_guard)
	for doctype, count in (pp2_clear.get("deleted") or {}).items():
		deleted[doctype] = deleted.get(doctype, 0) + int(count)

	std_clear = {"cleared": False}
	if clear_it_std:
		std_clear = _clear_it_std_draft()

	purge = None
	if purge_non_master:
		from kentender_procurement.procurement_lifecycle.seeds.purge_non_works_master_seed import (
			purge_non_works_master_seed,
		)

		purge = purge_non_works_master_seed(dry_run=False)

	frappe.db.commit()
	return {
		"ok": True,
		"deleted": deleted,
		"pp2_clear": pp2_clear,
		"std_clear": std_clear,
		"purge_non_master": purge,
	}
