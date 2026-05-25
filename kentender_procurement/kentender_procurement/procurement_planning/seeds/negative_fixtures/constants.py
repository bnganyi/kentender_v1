# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable NEG-PP2 fixture codes and isolated business record codes."""

from __future__ import annotations

from typing import Final

from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	DemandInclusion,
	PackageFromInclusion,
	PackageMarkReady,
	PackageMethodDecision,
	PackagePostReleaseLock,
	PackageReadiness,
	PackageReleaseConsumed,
	PackageReleaseToTender,
	PackageSubmitReview,
	PlanningPermission,
)

FIXTURE_NEG_PP2_DEMAND_NOT_APPROVED: Final[str] = "NEG-PP2-DEMAND-NOT-APPROVED-001"
FIXTURE_NEG_PP2_BUDGET_MISSING: Final[str] = "NEG-PP2-BUDGET-MISSING-001"
FIXTURE_NEG_PP2_DUP_DEMANDITEM: Final[str] = "NEG-PP2-DUP-DEMANDITEM-001"
FIXTURE_NEG_PP2_PKG_NO_LINE: Final[str] = "NEG-PP2-PKG-NO-LINE-001"
FIXTURE_NEG_PP2_TOTAL_MISMATCH: Final[str] = "NEG-PP2-TOTAL-MISMATCH-001"
FIXTURE_NEG_PP2_METHOD_MISSING: Final[str] = "NEG-PP2-METHOD-MISSING-001"
FIXTURE_NEG_PP2_STD_MISSING: Final[str] = "NEG-PP2-STD-MISSING-001"
FIXTURE_NEG_PP2_READINESS_STALE: Final[str] = "NEG-PP2-READINESS-STALE-001"
FIXTURE_NEG_PP2_RELEASE_STALE: Final[str] = "NEG-PP2-RELEASE-STALE-001"
FIXTURE_NEG_PP2_POST_RELEASE_EDIT: Final[str] = "NEG-PP2-POST-RELEASE-EDIT-001"
FIXTURE_NEG_PP2_TENDER_BASELINE_MISMATCH: Final[str] = "NEG-PP2-TENDER-BASELINE-MISMATCH-001"
FIXTURE_NEG_PP2_SUPPLIER_ACCESS: Final[str] = "NEG-PP2-SUPPLIER-ACCESS-001"

ALL_NEGATIVE_FIXTURE_CODES: Final[tuple[str, ...]] = (
	FIXTURE_NEG_PP2_DEMAND_NOT_APPROVED,
	FIXTURE_NEG_PP2_BUDGET_MISSING,
	FIXTURE_NEG_PP2_DUP_DEMANDITEM,
	FIXTURE_NEG_PP2_PKG_NO_LINE,
	FIXTURE_NEG_PP2_TOTAL_MISMATCH,
	FIXTURE_NEG_PP2_METHOD_MISSING,
	FIXTURE_NEG_PP2_STD_MISSING,
	FIXTURE_NEG_PP2_READINESS_STALE,
	FIXTURE_NEG_PP2_RELEASE_STALE,
	FIXTURE_NEG_PP2_POST_RELEASE_EDIT,
	FIXTURE_NEG_PP2_TENDER_BASELINE_MISMATCH,
	FIXTURE_NEG_PP2_SUPPLIER_ACCESS,
)

SUPPLIER_TEST_USER: Final[str] = "smoke.b@kentender.test"

NEG_ENTITY_CODES: dict[str, dict[str, str]] = {
	FIXTURE_NEG_PP2_DEMAND_NOT_APPROVED: {
		"plan_code": "PLAN-NEG-DEMAND-NOTAPPROVED-001",
		"demand_code": "DEM-NEG-NOTAPPROVED-001",
		"journey_code": "JRN-NEG-NOTAPPROVED-001",
	},
	FIXTURE_NEG_PP2_BUDGET_MISSING: {
		"plan_code": "PLAN-NEG-BUDGET-MISSING-001",
		"demand_code": "DEM-NEG-BUDGET-MISSING-001",
		"journey_code": "JRN-NEG-BUDGET-MISSING-001",
	},
	FIXTURE_NEG_PP2_DUP_DEMANDITEM: {
		"plan_code": "PLAN-NEG-DUP-DEMANDITEM-001",
		"demand_code": "DEM-NEG-DUP-DEMANDITEM-001",
		"demand_item_code": "DEMITEM-NEG-DUP-001",
		"journey_code": "JRN-NEG-DUP-DEMANDITEM-001",
		"inclusion_code": "PLANINCL-NEG-DUP-001",
		"package_code_a": "PKG-NEG-DUP-A-001",
		"package_code_b": "PKG-NEG-DUP-B-001",
	},
	FIXTURE_NEG_PP2_PKG_NO_LINE: {
		"plan_code": "PLAN-NEG-NO-LINE-001",
		"package_code": "PKG-NEG-NO-LINE-001",
		"journey_code": "JRN-NEG-NO-LINE-001",
	},
	FIXTURE_NEG_PP2_TOTAL_MISMATCH: {
		"plan_code": "PLAN-NEG-TOTAL-MISMATCH-001",
		"demand_code": "DEM-NEG-TOTAL-MISMATCH-001",
		"journey_code": "JRN-NEG-TOTAL-MISMATCH-001",
		"inclusion_code": "PLANINCL-NEG-TOTAL-MISMATCH-001",
		"package_code": "PKG-NEG-TOTAL-MISMATCH-001",
	},
	FIXTURE_NEG_PP2_METHOD_MISSING: {
		"plan_code": "PLAN-NEG-METHOD-MISSING-001",
		"demand_code": "DEM-NEG-METHOD-MISSING-001",
		"journey_code": "JRN-NEG-METHOD-MISSING-001",
		"inclusion_code": "PLANINCL-NEG-METHOD-MISSING-001",
		"package_code": "PKG-NEG-METHOD-MISSING-001",
	},
	FIXTURE_NEG_PP2_STD_MISSING: {
		"plan_code": "PLAN-NEG-STD-MISSING-001",
		"demand_code": "DEM-NEG-STD-MISSING-001",
		"journey_code": "JRN-NEG-STD-MISSING-001",
		"inclusion_code": "PLANINCL-NEG-STD-MISSING-001",
		"package_code": "PKG-NEG-STD-MISSING-001",
		"method_decision_code": "METHDEC-NEG-STD-MISSING-001",
	},
	FIXTURE_NEG_PP2_READINESS_STALE: {
		"plan_code": "PLAN-NEG-READINESS-STALE-001",
		"demand_code": "DEM-NEG-READINESS-STALE-001",
		"journey_code": "JRN-NEG-READINESS-STALE-001",
		"inclusion_code": "PLANINCL-NEG-READINESS-STALE-001",
		"package_code": "PKG-NEG-READINESS-STALE-001",
	},
	FIXTURE_NEG_PP2_RELEASE_STALE: {
		"plan_code": "PLAN-NEG-RELEASE-STALE-001",
		"demand_code": "DEM-NEG-RELEASE-STALE-001",
		"journey_code": "JRN-NEG-RELEASE-STALE-001",
		"inclusion_code": "PLANINCL-NEG-RELEASE-STALE-001",
		"package_code": "PKG-NEG-RELEASE-STALE-001",
		"release_code": "PKGREL-NEG-RELEASE-STALE-001",
		"tender_code": "TND-NEG-RELEASE-STALE-001",
	},
	FIXTURE_NEG_PP2_POST_RELEASE_EDIT: {
		"plan_code": "PLAN-NEG-POST-RELEASE-EDIT-001",
		"demand_code": "DEM-NEG-POST-RELEASE-EDIT-001",
		"journey_code": "JRN-NEG-POST-RELEASE-EDIT-001",
		"inclusion_code": "PLANINCL-NEG-POST-RELEASE-EDIT-001",
		"package_code": "PKG-NEG-POST-RELEASE-EDIT-001",
		"release_code": "PKGREL-NEG-POST-RELEASE-EDIT-001",
	},
	FIXTURE_NEG_PP2_TENDER_BASELINE_MISMATCH: {
		"plan_code": "PLAN-NEG-BASELINE-MISMATCH-001",
		"demand_code": "DEM-NEG-BASELINE-MISMATCH-001",
		"journey_code": "JRN-NEG-BASELINE-MISMATCH-001",
		"inclusion_code": "PLANINCL-NEG-BASELINE-MISMATCH-001",
		"package_code": "PKG-NEG-BASELINE-MISMATCH-001",
		"release_code": "PKGREL-NEG-BASELINE-MISMATCH-001",
		"tender_code": "TND-NEG-BASELINE-MISMATCH-001",
	},
	FIXTURE_NEG_PP2_SUPPLIER_ACCESS: {
		"plan_code": "PLAN-NEG-SUPPLIER-ACCESS-001",
		"package_code": "PKG-NEG-SUPPLIER-ACCESS-001",
	},
}

FIXTURE_METADATA: dict[str, dict[str, str]] = {
	FIXTURE_NEG_PP2_DEMAND_NOT_APPROVED: {
		"setup": "Create active procurement plan and demand in Submitted status (not approved).",
		"attempted_action": "include_demand_in_procurement_plan",
		"expected_result": "FAIL",
		"blocker_code": DemandInclusion.DEMAND_NOT_APPROVED,
		"message": "This demand is not approved and cannot be planned.",
	},
	FIXTURE_NEG_PP2_BUDGET_MISSING: {
		"setup": "Create approved demand without a linked budget line.",
		"attempted_action": "include_demand_in_procurement_plan",
		"expected_result": "FAIL",
		"blocker_code": DemandInclusion.BUDGET_MISSING,
		"message": "This demand has no approved budget line linked.",
	},
	FIXTURE_NEG_PP2_DUP_DEMANDITEM: {
		"setup": "Package the same demand item in two active packages.",
		"attempted_action": "create_package_line",
		"expected_result": "FAIL",
		"blocker_code": DemandInclusion.DEMAND_ITEM_ALREADY_PACKAGED,
		"message": "This demand item is already included in an active package.",
	},
	FIXTURE_NEG_PP2_PKG_NO_LINE: {
		"setup": "Create draft procurement package with zero active package lines.",
		"attempted_action": "submit_package_for_review",
		"expected_result": "FAIL",
		"blocker_code": PackageSubmitReview.NO_PACKAGE_LINE,
		"message": "This package has no package lines.",
	},
	FIXTURE_NEG_PP2_TOTAL_MISMATCH: {
		"setup": "Set package estimated value different from active line total.",
		"attempted_action": "run_package_readiness_checks",
		"expected_result": "FAIL",
		"blocker_code": PackageReadiness.READINESS_FAILED,
		"message": "Package total does not equal package line total.",
	},
	FIXTURE_NEG_PP2_METHOD_MISSING: {
		"setup": "Create package with line but no method decision.",
		"attempted_action": "run_package_readiness_checks",
		"expected_result": "FAIL",
		"blocker_code": PackageMethodDecision.METHOD_MISSING,
		"message": "Procurement method is missing.",
	},
	FIXTURE_NEG_PP2_STD_MISSING: {
		"setup": "Create method decision without required STD category.",
		"attempted_action": "run_package_readiness_checks",
		"expected_result": "FAIL",
		"blocker_code": PackageMethodDecision.STD_CATEGORY_MISSING,
		"message": "Required STD category is missing.",
	},
	FIXTURE_NEG_PP2_READINESS_STALE: {
		"setup": "Run readiness, then change package line value before release.",
		"attempted_action": "release_package_to_tender_management",
		"expected_result": "FAIL",
		"blocker_code": PackageReleaseToTender.READINESS_STALE,
		"message": "Readiness is stale because package data changed. Rerun readiness checks.",
	},
	FIXTURE_NEG_PP2_RELEASE_STALE: {
		"setup": "Release package then drift locked summary / package baseline.",
		"attempted_action": "mark_planning_release_consumed",
		"expected_result": "FAIL",
		"blocker_code": PackageReleaseConsumed.RELEASE_STALE,
		"message": "Release handoff is stale.",
	},
	FIXTURE_NEG_PP2_POST_RELEASE_EDIT: {
		"setup": "Release package and lock baseline fields.",
		"attempted_action": "edit_locked_package_field",
		"expected_result": "FAIL",
		"blocker_code": PackagePostReleaseLock.LOCKED_AFTER_RELEASE,
		"message": "This package has been released and cannot be edited directly.",
	},
	FIXTURE_NEG_PP2_TENDER_BASELINE_MISMATCH: {
		"setup": "Release Works/Open Tender package and link TM2 tender with conflicting method.",
		"attempted_action": "mark_planning_release_consumed",
		"expected_result": "FAIL",
		"blocker_code": PackageReleaseConsumed.BASELINE_MISMATCH,
		"message": "Tender baseline does not match planning release.",
	},
	FIXTURE_NEG_PP2_SUPPLIER_ACCESS: {
		"setup": "Create internal planning record and supplier test user context.",
		"attempted_action": "supplier_read_planning_record",
		"expected_result": "FAIL",
		"blocker_code": PlanningPermission.NOT_PERMITTED,
		"message": "Supplier users cannot access internal Planning records.",
	},
}
