# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-014 — Journey/handoff integration read API (PP2-SMOKE-BE-011)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import (
	ensure_currency_kes,
	ensure_department,
	ensure_procuring_entity,
	ensure_roles,
	upsert_seed_user,
)
from kentender_procurement.procurement_lifecycle.journey_step_aggregator import (
	aggregate_procurement_journey_steps,
)
from kentender_procurement.procurement_planning.api.planning_journey import (
	get_pp_planning_journey_handoffs,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEMAND_CODE,
	INCLUSION_CODE,
	JOURNEY_CODE,
	PKG_CODE,
	PKGREL_CODE,
	PLAN_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.services.planning_journey_integration import (
	get_planning_journey_handoff_context,
)
from kentender_strategy.seeds.works_master_strategy_hierarchy import upsert_works_master_strategy_hierarchy

_PE_CODE = "PE-MOH"
_PE_NAME = "Ministry of Health"
_OFFICER_USER = "procurement.officer@moh.test"
_TENDER_CODE = "TND-MOH-2026-001"


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))


def _bootstrap_upstream_only() -> None:
	ensure_currency_kes()
	ensure_procuring_entity(_PE_CODE, _PE_NAME)
	from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
	from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import upsert_works_master_demand
	from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import upsert_works_master_journey

	assert upsert_works_master_strategy_hierarchy().get("ok")
	assert upsert_works_master_budget().get("ok")
	assert upsert_works_master_demand().get("ok")
	assert upsert_works_master_journey().get("ok")


def _step_by_key(steps: list[dict], step_key: str) -> dict | None:
	for row in steps or []:
		if row.get("step_key") == step_key:
			return row
	return None


class TestPP2JourneyHandoffIntegrationP4014(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not _pp_ok():
			cls._skip = True
			return
		cls._skip = False
		_bootstrap_upstream_only()

	def setUp(self):
		super().setUp()
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		self._cleanup: list[tuple[str, str]] = []
		clear_master_planning_seed()
		frappe.db.commit()

	def tearDown(self):
		if getattr(self.__class__, "_skip", True):
			return
		frappe.set_user("Administrator")
		clear_master_planning_seed()
		for doctype, name in reversed(getattr(self, "_cleanup", [])):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _ensure_officer_user(self) -> str:
		frappe.set_user("Administrator")
		ensure_roles()
		moh = ensure_procuring_entity(_PE_CODE, _PE_NAME)
		dept = ensure_department(f"Dept Officer {frappe.generate_hash(length=4)}", moh)
		upsert_seed_user(
			_OFFICER_USER,
			"Procurement Officer MOH",
			"Procurement Officer",
			entity_name=moh,
			department_docname=dept,
		)
		return _OFFICER_USER

	def _load_consumed_works_seed(self) -> dict:
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed not available: {seed}")
		if not frappe.db.exists("Procurement Package", {"package_code": PKG_CODE}):
			self.skipTest("WORKS package seed not present on site.")
		return seed

	def test_001_be011_journey_steps_include_planincl_and_pkgrel(self):
		"""SEED-TEST-P4-014-001: BE-011 journey steps include PLANINCL and PKGREL handoffs."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		steps = aggregate_procurement_journey_steps(JOURNEY_CODE)
		inclusion_step = _step_by_key(steps, "planning_inclusion")
		release_step = _step_by_key(steps, "package_release")
		self.assertIsNotNone(inclusion_step)
		self.assertIsNotNone(release_step)
		self.assertEqual(inclusion_step.get("label"), "Procurement Planned")
		self.assertEqual(release_step.get("label"), "Package Released")
		self.assertEqual(inclusion_step.get("handoff_code"), INCLUSION_CODE)
		self.assertEqual(release_step.get("handoff_code"), PKGREL_CODE)

	def test_002_pkgrel_handoff_fields(self):
		"""SEED-TEST-P4-014-002: PKGREL handoff card has Planning → TM module routing."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		out = get_planning_journey_handoff_context(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		release = out.get("planning_release") or {}
		self.assertEqual(release.get("handoff_code"), PKGREL_CODE)
		self.assertEqual(release.get("source_module"), "Procurement Planning")
		self.assertEqual(release.get("target_module"), "Tender Management")
		self.assertEqual(release.get("source_object_code"), PKG_CODE)
		self.assertEqual(release.get("target_object_code"), _TENDER_CODE)
		self.assertEqual(release.get("status"), "Consumed")
		self.assertTrue(release.get("tender_open_route"), release)
		self.assertIn("tm2-tender", release.get("tender_open_route", "").lower())

	def test_003_planincl_linked_to_journey_with_demand_plan_codes(self):
		"""SEED-TEST-P4-014-003: PLANINCL handoff linked to journey with demand/plan codes."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		out = get_planning_journey_handoff_context(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		inclusion = out.get("planning_inclusion") or {}
		self.assertEqual(inclusion.get("handoff_code"), INCLUSION_CODE)
		self.assertEqual(inclusion.get("journey_code"), JOURNEY_CODE)
		self.assertEqual(inclusion.get("source_object_code"), DEMAND_CODE)
		self.assertEqual(inclusion.get("target_object_code"), PLAN_CODE)

	def test_004_service_response_shape_for_works_package(self):
		"""SEED-TEST-P4-014-004: Service response includes planning_steps and handoff summaries."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		out = get_planning_journey_handoff_context(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("package_code"), PKG_CODE)
		self.assertTrue(out.get("planning_steps"))
		self.assertIsNotNone(out.get("planning_inclusion"))
		self.assertIsNotNone(out.get("planning_release"))
		self.assertEqual((out.get("journey") or {}).get("journey_code"), JOURNEY_CODE)
		self.assertTrue(out.get("source_of_truth_note"))

	def test_005_officer_allowed(self):
		"""SEED-TEST-P4-014-005: Procurement Officer can read journey/handoff context."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		officer = self._ensure_officer_user()
		frappe.set_user(officer)
		out = get_pp_planning_journey_handoffs(package_code=PKG_CODE)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("package_code"), PKG_CODE)

	def test_006_guest_and_supplier_denied(self):
		"""SEED-TEST-P4-014-006: Guest and Supplier receive PP_ACCESS_DENIED."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		frappe.set_user("Guest")
		guest_out = get_pp_planning_journey_handoffs(package_code=PKG_CODE)
		self.assertFalse(guest_out.get("ok"))
		self.assertEqual(guest_out.get("error_code"), "PP_ACCESS_DENIED")

		supplier_email = f"supplier.journey.{frappe.generate_hash(length=6)}@moh.test"
		if not frappe.db.exists("User", supplier_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": supplier_email,
					"first_name": "Journey",
					"last_name": "Supplier",
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Supplier")
			self._cleanup.append(("User", supplier_email))

		frappe.set_user(supplier_email)
		supplier_out = get_pp_planning_journey_handoffs(package_code=PKG_CODE)
		self.assertFalse(supplier_out.get("ok"))
		self.assertEqual(supplier_out.get("error_code"), "PP_ACCESS_DENIED")

	def test_007_unknown_package_not_found(self):
		"""SEED-TEST-P4-014-007: Unknown package code returns NOT_FOUND."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		out = get_planning_journey_handoff_context("PKG-DOES-NOT-EXIST", "Administrator")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "NOT_FOUND")

	def test_008_api_delegates_to_service(self):
		"""SEED-TEST-P4-014-008: Whitelisted API delegates to planning journey service."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		frappe.set_user("Administrator")
		api_out = get_pp_planning_journey_handoffs(package_code=PKG_CODE)
		svc_out = get_planning_journey_handoff_context(PKG_CODE, "Administrator")
		self.assertTrue(api_out.get("ok"), api_out)
		self.assertTrue(svc_out.get("ok"), svc_out)
		self.assertEqual(api_out.get("package_code"), svc_out.get("package_code"))
		self.assertEqual(api_out.get("package_status"), svc_out.get("package_status"))
		self.assertEqual(
			[row.get("handoff_code") for row in api_out.get("planning_steps") or []],
			[row.get("handoff_code") for row in svc_out.get("planning_steps") or []],
		)
		self.assertEqual(
			(api_out.get("planning_release") or {}).get("handoff_code"),
			(svc_out.get("planning_release") or {}).get("handoff_code"),
		)

	def test_009_read_api_does_not_mutate_package_status(self):
		"""SEED-TEST-P4-014-009: Read API does not mutate Procurement Package status (PP2-NG-012)."""
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")

		self._load_consumed_works_seed()
		pkg_name = frappe.db.get_value("Procurement Package", {"package_code": PKG_CODE}, "name") or PKG_CODE
		before = frappe.db.get_value(
			"Procurement Package",
			pkg_name,
			("status", "release_code", "planning_inclusion_code", "journey_code"),
			as_dict=True,
		)
		frappe.set_user("Administrator")
		out = get_pp_planning_journey_handoffs(package_code=PKG_CODE)
		self.assertTrue(out.get("ok"), out)
		after = frappe.db.get_value(
			"Procurement Package",
			pkg_name,
			("status", "release_code", "planning_inclusion_code", "journey_code"),
			as_dict=True,
		)
		self.assertEqual(before, after)
