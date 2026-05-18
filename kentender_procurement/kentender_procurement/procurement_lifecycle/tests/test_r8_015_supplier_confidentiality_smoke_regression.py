# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R8-015 / LV-R8-REG-04 — Supplier confidentiality regression (NEG-SUP-EVIDENCE-ACCESS-001).

Also satisfies **§14 G9-008** (Final Acceptance) — *Supplier confidentiality preserved* / NG-006.

Bundles **R3-020** ``test_r3_020_supplier_confidentiality`` so PLC usability work cannot
re-open internal journey / handoff / evidence surfaces to supplier actors (**G0-006** /
**LV-R3-020-01**).

**Primary path:** ``get_journey_evidence`` denied for Guest and ``KenTender External Supplier``
(**NEG-SUP-EVIDENCE-ACCESS-001**). Full module also covers DocPerm structural checks and the
other four PLC API gates.

**Site prerequisites:** WORKS journey / handoff seeds (e.g. ``JRN-MOH-2026-001``,
``PKGREL-MOH-2026-001``) and supplier smoke user ``smoke.b@kentender.test`` where named-user
tests apply — see **LV-R8-BE-01** / PLC master seed.

Desk UI mirroring (**LV-R7-007-01**) remains separate; this ticket records the **server/API**
regression gate.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.procurement_lifecycle.tests.test_r8_015_supplier_confidentiality_smoke_regression

Companion evidence:
docs/prompts/0. usability handoff/R8_015_supplier_confidentiality_evidence.md
"""

from __future__ import annotations

import importlib
import unittest

_SUPPLIER_CONFIDENTIALITY_MODULES = (
	"kentender_procurement.procurement_lifecycle.tests.test_r3_020_supplier_confidentiality",
)


def load_tests(
	loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None
) -> unittest.TestSuite:
	suite = unittest.TestSuite()
	for mod_path in _SUPPLIER_CONFIDENTIALITY_MODULES:
		mod = importlib.import_module(mod_path)
		suite.addTests(loader.loadTestsFromModule(mod))
	return suite
