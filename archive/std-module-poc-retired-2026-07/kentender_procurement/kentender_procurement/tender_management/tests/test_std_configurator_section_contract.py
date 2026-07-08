# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0230 — configurator section service/API contract tests.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_configurator_section_contract
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api import std_configurator as cfg_api
from kentender_procurement.tender_management.services import std_configurator_service as svc
from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_config_section_schema import (
	expand_section,
	normalize_section,
	section_default,
	ui_fixture_std_config,
)


def _new_cfg_test_template(template_code: str) -> str:
	doc = frappe.new_doc("STD Template")
	doc.template_code = template_code
	doc.template_name = f"STD-CFG-0230 {template_code}"
	doc.template_short_name = template_code[:12]
	doc.template_title = f"Configurator Test {template_code}"
	doc.authority = "Test Authority"
	doc.country = "KE"
	doc.procurement_category = "WORKS"
	doc.template_family = "Works"
	doc.version_label = "1.0"
	doc.template_version = "1.0"
	doc.package_version = "1"
	doc.source_authority = "Test Authority"
	doc.package_json = json.dumps({"std_config": {}}, ensure_ascii=False)
	doc.package_hash = gov.compute_std_package_hash({"std_config": {}})
	doc.package_hash_algorithm = gov.HASH_ALGORITHM
	doc.canonicalization_version = gov.CANONICALIZATION_VERSION
	doc.lifecycle_status = gov.STATUS_IMPORTED
	doc.latest_validation_status = gov.VALIDATION_NOT_RUN
	doc.critical_finding_count = 0
	doc.warning_finding_count = 0
	doc.info_finding_count = 0
	doc.validation_is_current = 0
	doc.is_governed_version = 1
	doc.tender_usage_count = 0
	doc.locked_due_to_usage = 0
	doc.mutation_blocked = 0
	doc.delete_blocked = 1
	doc.payload_locked = 0
	doc.is_suspended = 0
	doc.is_historical = 0
	doc.approval_override_used = 0
	doc.is_default_active_version = 0
	doc.allowed_for_import = 1
	doc.allowed_for_tender_creation = 0
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return template_code


class TestStdConfiguratorSectionContractImports(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		if not frappe.db.exists("Page", "std-configurator"):
			page = frappe.new_doc("Page")
			page.page_name = "std-configurator"
			page.title = "STD Configurator"
			page.module = "Kentender Procurement"
			page.standard = "Yes"
			page.insert(ignore_permissions=True)
			frappe.db.commit()

	def test_page_related_imports(self) -> None:
		self.assertTrue(frappe.db.exists("Page", "std-configurator"))
		self.assertEqual(svc.STD_CONFIG_SECTIONS[0], "metadata")
		self.assertIn("overview", svc.TAB_SLUGS)
		self.assertTrue(hasattr(cfg_api, "get_std_configurator_context"))
		self.assertTrue(hasattr(cfg_api, "save_std_configurator_section"))
		self.assertTrue(hasattr(cfg_api, "run_std_configurator_applicability_test"))


class TestStdConfiguratorSectionRoundTrip(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"CFG0230-{frappe.generate_hash(length=10)}"
		_new_cfg_test_template(self._code)

	def tearDown(self) -> None:
		if frappe.db.exists("STD Template", self._code):
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
			frappe.db.commit()
		frappe.set_user("Administrator")

	def _assert_round_trip(self, section: str, payload: dict) -> None:
		saved = svc.save_section(self._code, section, payload)
		self.assertTrue(saved.get("ok"))
		normalized = normalize_section(section, payload)
		self.assertEqual(saved["data"], normalized)

		got = svc.get_section(self._code, section)
		self.assertTrue(got.get("ok"))
		self.assertEqual(got["data"], expand_section(section, normalized))

	def test_metadata_and_applicability_round_trip(self) -> None:
		metadata = {
			"title": "Works Building STD",
			"short_title": "Works STD",
			"description": "Test metadata section",
			"authority": "PPRA",
			"procurement_category": "WORKS",
			"funding_sources": {"gok_exchequer": True},
		}
		applicability = {
			"procurement_category": "WORKS",
			"procurement_method": "Open",
			"rules": [
				{
					"code": "RULE-001",
					"name": "Open tender works",
					"procurement_method": "Open",
					"active": True,
				}
			],
		}
		self._assert_round_trip("metadata", metadata)
		self._assert_round_trip("applicability", applicability)

		ctx = svc.get_configurator_context(self._code)
		self.assertTrue(ctx.get("editable"))
		self.assertEqual(ctx["std_config"]["metadata"]["title"], metadata["title"])
		self.assertGreaterEqual(ctx["std_config"]["applicability"]["count"], 1)

	def test_all_mocked_sections_round_trip(self) -> None:
		fixture = ui_fixture_std_config()
		for section in (
			"tender_fields",
			"supplier_requirements",
			"forms_and_attachments",
			"evaluation_setup",
			"contract_terms",
			"rules",
			"validations",
		):
			self._assert_round_trip(section, fixture[section])

	def test_applicability_simulator(self) -> None:
		fixture = ui_fixture_std_config()["applicability"]
		svc.save_section(self._code, "applicability", fixture)
		result = svc.run_applicability_test(self._code, fixture.get("test_case"))
		self.assertTrue(result.get("ok"))
		self.assertTrue(result.get("applies"))

		api_result = cfg_api.run_std_configurator_applicability_test(
			self._code, json.dumps(fixture.get("test_case"))
		)
		self.assertTrue(api_result.get("applies"))


class TestStdConfiguratorSectionDefaults(IntegrationTestCase):
	def test_section_defaults_cover_all_sections(self) -> None:
		for section in svc.STD_CONFIG_SECTIONS:
			default = section_default(section)
			self.assertIsInstance(default, dict)
			got = expand_section(section, {})
			for key in default:
				self.assertIn(key, got)


class TestStdConfiguratorProtectedSave(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"CFG0230-ACT-{frappe.generate_hash(length=8)}"
		_new_cfg_test_template(self._code)
		frappe.db.set_value("STD Template", self._code, "lifecycle_status", gov.STATUS_ACTIVE)
		frappe.db.commit()

	def tearDown(self) -> None:
		if frappe.db.exists("STD Template", self._code):
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
			frappe.db.commit()
		frappe.set_user("Administrator")

	def test_active_template_save_blocked(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			svc.save_section(self._code, "metadata", {"title": "Blocked"})


class TestStdConfiguratorTechnicalJsonRoleGate(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"CFG0230-TECH-{frappe.generate_hash(length=8)}"
		_new_cfg_test_template(self._code)
		self._user = f"cfg0230-tech-{frappe.generate_hash(length=6)}@example.com"
		if not frappe.db.exists("User", self._user):
			user = frappe.new_doc("User")
			user.email = self._user
			user.first_name = "CFG"
			user.last_name = "Reader"
			user.send_welcome_email = 0
			user.new_password = "test-pass-123"
			user.insert(ignore_permissions=True)
			frappe.db.commit()

	def tearDown(self) -> None:
		if frappe.db.exists("STD Template", self._code):
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
		if frappe.db.exists("User", self._user):
			frappe.delete_doc("User", self._user, force=True, ignore_permissions=True)
		frappe.db.commit()
		frappe.set_user("Administrator")

	def test_technical_json_hidden_for_unprivileged_role(self) -> None:
		frappe.set_user(self._user)
		with self.assertRaises(frappe.PermissionError):
			svc.get_technical_json(self._code)


class TestStdConfiguratorTechnicalJsonSave(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"CFG0230-SAVE-{frappe.generate_hash(length=8)}"
		_new_cfg_test_template(self._code)
		self._viewer = f"cfg0230-view-{frappe.generate_hash(length=6)}@example.com"
		if frappe.db.exists("User", self._viewer):
			frappe.delete_doc("User", self._viewer, force=True, ignore_permissions=True)
			frappe.db.commit()
		user = frappe.new_doc("User")
		user.email = self._viewer
		user.first_name = "CFG"
		user.last_name = "Viewer"
		user.send_welcome_email = 0
		user.new_password = "test-pass-123"
		user.insert(ignore_permissions=True)
		user.add_roles("STD Template Reviewer")
		frappe.db.commit()

	def tearDown(self) -> None:
		if frappe.db.exists("STD Template", self._code):
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
		if frappe.db.exists("User", self._viewer):
			frappe.delete_doc("User", self._viewer, force=True, ignore_permissions=True)
		frappe.db.commit()
		frappe.set_user("Administrator")

	def test_save_technical_json_round_trip_on_draft(self) -> None:
		payload = svc.get_technical_json(self._code)
		package = dict(payload.get("package_json") or {})
		std_config = package.setdefault("std_config", {})
		metadata = dict(std_config.get("metadata") or section_default("metadata"))
		metadata["title"] = "Technical JSON Save Test"
		std_config["metadata"] = metadata
		package["std_config"] = std_config
		result = svc.save_technical_json(self._code, package)
		self.assertTrue(result.get("ok"))
		reloaded = svc.get_technical_json(self._code)
		meta = (reloaded.get("package_json") or {}).get("std_config", {}).get("metadata", {})
		self.assertEqual(meta.get("title"), "Technical JSON Save Test")

	def test_save_technical_json_blocked_for_view_only_role(self) -> None:
		frappe.set_user(self._viewer)
		with self.assertRaises(frappe.PermissionError):
			svc.save_technical_json(self._code, {"std_config": {}})

	def test_save_technical_json_rejects_invalid_json_shape(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			svc.save_technical_json(self._code, ["not", "an", "object"])

	def test_save_technical_json_blocked_on_active_lifecycle(self) -> None:
		frappe.db.set_value("STD Template", self._code, "lifecycle_status", gov.STATUS_ACTIVE)
		frappe.db.commit()
		with self.assertRaises(frappe.ValidationError):
			svc.save_technical_json(self._code, {"std_config": {}})

	def test_context_exposes_can_edit_technical_json(self) -> None:
		ctx = svc.get_configurator_context(self._code)
		self.assertTrue(ctx.get("can_view_technical_json"))
		self.assertTrue(ctx.get("can_edit_technical_json"))
		tech_tab = next(t for t in ctx.get("tabs") or [] if t.get("slug") == "technical-json")
		self.assertFalse(tech_tab.get("read_only"))
