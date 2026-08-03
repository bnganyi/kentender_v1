# Copyright (c) 2026, KenTender and contributors
"""Focused STR-AC / §22 matrix samples for Strategy MVP-1."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import (
	list_applicable_value_commitments,
	list_active_targets,
	validate_strategy_reference,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_transitions import (
	transition_measurement,
	transition_plan,
)
from kentender_strategy.services.strategy_writes import save_measurement_draft


class TestStrategyMvp1AcMatrix(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()

	def test_str_ac_009_active_targets_only(self):
		rows = list_active_targets(procuring_entity=self.seed["procuring_entity"])
		self.assertTrue(all(r.get("node_code") for r in rows))
		self.assertTrue(any(r["node_code"] == TARGET_CODE for r in rows))

	def test_str_ac_010_applicability_filter(self):
		# Category-triggered PVOs require ICT category
		with_ict = list_applicable_value_commitments(
			plan_version=self.seed["plan"], procurement_category="ICT"
		)
		without = list_applicable_value_commitments(
			plan_version=self.seed["plan"], procurement_category="Works"
		)
		codes_ict = {(c.get("objective") or {}).get("code") for c in with_ict}
		codes_works = {(c.get("objective") or {}).get("code") for c in without}
		self.assertIn("PVO-ECO-01", codes_ict)  # universal
		self.assertNotIn("PVO-SUS-01", codes_works)

	def test_str_ac_013_duplicate_period_blocked(self):
		tgt = self.seed["target"]
		with self.assertRaises(frappe.ValidationError):
			save_measurement_draft(
				{
					"performance_target": tgt,
					"plan_version": self.seed["plan"],
					"measurement_period_start": "2027-09-01",
					"measurement_period_end": "2027-09-30",
					"measurement_date": "2027-10-06",
					"actual_numeric": 99.5,
					"evidence_reference": "DUP",
					"evidence_source": "test",
				}
			)

	def test_str_ac_008_historical_reference_resolves(self):
		tgt = self.seed["target"]
		ref = validate_strategy_reference(
			{
				"plan_version_id": self.seed["plan"],
				"node_id": tgt,
				"node_type": "PerformanceTarget",
			}
		)
		self.assertTrue(ref["valid"])
		self.assertTrue(ref.get("historical_ok", True))

	def test_api_whitelist_surface(self):
		from kentender_strategy.api import strategy_api

		self.assertTrue(callable(strategy_api.get_strategy_portfolio))
		self.assertTrue(callable(strategy_api.validate_strategy_reference))
		self.assertTrue(callable(strategy_api.get_plan_readiness_api))
