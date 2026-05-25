# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-011 — Package Readiness Result strict-spec seed compliance tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.pp2_constants import READINESS_PASSED
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
	PKGRDY_CODE,
	PKGRDY_RUN_AT,
	PLAN_CREATOR_USER_CODE,
	master_readiness_check_items,
	strict_readiness_snapshot,
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
from kentender_procurement.procurement_planning.services.package_review_service import (
	record_package_review_decision,
	submit_package_for_review,
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


def _parse_check_items(raw) -> list[dict]:
	if isinstance(raw, str):
		raw = frappe.parse_json(raw)
	if isinstance(raw, dict):
		raw = raw.get("checks") or []
	return raw if isinstance(raw, list) else []


def _get_master_readiness():
	if not frappe.db.exists("Package Readiness Result", PKGRDY_CODE):
		raise RuntimeError(f"Readiness result {PKGRDY_CODE} not found")
	return frappe.get_doc("Package Readiness Result", PKGRDY_CODE)


def _assert_strict_readiness_state(test_case) -> None:
	row = _get_master_readiness()
	test_case.assertTrue(row.is_master_seed)
	test_case.assertTrue(row.is_current)
	test_case.assertEqual(row.readiness_code, PKGRDY_CODE)
	test_case.assertEqual(row.package_code, PKG_CODE)
	test_case.assertEqual(_user_code(row.run_by), PLAN_CREATOR_USER_CODE)
	test_case.assertEqual(str(row.run_at).split(".")[0], PKGRDY_RUN_AT)
	test_case.assertEqual(row.result_status, READINESS_PASSED)
	test_case.assertEqual(row.blocking_failure_count, 0)
	test_case.assertEqual(row.warning_count, 0)
	test_case.assertFalse(row.stale)
	test_case.assertFalse((row.stale_reason or "").strip())

	checks = _parse_check_items(row.check_items_json)
	expected_checks = master_readiness_check_items()
	test_case.assertEqual(len(checks), 15)
	by_id = {item.get("check_id"): item for item in checks}
	for expected in expected_checks:
		check_id = expected["check_id"]
		test_case.assertIn(check_id, by_id, check_id)
		actual = by_id[check_id]
		test_case.assertEqual(actual.get("result"), "PASS", check_id)
		test_case.assertEqual(
			(actual.get("source_object_code") or "").strip(),
			expected["source_object_code"],
			check_id,
		)
		test_case.assertEqual(
			(actual.get("message") or "").strip(),
			expected["message"],
			check_id,
		)

	snapshot = row.source_snapshot_json
	if isinstance(snapshot, str):
		snapshot = frappe.parse_json(snapshot)
	expected_snapshot = strict_readiness_snapshot()
	for key, value in expected_snapshot.items():
		if key == "estimated_value":
			test_case.assertAlmostEqual(flt(snapshot.get(key)), flt(value), places=2, msg=key)
			continue
		if key == "required_std_template_version_code":
			test_case.assertIn(
				(snapshot.get(key) or "").strip(),
				{value, "Building and Associated Civil Engineering Works"},
				key,
			)
			continue
		test_case.assertEqual(snapshot.get(key), value, key)


def _prepare_approved_package_for_readiness() -> None:
	ensure_procurement_plan()
	ensure_planning_inclusion()
	ensure_master_package()
	ensure_method_decision()
	_ensure_upstream_handoffs()
	_ensure_schedule()
	submit_package_for_review(PKG_CODE, "Administrator")
	record_package_review_decision(PKG_CODE, {"decision": "Approved"}, "Administrator")
	frappe.db.commit()


class TestPP2PlanningWorksMasterSeedP3011(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Package Readiness Result"):
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

	def test_001_ready_for_release_checkpoint_sets_strict_readiness_fields(self):
		"""SEED-TEST-P3-011-001: READY_FOR_RELEASE seeds strict PKGRDY-PKG-MOH-2026-001-001 values."""
		if self._skip:
			self.skipTest("Package Readiness Result DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="READY_FOR_RELEASE")
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(frappe.db.exists("Package Readiness Result", PKGRDY_CODE))
		_assert_strict_readiness_state(self)

	def test_002_existing_readiness_result_is_repaired_to_spec(self):
		"""SEED-TEST-P3-011-002: Existing drifted PKGRDY is repaired by ensure_master_readiness_result."""
		if self._skip:
			self.skipTest("Package Readiness Result DocType not installed")

		_prepare_approved_package_for_readiness()

		if frappe.db.exists("Package Readiness Result", PKGRDY_CODE):
			frappe.delete_doc("Package Readiness Result", PKGRDY_CODE, force=1)

		doc = frappe.get_doc(
			{
				"doctype": "Package Readiness Result",
				"readiness_code": PKGRDY_CODE,
				"package_code": PKG_CODE,
				"run_by": "Administrator",
				"run_at": "2026-01-01 00:00:00",
				"result_status": "Failed",
				"blocking_failure_count": 3,
				"warning_count": 2,
				"check_items_json": {"checks": []},
				"source_snapshot_json": {"package_code": PKG_CODE},
				"stale": 1,
				"stale_reason": "Drifted stale",
				"is_current": 1,
				"is_master_seed": 0,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		ensure_master_readiness_result()
		_assert_strict_readiness_state(self)

	def test_003_validator_val_009_fails_on_readiness_drift(self):
		"""SEED-TEST-P3-011-003: VAL-009 fails when readiness fields drift from strict spec."""
		if self._skip:
			self.skipTest("Package Readiness Result DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="READY_FOR_RELEASE")
		self.assertTrue(out.get("ok"), out)

		frappe.db.set_value(
			"Package Readiness Result",
			PKGRDY_CODE,
			{
				"result_status": "Failed",
				"is_master_seed": 0,
				"run_at": "2026-01-01 00:00:00",
			},
			update_modified=False,
		)
		frappe.db.commit()

		validation = validate_procurement_planning_works_master_seed(checkpoint="READY_FOR_RELEASE")
		self.assertFalse(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_009 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-009"), {})
		self.assertEqual(val_009.get("result"), "FAIL")

	def test_004_ready_for_release_validation_passes_val_009(self):
		"""SEED-TEST-P3-011-004: READY_FOR_RELEASE validation passes VAL-009 after seed."""
		if self._skip:
			self.skipTest("Package Readiness Result DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="READY_FOR_RELEASE")
		self.assertTrue(out.get("ok"), out)

		validation = validate_procurement_planning_works_master_seed(checkpoint="READY_FOR_RELEASE")
		self.assertTrue(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_009 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-009"), {})
		self.assertEqual(val_009.get("result"), "PASS")
