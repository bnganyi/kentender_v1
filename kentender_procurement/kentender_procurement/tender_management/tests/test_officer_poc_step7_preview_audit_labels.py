# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer Tender Configuration POC — Officer step 7 preview/audit labels.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_officer_poc_step7_preview_audit_labels
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as controller,
)
from kentender_procurement.tender_management.services.officer_tender_config import (
	OFFICER_UX_PREVIEW_GENERATED,
	apply_officer_preview_audit_labels,
	get_officer_preview_audit_summary_enriched,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)


class TestOfficerPocStep7PreviewAuditLabelsUnit(UnitTestCase):
	def test_apply_officer_labels_adds_ux_and_identity_line(self) -> None:
		summary = {
			"ok": True,
			"tender": "PT-TEST",
			"audit": {
				"tender_status": "Tender Pack Generated",
				"template_code": "KE-PPRA-WORKS-BLDG-2022-04-POC",
				"template_short_name": "PPRA Works STD POC",
				"tender_title": "X",
			},
		}
		out = apply_officer_preview_audit_labels(summary)
		self.assertEqual(
			out["audit"]["officer_tender_status_ux_label"],
			OFFICER_UX_PREVIEW_GENERATED,
		)
		self.assertIn("KE-PPRA-WORKS-BLDG-2022-04-POC", out["audit"]["template_identity_primary"])


class TestOfficerPocStep7PreviewAuditEnrichedIntegration(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		self.tender = frappe.new_doc("Procurement Tender")
		self.tender.std_template = TEMPLATE_CODE
		self.tender.tender_title = "Officer Step7 Audit"
		self.tender.tender_reference = "OFF7-AUDIT"
		self.tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		self.tender.tender_scope = "NATIONAL"
		self.tender.insert(ignore_permissions=True)

	def test_enriched_summary_after_primary_preview_path(self) -> None:
		controller.load_sample_tender(self.tender.name)
		self.assertTrue(controller.validate_tender_configuration(self.tender.name).get("ok"))
		self.assertTrue(controller.generate_required_forms(self.tender.name).get("ok"))
		self.assertTrue(controller.generate_sample_boq(self.tender.name).get("ok"))
		self.assertTrue(controller.generate_tender_pack_preview(self.tender.name).get("ok"))

		out = get_officer_preview_audit_summary_enriched(self.tender.name)
		self.assertTrue(out.get("ok"))
		audit = out.get("audit") or {}
		self.assertEqual(audit.get("officer_tender_status_ux_label"), OFFICER_UX_PREVIEW_GENERATED)
		self.assertIn("KE-PPRA-WORKS-BLDG-2022-04-POC", audit.get("template_identity_primary", ""))
