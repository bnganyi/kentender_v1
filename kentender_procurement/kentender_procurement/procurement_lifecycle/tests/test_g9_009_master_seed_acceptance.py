# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""§14 G9-009 — WORKS master seed **accepted** (load + validator contract).

Bundles:

| Ticket | Role |
|--------|------|
| **R8-001 / PLC-SMOKE-BE-001** | ``load_procurement_lifecycle_works_master(reset=True, checkpoint="TENDER_PUBLISHED")`` + journey / seven base handoffs / no opening cards + **VAL-SEED-001**, **016–019** PASS |
| **R2-003** | Validator shape (**VAL-SEED-001…022**), unsupported checkpoint guard, PLC load → selected checks PASS |

**OPENING_READY** remains optional (spec §16 / tracker §16.5); this gate asserts **base** ``TENDER_PUBLISHED``.
Full aggregate ``validate … ok`` may still be false until TM2 satisfies **VAL-SEED-014/015/020/022** on the site — same caveat as **R8-001** evidence.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.procurement_lifecycle.tests.test_g9_009_master_seed_acceptance

Companion evidence:
docs/prompts/0. usability handoff/G9_009_master_seed_acceptance_evidence.md
"""

from __future__ import annotations

import importlib
import unittest

_G9_009_MODULES = (
	"kentender_procurement.procurement_lifecycle.tests.test_r8_001_plc_smoke_be_001_master_seed_load",
	"kentender_procurement.procurement_lifecycle.tests.test_r2_003_works_master_seed_validate",
)


def load_tests(
	loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
	suite = unittest.TestSuite()
	for mod_path in _G9_009_MODULES:
		mod = importlib.import_module(mod_path)
		suite.addTests(loader.loadTestsFromModule(mod))
	return suite
