# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-07 — New Tender Wizard APIs (doc 9 §15).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_07_new_tender_wizard
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.tm2_workbench import (
	complete_new_tender_wizard,
	list_new_tender_wizard_std_options,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.services.tm2_workbench_wizard import (
	list_new_tender_wizard_std_options as list_new_tender_wizard_std_options_service,
	submit_new_tender_wizard_completion,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP907NewTenderWizard(_P401Tm2Cleanup, IntegrationTestCase):
	def test_p9_07_list_std_options_shape(self) -> None:
		frappe.set_user("Administrator")
		out = list_new_tender_wizard_std_options_service("Administrator", "__no_such_pkg__")
		self.assertFalse(out.get("ok"))

	def test_p9_07_whitelist_list_matches_service_for_unknown_pkg(self) -> None:
		frappe.set_user("Administrator")
		api = list_new_tender_wizard_std_options("__no_such_pkg__")
		svc = list_new_tender_wizard_std_options_service("Administrator", "__no_such_pkg__")
		self.assertEqual(api.get("ok"), svc.get("ok"))

	def test_p9_07_submit_creates_and_binds(self) -> None:
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
		self.assertTrue(std_name)
		self.assertTrue(ver)
		self.assertTrue(prof)
		v2, p2 = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		self.assertEqual(ver, v2)
		self.assertEqual(prof, p2)

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
		self.assertTrue(out.get("tender_std_instance"))
		self.assertTrue(out.get("tm2_tender_std_binding"))

	def test_p9_07_whitelist_complete_new_tender_wizard(self) -> None:
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
		opt = list_new_tender_wizard_std_options(package_code=pc)
		self.assertTrue(opt.get("ok"), opt)
		first = (opt.get("options") or [])[0]
		api_out = complete_new_tender_wizard(
			package_code=pc,
			preferred_std_template=str(first.get("std_template") or ""),
			std_template_version_code=str(first.get("template_version_code") or ""),
			applicability_profile_code=str(first.get("applicability_profile_code") or ""),
		)
		self.assertTrue(api_out.get("ok"), api_out)
		self.addCleanup(self._cleanup_tm2, api_out.get("tm2_tender"))
