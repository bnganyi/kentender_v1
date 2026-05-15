# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""X-01 — manifest for planning + STD POC regression modules (cross-cutting gate).

The full gate runs ``frappe-bench/scripts/x_01_planning_std_poc_regression_gate.sh`` or
``make x-01-planning-std-poc-gate`` from ``apps/kentender_v1``.

**Keep** ``X01_PLANNING_STD_POC_BENCH_MODULES`` in sync with the ``modules=(...)`` array in
``scripts/x_01_planning_std_poc_regression_gate.sh``.
"""

from __future__ import annotations

import importlib.util
import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_governance import STATUS_ACTIVE
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

# Planning default STD (B2) → planning↔STD surface.
# Planning↔tender linkage (B1).
# STD template resolution / handoff (B6).
# Package → tender release (B3).
# STD governance usage (GOV008).
# Create tender from package (P4-01).
X01_PLANNING_STD_POC_BENCH_MODULES: tuple[str, ...] = (
	"kentender_procurement.procurement_planning.tests.test_procurement_template_default_std_b2",
	"kentender_procurement.tender_management.tests.test_planning_tender_linkage_b1",
	"kentender_procurement.tender_management.tests.test_std_template_handoff_resolution_b6",
	"kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3",
	"kentender_procurement.tender_management.tests.test_std_template_governance_usage_gov008",
	"kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package",
)


class TestX01PlanningStdPocRegressionManifest(unittest.TestCase):
	def test_x_01_declared_regression_modules_are_importable(self) -> None:
		for mod in X01_PLANNING_STD_POC_BENCH_MODULES:
			with self.subTest(module=mod):
				spec = importlib.util.find_spec(mod)
				self.assertIsNotNone(spec, msg=f"missing or unloadable module: {mod}")


class TestX01PocStdUpsertSupportsPlanningHandoff(IntegrationTestCase):
	"""Regression: loader + ``STD Template`` validate must not contradict manifest tender flag."""

	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def test_upsert_works_poc_std_keeps_allowed_for_tender_creation(self) -> None:
		upsert_std_template(commit=True)
		row = frappe.db.get_value(
			"STD Template",
			TEMPLATE_CODE,
			["allowed_for_tender_creation", "lifecycle_status"],
			as_dict=True,
		)
		self.assertIsNotNone(row)
		self.assertEqual(int(row.get("allowed_for_tender_creation") or 0), 1)
		self.assertEqual((row.get("lifecycle_status") or "").strip(), STATUS_ACTIVE)
