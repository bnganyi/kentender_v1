# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PD6 / PD12 — Generalized package detail blocker banner."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_RETURNED,
	READINESS_FAILED,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.services.package_detail_view_model import (
	_blocker_banner,
	get_pp3_package_detail_view_model,
)


class TestPD6BlockerBannerUnit(UnitTestCase):
	def test_returned_banner_kind_and_message(self) -> None:
		banner = _blocker_banner(
			None,
			status=PKG_RETURNED,
			blockers=[],
			readiness_status="",
			workflow_reason="Scope boundary needs clarification.",
		)
		self.assertTrue(banner.get("visible"))
		self.assertEqual(banner.get("kind"), "returned")
		self.assertIn("Returned", banner.get("title") or "")
		self.assertIn("Scope boundary", banner.get("message") or "")

	def test_funding_banner_kind(self) -> None:
		banner = _blocker_banner(
			None,
			status="Draft Package",
			blockers=["Package total exceeds linked funding."],
			readiness_status="",
			workflow_reason="",
		)
		self.assertEqual(banner.get("kind"), "funding")
		self.assertIn("Funding", banner.get("title") or "")

	def test_readiness_banner_kind(self) -> None:
		banner = _blocker_banner(
			None,
			status="Draft Package",
			blockers=["Readiness checks have not passed."],
			readiness_status=READINESS_FAILED,
			workflow_reason="",
		)
		self.assertEqual(banner.get("kind"), "readiness")
		self.assertIn("Readiness", banner.get("title") or "")


class TestPD6BlockerBannerIntegration(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False

	def test_returned_package_view_model_exposes_blocker_banner(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT", force_reset=True)
		if not out.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {out}")
		frappe.db.set_value(
			"Procurement Package",
			{"package_code": PKG_CODE},
			{
				"status": PKG_RETURNED,
				"workflow_reason": "Returned for missing BOQ attachment.",
			},
			update_modified=False,
		)
		frappe.db.commit()
		vm = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(vm.get("ok"), vm)
		banner = vm.get("blocker_banner") or {}
		self.assertTrue(banner.get("visible"))
		self.assertEqual(banner.get("kind"), "returned")
		sidebar = vm.get("sidebar_context") or {}
		self.assertEqual(sidebar.get("mode"), "blocked")
