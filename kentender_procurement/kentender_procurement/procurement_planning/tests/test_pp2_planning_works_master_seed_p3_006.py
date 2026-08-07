# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-006 — Procurement Plan strict-spec seed compliance tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PLAN_APPROVED_AT,
	PLAN_APPROVER_USER_CODE,
	PLAN_CODE,
	PLAN_CREATED_AT,
	PLAN_CREATOR_USER_CODE,
	PLAN_DESCRIPTION,
	PLAN_NAME,
	PLAN_PLANNING_CYCLE_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
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


class TestPP2PlanningWorksMasterSeedP3006(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Plan"):
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

	def test_001_included_checkpoint_sets_strict_plan_fields(self):
		"""SEED-TEST-P3-006-001: INCLUDED_IN_PLAN seeds strict PLAN-MOH-2026 values."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = seed_procurement_planning_works_master(checkpoint="INCLUDED_IN_PLAN")
		self.assertTrue(out.get("ok"), out)

		plan = frappe.get_doc("Procurement Plan", PLAN_CODE)
		self.assertEqual(plan.plan_name, PLAN_NAME)
		self.assertEqual(plan.plan_description, PLAN_DESCRIPTION)
		self.assertEqual(plan.planning_cycle_code, PLAN_PLANNING_CYCLE_CODE)
		self.assertEqual(_user_code(plan.created_by), PLAN_CREATOR_USER_CODE)
		self.assertEqual(_user_code(plan.approved_by), PLAN_APPROVER_USER_CODE)
		self.assertEqual(str(plan.created_at), PLAN_CREATED_AT)
		self.assertEqual(str(plan.approved_at), PLAN_APPROVED_AT)

	def test_002_existing_plan_is_repaired_to_spec(self):
		"""SEED-TEST-P3-006-002: Existing drifted PLAN-MOH-2026 is repaired by ensure_procurement_plan."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		doc = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_code": PLAN_CODE,
				"plan_name": "Drifted Plan",
				"fiscal_year": 2026,
				"procuring_entity": _PE_CODE,
				"currency": "KES",
				"status": "Draft",
				"is_active": 1,
				"is_master_seed": 0,
				"created_by": "Administrator",
				"created_at": "2026-01-01 00:00:00",
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		ensure_procurement_plan()
		plan = frappe.get_doc("Procurement Plan", PLAN_CODE)
		self.assertEqual(plan.plan_name, PLAN_NAME)
		self.assertEqual(plan.plan_description, PLAN_DESCRIPTION)
		self.assertEqual(plan.planning_cycle_code, PLAN_PLANNING_CYCLE_CODE)
		self.assertEqual(_user_code(plan.created_by), PLAN_CREATOR_USER_CODE)
		self.assertEqual(_user_code(plan.approved_by), PLAN_APPROVER_USER_CODE)
		self.assertEqual(str(plan.created_at), PLAN_CREATED_AT)
		self.assertEqual(str(plan.approved_at), PLAN_APPROVED_AT)
		self.assertTrue(plan.is_master_seed)
		self.assertEqual(plan.status, "Active")

	def test_003_validator_val_001_fails_on_plan_drift(self):
		"""SEED-TEST-P3-006-003: VAL-001 fails when plan fields drift from strict spec."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = seed_procurement_planning_works_master(checkpoint="INCLUDED_IN_PLAN")
		self.assertTrue(out.get("ok"), out)

		frappe.db.set_value(
			"Procurement Plan",
			PLAN_CODE,
			{
				"status": "Draft",
				"planning_cycle_code": "BUD-DRIFT",
			},
			update_modified=False,
		)
		frappe.db.commit()

		validation = validate_procurement_planning_works_master_seed(checkpoint="INCLUDED_IN_PLAN")
		self.assertFalse(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_001 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-001"), {})
		self.assertEqual(val_001.get("result"), "FAIL")
