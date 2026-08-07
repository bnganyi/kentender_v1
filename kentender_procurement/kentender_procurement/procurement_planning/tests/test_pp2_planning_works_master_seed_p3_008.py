# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-008 — Procurement Package strict-spec seed compliance tests."""

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
	ESTIMATED_VALUE,
	INCLUSION_CODE,
	JOURNEY_CODE,
	PKG_CODE,
	PKG_DESCRIPTION,
	PKG_FISCAL_YEAR,
	PKG_PREPARED_AT,
	PKG_PRIORITY,
	PKG_PROCUREMENT_CATEGORY,
	PKG_REQUIRED_STD_CATEGORY,
	PKG_REQUIRED_STD_TYPE,
	PKG_TITLE,
	PLAN_CODE,
	PLAN_CREATOR_USER_CODE,
	PE_CODE,
	STD_VERSION_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.inclusion import (
	ensure_planning_inclusion,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.package import (
	_resolve_template_for_works,
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


def _user_code(user_name: str | None) -> str:
	if not user_name or not frappe.db.exists("User", user_name):
		return ""
	return str(frappe.db.get_value("User", user_name, "username") or "").strip()


def _resolve_budget_line_name() -> str:
	name = frappe.db.get_value("Budget Line", {"budget_line_code": BUDGET_LINE_CODE}, "name")
	if name:
		return name
	if frappe.db.exists("Budget Line", BUDGET_LINE_CODE):
		return BUDGET_LINE_CODE
	raise RuntimeError(f"Budget Line {BUDGET_LINE_CODE} not found")


def _assert_strict_package_draft_state(test_case) -> None:
	pkg = frappe.get_doc("Procurement Package", PKG_CODE)
	test_case.assertTrue(pkg.is_master_seed)
	test_case.assertEqual(pkg.package_name, PKG_TITLE)
	test_case.assertEqual(pkg.package_description, PKG_DESCRIPTION)
	test_case.assertEqual(pkg.plan_id, PLAN_CODE)
	test_case.assertEqual(pkg.planning_inclusion_code, INCLUSION_CODE)
	test_case.assertEqual(pkg.procurement_category, PKG_PROCUREMENT_CATEGORY)
	test_case.assertEqual(pkg.procurement_method, "Open Tender")
	test_case.assertEqual(pkg.required_std_category, PKG_REQUIRED_STD_CATEGORY)
	test_case.assertEqual(pkg.required_std_type, PKG_REQUIRED_STD_TYPE)
	test_case.assertEqual(pkg.required_std_template_version_code, STD_VERSION_CODE)
	test_case.assertEqual(pkg.procuring_entity_code, PE_CODE)
	test_case.assertEqual(pkg.fiscal_year, PKG_FISCAL_YEAR)
	test_case.assertEqual(pkg.package_priority, PKG_PRIORITY)
	test_case.assertEqual(pkg.currency, CURRENCY)
	test_case.assertEqual(flt(pkg.estimated_value), ESTIMATED_VALUE)
	test_case.assertEqual(pkg.journey_code, JOURNEY_CODE)
	test_case.assertEqual(_user_code(pkg.created_by), PLAN_CREATOR_USER_CODE)
	test_case.assertEqual(str(pkg.prepared_at).split(".")[0], PKG_PREPARED_AT)
	test_case.assertEqual(pkg.status, PKG_DRAFT)
	test_case.assertEqual(pkg.readiness_status, "Not Run")
	test_case.assertFalse((pkg.release_code or "").strip())
	test_case.assertFalse((pkg.tender_code or "").strip())
	test_case.assertFalse(pkg.locked_after_release)


class TestPP2PlanningWorksMasterSeedP3008(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
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

	def test_001_package_draft_checkpoint_sets_strict_package_fields(self):
		"""SEED-TEST-P3-008-001: PACKAGE_DRAFT seeds strict PKG-MOH-2026-001 values."""
		if self._skip:
			self.skipTest("Procurement Package DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(frappe.db.exists("Procurement Package", PKG_CODE))
		_assert_strict_package_draft_state(self)

	def test_002_existing_package_is_repaired_to_spec(self):
		"""SEED-TEST-P3-008-002: Existing drifted PKG-MOH-2026-001 is repaired by ensure_master_package."""
		if self._skip:
			self.skipTest("Procurement Package DocType not installed")

		ensure_procurement_plan()
		ensure_planning_inclusion()
		template = _resolve_template_for_works()
		demand_name = resolve_demand_name(DEMAND_CODE)
		budget_line_name = _resolve_budget_line_name()
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"package_code": PKG_CODE,
				"plan_id": PLAN_CODE,
				"template_id": template["name"],
				"package_name": "Drifted Package",
				"procurement_method": "RFQ",
				"contract_type": "Fixed Price",
				"procurement_category": "Goods",
				"currency": CURRENCY,
				"status": PKG_DRAFT,
				"is_active": 1,
				"is_master_seed": 0,
				"method_override_flag": 0,
				"is_emergency": 0,
				"planning_inclusion_code": "PLANINCL-DRIFT",
				"demand_id": demand_name,
				"budget_line_id": budget_line_name,
				"journey_code": JOURNEY_CODE,
				"risk_profile_id": template.get("risk_profile_id"),
				"kpi_profile_id": template.get("kpi_profile_id"),
				"decision_criteria_profile_id": template.get("decision_criteria_profile_id"),
				"vendor_management_profile_id": template.get("vendor_management_profile_id"),
				"created_by": "Administrator",
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		ensure_master_package()
		_assert_strict_package_draft_state(self)

	def test_003_validator_val_004_fails_on_package_drift(self):
		"""SEED-TEST-P3-008-003: VAL-004 fails when package fields drift from strict spec."""
		if self._skip:
			self.skipTest("Procurement Package DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(out.get("ok"), out)

		frappe.db.set_value(
			"Procurement Package",
			PKG_CODE,
			{
				"package_name": "Drifted Package",
				"procuring_entity_code": "PE-DRIFT",
				"is_master_seed": 0,
			},
			update_modified=False,
		)
		frappe.db.commit()

		validation = validate_procurement_planning_works_master_seed(checkpoint="PACKAGE_DRAFT")
		self.assertFalse(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_004 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-004"), {})
		self.assertEqual(val_004.get("result"), "FAIL")

	def test_004_package_draft_validation_passes_val_004_and_005(self):
		"""SEED-TEST-P3-008-004: PACKAGE_DRAFT validation passes VAL-004/005 after seed."""
		if self._skip:
			self.skipTest("Procurement Package DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(out.get("ok"), out)

		validation = validate_procurement_planning_works_master_seed(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_004 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-004"), {})
		val_005 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-005"), {})
		self.assertEqual(val_004.get("result"), "PASS")
		self.assertEqual(val_005.get("result"), "PASS")
