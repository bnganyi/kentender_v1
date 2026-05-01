# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 16 — end-to-end smoke path (integration contract).

Maps to STEP16-AC-001..017 and §8 primary / §11–§14 negative / §15 variant checks.
Does not replace granular modules Steps 11–15; proves orchestrated behaviour.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_works_poc_step16_end_to_end_smoke
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as controller,
)
from kentender_procurement.tender_management.tests.test_std_works_poc_step12_actions import (
	PRIMARY_SAMPLE_ACTIVATED_FORMS,
)
from kentender_procurement.tender_management.tests.test_std_works_poc_step13_renderer import (
	POC_WARNING_KEY_PHRASE,
	REQUIRED_PREVIEW_HEADINGS,
)
from kentender_procurement.tender_management.tests.test_std_works_poc_step14_required_forms import (
	DEFAULT_REQUIRED_FORM_CODES,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	import_std_works_poc_template,
	upsert_std_template,
)

EXPECTED_PACKAGE_PAYLOAD_KEYS: frozenset[str] = frozenset(
	{
		"manifest",
		"sections",
		"fields",
		"rules",
		"forms",
		"render_map",
		"sample_tender",
		"package_hash",
		"import_metadata",
	}
)


class TestStdWorksPocStep16EndToEndSmoke(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

		self.tender = frappe.new_doc("Procurement Tender")
		self.tender.std_template = TEMPLATE_CODE
		self.tender.tender_title = "Step16 E2E Smoke Placeholder"
		self.tender.tender_reference = "STEP16-SMOKE"
		self.tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		self.tender.tender_scope = "NATIONAL"
		self.tender.insert(ignore_permissions=True)

	def _reload_tender(self):
		return frappe.get_doc("Procurement Tender", self.tender.name)

	# ------------------------------------------------------------------
	# STEP16-AC-001..013 — primary successful flow (§8 + §10.1–10.9)
	# ------------------------------------------------------------------

	def test_step16_primary_smoke_ac001_to_ac013(self) -> None:
		# STEP16-AC-001 — package import
		imp = import_std_works_poc_template()
		self.assertTrue(imp.get("ok"), "STEP16-AC-001: import must return ok")
		self.assertEqual(
			imp.get("template_code"),
			TEMPLATE_CODE,
			"STEP16-AC-001: template_code must match POC package",
		)
		self.assertTrue(imp.get("package_hash"), "STEP16-AC-001: package_hash required")

		# STEP16-AC-002 — STD Template persistence
		std_name = frappe.db.get_value(
			"STD Template", {"template_code": TEMPLATE_CODE}, "name"
		)
		self.assertTrue(std_name, "STEP16-AC-002: STD Template must exist after import")
		std = frappe.get_doc("STD Template", std_name)
		self.assertTrue(std.package_hash, "STEP16-AC-002: package_hash on document")
		self.assertTrue(std.package_json, "STEP16-AC-002: package_json on document")
		self.assertTrue(std.manifest_json, "STEP16-AC-002: manifest_json on document")
		payload = json.loads(std.package_json)
		self.assertGreaterEqual(
			set(payload.keys()),
			EXPECTED_PACKAGE_PAYLOAD_KEYS,
			"STEP16-AC-002: combined payload must carry standard keys",
		)

		# STEP16-AC-003 — Procurement Tender linked (created in setUp)
		t0 = self._reload_tender()
		self.assertEqual(t0.std_template, TEMPLATE_CODE)

		# STEP16-AC-004 / AC-005 — Load Sample Tender
		m = controller.load_sample_tender(self.tender.name)
		self.assertTrue(m.get("ok"))
		t1 = self._reload_tender()
		self.assertEqual(
			t1.tender_title,
			"Construction of Ward Administration Block",
			"STEP16-AC-004: sample identity title",
		)
		self.assertEqual(
			t1.tender_reference,
			"CGK/WKS/OT/001/2026",
			"STEP16-AC-004: sample identity reference",
		)
		self.assertTrue(t1.configuration_json, "STEP16-AC-005: configuration_json populated")
		self.assertEqual(len(t1.lots), 2, "STEP16-AC-006: two lots")
		self.assertEqual(len(t1.boq_items), 9, "STEP16-AC-006: nine BoQ rows")
		item_codes = [r.item_code for r in t1.boq_items]
		self.assertEqual(
			len(item_codes),
			len(set(item_codes)),
			"STEP16-AC-010: no duplicate BoQ item_code in primary sample",
		)

		# STEP16-AC-007 — validate
		v = controller.validate_tender_configuration(self.tender.name)
		self.assertTrue(v.get("ok"), "STEP16-AC-007: primary sample must not block")
		t2 = self._reload_tender()
		self.assertEqual(t2.validation_status, "Passed")
		blockers = {
			m.rule_code
			for m in t2.validation_messages
			if m.severity in ("BLOCKER", "ERROR")
		}
		self.assertEqual(blockers, set(), "STEP16-AC-007: no error-level messages")

		# STEP16-AC-008 / AC-009 — required forms
		g = controller.generate_required_forms(self.tender.name)
		self.assertTrue(g.get("ok"))
		t3 = self._reload_tender()
		codes = [r.form_code for r in t3.required_forms]
		self.assertEqual(
			codes,
			PRIMARY_SAMPLE_ACTIVATED_FORMS,
			"STEP16-AC-008: primary checklist order",
		)
		self.assertEqual(
			len(codes),
			len(set(codes)),
			"STEP16-AC-009: no duplicate required-form rows",
		)

		# STEP16-AC-011 / AC-012 / AC-013 — tender-pack preview
		p = controller.generate_tender_pack_preview(self.tender.name)
		self.assertTrue(p.get("ok"), "STEP16-AC-011: preview succeeds for valid sample")
		self.assertEqual(p.get("validation_status"), "Passed")

		t4 = self._reload_tender()
		html = t4.generated_tender_pack_html or ""
		self.assertIn("<div class=\"std-poc-preview\">", html, "STEP16-AC-011: HTML shell")
		self.assertIn(POC_WARNING_KEY_PHRASE, html, "STEP16-AC-012: global POC warning")
		self.assertIn("representative sample structured data", html.lower())
		for heading in REQUIRED_PREVIEW_HEADINGS:
			with self.subTest(heading=heading):
				self.assertIn(heading, html, f"STEP16-AC-012: missing {heading}")
		self.assertIn("Package Hash", html, "STEP16-AC-013: audit")
		self.assertIn("Configuration Hash", html, "STEP16-AC-013: audit")
		self.assertIn(p.get("configuration_hash") or "", html, "STEP16-AC-013: config hash in HTML")
		self.assertIn("Validation Status", html, "STEP16-AC-013: validation in audit")
		self.assertIn(TEMPLATE_CODE, html, "STEP16-AC-013: template code in output")
		self.assertIn("0.1.0-poc", html, "STEP16-AC-013: package version in preview")
		self.assertIn("DOC. 1", html, "STEP16-AC-013: source document in preview")
		self.assertIn(std.package_hash, html, "STEP16-AC-013: package hash matches template doc")

	# ------------------------------------------------------------------
	# STEP16-AC-014 / AC-015 — negative scenarios (blocks preview)
	# ------------------------------------------------------------------

	def test_step16_ac014_site_visit_variant_blocks_preview(self) -> None:
		controller.load_sample_variant(
			self.tender.name, variant_code="VARIANT-MISSING-SITE-VISIT-DATE"
		)
		pre = self._reload_tender()
		self.assertFalse(pre.generated_tender_pack_html)
		result = controller.generate_tender_pack_preview(self.tender.name)
		self.assertFalse(result.get("ok"), "STEP16-AC-014: preview must be blocked")
		self.assertTrue(result.get("blocks_generation"))
		t = self._reload_tender()
		self.assertFalse(t.generated_tender_pack_html)

	def test_step16_ac015_alternative_scope_variant_blocks_preview(self) -> None:
		controller.load_sample_variant(
			self.tender.name, variant_code="VARIANT-MISSING-ALTERNATIVE-SCOPE"
		)
		result = controller.generate_tender_pack_preview(self.tender.name)
		self.assertFalse(result.get("ok"), "STEP16-AC-015: preview must be blocked")
		self.assertTrue(result.get("blocks_generation"))
		t = self._reload_tender()
		self.assertFalse(t.generated_tender_pack_html)

	def test_step16_ac016_excessive_tender_security_blocks_preview(self) -> None:
		controller.load_sample_tender(self.tender.name)
		tender = self._reload_tender()
		cfg = json.loads(tender.configuration_json)
		cfg["SECURITY.TENDER_SECURITY_AMOUNT"] = 3_000_000
		self.assertEqual(cfg.get("TENDER.ESTIMATED_COST"), 100_000_000)
		tender.configuration_json = json.dumps(cfg, indent=2, sort_keys=True)
		tender.save(ignore_permissions=True)

		controller.validate_tender_configuration(self.tender.name)
		t2 = self._reload_tender()
		blocker_codes = {
			m.rule_code for m in t2.validation_messages if m.severity == "BLOCKER"
		}
		self.assertIn(
			"RULE_TENDER_SECURITY_AMOUNT_LIMIT_2_PERCENT",
			blocker_codes,
			"STEP16-AC-016: limit rule must fire",
		)

		result = controller.generate_tender_pack_preview(self.tender.name)
		self.assertFalse(result.get("ok"))
		self.assertTrue(result.get("blocks_generation"))

	# ------------------------------------------------------------------
	# STEP16-AC-017 — tender-securing declaration variant
	# ------------------------------------------------------------------

	def test_step16_ac017_tender_securing_declaration_variant(self) -> None:
		controller.load_sample_variant(
			self.tender.name, variant_code="VARIANT-TENDER-SECURING-DECLARATION"
		)
		controller.generate_required_forms(self.tender.name)
		t = self._reload_tender()
		codes = {r.form_code for r in t.required_forms}
		self.assertIn("FORM_TENDER_SECURING_DECLARATION", codes)
		self.assertNotIn("FORM_TENDER_SECURITY", codes)

	# ------------------------------------------------------------------
	# International variant (Step 16 §15.2 / smoke pass criteria 19)
	# ------------------------------------------------------------------

	def test_step16_international_variant_foreign_form(self) -> None:
		controller.load_sample_variant(self.tender.name, variant_code="VARIANT-INTERNATIONAL")
		controller.generate_required_forms(self.tender.name)
		t = self._reload_tender()
		codes = [r.form_code for r in t.required_forms]
		self.assertIn(
			"FORM_FOREIGN_TENDERER_LOCAL_INPUT",
			codes,
			"International variant must activate foreign tenderer form",
		)
		for fc in DEFAULT_REQUIRED_FORM_CODES:
			self.assertIn(fc, codes, "Default-required forms remain under international variant")
