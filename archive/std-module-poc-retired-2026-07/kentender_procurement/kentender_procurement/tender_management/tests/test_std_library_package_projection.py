# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB — package projection + library display metadata backfill tests."""

from __future__ import annotations

from types import SimpleNamespace

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from kentender_procurement.tender_management.services.std_library_package_projection import (
	backfill_std_template_library_display_metadata,
	format_procurement_method_profile,
	parse_package_json,
	project_advanced_section_content,
	project_source_mappings,
	raw_package_json_text,
	resolve_procurement_methods,
	resolve_template_title,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	load_template_package,
)


class TestStdLibraryPackageProjectionUnit(UnitTestCase):
	def test_resolve_template_title_from_manifest_source_document(self) -> None:
		doc = SimpleNamespace(template_code=TEMPLATE_CODE, template_name="Fallback Name")
		package = load_template_package()
		title = resolve_template_title(doc, package)
		self.assertIn("Standard Tender Document", title)
		self.assertIn("Building", title)

	def test_resolve_procurement_methods_from_manifest(self) -> None:
		doc = SimpleNamespace(procurement_method_profile="")
		package = load_template_package()
		methods = resolve_procurement_methods(doc, package)
		self.assertIn("Open Competitive Tendering", methods)
		self.assertIn("Restricted Competitive Tendering", methods)
		self.assertEqual(
			format_procurement_method_profile(methods),
			"Open Competitive Tendering, Restricted Competitive Tendering",
		)

	def test_project_legacy_advanced_sections_from_works_poc_package(self) -> None:
		package = load_template_package()
		payload = project_advanced_section_content(
			{
				"manifest": package["manifest"],
				"sections": package["sections"],
				"fields": package["fields"],
				"rules": package["rules"],
				"forms": package["forms"],
				"render_map": package["render_map"],
			}
		)
		self.assertGreaterEqual(len(payload["sections_clauses"]["rows"]), 10)
		self.assertGreaterEqual(len(payload["parameters"]["rows"]), 5)
		self.assertGreaterEqual(len(payload["forms"]["rows"]), 5)
		self.assertGreaterEqual(len(payload["readiness_rules"]["rows"]), 1)
		self.assertTrue(payload["sections_clauses"]["rows"][0].get("code"))

	def test_raw_package_json_text_truncates_when_needed(self) -> None:
		package = {"manifest": {"template_code": "X"}, "blob": "x" * 200_000}
		text, truncated = raw_package_json_text(package, max_chars=1000)
		self.assertTrue(truncated)
		self.assertLessEqual(len(text), 1100)

	def test_project_source_mappings_keeps_fallback_rows(self) -> None:
		fallback = [
			{
				"source": "Demo",
				"target_code": "DSM",
				"target_label": "Submission Requirements (DSM)",
				"generated_element": "submission_requirements.deadline",
				"mandatory": "Yes",
				"status": "Valid",
				"last_validated": "2026-05-08",
			}
		]
		out = project_source_mappings({"render_map": {"render_sections": []}}, fallback_rows=fallback)
		self.assertGreaterEqual(len(out["rows"]), 1)
		labels = {t["label"] for t in out["targets"]}
		self.assertIn("Submission Requirements (DSM)", labels)


class TestStdLibraryPackageProjectionIntegration(IntegrationTestCase):
	def test_backfill_updates_works_poc_display_metadata(self) -> None:
		if not frappe.db.exists("STD Template", TEMPLATE_CODE):
			self.skipTest("WORKS POC template not seeded")

		doc = frappe.get_doc("STD Template", TEMPLATE_CODE)
		doc.template_title = ""
		doc.procurement_method_profile = ""
		doc.flags.skip_std_template_guards = True
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		result = backfill_std_template_library_display_metadata(TEMPLATE_CODE)
		self.assertTrue(result.get("ok"))
		self.assertIn(TEMPLATE_CODE, result.get("updated") or [])

		doc.reload()
		self.assertTrue((doc.template_title or "").strip())
		self.assertIn("Open Competitive Tendering", doc.procurement_method_profile or "")
		methods = resolve_procurement_methods(doc, parse_package_json(doc.package_json))
		self.assertGreaterEqual(len(methods), 1)

	def test_works_poc_detail_projects_package_sections(self) -> None:
		if not frappe.db.exists("STD Template", TEMPLATE_CODE):
			self.skipTest("WORKS POC template not seeded")
		from kentender_procurement.tender_management.api.std_library_templates import (
			get_std_library_template_detail,
		)

		out = get_std_library_template_detail(TEMPLATE_CODE)
		self.assertTrue(out.get("ok"))
		detail = out.get("detail") or {}
		self.assertIn("Building", detail.get("title") or "")
		methods = (detail.get("summary") or {}).get("supported_use", {}).get("methods") or []
		self.assertGreaterEqual(len(methods), 1)
		sections = {
			s.get("key"): s for s in (detail.get("advanced") or {}).get("sections") or [] if isinstance(s, dict)
		}
		self.assertGreaterEqual(len(sections.get("sections_clauses", {}).get("rows") or []), 5)
		self.assertGreaterEqual(len((detail.get("advanced") or {}).get("raw_package", {}).get("json_text") or ""), 100)
