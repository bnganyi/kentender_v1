# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-014 — Planning Release Consumption strict-spec seed compliance tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_procurement.demand_intake.seeds.works_master_demand_seed import upsert_works_master_demand
from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey
from kentender_procurement.procurement_planning.pp2_constants import PKG_CONSUMED
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
	validate_procurement_planning_works_master_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKGCONSUME_AUDIT_EVENT_REF,
	PKGCONSUME_CODE,
	PKGCONSUME_CONSUMED_AT,
	PKGCONSUME_CONSUMED_BY_USER_CODE,
	PKGREL_CODE,
	PKG_CODE,
	TENDER_CODE,
	strict_consumption_result,
	strict_release_evidence_links,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.consumption import (
	ensure_release_consumed,
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


def _user_code(user_name: str | None) -> str:
	if not user_name or not frappe.db.exists("User", user_name):
		return ""
	return str(frappe.db.get_value("User", user_name, "username") or "").strip()


def _parse_handoff_evidence_links(raw) -> list[dict]:
	if isinstance(raw, str):
		raw = frappe.parse_json(raw)
	if isinstance(raw, dict):
		return list(raw.get("links") or [])
	if isinstance(raw, list):
		return raw
	return []


def _get_master_consumption_record():
	if not frappe.db.exists("Planning Release Consumption Record", PKGCONSUME_CODE):
		raise RuntimeError(f"Consumption record {PKGCONSUME_CODE} not found")
	return frappe.get_doc("Planning Release Consumption Record", PKGCONSUME_CODE)


def _assert_strict_consumption_state(test_case) -> None:
	row = _get_master_consumption_record()
	test_case.assertTrue(row.is_master_seed)
	test_case.assertEqual(row.consumption_code, PKGCONSUME_CODE)
	test_case.assertEqual(row.release_code, PKGREL_CODE)
	test_case.assertEqual(row.package_code, PKG_CODE)
	test_case.assertEqual(row.consumed_by_module, "Tender Management")
	test_case.assertEqual(_user_code(row.consumed_by), PKGCONSUME_CONSUMED_BY_USER_CODE)
	test_case.assertEqual(str(row.consumed_at).split(".")[0], PKGCONSUME_CONSUMED_AT)
	test_case.assertEqual(row.target_object_type, "TM2 Tender")
	test_case.assertEqual(row.target_object_code, TENDER_CODE)
	test_case.assertEqual(row.consumption_status, "Consumed")
	test_case.assertFalse((row.return_reason or "").strip())
	test_case.assertEqual((row.audit_event_ref or "").strip(), PKGCONSUME_AUDIT_EVENT_REF)

	result = (
		row.consumption_result_json
		if isinstance(row.consumption_result_json, dict)
		else frappe.parse_json(row.consumption_result_json)
	)
	test_case.assertEqual(result, strict_consumption_result())

	pkg = frappe.get_doc("Procurement Package", PKG_CODE)
	test_case.assertEqual(pkg.status, PKG_CONSUMED)
	test_case.assertEqual((pkg.tender_code or "").strip(), TENDER_CODE)
	test_case.assertEqual(str(pkg.consumed_at).split(".")[0], PKGCONSUME_CONSUMED_AT)
	test_case.assertTrue(cint(pkg.locked_after_release))
	test_case.assertEqual((pkg.release_code or "").strip(), PKGREL_CODE)

	handoff = frappe.get_doc("Procurement Handoff Card", PKGREL_CODE)
	test_case.assertEqual(handoff.status, "Consumed")
	test_case.assertEqual(handoff.target_object_type, "TM2 Tender")
	test_case.assertEqual(handoff.target_object_code, TENDER_CODE)
	test_case.assertEqual((handoff.consumed_by or "").strip(), PKGCONSUME_CONSUMED_BY_USER_CODE)
	test_case.assertEqual(str(handoff.consumed_at).split(".")[0], PKGCONSUME_CONSUMED_AT)

	links = _parse_handoff_evidence_links(handoff.evidence_links_json)
	expected_links = strict_release_evidence_links(include_tender=True)
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


def _prepare_package_for_consumption() -> None:
	ensure_procurement_plan()
	ensure_planning_inclusion()
	ensure_master_package()
	ensure_method_decision()
	_ensure_upstream_handoffs()
	_ensure_schedule()
	ensure_review_readiness_and_ready()
	ensure_planning_release()
	frappe.db.commit()


class TestPP2PlanningWorksMasterSeedP3014(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Planning Release Consumption Record"):
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

	def test_001_consumed_by_tender_checkpoint_sets_strict_consumption_fields(self):
		"""SEED-TEST-P3-014-001: CONSUMED_BY_TENDER seeds strict PKGCONSUME-MOH-2026-001 values."""
		if self._skip:
			self.skipTest("Planning Release Consumption Record DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(frappe.db.exists("Planning Release Consumption Record", PKGCONSUME_CODE))
		_assert_strict_consumption_state(self)

	def test_002_existing_consumption_record_is_repaired_to_spec(self):
		"""SEED-TEST-P3-014-002: Existing drifted PKGCONSUME is repaired by ensure_release_consumed."""
		if self._skip:
			self.skipTest("Planning Release Consumption Record DocType not installed")

		_prepare_package_for_consumption()

		if frappe.db.exists("Planning Release Consumption Record", PKGCONSUME_CODE):
			frappe.delete_doc("Planning Release Consumption Record", PKGCONSUME_CODE, force=1)

		doc = frappe.get_doc(
			{
				"doctype": "Planning Release Consumption Record",
				"consumption_code": PKGCONSUME_CODE,
				"release_code": PKGREL_CODE,
				"package_code": PKG_CODE,
				"consumed_by_module": "Tender Management",
				"consumed_by": "Administrator",
				"consumed_at": "2026-01-01 00:00:00",
				"target_object_type": "TM2 Tender",
				"target_object_code": "TND-DRIFT",
				"consumption_status": "Failed",
				"consumption_result_json": {"tender_code": "TND-DRIFT"},
				"return_reason": "Drifted",
				"audit_event_ref": "PPAUD-DRIFT",
				"is_master_seed": 0,
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		ensure_release_consumed()
		_assert_strict_consumption_state(self)

	def test_003_validator_val_018_fails_on_consumption_drift(self):
		"""SEED-TEST-P3-014-003: PP2-SEED-VAL-018 fails when consumption fields drift from strict spec."""
		if self._skip:
			self.skipTest("Planning Release Consumption Record DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)

		frappe.db.set_value(
			"Planning Release Consumption Record",
			PKGCONSUME_CODE,
			{
				"consumption_status": "Failed",
				"target_object_code": "TND-DRIFT",
				"is_master_seed": 0,
			},
			update_modified=False,
		)
		frappe.db.commit()

		validation = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertFalse(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_018 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-018"), {})
		self.assertEqual(val_018.get("result"), "FAIL")

	def test_004_consumed_by_tender_validation_passes_val_018(self):
		"""SEED-TEST-P3-014-004: CONSUMED_BY_TENDER validation passes PP2-SEED-VAL-018 after seed."""
		if self._skip:
			self.skipTest("Planning Release Consumption Record DocType not installed")

		out = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(out.get("ok"), out)

		validation = validate_procurement_planning_works_master_seed(checkpoint="CONSUMED_BY_TENDER")
		self.assertTrue(validation.get("ok"), validation)
		checks = validation.get("checks") or []
		val_018 = next((c for c in checks if c.get("check_id") == "PP2-SEED-VAL-018"), {})
		self.assertEqual(val_018.get("result"), "PASS")
