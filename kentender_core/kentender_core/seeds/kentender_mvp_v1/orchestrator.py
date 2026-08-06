# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Central KENTENDER_MVP_V1 seed / reset / validate entry points."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_core.seeds.kentender_mvp_v1.budget import upsert_budget
from kentender_core.seeds.kentender_mvp_v1.clear import clear_kentender_mvp_v1
from kentender_core.seeds.kentender_mvp_v1.org import upsert_org
from kentender_core.seeds.kentender_mvp_v1.strategy import upsert_strategy
from kentender_core.seeds.kentender_mvp_v1.users import upsert_canonical_users
from kentender_core.seeds.kentender_mvp_v1.validate import (
	validate_kentender_mvp_v1 as _validate,
)


def _assert_demo_allowed(*, force: bool = False) -> None:
	if force:
		return
	developer_mode = bool(frappe.conf.get("developer_mode"))
	allow = bool(
		frappe.conf.get("allow_kentender_mvp_v1_seed")
		or frappe.conf.get("allow_moh_mvp_v1_seed")
	)
	if not developer_mode and not allow:
		frappe.throw(
			"KENTENDER_MVP_V1 seed refused: enable developer_mode or "
			"allow_kentender_mvp_v1_seed (or pass force=True)."
		)


def run_kentender_mvp_v1(
	*,
	reset: bool = True,
	force: bool = False,
	validate: bool = True,
) -> dict[str, Any]:
	"""Clear (optional), seed org → users → strategy → budget, then validate."""
	frappe.only_for(("System Manager", "Administrator"))
	_assert_demo_allowed(force=force)
	frappe.set_user("Administrator")

	result: dict[str, Any] = {
		"ok": True,
		"fixture_namespace": C.FIXTURE_NS,
		"fixture_clock": C.FIXTURE_NOW_STR,
		"finance_freshness_days": C.FINANCE_FRESHNESS_DAYS,
	}
	if reset:
		result["clear"] = clear_kentender_mvp_v1(include_strategy=True, include_budget=True)

	result["org"] = upsert_org()
	result["users"] = upsert_canonical_users()
	result["strategy"] = upsert_strategy(reset=False)
	result["budget"] = upsert_budget()
	frappe.db.commit()

	if validate:
		report = _validate()
		result["validate"] = report
		result["ok"] = bool(report.get("ok"))
		print(report.get("summary") or "")
		if not report.get("ok"):
			frappe.msgprint("KENTENDER_MVP_V1 validation FAILED — see validate.failures")
	return result


def validate_kentender_mvp_v1() -> dict[str, Any]:
	frappe.only_for(("System Manager", "Administrator"))
	report = _validate()
	print(report.get("summary") or "")
	return report


# Thin aliases for one migration cycle.
def run_moh_mvp_v1(*, reset: bool = True, force: bool = False, validate: bool = True):
	return run_kentender_mvp_v1(reset=reset, force=force, validate=validate)


def validate_moh_mvp_v1():
	return validate_kentender_mvp_v1()
