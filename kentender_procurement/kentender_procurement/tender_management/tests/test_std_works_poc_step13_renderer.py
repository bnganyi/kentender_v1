# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 13 — Jinja tender-pack preview renderer.

Covers STEP13-AC-001..016 from the Step 13 specification, plus the §6 boundary
rules, §10 POC warning text, §14 rendering safety, and the §15 preview-output
table. Pattern follows STD-POC-010..013: focused module, no broader test
infrastructure.

Run:
    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_works_poc_step13_renderer
"""

from __future__ import annotations

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

REQUIRED_TEMPLATE_FILES = (
	"__init__.py",
	"tender_pack.html",
	"macros.html",
	"cover.html",
	"invitation.html",
	"active_sections.html",
	"locked_sections.html",
	"tds.html",
	"evaluation_summary.html",
	"forms_checklist.html",
	"boq_summary.html",
	"specifications.html",
	"drawings.html",
	"scc_summary.html",
	"contract_forms.html",
	"audit_summary.html",
)

PARTIAL_INCLUDES = tuple(
	name
	for name in REQUIRED_TEMPLATE_FILES
	if name.endswith(".html") and name not in ("tender_pack.html", "macros.html")
)

POC_WARNING_KEY_PHRASE = "POC Preview Only"

REQUIRED_PREVIEW_HEADINGS = (
	"Tender Cover and Identity",
	"Invitation to Tender",
	"Active STD Sections",
	"Locked STD Sections Notice",
	"Tender Data Sheet Summary",
	"Evaluation and Qualification Criteria Summary",
	"Required Bidder Forms Checklist",
	"Bills of Quantities Summary",
	"Specifications and Works Requirements Summary",
	"Drawings Summary",
	"Special Conditions of Contract Summary",
	"Contract Forms Checklist",
	"Template and Configuration Audit Summary",
)


def _templates_dir() -> Path:
	"""Resolve the std_works_poc Jinja templates folder under the app module."""
	app_root = Path(frappe.get_app_path("kentender_procurement"))
	# `frappe.get_app_path("kentender_procurement")` returns the inner module
	# folder (`<app>/<app>/`). Templates live alongside other module folders.
	return app_root / "templates" / "std_works_poc"


class TestStdWorksPocStep13Renderer(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

		self.tender = frappe.new_doc("Procurement Tender")
		self.tender.std_template = TEMPLATE_CODE
		self.tender.tender_title = "Step13 Smoke Tender"
		self.tender.tender_reference = "STEP13-SMOKE"
		self.tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
		self.tender.tender_scope = "NATIONAL"
		self.tender.insert(ignore_permissions=True)

	def _reload_tender(self):
		return frappe.get_doc("Procurement Tender", self.tender.name)

	def _populate_primary_sample(self) -> None:
		controller.load_sample_tender(self.tender.name)

	def _generate(self) -> dict:
		return controller.generate_tender_pack_preview(self.tender.name)

	# ------------------------------------------------------------------
	# STEP13-AC-001 — required template files exist
	# ------------------------------------------------------------------

	def test_step13_ac001_required_templates_exist(self) -> None:
		base = _templates_dir()
		self.assertTrue(base.is_dir(), f"STEP13-AC-001: {base} must exist")
		for name in REQUIRED_TEMPLATE_FILES:
			with self.subTest(template=name):
				self.assertTrue(
					(base / name).is_file(),
					f"STEP13-AC-001: required template {name} is missing",
				)

	# ------------------------------------------------------------------
	# STEP13-AC-002 — master template assembles every required partial
	# ------------------------------------------------------------------

	def test_step13_ac002_master_template_includes_all_partials(self) -> None:
		master_text = (_templates_dir() / "tender_pack.html").read_text(encoding="utf-8")
		self.assertIn(
			'from "templates/std_works_poc/macros.html"',
			master_text,
			"STEP13-AC-002: master template must import macros.html",
		)
		for partial in PARTIAL_INCLUDES:
			with self.subTest(partial=partial):
				self.assertIn(
					f'include "templates/std_works_poc/{partial}"',
					master_text,
					f"STEP13-AC-002: tender_pack.html must include {partial}",
				)

	# ------------------------------------------------------------------
	# Step 13 §12.1 — generate_tender_pack_preview is whitelisted
	# ------------------------------------------------------------------

	def test_generate_tender_pack_preview_is_whitelisted(self) -> None:
		self.assertTrue(hasattr(controller, "generate_tender_pack_preview"))
		fn = controller.generate_tender_pack_preview
		self.assertTrue(callable(fn))
		self.assertIn(
			fn,
			frappe.whitelisted,
			"generate_tender_pack_preview must be registered via @frappe.whitelist",
		)

	# ------------------------------------------------------------------
	# Step 13 §13 — Desk button under STD POC group
	# ------------------------------------------------------------------

	def test_step13_desk_button_present_in_sidecar_js(self) -> None:
		app_root = Path(frappe.get_app_path("kentender_procurement"))
		js_path = (
			app_root
			/ "kentender_procurement"
			/ "doctype"
			/ "procurement_tender"
			/ "procurement_tender.js"
		)
		source = js_path.read_text(encoding="utf-8")
		self.assertIn('__("Generate Tender Pack Preview")', source)
		self.assertIn('"generate_tender_pack_preview"', source)
		self.assertIn('const STD_POC_GROUP = __("STD POC");', source)

	# ------------------------------------------------------------------
	# STEP13-AC-003..AC-012 — happy path on the primary sample
	# ------------------------------------------------------------------

	def test_step13_happy_path_returns_ok_envelope(self) -> None:
		self._populate_primary_sample()
		result = self._generate()
		self.assertTrue(result["ok"])
		self.assertEqual(result["validation_status"], "Passed")
		self.assertFalse(result["blocks_generation"])
		self.assertEqual(result["status"], "Passed")
		self.assertEqual(result["tender"], self.tender.name)
		self.assertGreaterEqual(result["required_form_count"], 1)
		self.assertEqual(result["required_form_count"], 15)
		self.assertTrue(result["configuration_hash"])
		self.assertEqual(result["message"], "Tender-pack preview generated.")

	def test_step13_happy_path_persists_status_and_html(self) -> None:
		self._populate_primary_sample()
		self._generate()
		tender = self._reload_tender()
		self.assertEqual(tender.tender_status, "Tender Pack Generated")
		self.assertEqual(tender.validation_status, "Passed")
		self.assertIsNotNone(tender.last_generated_at)
		self.assertTrue(tender.generated_tender_pack_html)
		self.assertIn("<div class=\"std-poc-preview\">", tender.generated_tender_pack_html)

	def test_step13_ac003_poc_warning_present_at_top(self) -> None:
		self._populate_primary_sample()
		self._generate()
		html = self._reload_tender().generated_tender_pack_html
		warning_index = html.find(POC_WARNING_KEY_PHRASE)
		title_index = html.find("STD-WORKS-POC Tender Pack Preview")
		self.assertGreaterEqual(
			warning_index,
			0,
			"STEP13-AC-003: POC warning text must be present",
		)
		self.assertLess(
			warning_index,
			title_index,
			"STEP13-AC-003: POC warning must appear before the main preview title",
		)

	def test_step13_ac004_to_ac011_required_section_headings_present(self) -> None:
		self._populate_primary_sample()
		self._generate()
		html = self._reload_tender().generated_tender_pack_html
		for heading in REQUIRED_PREVIEW_HEADINGS:
			with self.subTest(heading=heading):
				self.assertIn(
					heading,
					html,
					f"STEP13-AC: required heading missing — {heading}",
				)

	def test_step13_ac004_tender_identity_values_rendered(self) -> None:
		self._populate_primary_sample()
		self._generate()
		html = self._reload_tender().generated_tender_pack_html
		self.assertIn("CGK/WKS/OT/001/2026", html)
		self.assertIn("County Government of Kisiwa", html)
		self.assertIn(TEMPLATE_CODE, html)

	def test_step13_ac012_audit_summary_carries_hashes_and_status(self) -> None:
		self._populate_primary_sample()
		result = self._generate()
		html = self._reload_tender().generated_tender_pack_html

		# Package + configuration hashes appear in <code>...</code> within audit_summary.
		self.assertIn("Package Hash", html)
		self.assertIn("Configuration Hash", html)
		self.assertIn(result["configuration_hash"], html)
		self.assertIn("Validation Status", html)

	def test_step13_ac008_required_forms_checklist_lists_all_active_forms(self) -> None:
		self._populate_primary_sample()
		self._generate()
		html = self._reload_tender().generated_tender_pack_html
		# Spot-check three representative forms across display groups.
		for form_code in (
			"FORM_OF_TENDER",
			"FORM_TECHNICAL_PROPOSAL",
			"FORM_PERFORMANCE_SECURITY",
		):
			with self.subTest(form_code=form_code):
				self.assertIn(form_code, html)

	def test_step13_ac009_boq_summary_renders_lot_and_row_counts(self) -> None:
		self._populate_primary_sample()
		self._generate()
		html = self._reload_tender().generated_tender_pack_html
		self.assertIn("Bills of Quantities Summary", html)
		self.assertIn("BoQ Row Count", html)
		self.assertIn("representative sample structured data", html.lower())
		self.assertIn("LOT-001", html)
		self.assertIn("LOT-002", html)
		self.assertIn("BQ-001", html)
		self.assertIn("BQ-009", html)

	def test_step13_ac011_contract_forms_filters_to_security_or_signature(self) -> None:
		self._populate_primary_sample()
		self._generate()
		html = self._reload_tender().generated_tender_pack_html
		self.assertIn("Contract Forms Checklist", html)
		self.assertIn("FORM_PERFORMANCE_SECURITY", html)
		# Award/contract generation should be flagged as outside POC scope.
		self.assertIn("outside the scope of this POC", html)

	# ------------------------------------------------------------------
	# STEP13-AC-013 — blocker path refuses to render
	# ------------------------------------------------------------------

	def test_step13_ac013_blocker_path_skips_html_render(self) -> None:
		controller.load_sample_variant(
			self.tender.name, variant_code="VARIANT-MISSING-SITE-VISIT-DATE"
		)
		# Pre-condition: HTML field empty before generation.
		pre = self._reload_tender()
		self.assertFalse(pre.generated_tender_pack_html)

		result = self._generate()
		self.assertFalse(result["ok"])
		self.assertTrue(result["blocks_generation"])
		self.assertEqual(result["validation_status"], "Blocked")
		self.assertGreaterEqual(result["message_count"], 1)
		self.assertNotIn("required_form_count", result)

		tender = self._reload_tender()
		self.assertEqual(tender.tender_status, "Validation Failed")
		self.assertEqual(tender.validation_status, "Blocked")
		self.assertFalse(
			tender.generated_tender_pack_html,
			"STEP13-AC-013: blocked generation must not write HTML",
		)
		self.assertGreaterEqual(len(tender.validation_messages), 1)

	# ------------------------------------------------------------------
	# Step 13 §14 — rendering safety
	# ------------------------------------------------------------------

	def test_step13_renderer_omits_unsafe_payload_blobs(self) -> None:
		self._populate_primary_sample()
		self._generate()
		html = self._reload_tender().generated_tender_pack_html

		# §14: no script execution, no PDF tooling, no external script tags.
		self.assertNotIn("<script", html)
		self.assertNotIn("wkhtmltopdf", html)

		# §14: package_json blob and full STD legal text are not embedded.
		self.assertNotIn("\"package_json\":", html)

	# ------------------------------------------------------------------
	# Step 13 §6 — boundary checks
	# ------------------------------------------------------------------

	def test_step13_boundary_no_pdf_or_print_format_emitted(self) -> None:
		self._populate_primary_sample()
		self._generate()
		html = self._reload_tender().generated_tender_pack_html
		for marker in ("<!DOCTYPE", "wkhtmltopdf", "Print Format"):
			with self.subTest(marker=marker):
				self.assertNotIn(marker, html)

	# ------------------------------------------------------------------
	# Idempotency — second run on same configuration yields stable HTML
	# (modulo timestamps + audit.generated_at)
	# ------------------------------------------------------------------

	def test_step13_idempotency_modulo_timestamps(self) -> None:
		self._populate_primary_sample()
		first = self._generate()
		html_first = self._reload_tender().generated_tender_pack_html

		# Second invocation — same configuration; configuration_hash must be stable.
		second = self._generate()
		html_second = self._reload_tender().generated_tender_pack_html

		self.assertEqual(first["configuration_hash"], second["configuration_hash"])
		self.assertEqual(first["required_form_count"], second["required_form_count"])
		self.assertEqual(first["validation_status"], second["validation_status"])

		# Strip the dynamic Last Generated At cell before comparing.
		def _strip_dynamic(html: str) -> str:
			marker = "<th>Last Generated At</th>"
			idx = html.find(marker)
			if idx == -1:
				return html
			end = html.find("</tr>", idx)
			return html[:idx] + html[end:] if end != -1 else html[:idx]

		self.assertEqual(_strip_dynamic(html_first), _strip_dynamic(html_second))

	# ------------------------------------------------------------------
	# Engine reuse — controller does not duplicate render-context logic
	# ------------------------------------------------------------------

	def test_step13_controller_uses_engine_render_context_keys(self) -> None:
		self._populate_primary_sample()
		tender = self._reload_tender()
		template = engine.load_template(tender.std_template)
		import json as _json

		config = _json.loads(tender.configuration_json)
		validation_result = engine.validate_config(template, config)
		required_forms = engine.resolve_required_forms(
			template, config, validation_result=validation_result
		)
		ctx = engine.build_render_context(
			template,
			config,
			lots=[row.as_dict() for row in tender.lots],
			boq_items=[row.as_dict() for row in tender.boq_items],
			validation_result=validation_result,
			required_forms=required_forms,
		)
		for key in (
			"template",
			"manifest",
			"configuration",
			"active_sections",
			"lots",
			"boq_items",
			"required_forms",
			"validation",
			"audit",
		):
			with self.subTest(context_key=key):
				self.assertIn(key, ctx)
