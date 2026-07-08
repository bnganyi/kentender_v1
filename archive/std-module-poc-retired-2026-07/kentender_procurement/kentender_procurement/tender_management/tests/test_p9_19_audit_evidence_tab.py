# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-19 — workbench Audit & Evidence tab DTO + desk export API (doc 9 §17.12, doc 6 §25).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_19_audit_evidence_tab
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.tm2_workbench import export_workbench_tender_evidence
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
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


class TestP919AuditEvidenceTab(_P401Tm2Cleanup, IntegrationTestCase):
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

	def test_p9_19_audit_evidence_tab_shape(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		tab = out.get("audit_evidence_tab")
		self.assertIsInstance(tab, dict)
		for k in (
			"read_only_notice",
			"evidence_export_notice",
			"lifecycle_events",
			"sensitive_denials",
			"tab_actions",
		):
			self.assertIn(k, tab)
		self.assertIsInstance(tab["lifecycle_events"], list)
		self.assertIsInstance(tab["sensitive_denials"], list)
		self.assertIsInstance(tab["tab_actions"], dict)
		self.assertIn("export_tender_evidence", tab["tab_actions"])
		self.assertIn("include_confidential_toggle_allowed", tab)
		self.assertIsInstance(tab["include_confidential_toggle_allowed"], bool)

	def test_p9_19_export_workbench_api_smoke(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		exp = export_workbench_tender_evidence(tender_code=tcode, include_confidential=0)
		self.assertTrue(exp.get("ok"), exp)
		self.assertIn("audit_trail", exp)
		self.assertIn("sensitive_denial_events", exp)
