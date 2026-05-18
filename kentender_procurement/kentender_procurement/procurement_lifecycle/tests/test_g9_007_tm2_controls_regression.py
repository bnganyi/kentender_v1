# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""§14 G9-007 — TM2 controls preserved (representative regression bundle).

Rolls up **targeted** acceptance tests so **publication**, **STD-backed readiness summary**, **sealed bid**
confidentiality, and **legacy Procurement Tender surface lockout** remain green after PLC work:

| Concern | Tests |
|---------|-------|
| Legacy lockout / TM2-canonical surfaces | **P11-04**, **P11-05** (G0-004 inventory; same as **R8-012**) |
| Publication via legal services | **EX-15** publish denial ↔ ``get_action_availability`` |
| STD readiness (WORKS TM2 summary) | **R3-016 BRS-001** — ``get_business_readiness_summary`` golden **Ready** / five PASS checks |
| Sealed bid pre-opening deny | **TM2-SMOKE-SEAL-001** (internal officer **AUTH_SEALED_BID_DENIED**) |

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.procurement_lifecycle.tests.test_g9_007_tm2_controls_regression

Companion evidence:
docs/prompts/0. usability handoff/G9_007_tm2_controls_evidence.md
"""

from __future__ import annotations

import unittest

_G9_007_CASES: tuple[str, ...] = (
	"kentender_procurement.tender_management.tests.test_p11_04_tm2_surface_no_procurement_tender.TestP1104Tm2SurfaceNoProcurementTender.test_p11_04_tm2_surface_has_no_procurement_tender_doc_api",
	"kentender_procurement.tender_management.tests.test_p11_05_tm2_surface_no_procurement_tender_literal.TestP11Tm2SurfaceNoProcurementTenderLiteral.test_p11_05_tm2_surface_has_no_procurement_tender_doctype_literal",
	"kentender_procurement.tender_management.tests.test_ex_15_action_availability_controls_legal_services.TestEx15ActionAvailabilityControlsLegalServices.test_EX_15_publish_denial_aligns_with_get_action_availability",
	"kentender_procurement.procurement_lifecycle.tests.test_r3_016_business_readiness_summary.TestR3016BusinessReadinessSummary.test_works_golden_scenario_status_ready",
	"kentender_procurement.tender_management.tests.test_o09_tm2_smoke_seal_001_internal_cannot_view_sealed_bid_before_opening.TestO09Tm2SmokeSeal001InternalCannotViewSealedBidBeforeOpening.test_TM2_SMOKE_SEAL_001_internal_user_cannot_view_sealed_bid_before_opening",
)


def load_tests(
	loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
	suite = unittest.TestSuite()
	for dotted in _G9_007_CASES:
		suite.addTests(loader.loadTestsFromName(dotted))
	return suite
