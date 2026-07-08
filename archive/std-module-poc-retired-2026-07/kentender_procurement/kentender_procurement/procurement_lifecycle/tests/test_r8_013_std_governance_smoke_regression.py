# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R8-013 / LV-R8-REG-02 — STD Template Governance regression (Doc 8 server slice).

Bundles the automated governance smoke gate (**STD-GOV-ST-001** … **ST-017**, **ST-020** /
``§C``) implemented in **`test_std_template_governance_smoke_doc8`** so PLC rectification
evidence stays aligned with *STD Production Readiness* **§8 Smoke Test Specification**
and Tender Management controlling docs.

Depends on tracker **LV-R8-BE-01** (WORKS PLC seed readiness on the shared site profile);
the bundled tests rely on seeded governance roles/users and POC template loaders.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.procurement_lifecycle.tests.test_r8_013_std_governance_smoke_regression

Companion evidence:
docs/prompts/0. usability handoff/R8_013_std_admin_regression_evidence.md
"""

from __future__ import annotations

import importlib
import unittest

_STD_GOVERNANCE_SMOKE_MODULES = (
	"kentender_procurement.tender_management.tests.test_std_template_governance_smoke_doc8",
)


def load_tests(
	loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
	suite = unittest.TestSuite()
	for mod_path in _STD_GOVERNANCE_SMOKE_MODULES:
		mod = importlib.import_module(mod_path)
		suite.addTests(loader.loadTestsFromModule(mod))
	return suite
