# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 12 — Procurement Tender server methods + Desk buttons.

Covers STEP12-AC-001..014 from the Step 12 specification, plus the §12
status-mapping table, §10 error paths, and the Guest permission guard.

Run:
    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_works_poc_step12_actions
"""

from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.procurement_tender import (
	procurement_tender as controller,
)
from kentender_procurement.tender_management.services import std_template_engine as engine
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

PRIMARY_SAMPLE_ACTIVATED_FORMS = [
	"FORM_OF_TENDER",
	"FORM_CONFIDENTIAL_BUSINESS_QUESTIONNAIRE",
	"FORM_CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION",
	"FORM_SELF_DECLARATION",
	"FORM_TENDER_SECURITY",
	"FORM_JV_INFORMATION",
	"FORM_ALTERNATIVE_TECHNICAL_PROPOSAL",
	"FORM_TECHNICAL_PROPOSAL",
	"FORM_SIMILAR_EXPERIENCE",
	"FORM_FINANCIAL_CAPACITY",
	"FORM_PERSONNEL_SCHEDULE",
	"FORM_EQUIPMENT_SCHEDULE",
	"FORM_BENEFICIAL_OWNERSHIP_DISCLOSURE",
	"FORM_PERFORMANCE_SECURITY",
	"FORM_ADVANCE_PAYMENT_SECURITY",
]

VARIANT_CODES = (
	"VARIANT-INTERNATIONAL",
	"VARIANT-TENDER-SECURING-DECLARATION",
	"VARIANT-RESERVED-TENDER",
	"VARIANT-MISSING-SITE-VISIT-DATE",
	"VARIANT-MISSING-ALTERNATIVE-SCOPE",
	"VARIANT-SINGLE-LOT",
	"VARIANT-RETENTION-MONEY-SECURITY",
)

WHITELISTED_METHODS = (
	"load_template_defaults",
	"load_sample_tender",
	"load_sample_variant",
	"validate_tender_configuration",
	"generate_required_forms",
	"generate_sample_boq",
	"prepare_render_context",
)


class TestStdWorksPocStep12Actions(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

		self.tender = frappe.new_doc("Procurement Tender")
		self.tender.std_template = TEMPLATE_CODE
		self.tender.tender_title = "Step12 Smoke Tender"
		self.tender.tender_reference = "STEP12-SMOKE"
		self.tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		self.tender.tender_scope = "NATIONAL"
		self.tender.insert(ignore_permissions=True)

	def _reload_tender(self):
		return frappe.get_doc("Procurement Tender", self.tender.name)

	# ------------------------------------------------------------------
	# STEP12-AC-001 — whitelisted server methods
	# ------------------------------------------------------------------

	def test_step12_ac001_required_methods_exist_and_whitelisted(self) -> None:
		for name in WHITELISTED_METHODS:
			with self.subTest(method=name):
				self.assertTrue(
					hasattr(controller, name),
					f"STEP12-AC-001: controller must expose {name}",
				)
				fn = getattr(controller, name)
				self.assertTrue(
					callable(fn),
					f"STEP12-AC-001: {name} must be callable",
				)
				self.assertIn(
					fn,
					frappe.whitelisted,
					f"STEP12-AC-001: {name} must be registered via @frappe.whitelist",
				)

	# ------------------------------------------------------------------
	# STEP12-AC-002 + AC-003 — client script + safety guards
	# ------------------------------------------------------------------

	def test_step12_ac002_client_script_present_with_seven_buttons(self) -> None:
		app_root = Path(frappe.get_app_path("kentender_procurement"))
		js_path = (
			app_root
			/ "kentender_procurement"
			/ "doctype"
			/ "procurement_tender"
			/ "procurement_tender.js"
		)
		self.assertTrue(js_path.is_file(), "STEP12-AC-002: procurement_tender.js must exist")
		source = js_path.read_text(encoding="utf-8")
		self.assertNotIn("frappe.db.set_value", source)

		self.assertIn('const STD_POC_GROUP = __("STD POC");', source)

		for label in (
			"Load Template Defaults",
			"Load Sample Tender",
			"Load Sample Variant",
			"Validate Configuration",
			"Generate Required Forms",
			"Generate Sample BoQ",
			"Prepare Render Context",
		):
			with self.subTest(label=label):
				self.assertIn(f'__("{label}")', source)

		self.assertIn("frm.is_new()", source)
		self.assertIn("frm.is_dirty()", source)
		self.assertIn("frm.doc.std_template", source)

	# ------------------------------------------------------------------
	# STEP12-AC-004 — write permission via helper + Guest runtime
	# ------------------------------------------------------------------

	def test_step12_ac004_methods_call_check_permission(self) -> None:
		py_path = Path(controller.__file__)
		source = py_path.read_text(encoding="utf-8")
		self.assertIn(
			'tender_doc.check_permission("write")',
			source,
			"STEP12-AC-004: _get_tender_doc must enforce write permission",
		)

	def test_step12_ac004_guest_cannot_call_load_template_defaults(self) -> None:
		try:
			frappe.set_user("Guest")
			with self.assertRaises((frappe.PermissionError, frappe.AuthenticationError)):
				controller.load_template_defaults(self.tender.name)
		finally:
			frappe.set_user("Administrator")

	# ------------------------------------------------------------------
	# STEP12-AC-005 — load_template_defaults
	# ------------------------------------------------------------------

	def test_step12_ac005_load_template_defaults(self) -> None:
		result = controller.load_template_defaults(self.tender.name)
		self.assertTrue(result["ok"])
		self.assertEqual(result["template_code"], TEMPLATE_CODE)
		self.assertEqual(result["tender"], self.tender.name)

		tender = self._reload_tender()
		self.assertEqual(tender.tender_status, "Configured")
		self.assertEqual(tender.validation_status, "Not Validated")
		self.assertEqual(len(tender.validation_messages), 0)

		cfg = json.loads(tender.configuration_json)
		self.assertIsInstance(cfg, dict)
		self.assertEqual(cfg["SYSTEM.TEMPLATE_CODE"], TEMPLATE_CODE)

	# ------------------------------------------------------------------
	# STEP12-AC-006 — load_sample_tender
	# ------------------------------------------------------------------

	def test_step12_ac006_load_sample_tender_populates_lots_and_boq(self) -> None:
		result = controller.load_sample_tender(self.tender.name)
		self.assertTrue(result["ok"])
		self.assertEqual(result["template_code"], TEMPLATE_CODE)

		tender = self._reload_tender()
		self.assertEqual(tender.tender_title, "Construction of Ward Administration Block")
		self.assertEqual(tender.template_code, TEMPLATE_CODE)
		self.assertEqual(tender.validation_status, "Not Validated")
		self.assertEqual(len(tender.lots), 2)
		self.assertEqual(len(tender.boq_items), 9)

	# ------------------------------------------------------------------
	# STEP12-AC-007 — load_sample_variant (7 codes)
	# ------------------------------------------------------------------

	def test_step12_ac007_load_sample_variant_each_of_seven_codes(self) -> None:
		for variant in VARIANT_CODES:
			with self.subTest(variant=variant):
				result = controller.load_sample_variant(self.tender.name, variant)
				self.assertTrue(result["ok"])
				self.assertEqual(result["variant_code"], variant)

				tender = self._reload_tender()
				cfg = json.loads(tender.configuration_json)

				if variant == "VARIANT-INTERNATIONAL":
					self.assertEqual(cfg["METHOD.TENDER_SCOPE"], "INTERNATIONAL")

				if variant == "VARIANT-SINGLE-LOT":
					self.assertEqual(len(tender.lots), 1)

				if variant == "VARIANT-MISSING-SITE-VISIT-DATE":
					self.assertIsNone(cfg.get("DATES.SITE_VISIT_DATETIME"))
					self.assertIsNone(cfg.get("DATES.SITE_VISIT_TIME"))

		with self.assertRaises(frappe.ValidationError) as ctx:
			controller.load_sample_variant(self.tender.name, "VARIANT-DOES-NOT-EXIST")
		self.assertIn("Unknown variant_code", str(ctx.exception))

	# ------------------------------------------------------------------
	# STEP12-AC-008 — validate_tender_configuration (pass + blocked)
	# ------------------------------------------------------------------

	def test_step12_ac008_validate_passes_for_primary_sample(self) -> None:
		controller.load_sample_tender(self.tender.name)
		result = controller.validate_tender_configuration(self.tender.name)

		self.assertTrue(result["ok"])
		self.assertEqual(result["status"], "Passed")
		self.assertFalse(result["blocks_generation"])
		self.assertEqual(result["message_count"], 0)

		tender = self._reload_tender()
		self.assertEqual(tender.validation_status, "Passed")
		self.assertEqual(tender.tender_status, "Validated")

		cfg = json.loads(tender.configuration_json)
		self.assertEqual(tender.configuration_hash, engine.hash_config(cfg))

	def test_step12_validate_blocked_when_required_field_removed(self) -> None:
		controller.load_sample_tender(self.tender.name)
		tender = self._reload_tender()
		cfg = json.loads(tender.configuration_json)
		del cfg["TENDER.PROCURING_ENTITY_NAME"]
		tender.configuration_json = json.dumps(cfg, indent=2, sort_keys=True)
		tender.save(ignore_permissions=True)

		result = controller.validate_tender_configuration(self.tender.name)
		self.assertFalse(result["ok"])

		tender2 = self._reload_tender()
		self.assertEqual(tender2.validation_status, "Blocked")
		self.assertEqual(tender2.tender_status, "Validation Failed")

		blockers = [
			m
			for m in tender2.validation_messages
			if m.rule_code == "RULE_REQUIRED_CORE_TENDER_IDENTITY"
			and m.severity == "BLOCKER"
		]
		self.assertGreaterEqual(len(blockers), 1)

	# ------------------------------------------------------------------
	# STEP12-AC-009 — generate_required_forms
	# ------------------------------------------------------------------

	def test_step12_ac009_generate_required_forms_writes_15_rows(self) -> None:
		controller.load_sample_tender(self.tender.name)
		result = controller.generate_required_forms(self.tender.name)

		self.assertTrue(result["ok"])
		self.assertEqual(result["required_form_count"], 15)

		tender = self._reload_tender()
		codes = [r.form_code for r in tender.required_forms]
		self.assertEqual(codes, PRIMARY_SAMPLE_ACTIVATED_FORMS)

	# ------------------------------------------------------------------
	# STEP12-AC-010 — generate_sample_boq
	# ------------------------------------------------------------------

	def test_step12_ac010_generate_sample_boq_writes_9_rows(self) -> None:
		controller.load_sample_tender(self.tender.name)
		tender = self._reload_tender()
		tender.set("boq_items", [])
		tender.save(ignore_permissions=True)

		result = controller.generate_sample_boq(self.tender.name)
		self.assertTrue(result["ok"])
		self.assertEqual(result["boq_row_count"], 9)
		self.assertEqual(result["message"], "Sample BoQ generated.")
		self.assertEqual(result["lot_verification"], "verified")
		self.assertEqual(len(result["categories"]), 9)

		tender2 = self._reload_tender()
		self.assertEqual(len(tender2.boq_items), 9)

	# ------------------------------------------------------------------
	# STEP12-AC-011 — prepare_render_context
	# ------------------------------------------------------------------

	def test_step12_ac011_prepare_render_context_no_blockers(self) -> None:
		controller.load_sample_tender(self.tender.name)
		controller.validate_tender_configuration(self.tender.name)
		result = controller.prepare_render_context(self.tender.name)

		self.assertTrue(result["ok"])
		self.assertFalse(result["blocks_generation"])
		self.assertEqual(result["required_form_count"], 15)

		tender = self._reload_tender()
		self.assertEqual(tender.tender_status, "Tender Pack Generated")
		self.assertIsNotNone(tender.last_generated_at)

		html = tender.generated_tender_pack_html or ""
		self.assertTrue(html.startswith(controller.RENDER_CONTEXT_BANNER))
		json_part = html.split("\n", 1)[1]
		ctx = json.loads(json_part)
		self.assertEqual(ctx["audit"]["template_code"], TEMPLATE_CODE)

	def test_step12_prepare_render_context_refuses_with_blockers(self) -> None:
		controller.load_sample_tender(self.tender.name)
		tender = self._reload_tender()
		cfg = json.loads(tender.configuration_json)
		del cfg["TENDER.PROCURING_ENTITY_NAME"]
		tender.configuration_json = json.dumps(cfg, indent=2, sort_keys=True)
		tender.save(ignore_permissions=True)

		controller.validate_tender_configuration(self.tender.name)
		tender_after = self._reload_tender()
		prev_html = tender_after.generated_tender_pack_html

		result = controller.prepare_render_context(self.tender.name)
		self.assertFalse(result["ok"])
		self.assertTrue(result["blocks_generation"])

		tender_final = self._reload_tender()
		self.assertEqual(tender_final.tender_status, "Validation Failed")
		self.assertEqual(tender_final.generated_tender_pack_html, prev_html)

	# ------------------------------------------------------------------
	# STEP12-AC-012 — §12 status table mapping
	# ------------------------------------------------------------------

	def test_step12_status_table_mapping(self) -> None:
		mapping = {
			"Passed": "Validated",
			"Passed With Warnings": "Validated",
			"Failed": "Validation Failed",
			"Blocked": "Validation Failed",
		}
		for validation_status, expected_tender_status in mapping.items():
			with self.subTest(validation_status=validation_status):
				self.assertEqual(
					controller._validation_status_to_tender_status(validation_status),
					expected_tender_status,
				)
		self.assertIsNone(controller._validation_status_to_tender_status(None))
		self.assertIsNone(controller._validation_status_to_tender_status(""))

	# ------------------------------------------------------------------
	# STEP12-AC-013 — no downstream rendering in controller
	# ------------------------------------------------------------------

	def test_step12_ac013_no_render_template_or_pdf_in_controller(self) -> None:
		"""Step 12 methods must not perform downstream rendering (HTML / PDF).

		Step 13 legitimately adds ``generate_tender_pack_preview`` which uses
		``frappe.render_template`` — that method lives below the Step 13 banner;
		this assertion only scans the Step 12 method block above it.
		"""
		full_source = Path(controller.__file__).read_text(encoding="utf-8")
		step13_marker = "# Step 13 §12 — generate_tender_pack_preview"
		idx = full_source.find(step13_marker)
		step12_source = full_source if idx == -1 else full_source[:idx]

		for forbidden in ("<html", "wkhtmltopdf", "pdfkit", "frappe.render_template", "bench build"):
			with self.subTest(forbidden=forbidden):
				self.assertNotIn(forbidden, step12_source)

	# ------------------------------------------------------------------
	# STEP12-AC-014 — missing std_template
	# ------------------------------------------------------------------

	def test_step12_ac014_missing_template_returns_clear_error(self) -> None:
		bare = frappe.new_doc("Procurement Tender")
		bare.tender_title = "No Template Tender"
		bare.tender_reference = "STEP12-NO-TPL"
		bare.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		bare.tender_scope = "NATIONAL"
		bare.std_template = TEMPLATE_CODE
		bare.insert(ignore_permissions=True)
		frappe.db.set_value("Procurement Tender", bare.name, "std_template", None)
		bare.reload()

		for fn in (
			controller.load_template_defaults,
			controller.load_sample_tender,
			controller.validate_tender_configuration,
			controller.prepare_render_context,
		):
			with self.subTest(fn=fn.__name__):
				with self.assertRaises(frappe.ValidationError) as ctx:
					fn(bare.name)
				self.assertIn("Select an STD Template", str(ctx.exception))
