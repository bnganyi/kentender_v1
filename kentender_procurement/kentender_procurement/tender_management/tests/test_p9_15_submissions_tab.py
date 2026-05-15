# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-15 — workbench Submissions tab DTO (doc 9 §17.8, doc 6 §21).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_15_submissions_tab
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


class TestP915SubmissionsTab(_P401Tm2Cleanup, IntegrationTestCase):
	def _mk_wizard_tender(self) -> tuple[str, str]:
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
		tm2 = str(out.get("tm2_tender") or "").strip()
		self.assertTrue(tcode and tm2)
		return tcode, tm2

	def test_p9_15_submissions_tab_shape(self) -> None:
		tcode, _tm2 = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		tab = out.get("submissions_tab")
		self.assertIsInstance(tab, dict)
		self.assertIn("rows", tab)
		self.assertIn("summary", tab)
		self.assertIn("internal_view_sealed", tab)
		self.assertIn("post_opening_financials_allowed", tab)
		self.assertIn("read_only_notice", tab)
		self.assertIsInstance(tab["rows"], list)
		self.assertIsInstance(tab["summary"], dict)

	def test_p9_15_sealed_notice_pre_opening_lifecycle(self) -> None:
		tcode, _tm2 = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		tab = get_workbench_tender_detail_service("Administrator", tcode).get("submissions_tab") or {}
		self.assertTrue(tab.get("internal_view_sealed"))
		self.assertTrue(str(tab.get("sealed_notice") or "").strip())
		self.assertTrue(str(tab.get("boq_rates_suppressed_notice") or "").strip())

	def test_p9_15_financial_fields_after_opening_completed_status(self) -> None:
		tcode, tm2 = self._mk_wizard_tender()
		frappe.db.set_value("TM2 Tender", tm2, "status", "Opening Completed", update_modified=False)
		frappe.set_user("Administrator")
		tab = get_workbench_tender_detail_service("Administrator", tcode).get("submissions_tab") or {}
		self.assertFalse(tab.get("internal_view_sealed"))
		self.assertTrue(tab.get("post_opening_financials_allowed"))
		self.assertFalse(str(tab.get("sealed_notice") or "").strip())
