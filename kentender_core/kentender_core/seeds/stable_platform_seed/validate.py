# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Validate stable platform seed integrity."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.stable_platform_seed.constants import (
	IT_BUDGET_LINE_CODE,
	IT_DEMAND_CODE,
	IT_INCLUSION_CODE,
	IT_OBJECTIVE_CODE,
	IT_PKG_CODE,
	IT_PROGRAM_CODE,
	IT_STD_FAMILY_CODE,
	IT_STD_VERSION_CODE,
	IT_TARGET_CODE,
	WORKS_DEMAND_CODE,
	WORKS_PKG_CODE,
	WORKS_PLAN_CODE,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	OBJECTIVE_CODE as WORKS_OBJECTIVE_CODE,
	PROGRAM_CODE as WORKS_PROGRAM_CODE,
	TARGET_CODE as WORKS_TARGET_CODE,
)


def validate_stable_platform_seed(
	*,
	planning_checkpoint: str | None = None,
	expect_it_std: bool = True,
	expect_it_supplement: bool = True,
) -> dict[str, Any]:
	"""Return validation summary for the stable platform seed pack."""
	frappe.only_for(("System Manager", "Administrator"))

	checks: list[dict[str, Any]] = []

	def _check(code: str, label: str, passed: bool, *, detail: str = "") -> None:
		checks.append({"code": code, "label": label, "ok": passed, "detail": detail})

	# MVP-1 Strategy teardown: legacy Strategy DocTypes removed; checks are skipped.
	_check(
		"STABLE-STRAT-001",
		"WORKS strategy program",
		True,
		detail="skipped:mvp1-strategy-teardown",
	)
	_check(
		"STABLE-STRAT-001B",
		"WORKS strategy objective",
		True,
		detail="skipped:mvp1-strategy-teardown",
	)
	_check(
		"STABLE-STRAT-001C",
		"WORKS strategy target",
		True,
		detail="skipped:mvp1-strategy-teardown",
	)

	if expect_it_supplement:
		_check(
			"STABLE-STRAT-002",
			"IT strategy program",
			True,
			detail="skipped:mvp1-strategy-teardown",
		)
		_check(
			"STABLE-STRAT-003",
			"IT strategy objective",
			True,
			detail="skipped:mvp1-strategy-teardown",
		)
		_check(
			"STABLE-STRAT-004",
			"IT strategy target",
			True,
			detail="skipped:mvp1-strategy-teardown",
		)
		_check(
			"STABLE-BUD-001",
			"IT budget line",
			True,
			detail="skipped:mvp1-budget-teardown",
		)
		_check(
			"STABLE-DIA-002",
			"IT demand approved",
			(frappe.db.get_value("Demand", {"demand_id": IT_DEMAND_CODE}, "status") or "") == "Approved",
		)
		_check(
			"STABLE-PLAN-002",
			"IT planning inclusion",
			bool(frappe.db.exists("Procurement Handoff Card", IT_INCLUSION_CODE)),
		)
		_check(
			"STABLE-PLAN-003",
			"IT procurement package draft",
			True,  # PP2 Package retired
		)

	_check(
		"STABLE-DIA-001",
		"WORKS demand approved",
		(frappe.db.get_value("Demand", {"demand_id": WORKS_DEMAND_CODE}, "status") or "") == "Approved",
	)
	_check(
		"STABLE-PLAN-001",
		"WORKS procurement plan (PP2 retired — skip)",
		True,
		detail="PP2_PLANNING_RETIRED",
	)
	_check(
		"STABLE-PLAN-004",
		"WORKS procurement package (PP2 retired — skip)",
		True,
		detail="PP2_PLANNING_RETIRED",
	)
	_check(
		"STABLE-PP2-001",
		"PP2 WORKS planning validation (retired — skip)",
		True,
		detail="PP2_PLANNING_RETIRED",
	)

	if expect_it_std:
		std_exists = bool(frappe.db.exists("STD Version", IT_STD_VERSION_CODE))
		_check("STABLE-STD-001", "IT STD version imported", std_exists)
		if std_exists:
			clause_count = frappe.db.count("STD Clause", {"package_id": IT_STD_VERSION_CODE})
			param_count = frappe.db.count("STD Parameter", {"package_id": IT_STD_VERSION_CODE})
			_check(
				"STABLE-STD-002",
				"IT STD clause count",
				clause_count >= 94,
				detail=f"clauses={clause_count}",
			)
			_check(
				"STABLE-STD-003",
				"IT STD parameter count",
				param_count >= 155,
				detail=f"parameters={param_count}",
			)
			family_ok = bool(frappe.db.exists("STD Family", IT_STD_FAMILY_CODE))
			_check("STABLE-STD-004", "IT STD family", family_ok)

	failed = [c for c in checks if not c["ok"]]
	return {
		"ok": not failed,
		"checks": checks,
		"failed_count": len(failed),
		"pp2_validate": pp2_validate,
	}
