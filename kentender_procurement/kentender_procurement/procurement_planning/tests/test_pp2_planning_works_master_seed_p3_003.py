# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-003 — PP2 WORKS master planning seed clear/reset tests."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint, now_datetime

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	clear_procurement_planning_works_master_seed,
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_CODE,
	INCLUSION_CODE,
	JOURNEY_CODE,
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
_DECOY_PLAN = "PLAN-P3-003-DECOY"
_DECOY_PKG = "PKG-P3-003-DECOY"
_DECOY_HANDOFF = "HCO-P3-003-DECOY"


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


def _minimal_evidence_links() -> dict:
	return {
		"links": [
			{
				"label": "Test evidence",
				"object_type": "Demand",
				"object_code": "DEM-P3-003-DECOY",
				"module": "Demand Intake and Approval",
				"route": "/desk/",
				"visibility": "Internal",
			}
		]
	}


def _insert_decoy_planning_rows() -> None:
	template_id = frappe.get_all("Procurement Template", limit=1, pluck="name")
	template_id = template_id[0] if template_id else None
	risk_id = frappe.get_all("Risk Profile", limit=1, pluck="name")
	kpi_id = frappe.get_all("KPI Profile", limit=1, pluck="name")
	vendor_id = frappe.get_all("Vendor Management Profile", limit=1, pluck="name")
	dcp_id = frappe.get_all("Decision Criteria Profile", limit=1, pluck="name")
	if not all((template_id, risk_id, kpi_id, vendor_id, dcp_id)):
		raise RuntimeError("Missing procurement package profile prerequisites for decoy insert")
	frappe.get_doc(
		{
			"doctype": "Procurement Plan",
			"plan_name": "P3-003 decoy plan",
			"plan_code": _DECOY_PLAN,
			"fiscal_year": 2026,
			"procuring_entity": _PE_CODE,
			"currency": "KES",
			"status": "Draft",
			"is_active": 1,
			"is_master_seed": 0,
		}
	).insert(ignore_permissions=True)
	pkg = frappe.get_doc(
		{
			"doctype": "Procurement Package",
			"package_name": "P3-003 decoy package",
			"package_code": _DECOY_PKG,
			"plan_id": _DECOY_PLAN,
			"template_id": template_id,
			"currency": "KES",
			"estimated_value": 1,
			"procurement_method": "Open Tender",
			"contract_type": "Fixed Price",
			"risk_profile_id": risk_id[0] if risk_id else None,
			"kpi_profile_id": kpi_id[0] if kpi_id else None,
			"vendor_management_profile_id": vendor_id[0] if vendor_id else None,
			"decision_criteria_profile_id": dcp_id[0] if dcp_id else None,
			"status": "Draft",
			"is_active": 1,
			"is_master_seed": 0,
		}
	)
	pkg.flags.ignore_mandatory = True
	pkg.insert(ignore_permissions=True)
	frappe.get_doc(
		{
			"doctype": "Procurement Handoff Card",
			"handoff_code": _DECOY_HANDOFF,
			"handoff_title": "P3-003 decoy handoff",
			"journey_code": JOURNEY_CODE,
			"source_module": "Procurement Planning",
			"target_module": "Procurement Planning",
			"source_object_type": "Demand",
			"source_object_code": "DEM-P3-003-DECOY",
			"status": "Draft",
			"generated_by": "Administrator",
			"generated_at": str(now_datetime()),
			"locked_summary": {},
			"passed_forward_summary": {},
			"next_action": "n/a",
			"evidence_links_json": _minimal_evidence_links(),
			"technical_refs_json": {},
			"is_master_seed": 0,
		}
	).insert(ignore_permissions=True)


def _delete_decoy_planning_rows() -> None:
	for doctype, code in (
		("Procurement Handoff Card", _DECOY_HANDOFF),
		("Procurement Package", _DECOY_PKG),
		("Procurement Plan", _DECOY_PLAN),
	):
		if frappe.db.exists(doctype, code):
			frappe.delete_doc(doctype, code, force=True, ignore_permissions=True)


class TestPP2PlanningWorksMasterSeedClearP3003(IntegrationTestCase):
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
		_delete_decoy_planning_rows()

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		clear_master_planning_seed()
		_delete_decoy_planning_rows()

	def test_001_clear_removes_master_planning_rows(self):
		"""SEED-TEST-P3-003-001: Clear removes master seed; validator fails afterward."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(seed.get("ok"), seed)

		out = clear_procurement_planning_works_master_seed()
		self.assertTrue(out.get("ok"), out)
		self.assertFalse(frappe.db.exists("Procurement Plan", PLAN_CODE))
		self.assertFalse(frappe.db.exists("Procurement Package", PKG_CODE))
		self.assertFalse(frappe.db.exists("Procurement Handoff Card", INCLUSION_CODE))
		self.assertFalse(frappe.db.exists("Procurement Handoff Card", PKGREL_CODE))

		validation = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertFalse(validation.get("ok"))

	def test_002_upstream_records_survive_clear(self):
		"""SEED-TEST-P3-003-002: Demand, budget, journey, and tender are not deleted."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(clear_procurement_planning_works_master_seed().get("ok"))

		self.assertTrue(frappe.db.exists("Demand", {"demand_id": DEMAND_CODE}))
		self.assertTrue(frappe.db.exists("Budget Line", {"budget_line_code": BUDGET_LINE_CODE}))
		self.assertTrue(frappe.db.exists("Procurement Journey", JOURNEY_CODE))
		self.assertTrue(frappe.db.exists("TM2 Tender", TENDER_CODE))

	def test_003_decoy_planning_rows_survive_clear(self):
		"""SEED-TEST-P3-003-003: Off-allowlist decoy plan/package/handoff survive clear."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		_insert_decoy_planning_rows()
		seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(clear_procurement_planning_works_master_seed().get("ok"))

		self.assertFalse(frappe.db.exists("Procurement Plan", PLAN_CODE))
		self.assertTrue(frappe.db.exists("Procurement Plan", _DECOY_PLAN))
		self.assertTrue(frappe.db.exists("Procurement Package", _DECOY_PKG))
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", _DECOY_HANDOFF))

	def test_004_allowlisted_plan_without_master_flag_survives(self):
		"""SEED-TEST-P3-003-004: PLAN-MOH-2026 with is_master_seed=0 is not deleted."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		plan = frappe.get_doc("Procurement Plan", PLAN_CODE)
		plan.is_master_seed = 0
		plan.save(ignore_permissions=True)

		self.assertTrue(clear_procurement_planning_works_master_seed().get("ok"))
		self.assertTrue(frappe.db.exists("Procurement Plan", PLAN_CODE))
		self.assertEqual(
			cint(frappe.db.get_value("Procurement Plan", PLAN_CODE, "is_master_seed")),
			0,
		)

	def test_005_master_audit_events_removed(self):
		"""SEED-TEST-P3-003-005: Master-seed Planning Audit Events for journey are cleared."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		before = frappe.db.count(
			"Planning Audit Event",
			{"journey_code": JOURNEY_CODE, "is_master_seed": 1},
		)
		self.assertGreater(before, 0)

		self.assertTrue(clear_procurement_planning_works_master_seed().get("ok"))
		after = frappe.db.count(
			"Planning Audit Event",
			{"journey_code": JOURNEY_CODE, "is_master_seed": 1},
		)
		self.assertEqual(after, 0)

	def test_006_force_reset_reloads_after_clear(self):
		"""SEED-TEST-P3-003-006: force_reset reloads master planning seed after clear."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		first = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(first.get("ok"), first)

		out = seed_procurement_planning_works_master(
			checkpoint="CONSUMED_BY_TENDER", force_reset=True
		)
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(frappe.db.exists("Procurement Package", PKG_CODE))
		validation = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(validation.get("ok"), validation)

	def test_007_guard_blocks_clear_outside_dev_test(self):
		"""SEED-TEST-P3-003-007: Clear blocked when not in_test/developer_mode/allow_tests."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		orig_dev = frappe.conf.get("developer_mode")
		orig_allow = frappe.conf.get("allow_tests")
		try:
			frappe.conf.developer_mode = 0
			frappe.conf.allow_tests = 0
			with patch.object(frappe, "in_test", False):
				out = clear_procurement_planning_works_master_seed()
			self.assertFalse(out.get("ok"))
			self.assertEqual(out.get("error_code"), "SEED_CLEAR_BLOCKED")
		finally:
			frappe.conf.developer_mode = orig_dev
			frappe.conf.allow_tests = orig_allow
