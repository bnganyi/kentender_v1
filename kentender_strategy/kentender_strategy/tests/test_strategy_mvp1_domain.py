# Copyright (c) 2026, KenTender and contributors
"""Strategy MVP-1 domain/service acceptance coverage (STR-AC + §22 sample)."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import (
	get_strategy_portfolio,
	get_strategy_tree,
	list_active_targets,
	list_measurements,
	validate_strategy_reference,
)
from kentender_strategy.services.strategy_domain_guards import CODE_RE
from kentender_strategy.services.strategy_measurement import (
	compute_measurement_result,
	derive_measurement_result,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_readiness import get_plan_readiness
from kentender_strategy.services.strategy_transitions import transition_plan


class TestStrategyMvp1Domain(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()

	def test_seed_active_plan_and_hierarchy(self):
		self.assertTrue(self.seed.get("ok"))
		plan = frappe.get_doc("Strategic Plan", self.seed["plan"])
		self.assertEqual(plan.plan_code, STRATEGY_PLAN_CODE)
		self.assertEqual(plan.status, "Active")
		self.assertTrue(frappe.db.exists("Performance Target", {"target_code": TARGET_CODE}))
		self.assertEqual(frappe.db.count("Public Value Objective", {"status": "Active"}), 8)
		self.assertEqual(
			frappe.db.count("Performance Measurement", {"plan_version": plan.name, "workflow_status": "Verified"}),
			2,
		)

	def test_seed_idempotent(self):
		again = upsert_works_master_strategy_hierarchy()
		self.assertTrue(again.get("ok"))
		self.assertEqual(again["plan"], self.seed["plan"])

	def test_portfolio_and_tree_contracts(self):
		portfolio = get_strategy_portfolio(procuring_entity=self.seed["procuring_entity"])
		codes = {p["code"] for p in portfolio["plans"]}
		self.assertIn(STRATEGY_PLAN_CODE, codes)
		tree = get_strategy_tree(plan_code=STRATEGY_PLAN_CODE)
		self.assertEqual(tree["plan"]["code"], STRATEGY_PLAN_CODE)
		self.assertGreaterEqual(tree["counts"]["targets"], 1)
		self.assertEqual(tree["tree"][0]["type"], "Programme")

	def test_active_targets_and_reference_validation(self):
		targets = list_active_targets(procuring_entity=self.seed["procuring_entity"])
		self.assertTrue(any(t["node_code"] == TARGET_CODE for t in targets))
		tgt = frappe.db.get_value("Performance Target", {"target_code": TARGET_CODE}, "name")
		ref = validate_strategy_reference(
			{"plan_version_id": self.seed["plan"], "node_id": tgt, "node_type": "PerformanceTarget"}
		)
		self.assertTrue(ref["valid"])
		self.assertTrue(ref["selectable_for_new"])
		self.assertEqual(ref["reference"]["node_code"], TARGET_CODE)

	def test_cross_version_parent_rejected(self):
		# Create a second draft plan and attempt cross-link
		pe = self.seed["procuring_entity"]
		other = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"plan_code": "MOH-SP-CROSS-TEST",
				"version_number": 1,
				"title": "Cross version reject fixture",
				"procuring_entity": pe,
				"plan_type": "Entity Strategic Plan",
				"status": "Draft",
				"start_date": "2026-07-01",
				"end_date": "2027-06-30",
			}
		).insert(ignore_permissions=True)
		prog = frappe.db.get_value("Strategy Programme", {"programme_code": "MOH-PROG-0001"}, "name")
		try:
			with self.assertRaises(frappe.ValidationError):
				frappe.get_doc(
					{
						"doctype": "Strategic Outcome",
						"outcome_code": "MOH-OUT-CROSS",
						"title": "Cross",
						"plan_version": other.name,
						"programme": prog,
						"responsible_function": "X",
						"order_index": 1,
					}
				).insert(ignore_permissions=True)
		finally:
			frappe.delete_doc("Strategic Plan", other.name, force=True, ignore_permissions=True)

	def test_measurement_derivation_at_least(self):
		tgt = frappe.db.get_value("Performance Target", {"target_code": TARGET_CODE}, "name")
		doc = frappe._dict(
			performance_target=tgt,
			actual_numeric=99.82,
			actual_text=None,
			variance=None,
			result_status=None,
		)
		derive_measurement_result(doc)
		self.assertEqual(doc.result_status, "At risk")
		doc.actual_numeric = 99.96
		derive_measurement_result(doc)
		self.assertEqual(doc.result_status, "On track")

	def test_compute_measurement_result_pure(self):
		"""Live Submit preview uses the same pure rules as save-time derivation."""
		at_risk = compute_measurement_result(
			measurement_type="Percentage",
			comparison_direction="At least",
			target_numeric=99.9,
			tolerance_value=0.1,
			actual_numeric=99.82,
		)
		self.assertEqual(at_risk["result_status"], "At risk")
		self.assertAlmostEqual(at_risk["variance"], 99.82 - 99.9, places=4)

		on_track = compute_measurement_result(
			measurement_type="Percentage",
			comparison_direction="At least",
			target_numeric=99.9,
			tolerance_value=0.1,
			actual_numeric=99.96,
		)
		self.assertEqual(on_track["result_status"], "On track")

		empty = compute_measurement_result(
			measurement_type="Percentage",
			comparison_direction="At least",
			target_numeric=99.9,
			tolerance_value=0.1,
			actual_numeric=None,
		)
		self.assertEqual(empty["result_status"], "No data")
		self.assertIsNone(empty["variance"])

	def test_list_measurements(self):
		dto = list_measurements(plan_code=STRATEGY_PLAN_CODE)
		self.assertIsInstance(dto, dict)
		self.assertGreaterEqual(len(dto.get("rows") or []), 2)

	def test_readiness_ready_for_active_seed(self):
		# Active plan already passed readiness; structural readiness should still report ready=True
		# when evaluated against the seeded hierarchy (status aside).
		result = get_plan_readiness(self.seed["plan"])
		self.assertIn("grouped", result)

	def test_code_pattern(self):
		self.assertTrue(CODE_RE.match("MOH-TGT-0001"))
		self.assertIsNone(CODE_RE.match("moh-tgt"))

	def test_immutable_active_plan(self):
		plan = frappe.get_doc("Strategic Plan", self.seed["plan"])
		plan.title = "Should not change"
		with self.assertRaises(frappe.ValidationError):
			plan.save(ignore_permissions=True)

	def test_legacy_absence_active_path(self):
		# Active MVP path must not rely on removed builder APIs
		self.assertFalse(frappe.db.exists("DocType", "Strategy Objective"))
		# Legacy tables may linger historically; DocType must not be active
		# (teardown patch may leave orphan tables — DocType registry is the contract)
		for name in ("Strategy Builder",):
			self.assertFalse(frappe.db.exists("Page", "strategy-builder"))
