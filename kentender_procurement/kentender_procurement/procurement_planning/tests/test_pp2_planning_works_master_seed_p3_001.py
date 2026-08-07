# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-001 — PP2 WORKS master planning seed loader tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.pp2_constants import PKG_CONSUMED, PKG_RELEASED, PLAN_ACTIVE
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	ESTIMATED_VALUE,
	INCLUSION_CODE,
	PKGREL_CODE,
	PKG_CODE,
	PKG_LINE_CODE,
	PKG_TITLE,
	PLAN_CODE,
	PLAN_NAME,
	TENDER_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_BUDGET_LINE_CODE = "BUD-MOH-INFRA-2026-001"


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

		# Tender seed requires released package; seed planning through release first when needed.
		if not frappe.db.exists("TM2 Tender", TENDER_CODE):
			if not frappe.db.exists("Procurement Package", PKG_CODE):
				from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
					run_load,
				)

				run_load(checkpoint="RELEASED_TO_TENDER", force_reset=False)
			upsert_works_master_tender()


class TestPP2PlanningWorksMasterSeedP3001(IntegrationTestCase):
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

	def test_001_fresh_load_consumed_by_tender(self):
		"""SEED-TEST-P3-001-001: CONSUMED_BY_TENDER creates all domain objects."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)

		plan = frappe.get_doc("Procurement Plan", PLAN_CODE)
		self.assertEqual(plan.plan_name, PLAN_NAME)
		self.assertEqual(plan.status, PLAN_ACTIVE)
		self.assertTrue(plan.is_master_seed)

		self.assertTrue(frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE))
		pkg = frappe.get_doc("Procurement Package", PKG_CODE)
		self.assertEqual(pkg.package_name, PKG_TITLE)
		self.assertEqual(pkg.status, PKG_CONSUMED)
		self.assertTrue(pkg.locked_after_release)

		ln_name = frappe.db.get_value(
			"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
		)
		self.assertIsNotNone(ln_name)
		ln = frappe.get_doc("Procurement Package Line", ln_name)
		self.assertEqual(ln.package_id, PKG_CODE)
		self.assertAlmostEqual(flt(ln.amount), ESTIMATED_VALUE, places=2)

		self.assertTrue(frappe.db.exists("Package Method Decision", {"package_code": PKG_CODE}))
		self.assertTrue(frappe.db.exists("Package Readiness Result", {"package_code": PKG_CODE}))
		self.assertTrue(frappe.db.exists("Package Review Decision", {"package_code": PKG_CODE}))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", PKGREL_CODE))
		self.assertTrue(
			frappe.db.exists("Planning Release Consumption Record", {"release_code": PKGREL_CODE})
		)
		self.assertTrue(frappe.db.exists("TM2 Tender", TENDER_CODE))

	def test_002_idempotent_second_run(self):
		"""SEED-TEST-P3-001-002: Second run does not duplicate lines or releases."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		first = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(first.get("ok"))
		line_count_1 = frappe.db.count("Procurement Package Line", {"package_id": PKG_CODE})
		release_count_1 = frappe.db.count(
			"Planning Release Consumption Record", {"release_code": PKGREL_CODE}
		)

		second = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(second.get("ok"))
		line_count_2 = frappe.db.count("Procurement Package Line", {"package_id": PKG_CODE})
		release_count_2 = frappe.db.count(
			"Planning Release Consumption Record", {"release_code": PKGREL_CODE}
		)
		self.assertEqual(line_count_1, line_count_2)
		self.assertEqual(release_count_1, release_count_2)

	def test_003_missing_upstream_demand_fails(self):
		"""SEED-TEST-P3-001-003: Missing demand returns structured failure."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		demand_name = frappe.db.get_value("Demand", {"demand_id": DEMAND_CODE}, "name")
		try:
			if demand_name:
				frappe.delete_doc("Demand", demand_name, force=True, ignore_permissions=True)
				frappe.db.commit()

			out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "MISSING_DEMAND")
		finally:
			upsert_works_master_demand()
			frappe.db.commit()

	def test_004_force_reset_reloads(self):
		"""SEED-TEST-P3-001-004: force_reset clears and reloads master planning rows."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		first = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(first.get("ok"))

		out = seed_procurement_planning_works_master(
			checkpoint="CONSUMED_BY_TENDER", force_reset=True
		)
		self.assertTrue(out.get("ok"))
		self.assertTrue(frappe.db.exists("Procurement Package", PKG_CODE))
		self.assertEqual(
			frappe.db.get_value("Procurement Package", PKG_CODE, "status"), PKG_CONSUMED
		)

	def test_005_summary_json_shape(self):
		"""SEED-TEST-P3-001-005: Summary matches pack §6.5 shape."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"))
		for key in ("module", "scenario", "checkpoint", "ok", "records", "links", "failures"):
			self.assertIn(key, out)
		self.assertEqual(out["module"], "Procurement Planning v2")
		self.assertEqual(out["checkpoint"], "CONSUMED_BY_TENDER")
		self.assertEqual(out["links"]["demand"], DEMAND_CODE)
		self.assertEqual(out["links"]["package"], PKG_CODE)
		self.assertEqual(out["links"]["release"], PKGREL_CODE)
		self.assertEqual(out["links"]["tender"], TENDER_CODE)
		self.assertGreaterEqual(out["records"]["procurement_plans"], 1)
		self.assertGreaterEqual(out["records"]["consumption_records"], 1)

	def test_006_legacy_shim_delegates_to_pp2_released(self):
		"""Legacy upsert_works_master_planning shim loads PKG-MOH via PP2 RELEASED_TO_TENDER."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		from kentender_procurement.procurement_planning.seeds.works_master_planning_seed import (
			upsert_works_master_planning,
		)

		out = upsert_works_master_planning()
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("package_code"), PKG_CODE)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", PKG_CODE, "status"),
			PKG_RELEASED,
		)
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", PKGREL_CODE))
