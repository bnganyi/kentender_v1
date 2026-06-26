# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-012 — Backend regression gate manifest for Procurement Planning."""

from __future__ import annotations

import importlib
from pathlib import Path

from frappe.tests import UnitTestCase

from kentender_procurement.procurement_planning.tests.pp8_gate_constants import (
	P8_BACKEND_REGRESSION_MODULES,
)


class TestPP8BackendRegressionGateP8012(UnitTestCase):
	def test_pp8_012_regression_manifest_lists_importable_modules(self) -> None:
		missing: list[str] = []
		for module_path in P8_BACKEND_REGRESSION_MODULES:
			try:
				importlib.import_module(module_path)
			except ModuleNotFoundError:
				missing.append(module_path)
		self.assertFalse(missing, msg=f"P8 regression modules not importable: {missing}")

	def test_pp8_012_gate_script_exists(self) -> None:
		bench_root = Path(__file__).resolve().parents[6]
		script = bench_root / "scripts" / "pp8_backend_regression_gate.sh"
		self.assertTrue(script.exists(), msg=f"missing gate script: {script}")
		text = script.read_text(encoding="utf-8")
		self.assertIn("kentender_procurement.procurement_planning.tests", text)
		self.assertIn("P8-012", text)
