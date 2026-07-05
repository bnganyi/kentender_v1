# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-002 — Package Detail header view model and UI contract."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.procurement_planning.api.package_detail import get_pp3_package_detail
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
	PKG_TITLE,
	PLAN_NAME,
)
from kentender_procurement.procurement_planning.services.package_detail_view_model import (
	get_pp3_package_detail_view_model,
)


def _pkg_public(*parts: str) -> Path:
	return Path(__file__).resolve().parents[2].joinpath("public", *parts)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))


class TestPP6PackageHeaderP6002Source(UnitTestCase):
	def test_package_detail_component_exposes_header_testids(self) -> None:
		path = _pkg_public("js", "package_detail_page.js")
		self.assertTrue(path.exists(), msg=f"missing {path}")
		source = path.read_text(encoding="utf-8", errors="replace")
		for tid in (
			"kt-pd-header",
			"kt-pd-title",
			"kt-pd-status-pill",
			"kt-pd-blocker-banner",
		):
			self.assertIn(tid, source, msg=f"missing {tid} (P6-002)")
		self.assertIn("get_pp3_package_detail", source)

	def test_view_model_module_defines_header_fields(self) -> None:
		path = (
			Path(__file__).resolve().parents[1]
			/ "services"
			/ "package_detail_view_model.py"
		)
		source = path.read_text(encoding="utf-8", errors="replace")
		for field in (
			"active_plan_label",
			"funding_label",
			"blockers_label",
			"next_action_label",
			"meta_line",
		):
			self.assertIn(field, source, msg=f"missing header field {field} (P6-002)")


class TestPP6PackageHeaderP6002API(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not _pp_ok():
			self._skip = True
			return
		self._skip = False
		seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT", force_reset=True)
		frappe.db.commit()

	def test_header_returns_title_method_value_active_plan_state_funding_blockers_next_action(
		self,
	) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(out.get("ok"), out)
		header = out.get("header") or {}
		self.assertEqual(header.get("title"), PKG_TITLE)
		self.assertIn("Open Tender", header.get("method_label") or header.get("meta_line") or "")
		self.assertTrue(header.get("value_label"), header)
		self.assertIn(PLAN_NAME, header.get("active_plan_label") or "")
		self.assertEqual(header.get("status_label"), "Draft Package")
		self.assertEqual(header.get("funding_label"), "Budget linked")
		self.assertEqual(header.get("blockers_label"), "None")
		self.assertIn("next_action_label", header)
		self.assertTrue(out.get("primary_action"))

	def test_whitelisted_api_delegates_to_view_model(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning not installed")
		api_out = get_pp3_package_detail(package=PKG_CODE)
		svc_out = get_pp3_package_detail_view_model(PKG_CODE, "Administrator")
		self.assertTrue(api_out.get("ok"), api_out)
		self.assertEqual(api_out.get("package_code"), svc_out.get("package_code"))
		self.assertEqual(
			(api_out.get("header") or {}).get("title"),
			(svc_out.get("header") or {}).get("title"),
		)
