# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-009 — Procurement Package Line strict-spec seed compliance tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.pp2_constants import PKG_DRAFT
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	CURRENCY,
	DEMAND_CODE,
	DEMAND_ITEM_CODE,
	ESTIMATED_VALUE,
	PKG_CODE,
	PKG_LINE_CODE,
	PKG_LINE_DESCRIPTION,
	PKG_LINE_QUANTITY,
	PKG_LINE_TITLE,
	PKG_LINE_UOM,
	PKG_PROCUREMENT_CATEGORY,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.inclusion import (
	ensure_planning_inclusion,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.package import (
	ensure_master_package,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	ensure_procurement_plan,
)
from kentender_procurement.procurement_planning.services.planning_references import resolve_demand_name
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


def _resolve_budget_line_name() -> str:
	name = frappe.db.get_value("Budget Line", {"budget_line_code": BUDGET_LINE_CODE}, "name")
	if name:
		return name
	if frappe.db.exists("Budget Line", BUDGET_LINE_CODE):
		return BUDGET_LINE_CODE
	raise RuntimeError(f"Budget Line {BUDGET_LINE_CODE} not found")


def _get_master_line():
	line_name = frappe.db.get_value(
		"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
	)
	if not line_name:
		raise RuntimeError(f"Package line {PKG_LINE_CODE} not found")
	return frappe.get_doc("Procurement Package Line", line_name)


def _assert_strict_package_line_draft_state(test_case) -> None:
	line = _get_master_line()
	demand_name = resolve_demand_name(DEMAND_CODE)
	budget_line_name = _resolve_budget_line_name()

	test_case.assertTrue(line.is_master_seed)
	test_case.assertTrue(line.is_active)
	test_case.assertEqual(line.package_line_code, PKG_LINE_CODE)
	test_case.assertEqual(line.package_id, PKG_CODE)
	test_case.assertEqual(line.demand_id, demand_name)
	test_case.assertEqual(line.demand_item_code, DEMAND_ITEM_CODE)
	test_case.assertEqual(line.budget_line_id, budget_line_name)
	test_case.assertEqual(line.line_title, PKG_LINE_TITLE)
	test_case.assertEqual(line.line_description, PKG_LINE_DESCRIPTION)
	test_case.assertEqual(line.procurement_category, PKG_PROCUREMENT_CATEGORY)
	test_case.assertEqual(line.unit_of_measure, PKG_LINE_UOM)
	test_case.assertEqual(flt(line.quantity), PKG_LINE_QUANTITY)
	test_case.assertAlmostEqual(flt(line.estimated_unit_cost), ESTIMATED_VALUE, places=2)
	test_case.assertAlmostEqual(flt(line.amount), ESTIMATED_VALUE, places=2)
	test_case.assertEqual(line.currency, CURRENCY)
	test_case.assertEqual(line.line_status, PKG_DRAFT)


class TestPP2PlanningWorksMasterSeedP3009(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package Line"):
			cls._skip = True
			return
		cls._skip = False
		_bootstrap_upstream()

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

	def test_001_package_draft_checkpoint_sets_strict_line_fields(self):
		"""SEED-TEST-P3-009-001: PACKAGE_DRAFT seeds strict PKGLINE-MOH-2026-001-001 values."""
		if self._skip:
			self.skipTest("Procurement Package Line DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(
			frappe.db.exists("Procurement Package Line", {"package_line_code": PKG_LINE_CODE})
		)
		_assert_strict_package_line_draft_state(self)

	def test_002_existing_line_is_repaired_to_spec(self):
		"""SEED-TEST-P3-009-002: Existing drifted line is repaired by ensure_master_package."""
		if self._skip:
			self.skipTest("Procurement Package Line DocType not installed")

		ensure_procurement_plan()
		ensure_planning_inclusion()
		ensure_master_package()
		demand_name = resolve_demand_name(DEMAND_CODE)
		budget_line_name = _resolve_budget_line_name()

		line = frappe.get_doc(
			{
				"doctype": "Procurement Package Line",
				"package_id": PKG_CODE,
				"package_line_code": PKG_LINE_CODE,
				"demand_id": demand_name,
				"budget_line_id": budget_line_name,
				"demand_item_code": "DEMITEM-DRIFT",
				"amount": 1.0,
				"quantity": 2.0,
				"line_title": "Drifted Line",
				"procurement_category": "Goods",
				"line_status": PKG_DRAFT,
				"is_active": 1,
				"is_master_seed": 0,
			}
		)
		line.flags.ignore_mandatory = True
		frappe.delete_doc(
			"Procurement Package Line",
			frappe.db.get_value(
				"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
			),
			force=1,
		)
		line.insert(ignore_permissions=True)
		frappe.db.commit()

		ensure_master_package()
		_assert_strict_package_line_draft_state(self)

	def test_003_validator_val_006_fails_on_line_drift(self):
		"""SEED-TEST-P3-009-003: VAL-006 fails when line fields drift from strict spec."""
		if self._skip:
			self.skipTest("Procurement Package Line DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(out.get("ok"), out)

		line_name = frappe.db.get_value(
			"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
		)
		frappe.db.set_value(
			"Procurement Package Line",
			line_name,
			{
				"line_title": "Drifted Line",
				"demand_item_code": "DEMITEM-DRIFT",
				"is_master_seed": 0,
			},
			update_modified=False,
		)
		frappe.db.commit()

		validation = validate_procurement_planning_works_master_seed(checkpoint="PACKAGE_DRAFT")
		self.assertFalse(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_006 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-006"), {})
		self.assertEqual(val_006.get("result"), "FAIL")

	def test_004_package_draft_validation_passes_val_006_and_007(self):
		"""SEED-TEST-P3-009-004: PACKAGE_DRAFT validation passes VAL-006/007 after seed."""
		if self._skip:
			self.skipTest("Procurement Package Line DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(out.get("ok"), out)

		validation = validate_procurement_planning_works_master_seed(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_006 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-006"), {})
		val_007 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-007"), {})
		self.assertEqual(val_006.get("result"), "PASS")
		self.assertEqual(val_007.get("result"), "PASS")
