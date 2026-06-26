# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-004 — Release cannot bypass required approval."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_release import (
	release_pp_package_to_tender,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_DRAFT, PKG_IN_REVIEW
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.services.package_detail_view_model import (
	get_pp3_package_detail_view_model,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackageReleaseToTender,
)


class TestPP8ReviewEnforcementP8004(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False

	def _seed(self, checkpoint: str) -> None:
		out = seed_procurement_planning_works_master(checkpoint=checkpoint, force_reset=True)
		if not out.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {out}")

	def test_pp8_004_release_blocked_for_draft_package(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		self._seed("PACKAGE_DRAFT")
		out = release_pp_package_to_tender(package_code=PKG_CODE)
		self.assertFalse(out.get("ok"))
		self.assertIn(
			out.get("error_code"),
			(
				PackageReleaseToTender.INVALID_STATE,
				PackageReleaseToTender.READINESS_FAILED,
				PackageReleaseToTender.PACKAGE_NOT_COMPLETE,
			),
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", {"package_code": PKG_CODE}, "status"),
			PKG_DRAFT,
		)

	def test_pp8_004_release_blocked_for_in_review_package(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		self._seed("PACKAGE_DRAFT")
		pkg = frappe.get_doc("Procurement Package", {"package_code": PKG_CODE})
		frappe.db.set_value("Procurement Package", pkg.name, "status", PKG_IN_REVIEW, update_modified=False)
		frappe.db.commit()
		out = release_pp_package_to_tender(package_code=PKG_CODE)
		self.assertFalse(out.get("ok"))
		self.assertIn(
			out.get("error_code"),
			(
				PackageReleaseToTender.INVALID_STATE,
				PackageReleaseToTender.READINESS_FAILED,
				PackageReleaseToTender.PACKAGE_NOT_COMPLETE,
			),
		)

	def test_pp8_004_review_tab_blocks_release_until_approved(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		self._seed("PACKAGE_DRAFT")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		review = (out.get("tabs") or {}).get("review") or {}
		release = (out.get("tabs") or {}).get("release") or {}
		self.assertFalse(review.get("approve_ok"), review)
		self.assertFalse(release.get("may_release"), release)
