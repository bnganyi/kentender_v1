# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-017 — Negative fixture validator tests (spec §22)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.seeds.negative_fixtures.bootstrap import (
	_resolve_demand_docname,
)
from kentender_procurement.procurement_planning.seeds.negative_fixtures.constants import (
	ALL_NEGATIVE_FIXTURE_CODES,
	FIXTURE_METADATA,
	FIXTURE_NEG_PP2_DEMAND_NOT_APPROVED,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	clear_procurement_planning_negative_fixture,
	load_procurement_planning_negative_fixture,
	seed_procurement_planning_works_master,
	validate_procurement_planning_negative_fixture,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"


def _bootstrap_upstream() -> None:
	ensure_currency_kes()
	ensure_procuring_entity(_PE_CODE, _PE_NAME)
	assert upsert_works_master_strategy_hierarchy().get("ok")
	assert upsert_works_master_budget().get("ok")
	assert upsert_works_master_demand().get("ok")
	assert upsert_works_master_journey().get("ok")


class TestPP2PlanningWorksMasterSeedP3017(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			cls._skip = True
			return
		cls._skip = False
		_bootstrap_upstream()
		seed_procurement_planning_works_master(checkpoint="RELEASED_TO_TENDER")
		frappe.db.commit()

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		for fixture_code in ALL_NEGATIVE_FIXTURE_CODES:
			clear_procurement_planning_negative_fixture(fixture_code)

	def test_001_unknown_fixture_returns_unknown_fixture(self):
		"""SEED-TEST-P3-017-001: Unknown fixture code returns ok=False + UNKNOWN_FIXTURE."""
		if self._skip:
			self.skipTest("Procurement Plan DocType not installed")

		out = validate_procurement_planning_negative_fixture("NEG-PP2-DOES-NOT-EXIST")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "UNKNOWN_FIXTURE")
		self.assertEqual(out.get("fixture_code"), "NEG-PP2-DOES-NOT-EXIST")

	def test_002_validate_without_load_returns_fixture_not_loaded(self):
		"""SEED-TEST-P3-017-002: Validate without load returns FIXTURE_NOT_LOADED."""
		if self._skip:
			self.skipTest("Procurement Plan DocType not installed")

		fixture_code = FIXTURE_NEG_PP2_DEMAND_NOT_APPROVED
		clear_procurement_planning_negative_fixture(fixture_code)
		out = validate_procurement_planning_negative_fixture(fixture_code)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "FIXTURE_NOT_LOADED")
		self.assertEqual(out.get("fixture_code"), fixture_code)

	def test_003_each_loaded_fixture_validates_expected_blocker(self):
		"""SEED-TEST-P3-017-003: Load then validate proves registry blocker for all 12 fixtures."""
		if self._skip:
			self.skipTest("Procurement Plan DocType not installed")
		if not frappe.db.exists("DocType", "TM2 Tender"):
			self.skipTest("TM2 Tender DocType not installed")

		for fixture_code in ALL_NEGATIVE_FIXTURE_CODES:
			with self.subTest(fixture_code=fixture_code):
				clear_procurement_planning_negative_fixture(fixture_code)
				load_out = load_procurement_planning_negative_fixture(fixture_code)
				self.assertTrue(load_out.get("ok"), load_out)
				meta = FIXTURE_METADATA[fixture_code]

				out = validate_procurement_planning_negative_fixture(fixture_code)
				self.assertTrue(out.get("ok"), out)
				self.assertEqual(out.get("fixture_code"), fixture_code)
				self.assertEqual(out.get("attempted_action"), meta["attempted_action"])
				self.assertEqual(out.get("expected_result"), "FAIL")
				self.assertEqual(out.get("expected_blocker_code"), meta["blocker_code"])
				self.assertEqual(out.get("observed_result"), "FAIL")
				self.assertEqual(out.get("observed_blocker_code"), meta["blocker_code"])
				self.assertIsInstance(out.get("proof"), dict)

	def test_004_drifted_setup_fails_validation(self):
		"""SEED-TEST-P3-017-004: Drifted precondition fails NEG_FIXTURE_VALIDATION_FAILED."""
		if self._skip:
			self.skipTest("Procurement Plan DocType not installed")

		fixture_code = FIXTURE_NEG_PP2_DEMAND_NOT_APPROVED
		clear_procurement_planning_negative_fixture(fixture_code)
		load_out = load_procurement_planning_negative_fixture(fixture_code)
		self.assertTrue(load_out.get("ok"), load_out)

		demand_code = load_out["records"]["demand_code"]
		demand_name = _resolve_demand_docname(demand_code)
		self.assertTrue(demand_name)
		frappe.db.set_value("Demand", demand_name, "status", "Approved", update_modified=False)
		frappe.db.commit()

		out = validate_procurement_planning_negative_fixture(fixture_code)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NEG_FIXTURE_VALIDATION_FAILED")
		self.assertEqual(out.get("fixture_code"), fixture_code)
