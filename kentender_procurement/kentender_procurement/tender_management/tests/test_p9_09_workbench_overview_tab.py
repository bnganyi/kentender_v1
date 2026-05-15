# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-09 — workbench Overview tab payload (doc 9 §17.2 / §19.2 via ``get_workbench_tender_detail``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_09_workbench_overview_tab
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


class TestP909WorkbenchOverviewTab(_P401Tm2Cleanup, IntegrationTestCase):
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

	def test_p9_09_overview_shape_matches_pack(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		ov = out.get("overview")
		self.assertIsInstance(ov, dict)
		self.assertIn("tender_summary", ov)
		self.assertIn("package_lineage", ov)
		self.assertIn("current_state", ov)
		self.assertIn("current_required_action", ov)
		self.assertIn("timeline", ov)
		self.assertIn("std_binding", ov)
		self.assertIn("output_refs", ov)
		self.assertIn("publication_snapshot_code", ov)
		self.assertIn("blockers_summary", ov)
		self.assertIn("tab_counts", ov)
		self.assertIn("recent_audit_events", ov)

		ts = ov["tender_summary"]
		self.assertEqual(ts.get("tender_code"), tcode)
		self.assertTrue(ts.get("tender_title"))
		self.assertTrue(ts.get("procurement_package_code"))

		pl = ov["package_lineage"]
		self.assertIn("lineage_display", pl)
		self.assertIn("package_status", pl)

		tl = ov["timeline"]
		self.assertIn("key_dates", tl)
		self.assertIsInstance(tl["key_dates"], list)

		tc = ov["tab_counts"]
		self.assertIn("clarifications_open", tc)
		self.assertIn("addenda_non_terminal", tc)
		self.assertIn("bid_submissions", tc)

		self.assertIsInstance(ov["recent_audit_events"], list)
