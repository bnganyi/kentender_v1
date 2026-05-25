# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Record PKGRDY-PKG-MOH-2026-001-001 (spec §12)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, get_datetime

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_RELEASED,
	READINESS_FAILED,
	READINESS_PASSED,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	JOURNEY_CODE,
	PKG_CODE,
	PKGRDY_CODE,
	PKGRDY_RUN_AT,
	PLAN_CREATOR_EMAIL,
	PLAN_CREATOR_USER_CODE,
	SEED_ACTOR,
	master_readiness_check_items,
	strict_readiness_snapshot,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	_ensure_seed_user,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.review import (
	sync_master_review_decision_links,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	evaluate_pp2_readiness_checks,
)

_REPAIRABLE_READINESS_FIELDS = (
	"readiness_code",
	"package_code",
	"run_by",
	"run_at",
	"result_status",
	"blocking_failure_count",
	"warning_count",
	"check_items_json",
	"source_snapshot_json",
	"stale",
	"stale_reason",
	"is_current",
	"is_master_seed",
)


def _readiness_seed_repair_allowed() -> bool:
	locked = cint(frappe.db.get_value("Procurement Package", PKG_CODE, "locked_after_release"))
	status = (frappe.db.get_value("Procurement Package", PKG_CODE, "status") or "").strip()
	return not locked and status not in (PKG_RELEASED, PKG_CONSUMED)


def _strict_readiness_values(
	*,
	run_by: str,
	snapshot: dict[str, Any],
	check_items: list[dict[str, Any]],
) -> dict[str, Any]:
	return {
		"readiness_code": PKGRDY_CODE,
		"package_code": PKG_CODE,
		"run_by": run_by,
		"run_at": get_datetime(PKGRDY_RUN_AT),
		"result_status": READINESS_PASSED,
		"blocking_failure_count": 0,
		"warning_count": 0,
		"check_items_json": {"checks": check_items},
		"source_snapshot_json": snapshot,
		"stale": 0,
		"stale_reason": None,
		"is_current": 1,
		"is_master_seed": 1,
	}


def _demote_other_current_readiness_rows() -> None:
	frappe.db.sql(
		"""
		UPDATE `tabPackage Readiness Result`
		SET is_current = 0
		WHERE package_code = %s AND is_current = 1 AND readiness_code != %s
		""",
		(PKG_CODE, PKGRDY_CODE),
	)


def _sync_package_readiness_fields(*, readiness_code: str, result_status: str) -> None:
	frappe.db.set_value(
		"Procurement Package",
		PKG_CODE,
		{
			"readiness_status": result_status,
			"latest_readiness_code": readiness_code,
		},
		update_modified=False,
	)


def _assert_evaluation_passed(evaluation: dict[str, Any]) -> None:
	if (evaluation.get("result_status") or "").strip() == READINESS_PASSED:
		return
	blockers = [
		check
		for check in evaluation.get("checks") or []
		if check.get("blocking") and check.get("result") == "FAIL"
	]
	first = blockers[0] if blockers else {}
	frappe.throw(
		first.get("message") or "Package readiness checks did not pass.",
		title=first.get("check_id") or READINESS_FAILED,
	)


def _ensure_master_readiness_result(*, actor: str) -> dict[str, Any]:
	del actor
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		frappe.throw("Procurement Package not found.", title="MISSING_PACKAGE")

	evaluation = evaluate_pp2_readiness_checks(PKG_CODE)
	_assert_evaluation_passed(evaluation)

	run_by = _ensure_seed_user(
		email=PLAN_CREATOR_EMAIL,
		user_code=PLAN_CREATOR_USER_CODE,
		full_name="Procurement Planner MOH",
	)
	live_snapshot = dict(evaluation.get("source_snapshot_json") or {})
	for key, value in strict_readiness_snapshot().items():
		if key == "required_std_template_version_code":
			continue
		live_snapshot[key] = value
	check_items = master_readiness_check_items()
	values = _strict_readiness_values(
		run_by=run_by,
		snapshot=live_snapshot,
		check_items=check_items,
	)
	existed = bool(frappe.db.exists("Package Readiness Result", PKGRDY_CODE))

	if existed:
		if _readiness_seed_repair_allowed():
			doc = frappe.get_doc("Package Readiness Result", PKGRDY_CODE)
			for fieldname in _REPAIRABLE_READINESS_FIELDS:
				doc.set(fieldname, values[fieldname])
			doc.flags.ignore_mandatory = True
			doc.save(ignore_permissions=True)
			action = "repaired"
		else:
			action = "existing"
	else:
		doc = frappe.get_doc({"doctype": "Package Readiness Result", **values})
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		action = "created"

	_demote_other_current_readiness_rows()
	frappe.db.set_value(
		"Package Readiness Result",
		PKGRDY_CODE,
		{"is_current": 1},
		update_modified=False,
	)
	_sync_package_readiness_fields(
		readiness_code=PKGRDY_CODE,
		result_status=READINESS_PASSED,
	)
	sync_master_review_decision_links()

	return {
		"action": action,
		"readiness_code": PKGRDY_CODE,
	}


def ensure_master_readiness_result(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	return _ensure_master_readiness_result(actor=actor)
