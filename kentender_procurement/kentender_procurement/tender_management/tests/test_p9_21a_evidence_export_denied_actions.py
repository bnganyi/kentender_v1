# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-21a — evidence export UI data + denied-actions parity with §13.3 ``sensitive_denial_events``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_21a_evidence_export_denied_actions
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cstr

from kentender_procurement.tender_management.api.tm2_workbench import export_workbench_tender_evidence
from kentender_procurement.tender_management.services.export_tender_evidence import (
	tender_status_in_post_opening_evidence_corridor,
)
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


class TestP921aEvidenceExportDeniedActions(_P401Tm2Cleanup, IntegrationTestCase):
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

	def test_p9_21a_denied_actions_codes_match_export_sensitive_slice(self) -> None:
		tcode = self._mk_wizard_tender()
		tm2_name = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		self.assertTrue(tm2_name)

		frappe.get_doc(
			{
				"doctype": "TM2 Tender Audit Event",
				"tm2_tender": tm2_name,
				"event_type": "Access Denied",
				"actor_type": "System",
				"denial_code": "AUTH_P921A_ACCESS",
				"event_payload": {"fixture": True},
			}
		).insert(ignore_permissions=True)

		frappe.get_doc(
			{
				"doctype": "TM2 Tender Audit Event",
				"tm2_tender": tm2_name,
				"event_type": "Supplier Viewed Tender",
				"actor_type": "System",
				"denial_code": "AUTH_P921A_GATE",
				"event_payload": {"fixture": True},
			}
		).insert(ignore_permissions=True)

		frappe.set_user("Administrator")
		detail = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(detail.get("ok"), detail)
		tab = detail.get("audit_evidence_tab") or {}
		self.assertIn("include_confidential_toggle_allowed", tab)
		self.assertFalse(tab["include_confidential_toggle_allowed"])
		denied = tab.get("sensitive_denials") or []
		tab_codes = {cstr(r.get("audit_event_code") or "").strip() for r in denied if cstr(r.get("audit_event_code") or "").strip()}

		exp = export_workbench_tender_evidence(tender_code=tcode, include_confidential=0)
		self.assertTrue(exp.get("ok"), exp)
		sens = exp.get("sensitive_denial_events") or []
		exp_codes = set()
		for r in sens:
			code = cstr(r.get("audit_event_code") or r.get("name") or "").strip()
			if code:
				exp_codes.add(code)

		self.assertEqual(tab_codes, exp_codes)
		self.assertEqual(len(tab_codes), 2)

	def test_p9_21a_include_confidential_toggle_post_opening_status(self) -> None:
		tcode = self._mk_wizard_tender()
		tm2_name = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		self.assertTrue(tm2_name)
		frappe.db.set_value("TM2 Tender", tm2_name, "status", "Opening Completed", update_modified=False)

		frappe.set_user("Administrator")
		detail = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(detail.get("ok"), detail)
		tab = detail.get("audit_evidence_tab") or {}
		self.assertTrue(tab.get("include_confidential_toggle_allowed"))
		self.assertTrue(tender_status_in_post_opening_evidence_corridor("Opening Completed"))
		self.assertFalse(tender_status_in_post_opening_evidence_corridor("Draft"))
