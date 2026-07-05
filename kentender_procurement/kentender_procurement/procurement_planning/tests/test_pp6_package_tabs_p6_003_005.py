# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-003 / P6-004 / P6-005 — Package Detail tabs contract."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import PKG_CODE
from kentender_procurement.procurement_planning.services.package_detail_view_model import (
	get_pp3_package_detail_view_model,
)

_EXPECTED_TABS = (
	"overview",
	"lines_funding",
	"readiness",
	"review",
	"release",
)

_FORBIDDEN_TAB_LABELS = ("Evidence", "Advanced", "Technical Details", "Audit Trail", "Handoff History")


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


class TestPP6PackageTabsP6003Source(UnitTestCase):
	def test_component_exposes_five_pp3_tabs(self) -> None:
		path = _pkg_public("js", "package_detail_page.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		self.assertIn('data-testid="kt-pd-tabs"', source)
		for tid in (
			"kt-pd-tab-overview",
			"kt-pd-tab-lines-funding",
			"kt-pd-tab-readiness",
			"kt-pd-tab-review",
			"kt-pd-tab-release",
		):
			self.assertIn(tid, source, msg=f"missing {tid} (P6-003)")

	def test_no_evidence_or_advanced_default_tabs(self) -> None:
		path = _pkg_public("js", "package_detail_page.js")
		source = path.read_text(encoding="utf-8", errors="replace")
		for label in _FORBIDDEN_TAB_LABELS:
			self.assertNotIn(
				f'label: __("{label}")',
				source,
				msg=f"forbidden default tab {label} (P6-004/P6-005)",
			)
		self.assertNotIn("kt-pd-tab-evidence", source)
		self.assertNotIn("kt-pd-tab-advanced", source)


class TestPP6PackageTabsP6003API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT", force_reset=True)
		frappe.db.commit()

	def test_view_model_tab_ids_match_wireframe(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(tuple(out.get("tab_ids") or []), _EXPECTED_TABS)
		tabs = out.get("tabs") or {}
		for key in _EXPECTED_TABS:
			self.assertIn(key, tabs, msg=f"missing tab payload {key}")
