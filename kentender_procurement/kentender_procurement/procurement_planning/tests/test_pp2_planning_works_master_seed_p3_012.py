# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-012 — Package Review Decision strict-spec seed compliance tests."""

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
	METHDEC_REVIEWER_USER_CODE,
	PKG_CODE,
	PKGREV_AUDIT_EVENT_REF,
	PKGREV_CODE,
	PKGREV_DECIDED_AT,
	PKGREV_DECISION_REASON,
	PKGREV_FROM_STATE,
	PKGREV_TO_STATE,
	PKGRDY_CODE,
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
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.readiness import (
	ensure_master_readiness_result,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.readiness_review import (
	_ensure_schedule,
	_ensure_upstream_handoffs,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.review import (
	ensure_master_review_decision,
	sync_master_review_decision_links,
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


def _get_master_review_decision():
	if not frappe.db.exists("Package Review Decision", PKGREV_CODE):
		raise RuntimeError(f"Review decision {PKGREV_CODE} not found")
	return frappe.get_doc("Package Review Decision", PKGREV_CODE)


def _assert_strict_review_decision_state(test_case, *, require_readiness_link: bool = True) -> None:
	row = _get_master_review_decision()
	test_case.assertTrue(row.is_master_seed)
	test_case.assertEqual(row.review_decision_code, PKGREV_CODE)
	test_case.assertEqual(row.package_code, PKG_CODE)
	test_case.assertEqual(row.decision_type, "Approved")
	test_case.assertEqual(_user_code(row.decided_by), METHDEC_REVIEWER_USER_CODE)
	test_case.assertEqual(str(row.decided_at).split(".")[0], PKGREV_DECIDED_AT)
	test_case.assertEqual(row.from_state, PKGREV_FROM_STATE)
	test_case.assertEqual(row.to_state, PKGREV_TO_STATE)
	test_case.assertEqual((row.decision_reason or "").strip(), PKGREV_DECISION_REASON)
	test_case.assertFalse((row.required_correction or "").strip())
	test_case.assertEqual((row.method_decision_code or "").strip(), METHDEC_CODE)
	test_case.assertEqual((row.audit_event_ref or "").strip(), PKGREV_AUDIT_EVENT_REF)
	if require_readiness_link:
		test_case.assertEqual((row.readiness_code or "").strip(), PKGRDY_CODE)


def _prepare_package_for_review() -> None:
	ensure_procurement_plan()
	ensure_planning_inclusion()
	ensure_master_package()
	ensure_method_decision()
	_ensure_upstream_handoffs()
	_ensure_schedule()
	frappe.db.commit()


class TestPP2PlanningWorksMasterSeedP3012(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Package Review Decision"):
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

	def test_001_ready_for_release_checkpoint_sets_strict_review_fields(self):
		"""SEED-TEST-P3-012-001: READY_FOR_RELEASE seeds strict PKGREV-PKG-MOH-2026-001-001 values."""
		if self._skip:
			self.skipTest("Package Review Decision DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="READY_FOR_RELEASE")
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(frappe.db.exists("Package Review Decision", PKGREV_CODE))
		_assert_strict_review_decision_state(self)

	def test_002_existing_review_decision_is_repaired_to_spec(self):
		"""SEED-TEST-P3-012-002: Existing drifted PKGREV is repaired by ensure_master_review_decision."""
		if self._skip:
			self.skipTest("Package Review Decision DocType not installed")

		_prepare_package_for_review()
		ensure_master_review_decision()
		ensure_master_readiness_result()
		sync_master_review_decision_links()

		if frappe.db.exists("Package Review Decision", PKGREV_CODE):
			frappe.delete_doc("Package Review Decision", PKGREV_CODE, force=1)

		doc = frappe.get_doc(
			{
				"doctype": "Package Review Decision",
				"review_decision_code": PKGREV_CODE,
				"package_code": PKG_CODE,
				"decision_type": "Returned for Correction",
				"decided_by": "Administrator",
				"decided_at": "2026-01-01 00:00:00",
				"from_state": "Draft",
				"to_state": "Returned for Correction",
				"decision_reason": "Drifted return",
				"required_correction": "Fix everything",
				"readiness_code": "PKGRDY-DRIFT",
				"method_decision_code": "METHDEC-DRIFT",
				"audit_event_ref": "PPAUD-DRIFT",
				"is_master_seed": 0,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		ensure_master_review_decision()
		sync_master_review_decision_links()
		_assert_strict_review_decision_state(self)

	def test_003_validator_val_016_fails_on_review_drift(self):
		"""SEED-TEST-P3-012-003: PP2-SEED-VAL-016 fails when review fields drift from strict spec."""
		if self._skip:
			self.skipTest("Package Review Decision DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="READY_FOR_RELEASE")
		self.assertTrue(out.get("ok"), out)

		frappe.db.set_value(
			"Package Review Decision",
			PKGREV_CODE,
			{
				"decision_type": "Returned for Correction",
				"is_master_seed": 0,
				"decided_at": "2026-01-01 00:00:00",
			},
			update_modified=False,
		)
		frappe.db.commit()

		validation = validate_procurement_planning_works_master_seed(checkpoint="READY_FOR_RELEASE")
		self.assertFalse(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_016 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-016"), {})
		self.assertEqual(val_016.get("result"), "FAIL")

	def test_004_ready_for_release_validation_passes_val_016(self):
		"""SEED-TEST-P3-012-004: READY_FOR_RELEASE validation passes PP2-SEED-VAL-016 after seed."""
		if self._skip:
			self.skipTest("Package Review Decision DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="READY_FOR_RELEASE")
		self.assertTrue(out.get("ok"), out)

		validation = validate_procurement_planning_works_master_seed(checkpoint="READY_FOR_RELEASE")
		self.assertTrue(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_016 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-016"), {})
		self.assertEqual(val_016.get("result"), "PASS")
