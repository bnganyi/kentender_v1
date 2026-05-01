# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Officer POC Step 9 — doc 9 OFF-ST-010..015 API contracts (engine + whitelisted controllers).

Desk-only cases live in Playwright (`officer-tender-poc-off-st-desk.spec.ts`). These tests
exercise the same STD scenarios the smoke spec names for branches that are impractical to
drive entirely through guided fields without raw JSON.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_officer_poc_step9_doc9_off_st_contracts
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as controller,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)


class TestOfficerPocStep9OffStContracts(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		self.tender = frappe.new_doc("Procurement Tender")
		self.tender.std_template = TEMPLATE_CODE
		self.tender.tender_title = "OFF-ST API"
		self.tender.tender_reference = "OFFST-API"
		self.tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		self.tender.tender_scope = "NATIONAL"
		self.tender.insert(ignore_permissions=True)

	def _reload(self):
		return frappe.get_doc("Procurement Tender", self.tender.name)

	def test_off_st_010_tender_securing_declaration_swaps_security_forms(self) -> None:
		"""OFF-ST-010 — declaration mode replaces Tender Security form with Tender-Securing Declaration."""
		controller.load_sample_variant(self.tender.name, "VARIANT-TENDER-SECURING-DECLARATION")
		self.assertTrue(controller.validate_tender_configuration(self.tender.name).get("ok"))
		self.assertTrue(controller.generate_required_forms(self.tender.name).get("ok"))
		t = self._reload()
		codes = [r.form_code for r in t.required_forms]
		self.assertIn("FORM_TENDER_SECURING_DECLARATION", codes)
		self.assertNotIn("FORM_TENDER_SECURITY", codes)
		self.assertEqual(len(codes), 15)

	def test_off_st_011_international_scope_adds_foreign_tenderer_form(self) -> None:
		"""OFF-ST-011 — international sample variant activates foreign tenderer form."""
		controller.load_sample_variant(self.tender.name, "VARIANT-INTERNATIONAL")
		self.assertTrue(controller.validate_tender_configuration(self.tender.name).get("ok"))
		self.assertTrue(controller.generate_required_forms(self.tender.name).get("ok"))
		t = self._reload()
		codes = [r.form_code for r in t.required_forms]
		self.assertIn("FORM_FOREIGN_TENDERER_LOCAL_INPUT", codes)

	def test_off_st_012_missing_site_visit_blocks_validation(self) -> None:
		"""OFF-ST-012 — mandatory site visit without date blocks generation."""
		controller.load_sample_variant(self.tender.name, "VARIANT-MISSING-SITE-VISIT-DATE")
		res = controller.validate_tender_configuration(self.tender.name)
		self.assertFalse(res.get("ok"))
		self.assertTrue(res.get("blocks_generation"))
		t = self._reload()
		self.assertIn(t.validation_status, ("Blocked", "Failed"))

	def test_off_st_013_missing_alternative_scope_blocks(self) -> None:
		"""OFF-ST-013 — alternatives allowed without scope blocks."""
		controller.load_sample_variant(self.tender.name, "VARIANT-MISSING-ALTERNATIVE-SCOPE")
		res = controller.validate_tender_configuration(self.tender.name)
		self.assertFalse(res.get("ok"))
		self.assertTrue(res.get("blocks_generation"))

	def test_off_st_014_boq_missing_required_category_blocks_preview(self) -> None:
		"""OFF-ST-014 — dayworks expected but BoQ rows removed blocks preview."""
		controller.load_sample_tender(self.tender.name)
		self.assertTrue(controller.validate_tender_configuration(self.tender.name).get("ok"))
		t = self._reload()
		t.set("boq_items", [])
		t.save(ignore_permissions=True)
		prev = controller.generate_tender_pack_preview(self.tender.name)
		self.assertFalse(prev.get("ok"))
		self.assertTrue(prev.get("blocks_generation"))

	def test_off_st_015_sync_resets_validation_state(self) -> None:
		"""OFF-ST-015 — officer sync after validation clears validation to Not Validated."""
		controller.load_sample_tender(self.tender.name)
		self.assertTrue(controller.validate_officer_configuration(self.tender.name).get("ok"))
		t = self._reload()
		self.assertEqual(t.validation_status, "Passed")
		t.tender_title = "Changed After Validate"
		t.save(ignore_permissions=True)
		self.assertTrue(controller.sync_officer_configuration(self.tender.name).get("ok"))
		t2 = self._reload()
		self.assertEqual(t2.validation_status, "Not Validated")
		self.assertEqual((t2.generated_tender_pack_html or "").strip(), "")
