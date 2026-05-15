# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-11 — workbench Timeline tab DTO (doc 9 §17.4, doc 6 §17.2–17.4).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_11_timeline_tab
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	get_workbench_tender_detail as get_workbench_tender_detail_service,
)
from kentender_procurement.tender_management.services.tm2_workbench_wizard import (
	list_new_tender_wizard_std_options as list_new_tender_wizard_std_options_service,
	submit_new_tender_wizard_completion,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP911TimelineTab(_P401Tm2Cleanup, IntegrationTestCase):
	def _mk_wizard_tender(self) -> str:
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name

		frappe.set_user("Administrator")
		opt = list_new_tender_wizard_std_options_service("Administrator", pc)
		self.assertTrue(opt.get("ok"), opt)
		options = opt.get("options") or []
		self.assertTrue(options, opt)
		first = options[0]
		std_name = str(first.get("std_template") or "").strip()
		ver = str(first.get("template_version_code") or "").strip()
		prof = str(first.get("applicability_profile_code") or "").strip()
		out = submit_new_tender_wizard_completion(
			"Administrator",
			pc,
			std_name,
			ver,
			prof,
			context={},
		)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))
		tcode = str(out.get("tender_code") or "").strip()
		self.assertTrue(tcode)
		return tcode

	def test_p9_11_timeline_tab_shape_draft(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		tab = out.get("timeline_tab")
		self.assertIsInstance(tab, dict)
		self.assertIn("key_dates", tab)
		self.assertIn("timezone", tab)
		self.assertIn("show_official_server_time", tab)
		self.assertIn("official_server_time_display", tab)
		self.assertIn("post_publication_notice", tab)
		self.assertIn("warnings", tab)
		self.assertIn("extension_history", tab)
		self.assertIsInstance(tab["key_dates"], list)
		self.assertFalse(tab.get("show_official_server_time"))
		self.assertFalse(tab.get("official_server_time_display"))
		self.assertIsNone(tab.get("post_publication_notice"))
		self.assertIsInstance(tab["warnings"], list)
		self.assertIsInstance(tab["extension_history"], list)

	def test_p9_11_official_server_time_when_published(self) -> None:
		tcode = self._mk_wizard_tender()
		tm2_name = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		self.assertTrue(tm2_name)
		frappe.db.set_value("TM2 Tender", tm2_name, "status", "Published")
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		tab = out.get("timeline_tab") or {}
		self.assertTrue(tab.get("show_official_server_time"))
		self.assertTrue(str(tab.get("official_server_time_display") or "").strip())
		self.assertTrue(str(tab.get("post_publication_notice") or "").strip())
