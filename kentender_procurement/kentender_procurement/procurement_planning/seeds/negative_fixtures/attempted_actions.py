# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Dispatch attempted_action proofs for NEG-PP2 fixture validation (P3-017)."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_planning.api.landing import get_pp_landing_shell_data
from kentender_procurement.procurement_planning.pp2_constants import (
	POST_RELEASE_LOCK_MESSAGE,
	READINESS_FAILED,
)
from kentender_procurement.procurement_planning.seeds.negative_fixtures.bootstrap import (
	_resolve_demand_docname,
)
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
from kentender_procurement.procurement_planning.seeds.negative_fixtures.registry import (
	NegativeFixtureSpec,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	run_package_readiness_checks,
)
from kentender_procurement.procurement_planning.services.package_release_service import (
	can_release_package_to_tender_management,
)
from kentender_procurement.procurement_planning.services.package_review_service import (
	can_submit_package_for_review,
)
from kentender_procurement.procurement_planning.services.planning_inclusion_service import (
	can_include_demand_in_plan,
)
from kentender_procurement.procurement_planning.services.planning_release_consumption_service import (
	can_mark_planning_release_consumed,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	DemandInclusion,
	PackageMethodDecision,
	PackagePostReleaseLock,
	PackageReadiness,
	PackageReleaseConsumed,
	PackageReleaseToTender,
	PackageSubmitReview,
	PlanningPermission,
)

SEED_ACTOR = "Administrator"

_READINESS_CHECK_BY_FIXTURE: dict[str, str] = {
	FIXTURE_NEG_PP2_TOTAL_MISMATCH: "PP2-READY-008",
	FIXTURE_NEG_PP2_METHOD_MISSING: "PP2-READY-010",
	FIXTURE_NEG_PP2_STD_MISSING: "PP2-READY-012",
}


def _blocker_codes_from_guard(guard: dict[str, Any]) -> list[str]:
	return [(b.get("code") or "").strip() for b in (guard.get("blockers") or []) if b.get("code")]


def _err_text(exc: BaseException) -> str:
	title = getattr(exc, "title", None)
	if title:
		return f"{title} {exc}".strip()
	return str(exc)


def _blocker_from_validation_error(exc: BaseException) -> str | None:
	title = getattr(exc, "title", None)
	if title:
		title_text = str(title).strip()
		if title_text:
			return title_text
	blob = _err_text(exc)
	for token in (
		PackagePostReleaseLock.LOCKED_AFTER_RELEASE,
		PackageReleaseConsumed.RELEASE_STALE,
		PackageReleaseConsumed.BASELINE_MISMATCH,
		DemandInclusion.DEMAND_NOT_APPROVED,
	):
		if token in blob:
			return token
	if POST_RELEASE_LOCK_MESSAGE in str(exc):
		return PackagePostReleaseLock.LOCKED_AFTER_RELEASE
	return None


def _fail_proof(*, guard: str, **extra: Any) -> dict[str, Any]:
	return {"guard": guard, **extra}


def _success_fail(*, observed_blocker_code: str, proof: dict[str, Any]) -> dict[str, Any]:
	return {
		"observed_result": "FAIL",
		"observed_blocker_code": observed_blocker_code,
		"proof": proof,
	}


def _check_failed(checks: list[dict[str, Any]], check_id: str) -> bool:
	for row in checks or []:
		if (row.get("check_id") or row.get("id") or "").strip() == check_id:
			return (row.get("result") or "").strip() == "FAIL"
	return False


def fixture_loaded(fixture_code: str) -> bool:
	records = NEG_ENTITY_CODES.get(fixture_code) or {}
	if not records:
		return False
	if (plan_code := (records.get("plan_code") or "").strip()) and not frappe.db.exists(
		"Procurement Plan", plan_code
	):
		return False
	for package_key in ("package_code", "package_code_a", "package_code_b"):
		pkg = (records.get(package_key) or "").strip()
		if pkg and not frappe.db.exists("Procurement Package", pkg):
			return False
	if (demand_code := (records.get("demand_code") or "").strip()) and not _resolve_demand_docname(
		demand_code
	):
		return False
	return True


def _prove_include_demand_blocked(
	*,
	fixture_code: str,
	demand_code: str,
	plan_code: str,
	demand_item_codes: list[str],
	expected_blocker: str,
) -> dict[str, Any]:
	guard = can_include_demand_in_plan(demand_code, demand_item_codes, plan_code, SEED_ACTOR)
	codes = _blocker_codes_from_guard(guard)
	if guard.get("allowed"):
		return {"observed_result": "PASS", "observed_blocker_code": None, "proof": _fail_proof(guard="can_include_demand_in_plan", guard_out=guard)}
	observed = next((c for c in codes if c == expected_blocker), codes[0] if codes else None)
	return _success_fail(
		observed_blocker_code=observed or expected_blocker,
		proof=_fail_proof(guard="can_include_demand_in_plan", guard_out=guard, blocker_codes=codes),
	)


def _prove_readiness_blocked(*, fixture_code: str, package_code: str, expected_blocker: str) -> dict[str, Any]:
	check_id = _READINESS_CHECK_BY_FIXTURE.get(fixture_code)
	out = run_package_readiness_checks(package_code, SEED_ACTOR)
	checks = out.get("checks") or []
	result_status = (out.get("result_status") or "").strip()
	if result_status != READINESS_FAILED:
		return {
			"observed_result": "PASS" if result_status else "UNKNOWN",
			"observed_blocker_code": None,
			"proof": _fail_proof(guard="run_package_readiness_checks", readiness_out=out),
		}
	if check_id and not _check_failed(checks, check_id):
		return {
			"observed_result": "FAIL",
			"observed_blocker_code": None,
			"proof": _fail_proof(
				guard="run_package_readiness_checks",
				readiness_out=out,
				expected_check_id=check_id,
			),
		}
	return _success_fail(
		observed_blocker_code=expected_blocker,
		proof=_fail_proof(
			guard="run_package_readiness_checks",
			readiness_out=out,
			check_id=check_id,
		),
	)


def _locked_release_summary(release_code: str) -> dict[str, Any]:
	raw = frappe.db.get_value("Procurement Handoff Card", release_code, "locked_summary")
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str) and raw.strip():
		try:
			parsed = json.loads(raw)
			return parsed if isinstance(parsed, dict) else {}
		except json.JSONDecodeError:
			pass
	return {}


def _prove_tender_baseline_mismatch_blocked(
	*,
	release_code: str,
	tender_code: str,
	expected_blocker: str,
) -> dict[str, Any]:
	locked = _locked_release_summary(release_code)
	locked_method = str(locked.get("procurement_method") or "").strip()
	tender_method = str(
		frappe.db.get_value("TM2 Tender", {"tender_code": tender_code}, "procurement_method") or ""
	).strip()
	if locked_method and tender_method and locked_method != tender_method:
		return _success_fail(
			observed_blocker_code=expected_blocker,
			proof=_fail_proof(
				guard="tender_baseline_vs_locked_release",
				locked_method=locked_method,
				tender_method=tender_method,
			),
		)
	guard = can_mark_planning_release_consumed(release_code, tender_code, SEED_ACTOR)
	return _prove_guard_blocked(
		guard_name="can_mark_planning_release_consumed",
		guard=guard,
		expected_blocker=expected_blocker,
	)


def _prove_guard_blocked(*, guard_name: str, guard: dict[str, Any], expected_blocker: str) -> dict[str, Any]:
	codes = _blocker_codes_from_guard(guard)
	if guard.get("allowed"):
		return {
			"observed_result": "PASS",
			"observed_blocker_code": None,
			"proof": _fail_proof(guard=guard_name, guard_out=guard),
		}
	observed = next((c for c in codes if c == expected_blocker), codes[0] if codes else None)
	return _success_fail(
		observed_blocker_code=observed or expected_blocker,
		proof=_fail_proof(guard=guard_name, guard_out=guard, blocker_codes=codes),
	)


def prove_fixture_blocker(fixture_code: str, spec: NegativeFixtureSpec) -> dict[str, Any]:
	frappe.set_user(SEED_ACTOR)
	records = NEG_ENTITY_CODES.get(fixture_code) or {}
	expected = spec.blocker_code
	action = spec.attempted_action

	if action == "include_demand_in_procurement_plan":
		demand_code = records["demand_code"]
		plan_code = records["plan_code"]
		item_codes = [f"DEMITEM-{demand_code}"]
		return _prove_include_demand_blocked(
			fixture_code=fixture_code,
			demand_code=demand_code,
			plan_code=plan_code,
			demand_item_codes=item_codes,
			expected_blocker=expected,
		)

	if action == "create_package_line":
		return _prove_include_demand_blocked(
			fixture_code=fixture_code,
			demand_code=records["demand_code"],
			plan_code=records["plan_code"],
			demand_item_codes=[records["demand_item_code"]],
			expected_blocker=DemandInclusion.DEMAND_ITEM_ALREADY_PACKAGED,
		)

	if action == "submit_package_for_review":
		guard = can_submit_package_for_review(records["package_code"], SEED_ACTOR)
		return _prove_guard_blocked(
			guard_name="can_submit_package_for_review",
			guard=guard,
			expected_blocker=PackageSubmitReview.NO_PACKAGE_LINE,
		)

	if action == "run_package_readiness_checks":
		return _prove_readiness_blocked(
			fixture_code=fixture_code,
			package_code=records["package_code"],
			expected_blocker=expected,
		)

	if action == "release_package_to_tender_management":
		guard = can_release_package_to_tender_management(records["package_code"], SEED_ACTOR)
		return _prove_guard_blocked(
			guard_name="can_release_package_to_tender_management",
			guard=guard,
			expected_blocker=PackageReleaseToTender.READINESS_STALE,
		)

	if action == "mark_planning_release_consumed":
		if fixture_code == FIXTURE_NEG_PP2_TENDER_BASELINE_MISMATCH:
			return _prove_tender_baseline_mismatch_blocked(
				release_code=records["release_code"],
				tender_code=records["tender_code"],
				expected_blocker=expected,
			)
		guard = can_mark_planning_release_consumed(
			records["release_code"],
			records["tender_code"],
			SEED_ACTOR,
		)
		return _prove_guard_blocked(
			guard_name="can_mark_planning_release_consumed",
			guard=guard,
			expected_blocker=expected,
		)

	if action == "edit_locked_package_field":
		package_code = records["package_code"]
		pkg = frappe.get_doc("Procurement Package", package_code)
		pkg.procurement_method = "Restricted Tender"
		try:
			pkg.save(ignore_permissions=True)
		except frappe.ValidationError as exc:
			code = _blocker_from_validation_error(exc)
			if code == PackagePostReleaseLock.LOCKED_AFTER_RELEASE:
				return _success_fail(
					observed_blocker_code=PackagePostReleaseLock.LOCKED_AFTER_RELEASE,
					proof=_fail_proof(guard="edit_locked_package_field", exception=_err_text(exc)),
				)
			return {
				"observed_result": "FAIL",
				"observed_blocker_code": code,
				"proof": _fail_proof(guard="edit_locked_package_field", exception=_err_text(exc)),
			}
		return {
			"observed_result": "PASS",
			"observed_blocker_code": None,
			"proof": _fail_proof(guard="edit_locked_package_field"),
		}

	if action == "supplier_read_planning_record":
		plan_code = records["plan_code"]
		if not frappe.db.exists("User", SUPPLIER_TEST_USER):
			return {
				"observed_result": "UNKNOWN",
				"observed_blocker_code": None,
				"proof": _fail_proof(guard="supplier_read_planning_record", missing_user=SUPPLIER_TEST_USER),
			}
		frappe.set_user(SUPPLIER_TEST_USER)
		try:
			out = get_pp_landing_shell_data(plan_code)
			if out.get("ok") is False and out.get("error_code") == "PP_ACCESS_DENIED":
				return _success_fail(
					observed_blocker_code=PlanningPermission.NOT_PERMITTED,
					proof=_fail_proof(guard="supplier_read_planning_record", landing_out=out),
				)
		except frappe.PermissionError as exc:
			return _success_fail(
				observed_blocker_code=PlanningPermission.NOT_PERMITTED,
				proof=_fail_proof(guard="supplier_read_planning_record", exception=str(exc)),
			)
		finally:
			frappe.set_user(SEED_ACTOR)
		return {
			"observed_result": "PASS",
			"observed_blocker_code": None,
			"proof": _fail_proof(guard="supplier_read_planning_record"),
		}

	return {
		"observed_result": "UNKNOWN",
		"observed_blocker_code": None,
		"proof": _fail_proof(guard="unsupported_attempted_action", attempted_action=action),
	}
