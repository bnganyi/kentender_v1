# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-013 — Planning Release Package strict-spec seed compliance tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.pp2_constants import PKG_RELEASED
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKGREL_CODE,
	PKGREL_RELEASED_AT,
	PKGREL_RELEASED_BY_USER_CODE,
	PKG_CODE,
	JOURNEY_CODE,
	strict_release_evidence_links,
	strict_release_locked_summary,
	strict_release_passed_forward_summary,
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
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.readiness_review import (
	_ensure_schedule,
	_ensure_upstream_handoffs,
	ensure_review_readiness_and_ready,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.release import (
	ensure_planning_release,
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


def _parse_handoff_evidence_links(raw) -> list[dict]:
	if isinstance(raw, str):
		raw = frappe.parse_json(raw)
	if isinstance(raw, dict):
		return list(raw.get("links") or [])
	if isinstance(raw, list):
		return raw
	return []


def _get_master_release_handoff():
	if not frappe.db.exists("Procurement Handoff Card", PKGREL_CODE):
		raise RuntimeError(f"Planning release {PKGREL_CODE} not found")
	return frappe.get_doc("Procurement Handoff Card", PKGREL_CODE)


def _assert_strict_release_state(test_case) -> None:
	row = _get_master_release_handoff()
	test_case.assertTrue(row.is_master_seed)
	test_case.assertEqual(row.handoff_code, PKGREL_CODE)
	test_case.assertEqual(row.journey_code, JOURNEY_CODE)
	test_case.assertEqual(row.source_module, "Procurement Planning")
	test_case.assertEqual(row.target_module, "Tender Management")
	test_case.assertEqual(row.source_object_type, "Procurement Package")
	test_case.assertEqual(row.source_object_code, PKG_CODE)
	test_case.assertEqual(row.status, "Handed Off")
	test_case.assertEqual((row.generated_by or "").strip(), PKGREL_RELEASED_BY_USER_CODE)
	test_case.assertEqual(str(row.generated_at).split(".")[0], PKGREL_RELEASED_AT)
	test_case.assertFalse((row.target_object_code or "").strip())
	test_case.assertFalse((row.target_object_type or "").strip())
	test_case.assertFalse((row.consumed_by or "").strip())
	test_case.assertFalse(row.consumed_at)

	locked = row.locked_summary if isinstance(row.locked_summary, dict) else frappe.parse_json(row.locked_summary)
	test_case.assertEqual(locked, strict_release_locked_summary())

	passed_forward = (
		row.passed_forward_summary
		if isinstance(row.passed_forward_summary, dict)
		else frappe.parse_json(row.passed_forward_summary)
	)
	test_case.assertEqual(passed_forward, strict_release_passed_forward_summary())

	links = _parse_handoff_evidence_links(row.evidence_links_json)
	expected_links = strict_release_evidence_links(include_tender=False)
	test_case.assertEqual(len(links), len(expected_links))
	for expected in expected_links:
		match = next(
			link
			for link in links
			if (link.get("object_code") or "").strip() == expected["object_code"]
		)
		test_case.assertEqual((match.get("label") or "").strip(), expected["label"])
		test_case.assertEqual((match.get("object_type") or "").strip(), expected["object_type"])
		test_case.assertEqual((match.get("module") or "").strip(), expected["module"])
		test_case.assertEqual((match.get("visibility") or "").strip(), expected["visibility"])

	pkg = frappe.get_doc("Procurement Package", PKG_CODE)
	test_case.assertEqual(pkg.status, PKG_RELEASED)
	test_case.assertEqual((pkg.release_code or "").strip(), PKGREL_CODE)
	test_case.assertTrue(cint(pkg.locked_after_release))
	test_case.assertEqual(str(pkg.released_to_tender_at).split(".")[0], PKGREL_RELEASED_AT)
	test_case.assertFalse((pkg.tender_code or "").strip())


def _prepare_package_for_release() -> None:
	ensure_procurement_plan()
	ensure_planning_inclusion()
	ensure_master_package()
	ensure_method_decision()
	_ensure_upstream_handoffs()
	_ensure_schedule()
	ensure_review_readiness_and_ready()
	frappe.db.commit()


class TestPP2PlanningWorksMasterSeedP3013(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Handoff Card"):
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

	def test_001_released_to_tender_checkpoint_sets_strict_release_fields(self):
		"""SEED-TEST-P3-013-001: RELEASED_TO_TENDER seeds strict PKGREL-MOH-2026-001 values."""
		if self._skip:
			self.skipTest("Procurement Handoff Card DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="RELEASED_TO_TENDER")
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", PKGREL_CODE))
		_assert_strict_release_state(self)

	def test_002_existing_release_handoff_is_repaired_to_spec(self):
		"""SEED-TEST-P3-013-002: Existing drifted PKGREL is repaired by ensure_planning_release."""
		if self._skip:
			self.skipTest("Procurement Handoff Card DocType not installed")

		_prepare_package_for_release()

		if frappe.db.exists("Procurement Handoff Card", PKGREL_CODE):
			frappe.delete_doc("Procurement Handoff Card", PKGREL_CODE, force=1)

		doc = frappe.get_doc(
			{
				"doctype": "Procurement Handoff Card",
				"handoff_code": PKGREL_CODE,
				"handoff_title": "Drifted Release",
				"journey_code": JOURNEY_CODE,
				"source_module": "Procurement Planning",
				"target_module": "Tender Management",
				"source_object_type": "Procurement Package",
				"source_object_code": PKG_CODE,
				"status": "Draft",
				"generated_by": "Administrator",
				"generated_at": "2026-01-01 00:00:00",
				"next_action": "Drift",
				"locked_summary": {"package_code": "DRIFT"},
				"passed_forward_summary": {"tender_title": "Drift"},
				"evidence_links_json": '{"links": []}',
				"is_master_seed": 0,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		ensure_planning_release()
		_assert_strict_release_state(self)

	def test_003_validator_val_017_fails_on_release_drift(self):
		"""SEED-TEST-P3-013-003: PP2-SEED-VAL-017 fails when release fields drift from strict spec."""
		if self._skip:
			self.skipTest("Procurement Handoff Card DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="RELEASED_TO_TENDER")
		self.assertTrue(out.get("ok"), out)

		frappe.db.set_value(
			"Procurement Handoff Card",
			PKGREL_CODE,
			{
				"status": "Draft",
				"generated_at": "2026-01-01 00:00:00",
				"is_master_seed": 0,
			},
			update_modified=False,
		)
		frappe.db.commit()

		validation = validate_procurement_planning_works_master_seed(checkpoint="RELEASED_TO_TENDER")
		self.assertFalse(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_017 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-017"), {})
		self.assertEqual(val_017.get("result"), "FAIL")

	def test_004_released_to_tender_validation_passes_val_017(self):
		"""SEED-TEST-P3-013-004: RELEASED_TO_TENDER validation passes PP2-SEED-VAL-017 after seed."""
		if self._skip:
			self.skipTest("Procurement Handoff Card DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="RELEASED_TO_TENDER")
		self.assertTrue(out.get("ok"), out)

		validation = validate_procurement_planning_works_master_seed(checkpoint="RELEASED_TO_TENDER")
		self.assertTrue(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_017 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-017"), {})
		self.assertEqual(val_017.get("result"), "PASS")
