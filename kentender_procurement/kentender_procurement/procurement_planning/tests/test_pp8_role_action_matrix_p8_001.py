# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-001 — Role/state action matrix: buttons only for permitted actor/state."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_release import release_pp_package_to_tender
from kentender_procurement.procurement_planning.pp2_constants import PKG_IN_REVIEW
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.services.package_detail_view_model import (
	get_pp3_package_detail_view_model,
)
from kentender_procurement.procurement_planning.services.workbench_item_view_model import (
	get_workbench_item_view_model,
)

_PLANNER = "planner@moh.test"
_REVIEWER = "planning.reviewer@moh.test"


class TestPP8RoleActionMatrixP8001(IntegrationTestCase):
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

	def test_pp8_001_draft_package_planner_may_submit_not_release(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not frappe.db.exists("User", _PLANNER):
			self.skipTest(f"{_PLANNER} not configured")
		self._seed("PACKAGE_DRAFT")
		out = get_pp3_package_detail_view_model(PKG_CODE, _PLANNER)
		self.assertTrue(out.get("ok"), out)
		review = (out.get("tabs") or {}).get("review") or {}
		release = (out.get("tabs") or {}).get("release") or {}
		self.assertTrue(review.get("may_submit"), review)
		self.assertFalse(review.get("may_approve"), review)
		self.assertFalse(release.get("may_release"), release)
		primary = out.get("primary_action") or {}
		self.assertNotEqual(str(primary.get("action") or "").strip(), "release")

	def test_pp8_001_ready_package_planner_cannot_release_via_api(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not frappe.db.exists("User", _PLANNER):
			self.skipTest(f"{_PLANNER} not configured")
		self._seed("READY_FOR_RELEASE")
		frappe.set_user(_PLANNER)
		out = release_pp_package_to_tender(package_code=PKG_CODE)
		self.assertFalse(out.get("ok"))
		self.assertIn(
			out.get("error_code"),
			("PP_ACCESS_DENIED", "PP2-BLOCK-NOT-PERMITTED", "PP2-BLOCK-INVALID-STATE"),
		)

	def test_pp8_001_workbench_draft_row_exposes_state_matched_primary_action(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not frappe.db.exists("User", _PLANNER):
			self.skipTest(f"{_PLANNER} not configured")
		self._seed("PACKAGE_DRAFT")
		out = get_workbench_item_view_model(
			queue="draft_packages",
			actor=_PLANNER,
			limit=50,
			start=0,
		)
		self.assertTrue(out.get("ok"), out)
		match = next(
			(
				item
				for item in out.get("items") or []
				if (item.get("underlying_object_code") or "") == PKG_CODE
			),
			None,
		)
		self.assertIsNotNone(match, msg=out.get("items"))
		primary = match.get("primary_action") or {}
		self.assertTrue(str(primary.get("label") or "").strip(), primary)
		self.assertNotEqual(str(primary.get("action") or "").strip(), "release")

	def test_pp8_001_reviewer_ready_package_may_approve_not_submit(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not frappe.db.exists("User", _REVIEWER):
			self.skipTest(f"{_REVIEWER} not configured")
		self._seed("PACKAGE_DRAFT")
		pkg = frappe.get_doc("Procurement Package", {"package_code": PKG_CODE})
		frappe.db.set_value("Procurement Package", pkg.name, "status", PKG_IN_REVIEW, update_modified=False)
		frappe.db.commit()
		out = get_pp3_package_detail_view_model(PKG_CODE, _REVIEWER)
		self.assertTrue(out.get("ok"), out)
		review = (out.get("tabs") or {}).get("review") or {}
		self.assertFalse(review.get("may_submit"), review)
		self.assertTrue(review.get("may_approve"), review)
