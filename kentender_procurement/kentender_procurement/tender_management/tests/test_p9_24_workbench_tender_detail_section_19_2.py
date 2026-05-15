# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-24 — doc 9 §19.2 tender detail API contract (``get_workbench_tender_detail_section_19_2``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_24_workbench_tender_detail_section_19_2
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.tm2_workbench import (
	get_workbench_tender_detail_section_19_2,
)
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.tm2_workbench_section_19_2 import (
	build_section_19_2_from_detail,
	get_section_19_2_tender_detail as get_section_19_2_tender_detail_service,
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


class TestP924WorkbenchTenderDetailSection192(_P401Tm2Cleanup, IntegrationTestCase):
	def _mk_wizard_tender(self) -> str:
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
			update_modified=False,
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

	def test_p9_24_section_19_2_required_keys(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = get_section_19_2_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		for key in (
			"tender_code",
			"tender_title",
			"tender_status",
			"tender_summary",
			"timeline",
			"std_binding",
			"output_refs",
			"publication_snapshot",
			"blockers",
			"tab_counts",
			"action_availability",
			"recent_audit_events",
			"readiness_summary",
			"handoff_summaries",
		):
			self.assertIn(key, out, msg=f"missing §19.2 key {key}")

		self.assertIsInstance(out["tender_summary"], dict)
		self.assertIn("tender_code", out["tender_summary"])
		self.assertIsInstance(out["timeline"], dict)
		self.assertIsInstance(out["std_binding"], dict)
		self.assertIsInstance(out["output_refs"], dict)
		self.assertIsInstance(out["publication_snapshot"], dict)
		self.assertIn("publication_snapshot_code", out["publication_snapshot"])
		self.assertIsInstance(out["blockers"], dict)
		self.assertIn("summary", out["blockers"])
		self.assertIsInstance(out["tab_counts"], dict)
		self.assertIsInstance(out["action_availability"], list)
		self.assertIsInstance(out["recent_audit_events"], list)
		self.assertIsInstance(out["readiness_summary"], dict)
		hs = out["handoff_summaries"]
		self.assertIsInstance(hs, dict)
		for sub in ("opening_readiness", "evaluation_handoff", "contract_handoff"):
			self.assertIn(sub, hs)

	def test_p9_24_whitelist_matches_service(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		api = get_workbench_tender_detail_section_19_2(tender_code=tcode)
		svc = get_section_19_2_tender_detail_service("Administrator", tcode)
		self.assertEqual(api.get("ok"), svc.get("ok"))
		self.assertEqual(api.get("tender_code"), svc.get("tender_code"))
		self.assertEqual(api.get("tab_counts"), svc.get("tab_counts"))

	def test_p9_24_build_matches_full_detail_subset(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		full = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(full.get("ok"), full)
		s19 = build_section_19_2_from_detail(full)
		ov = full.get("overview") or {}
		self.assertEqual(s19.get("timeline"), ov.get("timeline"))
		self.assertEqual(s19.get("action_availability"), full.get("actions"))

	def test_p9_24_not_found(self) -> None:
		frappe.set_user("Administrator")
		out = get_section_19_2_tender_detail_service("Administrator", "TND-NONEXISTENT-9999")
		self.assertFalse(out.get("ok"))
