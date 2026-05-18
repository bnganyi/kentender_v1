# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R8-012 / LV-R8-REG-01 — TM2 legal smoke regression.

Inventory (G0-004 TM2 legal control confirmation): aggregate **P11-04** and **P11-05**
acceptance modules so rectification **does not weaken** TM2 surface guards (see tracker **G0-004** /
``G0-004_tm2_legal_control_confirmation.md``).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r8_012_tm2_legal_smoke_regression

Companion evidence:
docs/prompts/0. usability handoff/R8_012_tm2_legal_regression_evidence.md
"""

from __future__ import annotations

import importlib
import unittest

_TM2_LEGAL_SMOKE_MODULES = (
	"kentender_procurement.tender_management.tests.test_p11_04_tm2_surface_no_procurement_tender",
	"kentender_procurement.tender_management.tests.test_p11_05_tm2_surface_no_procurement_tender_literal",
)


def load_tests(
	loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
	suite = unittest.TestSuite()
	for mod_path in _TM2_LEGAL_SMOKE_MODULES:
		mod = importlib.import_module(mod_path)
		suite.addTests(loader.loadTestsFromModule(mod))
	return suite
