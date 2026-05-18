# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R8-014 / LV-R8-REG-03 — Procurement planning → TM2 package release governance regression.

Bundles the **controlled inventory** below so PLC usability work cannot silently break
Planning Release (**PKGREL**), ``release_procurement_package_to_tender``, or TM2 linkage
contracts:

1. **R3-005** ``create_planning_release_package`` (rectification tracker **R3-005 / LV-R3-005-01**).
2. **B3** release service + hook — primary **R07** acceptance module.
3. **B7–B9** handoff configuration snapshot, audit, duplicate prevention (**doc 2** §§14–16, 18;
   Tender Management IMPLEMENTATION_TRACKER cites these with **B3** + **B10**).

4. **B10** consolidated release integration / failure modes.

Cross-ref: Tender Management IMPLEMENTATION_TRACKER **R07** row (bench module list).

Depends on tracker **LV-R8-BE-01** (**PLC-SMOKE-BE-001** / WORKS seed). B3/B7–B10 handoff
integration rows need an **active** ``Budget Line`` with ``sub_program`` (BX4
``BL-MOH-2026-001`` or **WORKS** ``BUD-MOH-INFRA-2026-001`` after **R2-005**).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.procurement_lifecycle.tests.test_r8_014_planning_release_governance_smoke_regression

Companion evidence:
docs/prompts/0. usability handoff/R8_014_planning_release_governance_evidence.md
"""

from __future__ import annotations

import importlib
import unittest

_PLANNING_RELEASE_GOVERNANCE_MODULES: tuple[str, ...] = (
	"kentender_procurement.procurement_lifecycle.tests.test_r3_005_planning_release_handoff",
	"kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3",
	"kentender_procurement.tender_management.tests.test_planning_tender_handoff_configuration_b7",
	"kentender_procurement.tender_management.tests.test_planning_tender_handoff_audit_b8",
	"kentender_procurement.tender_management.tests.test_planning_tender_handoff_duplicate_b9",
	"kentender_procurement.tender_management.tests.test_planning_tender_handoff_release_integration_b10",
)


def load_tests(
	loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
	suite = unittest.TestSuite()
	for mod_path in _PLANNING_RELEASE_GOVERNANCE_MODULES:
		mod = importlib.import_module(mod_path)
		suite.addTests(loader.loadTestsFromModule(mod))
	return suite
