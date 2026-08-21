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
	"""PP2 IT planning supplement retired."""
	return


def _clear_it_demand(*, deleted: dict[str, int]) -> None:
	demand_name = frappe.db.get_value("Demand", {"demand_id": IT_DEMAND_CODE}, "name")
	if not demand_name:
		return
	frappe.db.delete("Demand Item", {"parent": demand_name})
	_delete_doc("Demand", demand_name, deleted)


def _clear_it_budget_line(*, deleted: dict[str, int]) -> None:
	"""No-op: legacy Budget DocTypes removed in MVP-1 preparatory teardown."""
	deleted["Budget (teardown)"] = deleted.get("Budget (teardown)", 0)


def _clear_it_strategy(*, deleted: dict[str, int]) -> None:
	"""No-op: legacy Strategy DocTypes removed in MVP-1 preparatory teardown."""
	deleted["Strategy (teardown)"] = deleted.get("Strategy (teardown)", 0)


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

	:param purge_non_master: Remove Playwright/smoke rows outside the stable platform registry.
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

	pp2_clear = {"ok": True, "skipped": True, "reason": "PP2_PLANNING_RETIRED"}
	for doctype, count in (pp2_clear.get("deleted") or {}).items():
		deleted[doctype] = deleted.get(doctype, 0) + int(count)

	std_clear = {"cleared": False}
	if clear_it_std:
		std_clear = _clear_it_std_draft()

	purge = None
	if purge_non_master:
		from kentender_core.seeds.stable_platform_seed.purge import purge_non_stable_platform_seed

		purge = purge_non_stable_platform_seed(dry_run=False)

	frappe.db.commit()
	return {
		"ok": True,
		"deleted": deleted,
		"pp2_clear": pp2_clear,
		"std_clear": std_clear,
		"purge_non_master": purge,
	}
