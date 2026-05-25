# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-010 — Package Method Decision strict-spec seed compliance tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	METHDEC_CODE,
	METHDEC_CONTRACT_TYPE,
	METHDEC_DECIDED_AT,
	METHDEC_METHOD_BASIS,
	METHDEC_RULE_PROFILE_CODE,
	METHDEC_TEMPLATE_CODE,
	METHDEC_THRESHOLD_RESULT,
	PKG_CODE,
	PKG_PROCUREMENT_CATEGORY,
	PKG_REQUIRED_STD_CATEGORY,
	PKG_REQUIRED_STD_TYPE,
	PLAN_CREATOR_USER_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.inclusion import (
	ensure_planning_inclusion,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.method_decision import (
	ensure_method_decision,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.package import (
	ensure_master_package,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	ensure_procurement_plan,
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


def _user_code(user_name: str | None) -> str:
	if not user_name or not frappe.db.exists("User", user_name):
		return ""
	return str(frappe.db.get_value("User", user_name, "username") or "").strip()


def _get_master_method_decision():
	if not frappe.db.exists("Package Method Decision", METHDEC_CODE):
		raise RuntimeError(f"Method decision {METHDEC_CODE} not found")
	return frappe.get_doc("Package Method Decision", METHDEC_CODE)


def _assert_strict_method_decision_draft_state(test_case) -> None:
	row = _get_master_method_decision()
	test_case.assertTrue(row.is_master_seed)
	test_case.assertTrue(row.is_current)
	test_case.assertEqual(row.method_decision_code, METHDEC_CODE)
	test_case.assertEqual(row.package_code, PKG_CODE)
	test_case.assertEqual(row.procurement_category, PKG_PROCUREMENT_CATEGORY)
	test_case.assertEqual(row.procurement_method, "Open Tender")
	test_case.assertEqual(row.contract_type_expectation, METHDEC_CONTRACT_TYPE)
	test_case.assertEqual(row.required_std_category, PKG_REQUIRED_STD_CATEGORY)
	test_case.assertEqual(row.required_std_type, PKG_REQUIRED_STD_TYPE)
	test_case.assertEqual(row.method_basis, METHDEC_METHOD_BASIS)
	test_case.assertEqual(row.threshold_check_result, METHDEC_THRESHOLD_RESULT)
	test_case.assertEqual(row.template_code, METHDEC_TEMPLATE_CODE)
	test_case.assertEqual(row.rule_profile_code, METHDEC_RULE_PROFILE_CODE)
	test_case.assertFalse(row.override_flag)
	test_case.assertFalse((row.override_reason or "").strip())
	test_case.assertEqual(_user_code(row.decided_by), PLAN_CREATOR_USER_CODE)
	test_case.assertEqual(str(row.decided_at).split(".")[0], METHDEC_DECIDED_AT)
	test_case.assertFalse((row.approved_by or "").strip())
	test_case.assertFalse(row.approved_at)


class TestPP2PlanningWorksMasterSeedP3010(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Package Method Decision"):
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

	def test_001_package_draft_checkpoint_sets_strict_method_decision_fields(self):
		"""SEED-TEST-P3-010-001: PACKAGE_DRAFT seeds strict METHDEC-PKG-MOH-2026-001 values."""
		if self._skip:
			self.skipTest("Package Method Decision DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(frappe.db.exists("Package Method Decision", METHDEC_CODE))
		_assert_strict_method_decision_draft_state(self)

	def test_002_existing_method_decision_is_repaired_to_spec(self):
		"""SEED-TEST-P3-010-002: Existing drifted METHDEC is repaired by ensure_method_decision."""
		if self._skip:
			self.skipTest("Package Method Decision DocType not installed")

		ensure_procurement_plan()
		ensure_planning_inclusion()
		ensure_master_package()
		ensure_method_decision()

		if frappe.db.exists("Package Method Decision", METHDEC_CODE):
			frappe.delete_doc("Package Method Decision", METHDEC_CODE, force=1)

		doc = frappe.get_doc(
			{
				"doctype": "Package Method Decision",
				"method_decision_code": METHDEC_CODE,
				"package_code": PKG_CODE,
				"procurement_category": "Goods",
				"procurement_method": "RFQ",
				"required_std_category": "Goods",
				"method_basis": "Manual Confirmation",
				"threshold_check_result": "FAIL",
				"override_flag": 1,
				"override_reason": "Drifted override",
				"decided_by": "Administrator",
				"decided_at": "2026-01-01 00:00:00",
				"is_current": 1,
				"is_master_seed": 0,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		ensure_method_decision()
		_assert_strict_method_decision_draft_state(self)

	def test_003_validator_val_008_fails_on_method_decision_drift(self):
		"""SEED-TEST-P3-010-003: VAL-008 fails when method decision fields drift from strict spec."""
		if self._skip:
			self.skipTest("Package Method Decision DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(out.get("ok"), out)

		frappe.db.set_value(
			"Package Method Decision",
			METHDEC_CODE,
			{
				"procurement_category": "Goods",
				"procurement_method": "RFQ",
				"is_master_seed": 0,
			},
			update_modified=False,
		)
		frappe.db.commit()

		validation = validate_procurement_planning_works_master_seed(checkpoint="PACKAGE_DRAFT")
		self.assertFalse(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_008 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-008"), {})
		self.assertEqual(val_008.get("result"), "FAIL")

	def test_004_package_draft_validation_passes_val_008(self):
		"""SEED-TEST-P3-010-004: PACKAGE_DRAFT validation passes VAL-008 after seed."""
		if self._skip:
			self.skipTest("Package Method Decision DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(out.get("ok"), out)

		validation = validate_procurement_planning_works_master_seed(checkpoint="PACKAGE_DRAFT")
		self.assertTrue(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_008 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-008"), {})
		self.assertEqual(val_008.get("result"), "PASS")
