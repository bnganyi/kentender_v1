# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P8-005 — Released package lock behavior regression."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_line_edit import add_pp_package_line
from kentender_procurement.procurement_planning.permissions import pp_policy
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_RELEASED,
	POST_RELEASE_LOCK_MESSAGE,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.services.pp_governance_codes import (
	PackagePostReleaseLock,
)


class TestPP8ReleaseLockingP8005(IntegrationTestCase):
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

	def test_pp8_005_released_package_is_locked_after_release(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		self._seed("RELEASED_TO_TENDER")
		pkg = frappe.get_doc("Procurement Package", {"package_code": PKG_CODE})
		self.assertEqual((pkg.status or "").strip(), PKG_RELEASED)
		self.assertTrue(bool(pkg.locked_after_release))

	def test_pp8_005_line_edit_blocked_after_release(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		self._seed("RELEASED_TO_TENDER")
		pkg = frappe.get_doc("Procurement Package", {"package_code": PKG_CODE})
		with self.assertRaises(frappe.ValidationError) as ctx:
			pp_policy.assert_may_edit_package_lines(pkg)
		err = str(ctx.exception)
		self.assertTrue(
			PackagePostReleaseLock.LOCKED_AFTER_RELEASE in err
			or POST_RELEASE_LOCK_MESSAGE.lower() in err.lower()
			or "locked" in err.lower()
		)

	def test_pp8_005_add_line_api_denied_after_release(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		self._seed("RELEASED_TO_TENDER")
		out = add_pp_package_line(package=PKG_CODE, amount=1000, quantity=1)
		self.assertFalse(out.get("ok"))
		self.assertIn(
			out.get("error_code"),
			(
				PackagePostReleaseLock.LOCKED_AFTER_RELEASE,
				"PP2-BLOCK-LOCKED-AFTER-RELEASE",
			),
		)
