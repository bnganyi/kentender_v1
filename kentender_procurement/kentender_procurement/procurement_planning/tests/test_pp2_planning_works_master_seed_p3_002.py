# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-002 — PP2 WORKS master planning seed validator tests."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	ESTIMATED_VALUE,
	PKGREL_CODE,
	PKG_CODE,
	PLAN_CODE,
	TENDER_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"


def _bootstrap_upstream(*, with_tender: bool = True) -> None:
	ensure_currency_kes()
	ensure_procuring_entity(_PE_CODE, _PE_NAME)
	assert upsert_works_master_strategy_hierarchy().get("ok")
	assert upsert_works_master_budget().get("ok")
	assert upsert_works_master_demand().get("ok")
	assert upsert_works_master_journey().get("ok")
	from kentender_procurement.tender_management.seeds.works_master_std_seed import (
		upsert_works_master_std,
	)

	assert upsert_works_master_std().get("ok")
	if with_tender:
		from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
			upsert_works_master_tender,
		)

		if not frappe.db.exists("TM2 Tender", TENDER_CODE):
			if not frappe.db.exists("Procurement Package", PKG_CODE):
				from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
					run_load,
				)

				run_load(checkpoint="RELEASED_TO_TENDER", force_reset=False)
			upsert_works_master_tender()


class TestPP2PlanningWorksMasterSeedValidateUnsupported(unittest.TestCase):
	def test_005_unknown_checkpoint_returns_error_dict(self):
		"""SEED-TEST-P3-002-005: Unknown checkpoint returns UNSUPPORTED_CHECKPOINT."""
		out = validate_procurement_planning_works_master_seed(checkpoint="PHANTOM")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "UNSUPPORTED_CHECKPOINT")


class TestPP2PlanningWorksMasterSeedValidateP3002(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
			cls._skip = True
			return
		cls._skip = False
		_bootstrap_upstream(with_tender=True)

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		clear_master_planning_seed()

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		clear_master_planning_seed()

	def test_001_validate_passes_after_consumed_seed(self):
		"""SEED-TEST-P3-002-001: CONSUMED_BY_TENDER seed passes all 19 VAL checks."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(seed.get("ok"), seed)

		out = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(len(out["checks"]), 19)
		ids = {c["check_id"] for c in out["checks"]}
		self.assertEqual(
			ids,
			{f"PP2-SEED-VAL-{i:03d}" for i in range(1, 20)},
		)
		for check in out["checks"]:
			self.assertEqual(check["result"], "PASS", msg=f"{check['check_id']}: {check}")

	def test_002_validate_fails_without_seed(self):
		"""SEED-TEST-P3-002-002: Validator fails when planning seed records are absent."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		out = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertFalse(out.get("ok"))
		self.assertGreater(out.get("failed", 0), 0)
		by_id = {c["check_id"]: c for c in out["checks"]}
		self.assertEqual(by_id["PP2-SEED-VAL-001"]["result"], "FAIL")
		self.assertFalse(frappe.db.exists("Procurement Plan", PLAN_CODE))

	def test_003_summary_json_shape(self):
		"""SEED-TEST-P3-002-003: Validation output matches pack §21.2 summary contract."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		out = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		for key in (
			"module",
			"scenario",
			"checkpoint",
			"ok",
			"records",
			"links",
			"failures",
			"checks",
			"passed",
			"failed",
		):
			self.assertIn(key, out)
		self.assertEqual(out["module"], "Procurement Planning v2")
		self.assertEqual(out["checkpoint"], "CONSUMED_BY_TENDER")
		self.assertEqual(out["links"]["demand"], DEMAND_CODE)
		self.assertEqual(out["links"]["package"], PKG_CODE)
		self.assertEqual(out["links"]["release"], PKGREL_CODE)
		self.assertEqual(out["links"]["tender"], TENDER_CODE)

	def test_004_checkpoint_gating_package_draft(self):
		"""SEED-TEST-P3-002-004: PACKAGE_DRAFT validates package checks but not release/consumption."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		seed = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(seed.get("ok"), seed)

		out = validate_procurement_planning_works_master_seed(checkpoint="PACKAGE_DRAFT")
		ids = {c["check_id"] for c in out["checks"]}
		for required in (
			"PP2-SEED-VAL-001",
			"PP2-SEED-VAL-004",
			"PP2-SEED-VAL-008",
			"PP2-SEED-VAL-015",
		):
			self.assertIn(required, ids)
		for excluded in (
			"PP2-SEED-VAL-009",
			"PP2-SEED-VAL-010",
			"PP2-SEED-VAL-011",
			"PP2-SEED-VAL-012",
			"PP2-SEED-VAL-013",
			"PP2-SEED-VAL-014",
			"PP2-SEED-VAL-016",
			"PP2-SEED-VAL-017",
			"PP2-SEED-VAL-018",
			"PP2-SEED-VAL-019",
		):
			self.assertNotIn(excluded, ids)

	def test_006_tampered_package_total_fails_val_007(self):
		"""SEED-TEST-P3-002-006: Package total mismatch fails PP2-SEED-VAL-007."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		frappe.db.set_value(
			"Procurement Package",
			PKG_CODE,
			"estimated_value",
			flt(ESTIMATED_VALUE) + 1,
		)
		frappe.db.commit()

		out = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertFalse(out.get("ok"))
		by_id = {c["check_id"]: c for c in out["checks"]}
		self.assertEqual(by_id["PP2-SEED-VAL-007"]["result"], "FAIL")
