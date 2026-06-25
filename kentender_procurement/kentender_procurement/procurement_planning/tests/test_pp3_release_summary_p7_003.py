# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-003 — Release summary view-model and UI contract."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.released_to_tender import (
	get_pp_released_package_summary,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
	PKG_TITLE,
	TENDER_CODE,
)


def _summary_js_path() -> Path:
	return (
		Path(frappe.get_app_path("kentender_procurement"))
		/ "public"
		/ "js"
		/ "pp3_planning_release_summary.js"
	)


class TestPP3ReleaseSummaryP7003(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER", force_reset=True)
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {seed}")

	def test_pp7_003_summary_api_contract(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = get_pp_released_package_summary(package_code=PKG_CODE)
		self.assertTrue(out.get("ok"), msg=out)
		self.assertEqual((out.get("package") or {}).get("name"), PKG_TITLE)
		self.assertEqual(out.get("status_label"), "Tender created")
		self.assertEqual(out.get("next_action_label"), "Continue in Tender")
		tender = out.get("tender") or {}
		self.assertEqual(tender.get("code"), TENDER_CODE)
		self.assertTrue(out.get("may_open_tender"))
		self.assertTrue(out.get("may_open_package"))
		self.assertTrue(out.get("may_view_evidence"))

	def test_pp7_003_summary_component_exposes_required_testids(self) -> None:
		path = _summary_js_path()
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"pp3-release-summary",
			"pp3-release-summary-tender",
			"pp3-release-summary-status",
			"pp3-release-summary-next-action",
			"pp3-open-tender-button",
			"pp3-open-package-button",
			"pp3-view-release-evidence",
		):
			self.assertIn(tid, source, msg=f"missing {tid}")
