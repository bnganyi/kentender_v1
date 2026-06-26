# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-003 — Release cannot bypass failed readiness."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_release import (
	mark_pp_package_ready_for_release,
	release_pp_package_to_tender,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_APPROVED, PKG_DRAFT
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
	PackageMarkReady,
	PackageReleaseToTender,
)


class TestPP8ReadinessEnforcementP8003(IntegrationTestCase):
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

	def test_pp8_003_draft_package_cannot_mark_ready_without_readiness(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		self._seed("PACKAGE_DRAFT")
		pkg = frappe.get_doc("Procurement Package", {"package_code": PKG_CODE})
		frappe.db.set_value("Procurement Package", pkg.name, "status", PKG_APPROVED, update_modified=False)
		frappe.db.commit()
		out = mark_pp_package_ready_for_release(package_code=PKG_CODE)
		self.assertFalse(out.get("ok"))
		self.assertIn(
			out.get("error_code"),
			(PackageMarkReady.READINESS_FAILED, PackageMarkReady.INVALID_STATE, "READINESS_FAILED"),
		)

	def test_pp8_003_release_api_blocked_when_readiness_stale(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		self._seed("READY_FOR_RELEASE")
		frappe.db.set_value(
			"Procurement Package",
			{"package_code": PKG_CODE},
			"estimated_value",
			frappe.db.get_value("Procurement Package", {"package_code": PKG_CODE}, "estimated_value") + 5000,
			update_modified=False,
		)
		frappe.db.commit()
		out = release_pp_package_to_tender(package_code=PKG_CODE)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), PackageReleaseToTender.READINESS_STALE)

	def test_pp8_003_package_detail_release_tab_blocked_on_draft(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		self._seed("PACKAGE_DRAFT")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		release = (out.get("tabs") or {}).get("release") or {}
		self.assertFalse(release.get("may_release"), release)
		self.assertTrue(release.get("blockers"), release)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", {"package_code": PKG_CODE}, "status"),
			PKG_DRAFT,
		)
