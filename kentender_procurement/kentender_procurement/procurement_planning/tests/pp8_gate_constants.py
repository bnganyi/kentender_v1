# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP3 P8 gate — shared prohibited strings and regression module manifest."""

from __future__ import annotations

# §18.3 — must not appear in ordinary UI before Evidence → Technical Details expansion.
P8_PROHIBITED_ORDINARY_UI: tuple[str, ...] = (
	"PLANINCL-MOH-2026-001",
	"PKGREL-MOH-2026-001",
	"PKGCONSUME-MOH-2026-001",
	"source_object_code",
	"target_object_code",
	"locked_summary_json",
	"passed_forward_summary_json",
	"technical_refs_json",
	"audit_event_ref",
	"package_release",
	"handed_off",
	"shell baseline",
	"feature content deferred",
	"stub",
	"P5",
	"Planning Workflow Status",
)

P8_FORBIDDEN_IMPLEMENTATION_COPY: tuple[str, ...] = (
	"shell baseline",
	"feature content deferred",
	"stub content",
	"P5 surfaces completed",
	"this will be implemented later",
	"technical placeholder",
	"Choose a planning workspace action",
	"Open a planning queue from the sidebar",
	"Canonical PP2 rendering is active",
	"9.1 shell baseline",
)

P8_FORBIDDEN_NAV_LABELS: frozenset[str] = frozenset(
	{
		"Planning Home",
		"Approved Demands",
		"Packages",
		"Planning Evidence",
		"Procurement Packages",
	}
)

P8_FORBIDDEN_NAV_HREF_SUBSTRINGS: tuple[str, ...] = (
	"/procurement-planning/approved-demands",
	"/procurement-planning/packages",
	"/procurement-planning/evidence",
)

# Curated backend modules for P8-012 regression gate (procurement_planning.tests).
P8_BACKEND_REGRESSION_MODULES: tuple[str, ...] = (
	"kentender_procurement.procurement_planning.tests.test_pp8_role_action_matrix_p8_001",
	"kentender_procurement.procurement_planning.tests.test_pp8_no_active_plan_p8_002",
	"kentender_procurement.procurement_planning.tests.test_pp8_readiness_enforcement_p8_003",
	"kentender_procurement.procurement_planning.tests.test_pp8_review_enforcement_p8_004",
	"kentender_procurement.procurement_planning.tests.test_pp8_release_locking_p8_005",
	"kentender_procurement.procurement_planning.tests.test_pp8_technical_leakage_p8_006",
	"kentender_procurement.procurement_planning.tests.test_pp8_implementation_copy_p8_007",
	"kentender_procurement.procurement_planning.tests.test_pp8_navigation_negative_p8_008",
	"kentender_procurement.procurement_planning.tests.test_pp8_evidence_permission_p8_009",
	"kentender_procurement.procurement_planning.tests.test_pp8_supplier_confidentiality_p8_010",
	"kentender_procurement.procurement_planning.tests.test_pp8_works_seed_regression_p8_011",
	"kentender_procurement.procurement_planning.tests.test_pp8_backend_regression_gate_p8_012",
	"kentender_procurement.procurement_planning.tests.test_pp2_role_permissions_p2_014",
	"kentender_procurement.procurement_planning.tests.test_pp5_no_technical_leakage_p5_009",
	"kentender_procurement.procurement_planning.tests.test_pp2_post_release_lock_p2_012",
	"kentender_procurement.procurement_planning.tests.test_pp2_planning_works_master_seed_p3_005",
)
